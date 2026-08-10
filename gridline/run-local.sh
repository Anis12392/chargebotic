#!/usr/bin/env bash
#
# Run GridLine AI without Docker.
#
# This is the path verified end to end during development: Postgres + PostGIS
# on the host, the API on :8000, the PWA on :3000, photos on local disk. No
# S3, no API keys, no container runtime.
#
# Usage:  ./run-local.sh          start everything
#         ./run-local.sh stop     stop the API and web servers
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
DB_URL="postgresql+asyncpg://gridline:gridline@127.0.0.1:5432/gridline"
LOG_DIR="$ROOT/.logs"

note() { printf '\033[36m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

stop() {
  note "Stopping API and web servers"
  # Match on the exact commands this script starts, so nothing else is touched.
  pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
  pkill -f "next start -p 3000" 2>/dev/null || true
  note "Stopped. Postgres was left running."
  exit 0
}

[[ "${1:-}" == "stop" ]] && stop

# Any previous run is replaced, not duplicated. A second uvicorn on a held port
# just dies, leaving the old one serving stale configuration — which looks
# exactly like "my new API key did nothing".
pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
pkill -f "next start -p 3000" 2>/dev/null || true
sleep 1

# --- Prerequisites -----------------------------------------------------------
command -v python3 >/dev/null || fail "python3 is required"
command -v node    >/dev/null || fail "node 20+ is required"
command -v psql    >/dev/null || fail "the postgresql client is required"

if ! pg_isready -q 2>/dev/null; then
  fail "PostgreSQL is not running.
  macOS:  brew install postgresql@16 postgis && brew services start postgresql@16
  Ubuntu: sudo apt install postgresql-16 postgresql-16-postgis-3 && sudo pg_ctlcluster 16 main start"
fi

# --- Database ----------------------------------------------------------------
# How you reach Postgres as an admin differs by platform: Homebrew makes your
# own account the superuser, Debian/Ubuntu uses peer auth on the `postgres`
# system user, and a container may allow -U postgres directly. Rather than
# assume, find one that actually works.
PG_ADMIN=""
for candidate in "psql -U postgres" "psql -d postgres" "sudo -n -u postgres psql"; do
  if $candidate -tAc "SELECT 1" >/dev/null 2>&1; then
    PG_ADMIN="$candidate"
    break
  fi
done
[[ -n "$PG_ADMIN" ]] || fail "could not connect to Postgres as an administrator.
  Tried: psql -U postgres | psql -d postgres | sudo -u postgres psql
  Connect manually and run:
    CREATE ROLE gridline LOGIN PASSWORD 'gridline' SUPERUSER;
    CREATE DATABASE gridline OWNER gridline;
    \\\\c gridline
    CREATE EXTENSION IF NOT EXISTS postgis;
  then re-run this script."

note "Preparing the gridline database (admin via: $PG_ADMIN)"
if ! $PG_ADMIN -tAc "SELECT 1 FROM pg_roles WHERE rolname='gridline'" 2>/dev/null | grep -q 1; then
  $PG_ADMIN -qc "CREATE ROLE gridline LOGIN PASSWORD 'gridline' SUPERUSER;" \
    || fail "could not create the gridline role"
fi
if ! $PG_ADMIN -tAc "SELECT 1 FROM pg_database WHERE datname='gridline'" 2>/dev/null | grep -q 1; then
  $PG_ADMIN -qc "CREATE DATABASE gridline OWNER gridline;" \
    || fail "could not create the gridline database"
fi
$PG_ADMIN -d gridline -qc "CREATE EXTENSION IF NOT EXISTS postgis;" \
  || fail "PostGIS is not available for this PostgreSQL version.
  macOS:  brew install postgis
  Ubuntu: sudo apt install postgresql-16-postgis-3"

# --- Backend -----------------------------------------------------------------
note "Installing backend dependencies"
cd "$BACKEND"
[[ -d .venv ]] || python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

note "Applying migrations"
DATABASE_URL="$DB_URL" ./.venv/bin/alembic upgrade head

mkdir -p "$LOG_DIR"
note "Starting the API on :8000"
DATABASE_URL="$DB_URL" \
CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}" \
LOCAL_STORAGE_DIR="$BACKEND/.storage" \
OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
VISION_MODEL="${VISION_MODEL:-gpt-4o}" \
  nohup ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  > "$LOG_DIR/backend.log" 2>&1 &

# --- Frontend ----------------------------------------------------------------
note "Installing frontend dependencies"
cd "$FRONTEND"
[[ -d node_modules ]] || npm install --no-audit --no-fund

note "Building the web app"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run build >/dev/null

note "Starting the web app on :3000"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 \
  nohup npx next start -p 3000 > "$LOG_DIR/frontend.log" 2>&1 &

# --- Wait --------------------------------------------------------------------
note "Waiting for both servers"
for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1 \
     && curl -sf http://localhost:3000 >/dev/null 2>&1; then
    echo
    note "GridLine AI is up:"
    echo "      app       http://localhost:3000"
    echo "      api docs  http://localhost:8000/docs"
    echo "      logs      $LOG_DIR/"
    echo
    echo "  Vision is off (no OPENAI_API_KEY), so reports will say so and return"
    echo "  'unknown' rather than guessing. Export OPENAI_API_KEY before running"
    echo "  to enable image analysis."
    echo
    echo "  Stop with: ./run-local.sh stop"
    exit 0
  fi
  sleep 1
done

fail "servers did not come up — check $LOG_DIR/backend.log and $LOG_DIR/frontend.log"

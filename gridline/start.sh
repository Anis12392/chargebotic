#!/usr/bin/env bash
#
# Start GridLine AI.
#
#   ./start.sh              on this machine     -> http://localhost:3000
#   ./start.sh --phone      on your phone too   -> https://<random>.trycloudflare.com
#   ./start.sh --stop       shut everything down
#   ./start.sh --install-deps   brew-install PostgreSQL 16 + PostGIS (macOS)
#
# --phone matters because iOS Safari refuses the camera and GPS on a plain-HTTP
# origin. Opening your laptop's LAN address from an iPhone gives you a page with
# a dead shutter and no location. A tunnel provides a real HTTPS origin, which is
# what unlocks both.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env"
TUNNEL_LOG="$ROOT/.logs/tunnel.log"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
note() { printf '\033[36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[33m !\033[0m %s\n' "$1"; }
fail() { printf '\033[31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

PHONE=0
STOP=0
INSTALL_DEPS=0
for arg in "$@"; do
  case "$arg" in
    --phone) PHONE=1 ;;
    --stop)  STOP=1 ;;
    --install-deps) INSTALL_DEPS=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) fail "unknown option: $arg (try --help)" ;;
  esac
done

USE_DOCKER=0
DOCKER_STATE="absent"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    USE_DOCKER=1
    DOCKER_STATE="running"
  else
    DOCKER_STATE="installed-but-stopped"
  fi
fi

# --- Stop --------------------------------------------------------------------
if [[ "$STOP" == "1" ]]; then
  note "Stopping the tunnel"
  pkill -f "cloudflared tunnel --url http://localhost:3000" 2>/dev/null || true
  if [[ "$USE_DOCKER" == "1" ]]; then
    note "Stopping containers"
    docker compose down 2>/dev/null || true
  fi
  ./run-local.sh stop 2>/dev/null || true
  note "Stopped."
  exit 0
fi

# --- Optional dependency install ---------------------------------------------
if [[ "$INSTALL_DEPS" == "1" ]]; then
  command -v brew >/dev/null 2>&1 \
    || fail "--install-deps needs Homebrew. Install it from https://brew.sh first."
  note "Installing PostgreSQL 16 and PostGIS via Homebrew"
  brew install postgresql@16 postgis
  brew services start postgresql@16
  note "Waiting for the server to accept connections"
  PGBIN="$(brew --prefix postgresql@16)/bin"
  export PATH="$PGBIN:$PATH"
  for _ in $(seq 1 30); do pg_isready -q 2>/dev/null && break; sleep 1; done
  pg_isready -q 2>/dev/null || fail "PostgreSQL did not start. Try: brew services restart postgresql@16"
  note "Done. Continuing."
fi

# --- Vision key --------------------------------------------------------------
# Ask once, store in .env. Without it the app runs but every report reads
# "Undetermined at 0% confidence", which looks broken even though it isn't.
if [[ -f "$ENV_FILE" ]] && grep -qE '^OPENAI_API_KEY=.+' "$ENV_FILE"; then
  note "Using the OpenAI key already in .env"
elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
  note "Using OPENAI_API_KEY from your shell"
else
  echo
  bold "Image analysis needs an OpenAI API key."
  echo "  Without one the app still runs, but every report will say"
  echo "  \"Undetermined, 0% confidence\" because it refuses to guess."
  echo "  Get one at https://platform.openai.com/api-keys — or press Enter to skip."
  echo
  printf '  OpenAI API key (input hidden): '
  read -rs TYPED_KEY || TYPED_KEY=""
  echo
  if [[ -n "$TYPED_KEY" ]]; then
    touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
    # Replace any existing line rather than appending a second one.
    if grep -q '^OPENAI_API_KEY=' "$ENV_FILE" 2>/dev/null; then
      grep -v '^OPENAI_API_KEY=' "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
    fi
    printf 'OPENAI_API_KEY=%s\n' "$TYPED_KEY" >> "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    note "Saved to .env (git-ignored, permissions 600)"
  else
    warn "No key — reports will read \"Undetermined\". Re-run ./start.sh to add one later."
  fi
fi
[[ -f "$ENV_FILE" ]] && set -a && . "$ENV_FILE" && set +a || true

# --- Bring the stack up ------------------------------------------------------
mkdir -p "$ROOT/.logs"

if [[ "$USE_DOCKER" == "1" ]]; then
  note "Starting with Docker (first run pulls images and builds — a few minutes)"
  # --force-recreate so a newly added OPENAI_API_KEY actually reaches the
  # container instead of an already-running one keeping the old environment.
  docker compose up --build -d --force-recreate
else
  if [[ "$DOCKER_STATE" == "installed-but-stopped" ]]; then
    warn "Docker is installed but not running."
    warn "Opening Docker Desktop and re-running this script is the easiest path —"
    warn "it needs nothing else installed. Trying the local Postgres path meanwhile."
  else
    warn "Docker is not installed — using the local Postgres path."
  fi
  ./run-local.sh
fi

note "Waiting for the app"
for _ in $(seq 1 180); do
  if curl -sf http://localhost:3000 >/dev/null 2>&1 \
     && curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -sf http://localhost:3000 >/dev/null 2>&1 \
  || fail "the app did not come up. Logs: docker compose logs  (or $ROOT/.logs/)"

VISION="$(curl -s http://localhost:8000/health | sed -n 's/.*"vision":"\([a-z]*\)".*/\1/p')"

echo
bold "GridLine AI is running."
echo "   On this machine:  http://localhost:3000"
echo "   API docs:         http://localhost:8000/docs"
if [[ "$VISION" == "ok" ]]; then
  echo "   Image analysis:   on"
else
  echo "   Image analysis:   off — reports will read \"Undetermined\""
fi

# --- Phone ------------------------------------------------------------------
if [[ "$PHONE" == "1" ]]; then
  if ! command -v cloudflared >/dev/null 2>&1; then
    echo
    fail "--phone needs cloudflared (it provides the HTTPS origin iOS requires).
  macOS:  brew install cloudflared
  Linux:  see https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  Then re-run: ./start.sh --phone"
  fi

  note "Opening an HTTPS tunnel"
  pkill -f "cloudflared tunnel --url http://localhost:3000" 2>/dev/null || true
  : > "$TUNNEL_LOG"
  nohup cloudflared tunnel --url http://localhost:3000 --no-autoupdate \
    >>"$TUNNEL_LOG" 2>&1 &

  URL=""
  for _ in $(seq 1 60); do
    URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1 || true)"
    [[ -n "$URL" ]] && break
    sleep 1
  done
  [[ -n "$URL" ]] || fail "the tunnel did not report a URL. See $TUNNEL_LOG"

  # The browser origin is now the tunnel host. The web app only ever calls its
  # own origin (/api and /media are proxied server-side), so nothing else needs
  # to know this URL — but the API's CORS list should still include it for any
  # direct calls.
  echo
  bold "On your iPhone, open:"
  echo
  printf '   \033[1;36m%s\033[0m\n' "$URL"
  echo
  if command -v qrencode >/dev/null 2>&1; then
    qrencode -t ANSIUTF8 "$URL"
  else
    echo "   (brew install qrencode to get a scannable QR code here)"
  fi
  echo
  echo "   Safari will ask for camera and location — allow both."
  echo "   Share ▸ Add to Home Screen installs it as a real app."
  echo
  warn "That URL is public while the tunnel runs. Stop it with ./start.sh --stop"
fi

echo
echo "Stop everything with:  ./start.sh --stop"

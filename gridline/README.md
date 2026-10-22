# GridLine AI

Identify overhead electrical power lines from a photograph and a GPS fix.

GridLine fuses computer vision, GPS, public GIS data and a rule-based reasoning
engine into an evidence-based engineering report. It is the data layer for
Chargebotic's long-term goal: autonomously locating, evaluating and learning the
best power lines for drone energy harvesting.

---

## The one rule

**GridLine never claims an exact voltage or amperage.**

Every figure it returns is an estimate carrying a confidence score and a
traceable evidence chain:

| Output | What it is | What it is not |
| --- | --- | --- |
| Voltage class | Weighted inference over vision + GIS + published standards | A meter reading |
| Possible nominal voltages | The set the class and the operator's construction standard both allow | A single answer |
| Current range | Conductor thermal rating × published loading factors | Current flowing in this circuit |
| Conductor | Catalogue match on estimated diameter | A confirmed conductor spec |
| Utility | Proximity-weighted OSM operator tags | A billing relationship |

`current.is_measured` is `false` unless an engineer has entered a real field
measurement through `POST /verify`. When evidence is thin, the engine returns
`voltage_class: "unknown"` with zero confidence rather than guessing the most
statistically common answer. Conflicts between GIS and imagery are surfaced as
warnings, not silently resolved.

Nothing in this system is a clearance authorisation.

---

## Quick start

```bash
cd gridline
./start.sh
```

That is the whole thing. It asks once for an OpenAI API key (optional — skip it
and the app still runs), brings up Postgres/PostGIS, the API and the web app,
and prints where to open it. Uses Docker if it is running; otherwise falls back
to a host PostgreSQL install.

```
GridLine AI is running.
   On this machine:  http://localhost:3000
   API docs:         http://localhost:8000/docs
   Image analysis:   on
```

Stop with `./start.sh --stop`.

### On a phone

```bash
./start.sh --phone
```

Prints an `https://….trycloudflare.com` URL to open in Safari or Chrome on the
handset. Allow camera and location when asked; **Share ▸ Add to Home Screen**
installs it as a real app with its own icon.

The tunnel is not a convenience — it is required. iOS Safari refuses
`getUserMedia` and high-accuracy geolocation on any non-secure origin, so
browsing to your laptop's LAN address over plain HTTP gives you a dead shutter
and no GPS fix. The tunnel supplies a genuine HTTPS origin, which is what
unlocks both. Needs `cloudflared` (`brew install cloudflared`).

That URL is public for as long as the tunnel runs. `./start.sh --stop` closes it.

### Without the key

Everything works, but each report reads **"Undetermined, 0% confidence"** with
no current range, because the engine refuses to guess from an image it could not
analyse. That is the intended degradation, not a failure — but it does mean the
app looks inert until you supply a key.

### Storage

Photos go to a local volume by default, so their URLs are relative and resolve
against whatever origin the browser used — which is what makes the phone case
work. To exercise the S3 path instead:

```bash
docker compose --profile s3 up --build
```

### Running the pieces by hand

```bash
./run-local.sh          # Postgres on the host, no containers
./run-local.sh stop
```

### Tests

```bash
cd gridline/backend  && .venv/bin/pytest -q && .venv/bin/ruff check app tests
cd gridline/frontend && npm run typecheck && npm test && npm run build
```

Frontend tests default to the Node environment; the ones needing a DOM opt in
with a `@vitest-environment jsdom` docblock.

---

## Architecture

```
 Phone (PWA)                    FastAPI                        External
┌──────────────┐   multipart   ┌──────────────────┐
│ Camera       │──────────────▶│ POST /analyze    │
│ GPS watch    │  photo +      │                  │
│ Compass      │  capture ctx  │  ┌────────────┐  │   image    ┌──────────────┐
│ IndexedDB    │               │  │  Vision    │──┼───────────▶│ OpenAI       │
│ offline queue│               │  └────────────┘  │            └──────────────┘
└──────────────┘               │        │         │
                               │  ┌────────────┐  │   lat/lon  ┌──────────────┐
                               │  │ GIS engine │──┼───────────▶│ Overpass/OSM │
                               │  └────────────┘  │            │ HIFLD / USGS │
                               │        │         │            └──────────────┘
                               │  ┌────────────┐  │
                               │  │ Inference  │  │  knowledge.py: ANSI C84.1,
                               │  │  engine    │  │  C29.1/2, NESC 235,
                               │  └────────────┘  │  ACSR catalogue, utility
                               │        │         │  construction standards
                               │  ┌────────────┐  │
                               │  │ Perch      │  │  physics.py: Ampère's law,
                               │  │  scorer    │  │  CT coupling, Strouhal
                               │  └────────────┘  │
                               └────────┬─────────┘
                                        ▼
                          PostgreSQL + PostGIS  ·  S3
```

Vision and GIS run concurrently — they are independent, and a slow Overpass day
should not serialise behind the vision call.

### Backend layout

| Module | Responsibility |
| --- | --- |
| `services/knowledge.py` | Published reference data. Nothing outside this file may introduce an engineering constant. |
| `services/physics.py` | Closed-form models: flux density, CT harvest, catenary sag, aeolian vibration. |
| `services/vision.py` | Schema-constrained vision call, sanity checks, honest null fallback. |
| `services/gis.py` | Overpass + ArcGIS feature services, Postgres-backed cache. |
| `services/inference.py` | Weighted evidence fusion → voltage class, nominals, conductor, current range. |
| `services/perch.py` | Ten-factor Perch Suitability Score with hard blockers. |
| `services/pipeline.py` | Orchestration and persistence. |
| `services/training.py` | Verification → training data and calibration reporting. |

---

## How the voltage inference works

Each candidate class accumulates weighted evidence; the winner's share of total
score, adjusted by its margin over the runner-up, becomes the confidence.

| Evidence | Weight | Source |
| --- | --- | --- |
| OSM `voltage` tag on the nearest mapped line | up to 3.2, scaled by proximity | Surveyed GIS |
| Hardware constraints (transformer, cutout, corona ring, shield wire) | 1.6 × detection confidence | Equipment voltage ratings |
| Suspension disc count | 1.0–2.0 | ANSI C29.2 |
| Structure type | 1.4 × share | Utility construction practice |
| Pin/post insulator length | 1.1 | ANSI C29.1 |
| Phase spacing | 0.8 | NESC Rule 235 |
| Pole material | 0.9 × share | Construction practice |
| Operator's construction standard | 0.10–0.15 | `UTILITY_STANDARDS` |

A total below 0.5 returns `unknown`. Some rules are near-decisive: a
pole-mounted distribution transformer bounds the primary at 34.5 kV because
those units are not manufactured above it.

Nominal voltages are then narrowed by the operator's standard. If PG&E is the
attributed operator, only PG&E's 12 kV / 17.2 kV / 21 kV primary voltages are
offered — 13.8 kV is not a live option in their territory however common it is
nationally.

## How the Perch Suitability Score works

Ten weighted factors, each 0–100 with its own confidence and written rationale:

| Factor | Weight | Factor | Weight |
| --- | --- | --- | --- |
| Magnetic field strength | 0.20 | Nearby obstacles | 0.08 |
| Harvest potential | 0.15 | Wind exposure | 0.08 |
| Safe drone approach | 0.12 | GPS quality | 0.07 |
| Line accessibility | 0.10 | Landing risk | 0.06 |
| Vegetation clearance | 0.10 | Historical success | 0.04 |

A factor with no supporting evidence scores a neutral 50 at confidence 0, so an
evidence-free span lands mid-scale rather than looking attractive. Score
confidence is capped by the voltage call it rests on.

Four conditions are hard blockers that zero the score outright: estimated
voltage above the 35 kV coupler envelope, transmission/EHV class, coupled power
below 2 W, and spacer-cable geometry with no clear conductor run.

---

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/analyze` | Multipart photo + capture context → full engineering report |
| `POST` | `/analyze/json` | Same, base64 body, for integrations |
| `GET` | `/inspection/{id}` | Stored inspection with report and verifications |
| `GET` | `/inspections` | Filterable list |
| `POST` | `/verify` | Engineer records ground truth |
| `GET` | `/map` | Nearby infrastructure and past inspections |
| `GET` | `/perch/ranking` | Best spans for harvesting |
| `GET` | `/admin/stats` | Dashboard aggregates (auth) |
| `GET` | `/admin/training-data.jsonl` | Verified examples for fine-tuning (auth) |
| `GET` | `/health`, `/ready` | Probes |

```bash
curl -X POST http://localhost:8000/analyze \
  -F photo=@pole.jpg \
  -F 'capture={"latitude":37.7749,"longitude":-122.4194,"accuracy_m":6,"heading_deg":275}'
```

The admin surface is gated by `X-Admin-Key`. With no `ADMIN_API_KEY`
configured it is open in development and **refuses every request in
production** — an unset secret must never mean "no auth" on a deployed system.

---

## Learning loop

1. An engineer records ground truth through `POST /verify`.
2. The verification is stored with a **frozen snapshot** of what the model
   predicted at that moment, so a later model change cannot rewrite history for
   the training set.
3. Verdicts are derived by comparing voltage *classes*, not exact volts —
   predicting "distribution, probably 12.47 kV" against an actual 13.2 kV is a
   correct class call and scoring it as a miss would poison the metric.
4. `/admin/training-data.jsonl` exports verified examples. `calibration_report`
   reports per-class accuracy and whether confidence separates correct from
   incorrect predictions — a model whose confidence does not separate those
   populations is uncalibrated, whatever its accuracy.

Only verified inspections are exported. Training on unverified model output is
how a system convinces itself of its own mistakes.

---

## Deployment

- `infra/k8s/base.yaml` — namespace, deployments, HPA, PDB, ingress, migration
  Job. Migrations run as a Job rather than an init container so replicas cannot
  race `alembic upgrade`.
- `.github/workflows/gridline-ci.yml` — lint, test, migration up **and down**
  against real PostGIS, typecheck, build, and container images to GHCR. CI runs
  with `VISION_ENABLED=false` and `EXTERNAL_GIS_ENABLED=false` so tests stay
  deterministic and free.

Assumes managed Postgres with PostGIS and managed object storage. Running the
database in-cluster is out of scope on purpose: the inspection record is the
only irreplaceable asset here.

---

## Known limits

- **OSM distribution coverage is sparse outside cities.** Rural captures often
  return no mapped assets, and the report says so rather than compensating.
- **The current range is a population statistic.** A circuit can be open and
  carrying nothing while the report shows a plausible range. It is labelled.
- **Dimensional estimates need a scale reference.** With no cutout, crossarm or
  disc in frame, the vision stage returns nulls and the conductor match falls
  back to the population typical of the inferred class.
- **The rate limiter is in-process.** Behind more than one replica it becomes
  per-replica; move it to Redis before scaling out.
- **HIFLD covers US transmission only.** Non-US captures rely on OSM alone.
- **The harvest model is a design-point estimate**, not a bench measurement of
  Chargebotic hardware. Every assumption ships with the number.
- **The map needs outbound access to `tile.openstreetmap.org`.** Behind a
  restrictive egress policy the basemap tiles fail and the map renders markers
  on an empty dark canvas. Markers, legend and the asset list still work.

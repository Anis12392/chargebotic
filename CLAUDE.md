# CLAUDE.md — Chargebotic repo

Read `directives/project_brief.md` FIRST every session. It is the single source of truth: product, team, deals, fundraising, roadmap.

## What this company is

Chargebotic sells expeditionary field power systems that draw energy from live power lines.
- **Kestrel**: portable charging system ($65K). An aircraft perches on a power line, Magline harvests energy by induction from the magnetic field, power flows down a tether to a box on the ground that powers equipment (C2, radios, EW, sensors, batteries).
- **Spark E**: aircraft that lands on a power line, recharges itself, flies on.
- **Software**: telemetry, line health, metering.

## Hard rules for ALL content (site, deck, docs, posts)

1. **Never sell with the word "drone."** Headlines and product copy say "expeditionary field power platform" / "Kestrel platform" / "the box." "Drone" appears only for machines Chargebotic powers, and for the Spark E category name (self-charging drone).
2. **Proof before promise.** Every claim: demonstrated fact first, then dated next step. Current truth: lab-validated harvesting (50 to 150 W), piloted flight (no autonomy claims), JIFX demo. Never state targets as achievements.
3. **Tone: sober, factual, austere** (Anduril/Hendrick register). No emoji. No em/en dashes. No startup fluff ("thrilled to announce", "revolutionary").
4. **Additive positioning.** We integrate alongside generators and solar, we do not replace them. Competitors are framed as weather-dependent power and fuel-dependent power, never other drone companies.
5. **Public narrative leads with logistics and lives saved** (1 fuel convoy in 24 = casualty). Stealth or offensive use cases stay in NDA conversations.

## Website (`website/`)

- Static site. Preview locally: `python3 -m http.server 4321 --directory website` then open http://localhost:4321
- Pages: index.html (main), whitepaper.html, map.html (grid globe). 3D hero: drone3d.js. Scrub frames: frames/
- Deploy: `vercel --prod` from `website/` — auto-aliases powerbird.io. chargebotic.com sits on a separate Vercel project: after deploying, run `vercel alias set <deployment-url> chargebotic.com` (and www).
- ALWAYS `git pull` before working and push after. Deploys come from local files, so a stale local copy erases the other person's work on the live site.

## Style

Match the existing austere design: dark #0a0a0b, brand orange #e8490a, Inter, thin hairlines, no gradients, no rounded-card salad. Copy is short declarative sentences.

# Chargebotic — Project Index

> Universal energy infrastructure for autonomous robots.
> Pre-seed | San Francisco | 2 co-founders

## Project Structure

```
chargebotic/
├── research/
│   ├── market-sizing.md            # TAM/SAM/SOM, market size by vertical
│   ├── concept-validation.md       # Rail-mounted arm analysis, how robots charge today
│   ├── charging-power-analysis.md  # 100W vs market standard, power roadmap
│   └── ip-strategy.md             # Patents, trade secrets, free resources SF
├── onepager/
│   ├── chargebotic-onepager.pdf    # One-pager PDF (A4, printable)
│   └── export_onepager.py         # Script to regenerate PDF
├── website/
│   ├── chargebotic-one-pager.html  # Main pitch page
│   ├── chargebotic-built.html      # What we've built
│   ├── chargebotic-story.html      # Our story
│   ├── chargebotic-advisors.html   # Advisory board
│   └── chargebotic-timeline.html   # Product roadmap
├── gridline/                       # GridLine AI — power line identification platform
│   ├── backend/                    # FastAPI + PostGIS + vision/GIS/inference engines
│   ├── frontend/                   # Next.js mobile-first PWA
│   ├── infra/k8s/                  # Kubernetes manifests
│   └── README.md                   # Architecture, methodology, API
├── notion-workspace.md             # Template to import into Notion
├── SPARK chargebotic.pdf           # Original spark deck
└── README.md                       # This file
```

## Quick Links

- **Notion workspace template**: `notion-workspace.md` → import into Notion
- **Live site**: https://chargebotic.com
- **One-pager PDF**: `onepager/chargebotic-onepager.pdf`
- **GridLine AI**: `gridline/README.md` → `cd gridline && docker compose up`

## GridLine AI

Photograph an overhead line, get an evidence-based engineering report: voltage
class, plausible nominal voltages, conductor, operating current *range*, utility
attribution and a 0–100 Perch Suitability Score for autonomous energy
harvesting. Computer vision plus OpenStreetMap/HIFLD/USGS plus a rule engine
built on ANSI C84.1, ANSI C29, NESC and published conductor tables.

It never claims an exact voltage or amperage — every figure carries a
confidence score and a traceable evidence chain, and thin evidence returns
"unknown" rather than a guess. This is the data layer for locating and ranking
the best lines for Chargebotic drones to harvest from.

## Current Phase: Research → Prototype

**Priority #1**: File provisional patent ($65) — this week
**Priority #2**: Upgrade 100W → 500W prototype — this month
**Priority #3**: 5 customer interviews (warehouse operators) — this month

# Chargebotic Inc — Master Project Brief

> **Read this first at the start of every session.**  
> Last updated: 2026-06-23

---

## Company

**Name:** Chargebotic Inc  
**Domain:** chargebotic.com  
**Program:** Nvidia Inception, Founder Inc SF  
**Bank:** Rho  
**Legal:** Clerky (SAFEs, incorporation)

---

## Product (UPDATED Jul 24 2026 — two products + software)

**Narrative frame:** range is the key constraint for every electric machine; Tesla's key innovation was the charging network, not the car. Chargebotic = the charging network for machines in the field. Power is everywhere (power lines), just historically not available.

**Product 1 — Kestrel: portable charging system, $65K, defense launch market**
- Perch on the line (Magline harvester), power flows down a tether to a converter, then to a battery or direct to the machine
- Kestrel 1 (now): 50-150W lines, demonstrated on Orca drone, remote piloted, BOM $15K
- Kestrel 2 (ship Q3 2026): 50-250W, retrofit to multiple bodies, semi-autonomous find+attach, integrates with customer autonomy, BOM $20K
- Traction: Chariot Defense, **Overland** (new customer name, details TBD)
- Do not claim full autonomy; K1 is piloted, K2 is semi-autonomous find+attach

**Product 2 — Spark E: self-charging drone (lands on powerline, charges itself)**
- Market: drone operators covering large areas; range extension improves unit economics
- V1 on **Orca X30**: 30 min flight per charge, up to 80 km/h, BVLOS + autonomous modes
- V2: 120 min flight, model TBD. Custom: engineering collab w/ customer sensors
- Customers: Cupertino (largest utility inspector Argentina, 17,000 km to cover), reforestation drones, aerial imagery, defense

**Product 3 — Software:** telemetry, power line health reporting, metering to pay for the energy

**Business model:** hardware + software subscription, training & support
**Legality slide:** advisor ex-PG&E (name TBD); utilities angle: safety first + redundancies, new revenue for utilities, line health reporting
**Next 12 months target:** $6M revenue, Gen 3 Kestrel production scale (3 customers x 10 units), Gen 2 Spark E (30 sold), SBIR direct-to-phase-II

**Current TRL:** 4 (per Anis, Jul 9 2026)  
**Target TRL:** 6 by August 2026  
**Demo event:** JIFX 26-4, Camp Roberts CA — August 10–14, 2026

---

## Team

| Person | Role | Notes |
|--------|------|-------|
| Anis Cheriet | CEO | Background in EV charging. anis@chargebotic.com |
| Bo Christopher Redfearn | CTO | Formerly Apple. bo@chargebotic.com |
| Armin | AI/ML Engineer | |
| Becket | Intern | ME student, FPV champion |
| Patrick Consorti | Advisor/connector | patrick.consorti@gmail.com — made Terna intro |

---

## Active Deals

### 1. Chariot Defense — 🔴 Priority #1
- **What:** Defense tech co, San Bruno CA. Makes **Amphora** — universal battlefield power hub. Takes ANY input (solar, generator 24V DC, vehicle, grid AC 100–240V, and Chargebotic drone). Stores in battery. Outputs 24V DC + 320W AC circuits. Has 15kW/600lb larger version. $41M raised (a16z Series A Feb 2026).
- **Deal:** Paid pilot accepted: 2 units at $80K total. NOT a $6.5M order. The $6.5M/year is the estimated account value IF the pilot succeeds and Chariot scales to ~100 units. Never present $6.5M as a signed or pending order.
- **Contact:** Adam Warmoth — adam@chariotdefense.com
- **Pilot payment structure:** 2 parts — 1st half upfront, **2nd half on technical demo success** (even if customer discovery is still ongoing)
- **Commercial order trigger:** Technical success + joint customer discovery validates price/power level

#### 5 open contract items (from Jun 19 site visit transcript):

**1. Pilot success criteria**
- **Minimum success = 40W continuous for 10 minutes on a REAL power line** (agreed with Chariot)
- Must do a demo on a **real power line** (not just simulated) — Adam will accept going to Mexico if needed
- Power range in agreement: 40–150W. If only 40W achieved, Adam pays 2nd half but may not place purchase order (40W can't power anything useful)
- ~70W = powers a Starlink. 100W+ = compelling. 500W = very compelling.

**2. Real powerline testing**
- Simulated power line at JIFX is good for demo, but Adam wants a real-line test as part of success
- "Let's go drive to Mexico" — he's flexible on logistics, just needs it to happen

**3. Customer discovery (joint)**
- Adam will co-market to his customers during the pilot
- Not about having customers AT the demo — it's about capturing video/data/photos that become sales collateral
- Joint customer calls after JIFX: validate price point and minimum useful power level
- This is separate from technical success — doesn't block 2nd pilot payment, but gates the purchase order

**4. Operations / training / support**
- First 10 units: Chargebotic expected to be on-site for every demo (like Chariot did for their early units)
- Options: (a) train-the-trainer, (b) Chargebotic comes to each delivery/demo
- Hardware upgrade policy: Chariot expects to send back old units for upgrades (precedent: they recalled all v4 units)
- Include in price or price separately — needs to be defined before purchase order

**5. IP framework**
- Adam wants foreground + background IP agreement in place **before any co-development begins**
- Current pilot language: just acknowledge intent, no IP exchange until proper legal agreement signed
- "We will not commence co-development until IP framework is established"
- Need a lawyer to draft this — do NOT exchange technical details before this is signed

#### Integration specs (from site visit):
- Preferred: Chargebotic delivers **DC** (24V or higher voltage). Higher V = thinner cable, less losses.
- If higher voltage: Chariot builds a small "expansion box" DCDC converter → plugs into Amphora
- Alternative: Chargebotic delivers **AC (110–240V)** → Amphora already has rectifier, no work on Chargebotic side
- DC preferred because: as Chargebotic generates power, bus voltage rises → Amphora automatically starts charging (no communication needed)
- Amphora can also do power + communications over the same tether line

#### Key use case that resonated (Adam's example):
Robotic combat vehicle (e.g., with Starlink + acoustic sensor) drives 10km into enemy territory on its engine. Shuts engine off (reduces heat/acoustic signature). Chargebotic drone launches to nearby power line → provides persistent power for days/weeks. When acoustic sensor detects incoming drone: Starlink sends alert back to base. Engine stays off = undetectable. Pairs with Chariot Amphora onboard. **"1+1=3"**

#### JIFX 26-4 plan (Aug 10–14, Camp Roberts CA):
- Demo goal: show energy harvesting from power line → delivered to Chariot Amphora ground system
- No actual end-user customers at JIFX — footage/data goes into sales materials
- Hardware ordered from **ORQA** (delivery by Jul 1 to 125 Cervantes Blvd, SF CA 94123):
  - 1x MRM2-10 drone
  - ORQA FPV.Ctrl (or Tac.Ctrl)
  - IRONghost QS Ground Unit
  - IRONghost RF 5.8 Ground Unit
  - ORQA FPV.One Goggles
- JIFX requirement: no components from China, insurance required

- **Action:** Send Adam redlined contract with 5 items addressed above

### 2. Cupertino Aerial Intelligence (cupertino.ai)
- **What:** Argentine company, self-described biggest drone service provider in Argentina. Robotic inspection of high-voltage lines, towers, substations (thermal, LiDAR, UT). Has several power line and utility customers. NOT US-based (old brief was wrong).
- **Contacts:** Santiago Búa, BD (santiago.bua@cupertino.ai, +549 11 3631 9805); matias.larumbe@, diego.karl@, emilianoumano@cupertino.ai
- **History:** Inbound via Twitter May 13 2026 ("WireBird Argentina"). Calls May 28/29 and Jun 11/12 2026.
- **Status:** Confirmed Letter of Interest
- **Action:** TBD

### 3. Terna Forward (Italian grid CVC)
- **What:** Terna is Italy's national power grid operator. Their CVC arm (Terna Forward) reached out.
- **Contacts:** Luca Scherling (luca.scherling@terna.it), Pietro Rossi (pietro.rossi@terna.it — leads CVC)
- **Status:** Intro call done Jun 24. Deep-dive scheduled **Jun 30, 9AM Pacific / 6PM Rome**
- **Action:** Prep deep dive for Jun 30

---

## Fundraising Status

**Stage:** Pre-seed  
**Ask (updated Jul 9 2026):** $4M for 24 months of runway  
**Bridge:** $200K SAFE at $5M cap (angels — in progress)

### Business model (updated Jul 9 2026)
1. Hardware: drones with energy-harvesting payload
2. Software: line detection, flight, attach, harvest. The real product IS autonomous (per Anis, Jul 9 2026). Only the JIFX Aug 2026 demo is piloted. Pitch the product as autonomous; show JIFX as the piloted demo milestone on the roadmap.
3. Services: training
4. Insurance: drone replacement plan when a unit fails or breaks

### FoundersInc
- Sent funding ask Jun 15, 2026
- **No response received yet**

### Angels
- Following up this week — status TBD

### Key investors to track
- FoundersInc (no feedback yet)
- Others TBD

---

## This Week — Sprint June 23–27

- [ ] Sign **Chariot contract** — deadline this week
- [ ] Follow up with **angels** — status per angel
- [ ] Confirm **6-month fundraising costs** (exact number)
- [ ] **CAD files — drone base** — finalize/receive
- [ ] **Drone stabilization** — must hold position in flight

---

## Markets

| Market | Opportunity | Notes |
|--------|-------------|-------|
| US Military | 250,000 ground vehicles | 18-month build + cert timeline |
| Power line inspection | $30B+ market | Terna is a live lead |
| Defense ground power | Battlefield edge power | Chariot Defense is the beachhead |

---

## Events / Calendar

| Date | Event | Status |
|------|-------|--------|
| Jun 24, 2026 | Terna intro call | Done |
| Jun 30, 2026 | Terna deep dive (9AM PT) | Upcoming |
| Aug 10–14, 2026 | JIFX 26-4, Camp Roberts CA | Demo — prep in progress |

---

## What NOT to confuse

- The company is **Chargebotic Inc** — not Wirebird (that was a temporary concept name, no longer used)
- Bo Christopher Redfearn is the **CTO** (not just "Hardware Lead")
- Rafael M. was removed from team
- Old Chargebotic charging-station-for-robots concept = **dead**. Product is now the power-line drone.

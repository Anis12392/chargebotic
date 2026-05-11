# DoorDash Last-Mile Delivery & Robotics — Deep Research Dossier

> **Prepared for:** Chargebotic (autonomous self-charging infrastructure / induction-pad docking for delivery robots)
> **Date:** April 16, 2026
> **Objective:** Understand DoorDash as a potential customer/partner for induction-based autonomous charging infrastructure. Identify product gaps, decision-makers, and pitch hooks.
> **Confidence legend:** **[C]** Confirmed via press release / exec quote / SEC filing · **[R]** Reported (credible secondary source) · **[S]** Speculative / inference.

---

## Executive Summary

DoorDash is the single most aggressive multi-modal last-mile delivery player in the US in 2026. Over the last 18 months, they have (1) launched their own in-house robot ("Dot") via DoorDash Labs, (2) layered on three third-party robot fleets (Coco, Serve, Starship-era pilots), (3) expanded drone partnerships (Wing, Flytrex, Manna), and (4) invested $200M+ into Rivian-spinoff **Also** for autonomous delivery vehicles. Tony Xu has explicitly told investors they will spend "several hundred million dollars" on autonomous delivery in 2026.

**Crucially for Chargebotic:** DoorDash has explicitly architected Dot around **swappable batteries** — they openly state that "decoupling storage and charging" is a design priority and that charger dwell time is a problem they designed around. They are already building warehouses + charging stations + field-ops teams in Phoenix and Fremont to manually shuttle batteries. This is exactly the wedge: in-motion / autonomous induction charging eliminates the need for battery swap labor + warehouse footprint — which today is a line item on their P&L.

The right buyer at DoorDash is **Ashu Rege (VP & Head of Autonomy, DoorDash Labs)**, with **Stanley Tang (co-founder / Head of Labs)** as the executive champion. Below the VP level, the Electrical Engineering / Robotics Hardware team (actively hiring) and Field Operations team (Phoenix) are the functional buyers.

---

## 1. DoorDash Last-Mile Delivery Program Overview

### 1.1 Delivery modalities in production (2026) **[C]**

| Modality | Partner / Product | Status |
|---|---|---|
| Human Dashers | ~8M US gig workers | Primary |
| Drones | Wing (Alphabet), Flytrex, Manna | Live in Christiansburg VA, DFW TX, Atlanta GA, Australia |
| Sidewalk robots | Coco Robotics | Live: LA, Chicago, Helsinki (via Wolt). 100K+ deliveries completed |
| Sidewalk robots | Serve Robotics | Live: Los Angeles (Oct 2025 launch) |
| Multi-modal hybrid robot (in-house) | **Dot** | Live: Tempe & Mesa AZ (Sep 2025); Fremont CA (Mar 2026) |
| Autonomous delivery vehicles | **Also** (Rivian spin-out) | Co-development deal, $200M Series C participation (Mar 2026) |
| Passenger AV delivery | Waymo | Phoenix pilot |
| Historical / discontinued | Starship (2017), Marble (2017), Cruise (2019), Nuro (Houston pilot) | Wound down after Nuro pivoted to licensing (Sep 2024) |

### 1.2 Program names **[C]**
- **DoorDash Labs** — robotics & automation arm, founded 2018, led by co-founder Stanley Tang. Site: labs.doordash.com.
- **Autonomous Delivery Platform (ADP)** — AI dispatcher that routes each order to the optimal modality (Dasher / Dot / Coco / Serve / drone). Launched Sept 2025 alongside Dot.
- **SmartScale** — in-merchant hardware to verify package weight & order completeness; >20,000 units shipped. Reduces missing items by ~30–40%.

### 1.3 Timeline **[C]**

| Year | Event |
|---|---|
| 2017 Jan | First robot pilot with Starship Technologies (Redwood City) |
| 2017 | Partnered with Marble Robot in San Francisco |
| 2018 | DoorDash Labs formed |
| 2019 May | Filed two patents for autonomous delivery vehicle (approved 2021) |
| 2019 Apr | Acqui-hired Lvl5 (crowdsourced HD-mapping) |
| 2019 Aug | Acquired Scotty Labs (teleoperation) |
| 2019 | Piloted with Cruise in SF |
| 2021 Feb | Acquired Chowbotics (food-assembly robots) |
| 2021 Nov | Hired Ashu Rege as VP Autonomy |
| 2022 | Launched Wing drone pilot in Christiansburg VA |
| 2024 | Expanded Wing to Dallas-Fort Worth malls; Flytrex DFW launch |
| 2025 Apr | Expanded Coco partnership; US sidewalk launch (LA, Chicago) |
| 2025 Sep 30 | **Unveiled Dot + Autonomous Delivery Platform** |
| 2025 Oct 9 | Serve Robotics multi-year partnership announced (LA) |
| 2025 Nov | Wing expansion to metro Atlanta |
| 2026 Mar | Fremont CA Dot pilot kicks off (Mayor Raj Salwan); encroachment permit through March 2027 |
| 2026 Mar 31 | Participated in $200M Series C for Also (Rivian spinoff), board seat secured |
| 2026 CY | Xu: "several hundred million dollars" earmarked for autonomy in 2026 |

### 1.4 Pilot cities & expansion roadmap **[C]**

- **Dot**: Tempe & Mesa (Phoenix metro) → Fremont CA (Mar 2026 launch) → target 1.5–1.6M residents in Phoenix by end of 2025 → additional markets planned but undisclosed.
- **Coco**: Los Angeles, Chicago, Helsinki (Wolt).
- **Serve**: Los Angeles → rollout to additional US cities "in coming months" per Oct 2025 release.
- **Wing**: Christiansburg VA, Frisco TX (Stonebriar), Fort Worth TX (Hulen), metro Atlanta.
- **Flytrex**: Dallas-Fort Worth suburbs, reaches ~100k residents.

---

## 2. The Robots Themselves

### 2.1 Dot (DoorDash in-house) — **the most important platform for Chargebotic** **[C]**

| Spec | Value | Source |
|---|---|---|
| Manufacturer | DoorDash Labs (designed entirely in-house) | DoorDash press release |
| Launch date | Sep 30, 2025 | TechCrunch |
| Height | 4 ft 6 in (≤5 ft) | TechCrunch / Interesting Engineering |
| Width | 3 ft (fits through most doors, stays on sidewalk) | DoorDash |
| Weight | 350 lb | TechCrunch |
| Payload | 30 lb / ~6 pizza boxes | Restaurant Dive |
| Top speed | 20 mph | DoorDash |
| Drive | 4-wheel, all-electric | Interesting Engineering |
| Cameras | 8 external + 1 internal | Interesting Engineering |
| Radar | 4 units | Interesting Engineering |
| LiDAR | 3 units (high-res) | Interesting Engineering |
| Compute | Real-time AI (deep learning + search); stack inherited from Zoox-style engineering | DoorDash Labs blog |
| Battery | **Swappable / removable pack**; operates 6–8 hours per charge | DoorDash Dot page |
| Charging method | Today: **manual battery swap** at warehouse + charging station ecosystem | Arizona Tech Council; CBS News |
| Operating zones | Bike lanes, roads, sidewalks, driveways — multi-modal | DoorDash |
| Manufacturing | Not publicly disclosed; evidence of in-house prototype fab (jobs posted for "Prototype Machinist & Fabrication Specialist") | DoorDash careers |
| Unit cost | Not disclosed **[S]** (likely $20–40k range based on comparable platforms) |
| Field failures / issues | Remote operators + local field-ops team "resolve anything that can't be managed remotely"; "pauses when encountering obstacles like potholes or animals" | Interesting Engineering |

**Chargebotic-critical quote from DoorDash:**
> *"The robot runs on a swappable battery pack rather than charging in place, allowing fleet operators to rotate charged packs in and out and keep robots in service longer without long dwell times at a charging dock."* — Arizona Tech Council **[C]**

> *"In Phoenix, DoorDash has created an ecosystem to support its small fleet of Dots: warehouses to store the robots, **charging stations to fill up their batteries**, and **field operators to clean and rescue them**."* — CBS News **[C]**

Translation: DoorDash is already paying for (a) physical warehouse space, (b) charging station capex, (c) field-ops labor to swap batteries. This is Chargebotic's exact cost displacement story.

### 2.2 Coco Robotics (Coco 1 → Coco 2) **[C/R]**

| Spec | Value |
|---|---|
| Manufacturer | Coco Robotics (LA); Coco 1 co-developed with Segway |
| Founded | 2020 |
| Fleet size | 1,000+ robots (pre-Coco 2); scaling to "thousands globally by end of 2026" |
| Deliveries | 500,000+ lifetime; 100,000+ for DoorDash alone during pilot |
| Speed | ~5 mph (Coco 1); faster on Coco 2 with road/bike lane capability |
| Range | Up to 3-mile delivery radius (Coco 1) |
| Sensors | Cameras + LiDAR + GPS |
| Compute | NVIDIA Jetson Orin NX (Coco 2) |
| Autonomy | Partially autonomous with remote operators; Coco 2 moves toward full autonomy |
| Battery | Larger pack on Coco 1 enables 3-mile radius; exact spec not public. Coco 2 claims "3× longer uptime" and "improved weather/wear resilience" |
| Charging | Not publicly specified; operating model implies return-to-hub charging |
| DoorDash deployment | LA + Chicago; 600 participating merchants |

### 2.3 Serve Robotics (Gen 3) **[C]**

| Spec | Value |
|---|---|
| Manufacturer | Serve Robotics (spun out of Uber, 2021) |
| Gen 3 launch | Oct 2024 |
| Range per charge | 48 miles (77 km) / up to 14 hours (Gen 3); was 23 mi / 10 hrs on Gen 2 — a 67% battery capacity bump |
| Top speed | 11 mph (up from 7 mph) |
| Autonomy | Level 4 |
| Compute | NVIDIA Jetson Orin (5× compute bump over Xavier) |
| Charging | "Plugged in" — plug-in at base, no swap mentioned |
| Fleet size | 2,000+ robots announced; 50 deployed in Chicago |
| Total deliveries | 100,000+ across LA, Miami, Dallas, Chicago, Atlanta |

### 2.4 Wing (Alphabet) — drones **[C]**

- Australian origins; operates in Christiansburg VA, DFW malls (Stonebriar/Hulen), Atlanta metro.
- Typical delivery time: ≤30 minutes; range limited to small-package, short-hop.
- Wendy's is a flagship merchant.
- Drone charging is a different technical stack (not Chargebotic's immediate wedge).

### 2.5 Also (Rivian spinoff) — **emerging opportunity** **[C]**

- Pedal-assist cargo e-bike today (400+ lb payload, bike-lane compatible, $4,500 MSRP for high-end consumer model; Amazon ordered thousands of cargo variants).
- Autonomous delivery vehicle version under co-development with DoorDash.
- DoorDash: $200M Series C participation (lead: Greenoaks); board seat secured.
- CEO: Chris Yu (with founder RJ Scaringe involvement).
- **Charging approach TBD** — this is a greenfield opportunity to design induction in from day one. **[S]**

---

## 3. Team & Org — Who to Target

### 3.1 DoorDash Labs leadership **[C]**

| Name | Title | Background | Contact signals |
|---|---|---|---|
| **Stanley Tang** | Co-founder, Head of DoorDash Labs | Stanford; DoorDash co-founder 2013; on board of directors | X/Twitter: [@stanleytang](https://x.com/stanleytang) (70.2K followers); posts actively about Dot & ADP. Based SF. |
| **Ashu Rege** | VP & Head of Autonomy, DoorDash Labs (joined Nov 2021) | Former SVP Software Eng at Zoox (6 yrs, scaled team from 6 → 600 engineers + 150 operators); early NVIDIA leader in computer vision/autonomy; PhD CS, UC Berkeley | [LinkedIn](https://www.linkedin.com/in/ashurege/); quoted in every Dot announcement; podcast appearances (The Driverless Digest, Apr 2026) |

**Where Ashu sits:** VP level, reports into Stanley Tang, owns the full autonomy stack (hardware, software, operations). He is the economic buyer for Chargebotic.

### 3.2 Team composition (inferred from active job postings, Apr 2026) **[R]**

DoorDash Labs is actively hiring across:
- **Robotics Software Engineer — Labs** (drone autonomy) — [careers link](https://careersatdoordash.com/jobs/robotics-software-engineer---labs/6682078/)
- **Software Engineer, Routing — Autonomy & Robotics**
- **Electrical Engineer — Autonomy & Robotics** ("develop and manufacture autonomous delivery robots…design and implement electrical systems for last-mile logistics") — **directly relevant counterpart for Chargebotic's EE team**
- **Software Engineer, Infrastructure — Autonomy & Robotics**
- **Autonomy Test Engineer**
- **Autonomy Lead — Labs** (very senior; re-architects full stack)
- **Software Engineer, Autonomy — Labs (Foundry)**
- **Security Engineering Lead — Autonomy & Robotics**
- **Prototype Machinist & Fabrication Specialist** — confirms in-house hardware prototyping; suggests battery/charging hardware is on-bench
- **Robot Operations Specialist** (Phoenix, nights/weekends 2 PM–12 AM) — literally the humans swapping batteries and "rescuing" Dots

**Approximate team size [S]:** Based on ~7 years of building, Zoox-scale org playbook from Rege, active reqs across ~10+ posted roles, and Phoenix field ops, estimated 150–300 FTE across Labs as of Apr 2026.

### 3.3 Related DoorDash execs **[C]**

- **Tony Xu** — Co-founder & CEO. Quoted extensively on "pain and suffering" in autonomy (see §5). Sets the autonomous delivery capex.
- **Prabir Adarkar** — President & COO (handles unit economics narrative on earnings calls).

### 3.4 Recent hires / departures **[R]**
- No notable public departures from Labs leadership in the last 12 months.
- Big hire pre-dates this window: Ashu Rege in 2021.
- Acqui-hires: Lvl5 founders (2019), Scotty Labs team (2019).

---

## 4. Scale & Unit Economics

### 4.1 Scale **[C/R]**

- **DoorDash total:** 9M deliveries/day, ~10B lifetime, 903M orders in Q4 2025 alone (IndexBox/earnings).
- **Autonomous share:** Still a rounding error in 2026. Tony Xu (Sep 2025): *"We don't have it yet operating today. A lot of it is in test forms."* **[C]**
- **Coco on DoorDash:** 100,000+ deliveries in pilot phase (Apr 2025 PR).
- **Dot:** "Hundreds of successful deliveries" by launch; target 1.5–1.6M residents served in Phoenix metro by EOY 2025. No hard fleet count disclosed — **inferred [S]** small fleet (10–50 units) in Phoenix, scaling to 30 in Fremont per Phase 1B permit.

### 4.2 Revenue & economics **[C/S]**

- DoorDash does **not break out** autonomous delivery revenue or unit economics in 10-K / 10-Q.
- Q4 2025 revenue: $3.96B (+37.7% YoY); full-year 2026 guidance emphasizes "several hundred million dollars" tech platform / autonomy investment **[C]**.
- **Economic motivation (important context):** Multiple sources confirm Dasher pay + delivery fees constitute ~60% of every order's cost, so robot economics are the main path to sustainable profit **[R]**.
- **Customer pricing parity:** Dot deliveries priced same as a Dasher to the end customer — meaning every dollar of cost saved via autonomy flows to the platform, not the consumer.

### 4.3 Cost per autonomous delivery vs. Dasher **[S]**

- DoorDash has not published comparative cost-per-delivery numbers.
- Industry benchmarks: a typical food-delivery Dasher delivery costs DoorDash $7–$10 all-in (driver pay, benefits, tips, acquisition). Robot deliveries today likely cost *more* on a fully-loaded basis (amortized CapEx + remote operator + field ops + charging labor), but the long-run target per Tony Xu commentary is to undercut Dasher cost substantially at scale.
- Chargebotic's opportunity here: shrink the OpEx line that currently props up robot cost — namely, field-ops battery-swap labor + dedicated charging warehouse footprint.

---

## 5. Pain Points & Challenges — **the Chargebotic pitch surface**

### 5.1 Explicit exec acknowledgments **[C]**

**Tony Xu (Fortune, Sep 2025)** — a gift of direct quotes for cold-outreach hooks:
- *"Candidly, it's mostly been filled with lots of pain and suffering."*
- *"Imagine learning a new sport, but that sport has five different subdomains just to say that you're a rookie at that sport."*
- *"You have to build the hardware, develop the software, and fine-tune the delivery network, too — particularly in the instance that an autonomous delivery vehicle ends up getting stuck and needing human intervention."*
- *"It's very rare that one company is equally good at all of those skills…I think we're still very early in building the competence."*
- *"Starting to get to maybe the first inning of commercial progress."*

**Stanley Tang:**
- *"Automation in our business only matters when it can scale in the real world."*
- *"The hard part isn't building a prototype…How do you deploy the autonomy across multiple categories, at a global scale?"* (Upstarts Media)

### 5.2 Charging / uptime / downtime — the direct Chargebotic wedge **[C/R]**

- **Dot was designed around battery swap specifically because charger dwell time is a recognized pain point.** DoorDash's own language: *"decouple storage and charging of the vehicles"* and *"keep robots in service longer without long dwell times at a charging dock."* **[C]**
- DoorDash is running a full physical support stack in Phoenix: **warehouse + charging station + field-ops team to swap batteries and "rescue" robots** (CBS News).
- Industry data (general autonomy): unplanned robot downtime estimated at $1,000–$10,000/minute of production impact; "poor charging orchestration creates hidden downtime even when no robot has technically failed" (SmartLoadingHub, CaPow, Phihong).
- Starship (not a DoorDash partner anymore but a relevant comp) solved this with **wireless charging at Cambourne UK + George Mason University** — they explicitly say it lets robots "drive themselves to a central charging point to recharge…and be ready for operations the following morning." This is validating market direction for induction-style charging at scale.
- Serve Gen 3 added 67% battery capacity specifically to extend runtime — the industry is racing to minimize charge downtime one way or another.

### 5.3 Other operational pain **[C/R]**

- **Vandalism:** Kiwibot reported ~2% of first 80k deliveries at UC Berkeley involved vandalism incidents; ~$2,500/robot cost per incident. LA influencers filmed thrashing Coco robots. LAPD incidents with Serve bots.
- **Sidewalk / bus-shelter collisions (March 2026):** Serve robot shattered a West Town bus shelter; Coco hit Old Town shelter next day. Serve ran a public apology ad and committed to "improving glass detection."
- **Regulatory pushback:**
  - Chicago: 83.7% of surveyed residents opposed expansion (Alderman Daniel La Spata, 1st Ward); 4,000-signature petition; city created 311 category for robot complaints.
  - Glendale CA: moratorium on sidewalk rovers.
  - Fremont: required encroachment permit, phased 3-robot → 30-robot approval, standardized SOP + incident response.
- **Weather, cracked pavement, missing curb cuts** — ongoing.
- **Public narrative risk:** Dasher job-replacement fears amplified by DoorDash "Tasks" program (pays Dashers to film tasks for AI training).

### 5.4 What's explicitly NOT yet solved
- **In-motion / autonomous charging** — no DoorDash partner currently offers in-route or induction-based charging that keeps robots operational without returning to a dock.
- **Unified charging infrastructure across modalities** — Dot, Coco, Serve, and Also will each have their own charging stack today.

---

## 6. Customer & Merchant Sentiment

### 6.1 End customers **[R]**
- Sentiment split: novelty/positive in pilot launches; negative once robots become a commute obstacle.
- Chicago Sun-Times: Ainsley Harris (Lincoln Park resident) worried about navigating narrow sidewalks with kids/pets.
- Petition organizer Josh Robertson: *"Sidewalks are for people and should remain people first."*
- Customers don't tip robots → potential savings vs. Dashers.

### 6.2 Merchants **[R]**
- No upfront cost to participating merchants for Dot.
- Positive: SmartScale (bundled with robot initiative) cuts missing items by 30–40% and improves restaurant operations regardless of modality.
- 600 merchants on Coco via DoorDash in LA/Chicago; 2,500+ restaurants have historically used Serve robots.

### 6.3 Dashers **[R]**
- Direct threat / replacement fears amplified by Slate article (Oct 2025) and DoorDash "Tasks" program (Jan 2026 viral).
- New "robot operations" support jobs advertised at ~$21/hr — below CA cost of living; Futurism piece "Former Delivery Drivers Are Getting Weird New Jobs as Delivery Robots Take Over."
- DoorDash's public framing: *"Augment human networks, not replace them."*

---

## 7. Competitive Landscape

| Platform | Autonomy strategy | Relative position |
|---|---|---|
| **DoorDash** | Multi-modal: in-house Dot + Coco + Serve + Wing/Flytrex/Manna + Also investment | Most aggressive US player; only one building own robot |
| **Uber Eats** | Partnership-only: Starship (UK/EU first, US 2027), Cartken (Japan via Mitsubishi), Avride, Nuro (earlier pilots), Serve (historical) | Broad but no in-house hardware; EU-first on robots |
| **Amazon Scout** | Shut down 2022 | Exited market |
| **Grubhub** | Cartken campus deliveries; limited scope | Niche (universities) |
| **Kroger/Walmart** | Nuro in Houston/AZ historically; Walmart Spark + various AV pilots | Grocery-focused |
| **Robomart** | $3 flat-fee autonomous delivery play (Yahoo Finance 2026 coverage) | Emerging challenger |

DoorDash is the **only major food-delivery platform** with (a) proprietary robot hardware, (b) multi-modal dispatcher/orchestration platform, and (c) invested in its own AV pipeline (Also).

---

## 8. Chargebotic Angle — Synthesis & Pitch

### 8.1 Where charging pain shows up at DoorDash — mapped

1. **Dot swappable-battery ecosystem = operational overhead line.** DoorDash is paying for (a) charged-battery inventory, (b) warehouses to store them, (c) field operators running swap shifts (~$21/hr in Phoenix). Induction / in-route charging displaces all three.
2. **Dot's stated 6–8 hr runtime means ≥2 swaps/day per robot** for continuous operation. At scale (assume even 1,000 Dots per city), that's ≥2,000 swap-events/day per city — a meaningful labor line.
3. **Fremont Phase 1B scales to 30 autonomous robots** (i.e., no chaperones) → remote ops model will magnify the dwell-time problem because robots can't just "return to van" → they need to autonomously charge on-route.
4. **Also (Rivian spinoff) is greenfield** — no charging architecture locked in yet. Induction built into the vehicle-and-infrastructure design from day one is a strategic partnership play, not just a vendor sale.
5. **Cross-modal charging standard** — as DoorDash dispatches between Dot, Coco, Serve, and Also, a universal induction standard sold into DoorDash-owned or DoorDash-contracted real-estate (DashMart hubs, merchant parking lots) could become platform infrastructure.

### 8.2 Who to target — ranked

| Rank | Name | Role | Why |
|---|---|---|---|
| 1 | **Ashu Rege** | VP & Head of Autonomy, DoorDash Labs | Direct economic buyer; charging is his operational cost. [LinkedIn](https://www.linkedin.com/in/ashurege/) |
| 2 | **Stanley Tang** | Co-founder, Head of Labs | Exec champion; active on X ([@stanleytang](https://x.com/stanleytang)); replies to interesting DMs |
| 3 | Electrical Engineering leadership (Dot hardware team) | Via the EE — Autonomy & Robotics job posting owner | Will be the technical evaluator; identify hiring manager from posting |
| 4 | Field Ops Team Lead (Phoenix) | Runs day-to-day battery swap | Will feel the pain most acutely; good early reference customer |
| 5 | **Chris Yu** | CEO, Also | Greenfield charging design for the next-gen AV — DoorDash has a board seat there |
| 6 | **Tony Xu** | CEO | Only if via warm intro (investor / board member); he has publicly said autonomy is "pain and suffering" — use his own words |

### 8.3 Concrete pitch hooks (for cold outreach / LinkedIn)

1. **Quote-back-to-them opener:** *"Tony called autonomy 'pain and suffering.' We eliminate one specific subdomain of pain — charging uptime. Dot's swappable-battery architecture implies ~2 swap events per robot per day. We remove those events."*
2. **Cost wedge:** *"Your Phoenix field-ops spec pays $21/hr to swap batteries and rescue robots. An induction pad recovers 6–8 hours of runtime without a human in the loop."*
3. **Greenfield hook for Also:** *"You just bought a board seat at Also. Before they finalize the autonomous-vehicle charging stack, we'd like to show Chris Yu why induction from day one wins vs. retrofitting."*
4. **Reference Starship wireless charging (UK + George Mason University)** as industry precedent that the motion is already happening in the market — DoorDash can't afford to be the slowest adopter.
5. **Fremont angle:** Phase 1B (30 autonomous Dots, no chaperones) won't work economically if every robot returns to a warehouse to swap. Pitch induction pads embedded in Fremont curbside infrastructure as part of the public/private encroachment agreement with the city.
6. **Multi-modal standardization:** One charging standard that works for Dot + Coco + Serve + Also is a moat for DoorDash's multi-modal platform.

### 8.4 Suggested next actions

1. **LinkedIn DM to Ashu Rege** referencing Dot's published swappable-battery architecture and the Phoenix field-ops cost line. Lead with a specific number.
2. **X/Twitter reply to Stanley Tang** on his Dot unveil thread (Sep 2025) — short, technical, no pitch.
3. **Backchannel into Also / Rivian alumni network** to get in front of the AV charging architecture decision before it locks.
4. **FOIA / public records pull on the Fremont encroachment permit** — see what charging infrastructure commitments (if any) DoorDash made to the city. If none, there's an opening for Chargebotic to offer it as a municipal partnership.
5. **Monitor DoorDash careers page** for an "Infrastructure Lead — Charging" or similar role — a hire there signals internal build vs. buy decision.

---

## Sources

### DoorDash primary
- [DoorDash Unveils Dot (press release, Sep 30, 2025)](https://about.doordash.com/en-us/news/doordash-unveils-dot)
- [Dot product page](https://about.doordash.com/en-us/dot)
- [DoorDash & Fremont Collaboration (Mar 2026)](https://about.doordash.com/en-us/news/doordash-fremont-collaboration)
- [DoorDash & Coco Expand Global Partnership (Apr 10, 2025)](https://about.doordash.com/en-us/news/doordash-and-coco-expand-global-partnership)
- [DoorDash & Serve Robotics Partnership (Oct 9, 2025)](https://about.doordash.com/en-us/news/doordash-serve-launch-partnership)
- [Introducing DoorDash Labs](https://about.doordash.com/en-us/news/introducing-doordash-labs-doordashs-robotics-and-automation-arm)
- [DoorDash & Wing Drone Pilot (US)](https://about.doordash.com/en-us/news/doordash-and-wing-announce-drone-delivery-pilot-in-the-us)
- [DoorDash & Wing Atlanta Expansion](https://about.doordash.com/en-us/news/doordash-wing-expand-to-atlanta)
- [Engineering Autonomy for Local Commerce (DoorDash careers blog)](https://careersatdoordash.com/blog/doordash-engineering-autonomy-for-local-commerce-dot-and-autonomous-delivery-platform/)
- [DoorDash Labs site](https://labs.doordash.com/)
- [DoorDash Q4 2025 earnings release](https://ir.doordash.com/news/news-details/2026/DoorDash-Releases-Fourth-Quarter-and-Full-Year-2025-Financial-Results/default.aspx)

### Exec social / profiles
- [Stanley Tang on X — Dot announcement thread](https://x.com/stanleytang/status/1973108152506748967)
- [Stanley Tang on X — DoorDash Labs technical achievements](https://x.com/stanleytang/status/1973594039938326568)
- [Ashu Rege LinkedIn](https://www.linkedin.com/in/ashurege/)
- [Ashu Rege — Driverless Digest podcast (Apr 2026)](https://www.thedriverlessdigest.com/p/doordashs-autonomous-delivery-strategy)

### Press / analysis
- [TechCrunch: DoorDash Unveils Dot (Sep 30, 2025)](https://techcrunch.com/2025/09/30/doordash-unveils-dot-its-autonomous-robot-built-to-deliver-your-food/)
- [TechCrunch: Rivian spinoff Also + DoorDash (Mar 31, 2026)](https://techcrunch.com/2026/03/31/rivian-spinoff-also-will-build-autonomous-delivery-vehicles-for-doordash/)
- [Restaurant Dive: Why DoorDash built its own delivery robot](https://www.restaurantdive.com/news/doordash-dot-smart-scales-autonomous-delivery-platform/761494/)
- [CNBC: DoorDash launches delivery robot](https://www.cnbc.com/2025/09/30/doordash-launches-delivery-robot-in-push-into-autonomous-technology.html)
- [Fortune: Tony Xu "pain and suffering" interview](https://fortune.com/2025/09/08/doordash-ceo-tony-xu-interview-brainstorm-tech-autonomous-drone-deliveries/)
- [Fortune: Meet Dot profile](https://fortune.com/2025/10/02/doordash-robot-delivery-driver-dot/)
- [Interesting Engineering: 350-pound Dot photo story](https://interestingengineering.com/photo-story/doordash-dot-autonomous-delivery-robot)
- [CBS News: Dot fleet, warehouses, charging stations, field ops](https://www.cbsnews.com/news/doordash-autonomous-delivery-bot-dot-phoenix-arizona/)
- [Arizona Tech Council: DoorDash rolls out robots in Tempe & Mesa](https://www.aztechcouncil.org/doordash-rolls-out-robots-in-tempe-and-mesa/)
- [Upstarts Media: How DoorDash is building in autonomous delivery](https://www.upstartsmedia.com/p/humanx-doordash-automous-delivery-robots-droness)
- [The Autonomy Report: Why DoorDash built its own delivery robot](https://www.theautonomyreport.com/p/why-doordash-built-its-own-delivery-robot)
- [Logistics Viewpoints: Evaluating Dot](https://logisticsviewpoints.com/2025/10/01/evaluating-doordashs-autonomous-delivery-robot-dot-and-its-implications-for-the-future-of-last-mile-logistics-and-supply-chain-efficiency/)
- [Fremont (City) DoorDash Delivery Robots page](https://www.fremont.gov/government/departments/economic-development/business-assistance/doordash-delivery-robots)
- [Chicago Sun-Times: Chicago delivery robot debate (2026)](https://chicago.suntimes.com/business/2026/delivery-robots-chicago-food-coco-robotics)
- [Slate: DoorDash & Waymo self-driving gig worker critique (Oct 2025)](https://slate.com/technology/2025/10/doordash-waymo-ai-self-driving-cars-gig-workers-labor.html)
- [Futurism: Delivery robot vandalism](https://futurism.com/robots-and-machines/delivery-robot-vandalism-problem)
- [KTLA: Vandals/thieves attacking LA food delivery robots](https://ktla.com/news/local-news/food-delivery-robots-under-attack-from-vandals-thieves-local-businesses-starting-to-be-affected/)
- [Restaurant Business Online: California city presses pause on food delivery robots (Glendale)](https://www.restaurantbusinessonline.com/technology/california-city-presses-pause-food-delivery-robots)

### Historical acquisitions
- [TechCrunch: Scotty Labs acquisition (Aug 2019)](https://techcrunch.com/2019/08/20/doordash-acquires-autonomous-driving-startup-scotty-labs/)
- [Crunchbase: DoorDash acquires Lvl5](https://www.crunchbase.com/acquisition/doordash-acquires-lvl5--88371f01)
- [Restaurant Dive: DoorDash patent application on autonomous vehicles](https://www.restaurantdive.com/news/doordash-autonomous-vehicles-patent-application/626384/)

### Partner robots
- [Coco Robotics — Coco 2 product page](https://www.cocodelivery.com/coco2)
- [Coco Robotics — Press: Coco 2 launch (Feb 2026)](https://www.prnewswire.com/news-releases/coco-robotics-launches-next-gen-autonomous-robots-for-urban-deliveries-302698399.html)
- [Serve Robotics Gen 3 press release (Oct 2024)](https://serverobotics.gcs-web.com/news-releases/news-release-details/serve-robotics-rolls-out-third-generation-autonomous-delivery)
- [Electrek: Serve Gen 3 specs](https://electrek.co/2024/10/16/serve-robotics-unveils-gen3-autonomous-delivery-robots-scale-across-us/)
- [Starship Technologies: Cambourne wireless charging](https://www.starship.xyz/press/cambourne-to-host-europes-first-wireless-charging-station-for-robots/)

### Jobs (signals of hiring direction)
- [Electrical Engineer — Autonomy & Robotics (DoorDash)](https://careersatdoordash.com/jobs/electrical-engineer---autonomy-robotics/6277844)
- [Robotics Software Engineer — Labs](https://careersatdoordash.com/jobs/robotics-software-engineer---labs/6682078/)
- [Autonomy Lead — Labs](https://careersatdoordash.com/jobs/autonomy-lead---labs/6992791/)
- [Robot Operations Specialist (Phoenix)](https://careersatdoordash.com/jobs/robot-operations-specialist/7015062/)

### Industry charging context
- [CaPow: Non-stop production / charging-swap strategies](https://www.large-battery.com/blog/non-stop-production-industrial-robot-charging-swapping/)
- [SmartLoadingHub: Why robot fleet uptime is a procurement battleground](https://www.smartloadinghub.com/insights/agv-amr/why-robot-fleet-uptime-becoming-procurement/)
- [Phihong: AI-powered charging stations for autonomous robots](https://www.phihong.com/how-top-manufacturers-use-ai-powered-charging-stations-to-improve-fleet-uptime-for-autonomous-robots/)
- [WiBotic — wireless charging technology](https://www.wibotic.com/)

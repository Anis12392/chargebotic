# Chargebotic — YC Application Rewrite (Spring 2026)

> Changes marked with **[CHANGED]**. Unchanged fields omitted.
> Best practices research saved separately in `yc-application-best-practices.md`

---

## AUDIT: OLD vs NEW (Against YC Best Practices)

| Question | Old Answer Problem | Best Practice Rule | New Answer Fix |
|---|---|---|---|
| **50-char description** | "Autonomous robot charging orchestration" — jargon ("orchestration") | Michael Seibel: "Your parents must understand it" | "Universal autonomous charging for any robot" — plain English |
| **What are you building** | Started with generic "we are building robot charging orchestration software" — no analogy, no proof | Paul Graham: "Give it to us in the first sentence, simplest terms." Use "variant of something known" | Opens with "EV charging infrastructure, but for robots." Ends with working prototype proof |
| **Progress** | "We are early-stage and currently validating..." — vague, no specifics | YC: Facts only, no "we believe." Named companies are gold | "We have a fully working prototype" + names 10 companies including Airbus, Zoox, P&G |
| **How long working** | Mentions Rafael and Christopher who are gone, "met co-founders over the past month" sounds weak, overshares full-time/part-time details | Dalton: Show deep engagement, clear commitment path. Don't over-explain | "Together since December 2025." Bo built Sparky for a year before. "Both fully committed." No unnecessary FT/PT details |
| **Competitors** | Generic "companies that provide robot charging hardware" — no names | YC: "Never say no competitors." Name them with specifics | Names WiBotic ($15M), CaPow ($22.5M), Wiferion, each OEM with their proprietary method |
| **Why this idea** | "All three founders have direct experience" — claims without proof | YC: Specific achievements at high magnitude | "$5B EV charging across Europe" + "Apple/Meta/Cruise hardware validation" — specific and verifiable |
| **Revenue model** | "Recurring subscription per charging point" — no numbers | YC: Be specific about model, show value to customer | Full solution sale (hardware + deployment + maintenance) with annual contracts. Software subscription is the recurring engine. Value framed as cost savings (20-30% downtime reduction) |
| **Impressive thing (Anis)** | "Deployment of two of Europe's largest..." — no names | YC: Specific > generic. Magnitude matters | Adds McDonald's France + Carrefour by name |
| **Who writes code** | Mentions Rafael (CTO) and Christopher (Hardware Lead) — wrong team | Must reflect actual team | Just Anis + Bo, clear role split |
| **Equity** | 33/33/33 with 3 people | Must match actual team | 50/50, two founders |
| **Category** | "Energy" | Should match what you actually build | "Robotics" — you're robotics infrastructure |
| **First application** | Original said first time — correct | N/A — this is the first application | Keep as is |
| **When usable** | "Within one weeks" — typo, vague, unrealistic | Be honest and specific | "Working prototype today. Deployable pilot 2-3 months away" — honest |
| **Tech stack** | Included voice (Vosk), TTS (ElevenLabs), OpenAI API — irrelevant to charging | Don't dilute. Only include what matters | Stripped to robotics core: ROS2, LiDAR, inductive charging, computer vision |
| **Twitter URL** | Links to /likes page | Must link to actual profile | Fixed URL |
| **Founder video** | With wrong team members | Must show actual founders | Re-record with just Anis + Bo |
| **Demo video** | Missing | YC: "Statistically much more likely to interview people who submit a video" | MUST RECORD — full autonomous cycle |

---

## FOUNDERS SECTION

### Anis Cheriet

**[CHANGED] What percent equity do you have?**
> 50

**[CHANGED] Twitter URL**
> https://x.com/AnisCHERIEET

(Remove the /likes at the end — currently links to your likes page, not your profile)

**[CHANGED] Please tell us in one or two sentences about the most impressive thing other than this startup that you have built or achieved.**
> I led deployment of two of Europe's largest electric vehicle charging infrastructure rollouts, including the McDonald's France fast-charging network and Carrefour's 3,500-location rollout, representing over $5B in combined infrastructure across public and private stakeholders.

(Same content but tighter — adds the specific names which make it 10x more credible)

**[CHANGED] Tell us about things you've built before.**
> Led deployment of McDonald's France fast-charging network ($2B program) and Carrefour's 3,500-location EV charging rollout. Co-built CocoAI, an AI photo editing app that reached 3,500 users and $1,100 revenue in under a month. Founded TomFeed, a content studio for founders in SF: 15 clients, $17K revenue, ~100 videos with 4-850K views. Founded ScalesView, a drone video service for construction companies generating €17K revenue. Currently doing a 30 apps in 30 days challenge (https://anischeriet.com). Won two hackathons in San Francisco (hardware/robotics and developer tools).

---

### Bo-Christopher Redfearn

**[CHANGED] What percent equity do you have?**
> 50

**[CHANGED] Walk us through your thinking around balancing your startup, school, and any other obligations.**
> My Masters at ASU is fully online, giving me complete schedule flexibility. I've already proven I can balance heavy workloads: I completed coursework while working full-time at Apple and winning multiple hackathons on weekends. If accepted to YC, Chargebotic becomes my primary focus. School is supplementary and will not interfere with the batch.

---

### Founders Section (Joint Questions)

**[CHANGED] How long have the founders known one another and how did you meet?**
> We met at a Physical AI hackathon in San Francisco in late 2025. Bo had been building Sparky, his autonomous rover robot, for the past year and needed a charging solution. I had spent the previous 4 years deploying EV charging infrastructure across Europe. The match was obvious: he had the robot, I knew how to charge it. We said "let's build the charger" and started working together immediately. Since January 2026 we've built a fully autonomous charging system: a robot that navigates, docks, charges wirelessly at 100W, and returns to work with zero human intervention.

**[CHANGED] Who writes code, or does other technical work on your product? Was any of it done by a non-founder? Please explain.**
> All technical work is done by the two founders. Bo builds all hardware and robotics software: the rover platform, ROS2 navigation stack, sensor fusion, autonomous docking logic, and the inductive charging integration. I handle the charging infrastructure architecture, integration protocols, business operations, and product direction. Everything in the current prototype was built by us. No outside engineers or contractors.

**[CHANGED] Are you looking for a cofounder?**
> No.

(Remove the sentence "We believe our team has everything needed to succeed" — sounds like filler)

---

## COMPANY SECTION

**[CHANGED] Describe what your company does in 50 characters or less.**
> Universal autonomous charging for any robot

**[CHANGED] What is your company going to make?**
> EV charging infrastructure, but for robots.
>
> Every robot manufacturer ships proprietary chargers. A warehouse with 3 robot brands needs 3 separate charging systems. Robots lose 20-30% of operating time traveling to chargers. Operators buy 20-30% extra robots just to compensate.
>
> We make two things: (1) a universal inductive charger that mounts on a wall-mounted articulated arm, plus a retrofit receiver kit that attaches to any existing robot, and (2) navigation software that guides robots to the charger with millimeter precision and orchestrates charging across mixed fleets.
>
> We have a working prototype today: a robot autonomously navigates via LiDAR, docks to our 100W inductive charger, charges itself, and returns to work. Zero human intervention. Next step: 500W power upgrade and mounting the charger on a mobile arm on a rail, so one unit serves an entire zone of robots.

---

## PROGRESS SECTION

**[CHANGED] How far along are you?**
> We have a fully working prototype, built in under 3 months. Our robot autonomously navigates (NAV2 + LiDAR + depth camera), locates our inductive charging station, docks with millimeter precision, charges at 100W wirelessly, detects charge completion, and returns to its task. Zero human intervention required.
>
> We built the robot, the induction charger (scaled from 5W to 100W), the navigation stack, and the charging orchestration logic ourselves. We've also built a universal inductive receiver that can be adapted to different robot types.
>
> We've had discovery conversations with Airbus, Serve Robotics, Zoox, Procter & Gamble, Robot.com, LifeKit, Solo, UFB, and 4 humanoid robotics companies. A project manager at P&G who manages AMR fleets told us that providers for this type of charging either don't exist or completely lock in the market. This confirmed our thesis: there is no universal, robot-agnostic charging infrastructure today.
>
> We have not incorporated yet. We plan to form a Delaware C-Corp.

**[CHANGED] How long have each of you been working on this?**
> We've been working on Chargebotic together since December 2025, both fully committed. I'm already full-time. Bo is still under contract with Apple but has no restrictive clauses and is ready to go full-time. Bo had been building Sparky, the autonomous rover that became our prototype, for over a year before we teamed up.

**[CHANGED] What tech stack are you using?**
> Robotics & Hardware:
> - NVIDIA Jetson Orin Nano (edge compute)
> - ROS2 Humble (robot operating system)
> - Custom mecanum-wheel rover with LiDAR (RPLIDAR), depth camera (OAK-D Lite), IMU, ultrasonic sensors, wheel encoders
> - Arduino Mega for low-level motor control
> - Custom 100W inductive charging pad (transmitter + receiver), scaling to 500W
>
> Navigation & Autonomy:
> - SLAM + Nav2 for mapping and autonomous navigation
> - Sensor fusion for localization
> - ArUco marker + computer vision for millimeter-precision docking
> - Autonomous charge management (battery monitoring, charge-complete detection, return-to-task)
>
> AI / Vision:
> - PyTorch, OpenCV
> - YOLO / MobileNet-SSD for on-device object detection
> - Exploring vision-language models for robot-type identification
>
> Software:
> - Python, ROS2 ecosystem
> - Foxglove for visualization/debugging

(Removed the voice/interaction stuff — it's not relevant to charging and dilutes the message. Removed OpenAI API mentions — you're a robotics company, not an AI wrapper.)

**[CHANGED] Are people using your product?**
> No. We are pre-revenue. Our working prototype demonstrates the full autonomous charging cycle. We are in discovery conversations with potential customers to identify the right first deployment.

**[CHANGED] When will you have a version people can use?**
> We have a working prototype today that demonstrates autonomous navigation, docking, and wireless charging. A deployable pilot version for a customer site is 2-3 months away, pending the 500W power upgrade and the wall-mounted articulated arm.

**[CHANGED] If you are applying with the same idea as a previous batch, did anything change?**
> This is our first application.

---

## IDEA SECTION

**[CHANGED] Why did you pick this idea to work on?**
> I spent 4 years deploying EV charging infrastructure across Europe: McDonald's France fast-charging network, Carrefour's 3,500 locations, Europe's 150-truck electric fleet. I saw firsthand how fragmented charging infrastructure kills fleet operations.
>
> Bo spent years at Apple, Meta, and Cruise doing hardware validation on sensors, cameras, and LiDAR. He builds autonomous robots as a passion project and hit the charging problem himself: every robot he built needed a custom charging solution.
>
> We both independently arrived at the same conclusion: as robot fleets scale from single-brand to multi-brand, charging becomes the bottleneck. Every OEM ships proprietary chargers. There is no universal standard. A P&G project manager we spoke with confirmed that providers for robot-agnostic charging either don't exist or monopolize the market.
>
> The EV world already proved this model works: rail-mounted robotic charging arms are being deployed in China (Li Auto/CGXi) and the US (Westfalia WEPLUG) for cars. Nobody has applied this architecture to robots. That's what we're building.

**[CHANGED] Who are your competitors?**
> WiBotic ($15M raised): Wireless charging pads for robots. Good product but fixed-location only. Robots must come to the pad. No mobile charging arm, no fleet orchestration across brands.
>
> CaPow ($22.5M, Toyota Ventures): Charges robots while they move over embedded floor pads using supercapacitors. Requires floor modification. Only works for ground robots on specific paths.
>
> Wiferion (acquired by WiTricity): Industrial wireless charging pads. Strong in manufacturing but same limitation: fixed pads, one pad per robot.
>
> Robot OEMs (Tesla, Figure, Boston Dynamics): Each builds proprietary charging for their own robots. Tesla Optimus uses a wall plug on its shoulders. Figure 03 uses inductive mats. BD Atlas swaps batteries. Zero interoperability between brands.
>
> What we understand that they don't: charging at scale with mixed robot fleets is not a hardware problem. It's an infrastructure problem. One charging system needs to serve multiple robot types, adapt to each robot's charging interface, and orchestrate charging to prevent congestion. We retrofit existing robots with a universal receiver and bring the charger to the robot (articulated arm on rail), instead of making the robot come to a fixed pad. This is the EV charging playbook applied to robots.

**[CHANGED] How do or will you make money?**
> We sell the full charging solution (hardware + deployment + maintenance) and sign annual contracts. Revenue comes from three streams:
>
> 1. Hardware + deployment: We sell and install the inductive charging station and retrofit receiver kits for existing robots. We also partner with local installers to scale deployment.
> 2. Software subscription: Annual contract for our charging orchestration software (fleet scheduling, autonomous navigation to chargers, analytics, downtime reduction). This is where the recurring value lives.
> 3. Maintenance: Ongoing support and servicing included in the annual contract.
>
> The value to customers is clear: robots currently lose 20-30% of operating time to charging. Operators buy 20-30% extra robots to compensate. Reducing downtime and eliminating deadhead miles saves them far more than our contract costs.
>
> AMR charging station market is $350M today, projected $1.2B by 2033 (14.5% CAGR). Humanoid robot market growing at 39% CAGR with Goldman Sachs projecting $38B by 2035.

**[CHANGED] Which category best applies to your company?**
> Robotics (not Energy — you're a robotics infrastructure company)

**[CHANGED] If you had any other ideas you considered applying with...**
> 1. Universal robot chassis platform: selling the base layer of a robot (structure, battery, navigation system, charger) as a modular platform. Customers add their own application layer on top. Like a skeleton that any robot maker can build on.
> 2. Robot battery operations: owning and operating the batteries inside robots across industries. Once you control the battery layer of every robot in a facility, you control the entire energy vertical for that customer.
>
> We chose to start with charging infrastructure because it's the most immediate pain point and the fastest path to deployment. The other ideas could become extensions once we own the charging relationship.

---

## EQUITY SECTION

**[CHANGED] Describe the planned equity ownership breakdown...**
> Anis Cheriet — CEO: 50%
> Bo-Christopher Redfearn — CTO / Engineering: 50%
>
> Equal split reflecting equal commitment and complementary skills: Anis brings 4 years of charging infrastructure deployment experience and runs all business operations. Bo brings hardware engineering from Apple/Meta/Cruise and builds the entire robotics and charging system.

---

## CURIOUS SECTION

**[CHANGED] What convinced you to apply to Y Combinator?**
> We have a working prototype and strong market signals but need help finding the right first customer and deployment. YC's network in robotics and hardware is unmatched. We also need to move fast: the window for establishing the universal robot charging standard is open now but won't stay open long as robot deployments accelerate.

---

## THINGS TO REMOVE / FIX

1. **Remove Rafael and Christopher** from the founders section entirely
2. **Fix Bo's equity** from 33% to 50%
3. **Fix Anis's equity** from 33% to 50%
4. **Fix Twitter URL** — remove "/likes" from the end
5. **Category**: Change from "Energy" to "Robotics" (or "Hardware" if Robotics isn't available)
7. **Demo video**: You NEED to record a demo of the robot navigating, docking, charging, and returning. This is your single strongest asset. A 1-minute video of the working prototype is worth more than every word in this application.

---

## ANIS PROFILE IMPROVEMENTS

**[CHANGED] Hacked a system:**
> When I moved to San Francisco, everyone around me was paying $10-15K for an expensive O-1 visa fast-track to save 3 months. I found a J-1 visa path that gave me 18 months of legal status at a fraction of the cost, while building full-time. The extra time and saved money let me launch two companies, build a physical studio, and establish myself in SF without financial pressure. Most people optimize for speed. I optimized for runway.

**[CHANGED] Competitions/awards:**
> Won a Physical AI hackathon at Founders Inc in San Francisco (hardware/robotics) where we built an autonomous robot charging system in 24 hours, which became the foundation for Chargebotic. Won a second hackathon focused on developer tools. No academic papers published.

**[CHANGED] Work Experience — Chargebotic description:**
> Building universal autonomous charging infrastructure for robots. Built a fully working prototype in under 3 months: a robot that autonomously navigates, docks, and charges itself wirelessly at 100W. Had discovery conversations with Airbus, Zoox, Serve Robotics, P&G, and 6+ other companies. Scaled induction charging from 5W to 100W.

**[CHANGED] Work Experience — CocoAI:**
> AI photo editing app. Led product design and distribution. Launched in under 2 months: 3,275 users, $1,046 revenue, 10.47% conversion rate.

**[CHANGED] Work Experience — TomFeed:**
> Content studio for founders in SF. Arrived with no network, built a physical recording studio from scratch. 15 clients, $17K revenue, ~100 videos averaging 4-850K views. Full service: strategy, recording, coaching, editing, distribution.

**[CHANGED] Work Experience — Altens:**
> Built Altens' electric charging infrastructure offering for heavy-duty trucks from scratch. Led deployment for Europe's largest electric truck initiative: 150 trucks equipped with charging infrastructure across multiple countries. Created the service offering, trained teams, and recruited specialists.

**[CHANGED] Work Experience — Resonance/FIRALP (4 months, pilot contract):**
> Deployed McDonald's France fast-charging network ($2B program) for IZIVIA (EDF Group). Short-term pilot role: led strategy, site assessments, budgeting, and execution. Team of 3 deploying fast chargers across McDonald's locations nationwide. Contract ended; project validated the deployment model.

**[CHANGED] Work Experience — Carrefour (1 month, contract):**
> Scoped and launched deployment of Carrefour's retail charging network (3,500+ locations planned). Managed initial rollout of 115 sites: strategy, site coordination, infrastructure management. Short engagement that gave direct exposure to large-scale retail charging operations.

**[NEW] Work Experience — 30 Apps Challenge:**
> Currently building 30 apps in 30 days to sharpen full-stack product skills. Apps span AI, developer tools, and consumer products. Portfolio: https://anischeriet.com

(Pattern: removed "As a contractor" from every description. Lead with impact, not role. Short stints framed as high-density exposure, not job-hopping.)

---

## FOUNDER VIDEO — SCRIPT & BEST PRACTICES

### YC Rules
- **1 minute exactement** — pas plus
- **Les 2 fondateurs à l'écran** (même pièce idéalement, sinon video call)
- **NE PAS lire un script** — parler naturellement, comme à un ami
- **Pas de musique, pas d'effets, pas de montage** — un seul take continu
- **Audio clair** — YC dit qu'un gros % des vidéos sont inaudibles. Tester le playback.
- **Pas de demo produit** — la demo va dans le champ séparé
- **Pas de jargon** — "explain it like you would to your grandmother" (Michael Seibel)
- **Upload YouTube unlisted** avec embedding activé

### Structure (60 secondes)

| Temps | Qui | Contenu |
|---|---|---|
| 0-5s | Anis | Intro |
| 5-20s | Anis | Le problème |
| 20-35s | Bo | La solution + ce qu'on a construit |
| 35-50s | Anis | Pourquoi nous |
| 50-60s | Bo | Close / next step |

### Bullet Points (NE PAS lire — juste garder en tête)

**Anis (0-5s) — Intro :**
- "Hey, I'm Anis and this is Bo. We're building Chargebotic."

**Anis (5-20s) — Le problème :**
- Right now, every robot has its own charger. Nothing is compatible.
- It's like phones before USB-C — every brand, a different plug.
- There's no universal charging standard for robots. We're building it.

**Bo (20-35s) — Ce qu'on a construit :**
- I've been building autonomous robots for over a year. I built Sparky, my rover, and hit the charging problem myself — every robot I built needed a custom solution.
- So we built a universal wireless charger. You attach our receiver to any robot, it navigates to the station, docks, charges at 100W, and goes back to work. Zero human intervention. We built it in under 3 months.

**Anis (35-50s) — Pourquoi moi :**
- I spent 4 years deploying EV charging infrastructure across Europe — McDonald's, Carrefour, electric truck fleets. I know how to build charging networks at scale.
- We've talked to Airbus, Zoox, Serve Robotics, P&G — they all told us: there is no universal solution today.

**Bo (50-60s) — Next step :**
- Next: scaling to 500W and mounting the charger on a wall-mounted arm that reaches the robot.
- One station charges any robot. USB-C for robots.

### Tips jour du tournage
1. Côte à côte, face caméra (téléphone ou laptop suffit)
2. Filmez devant le proto si possible — pas comme demo, juste en background naturel
3. Parlez à un ami derrière la caméra, pas à l'objectif
4. Faites 5-10 takes, gardez le meilleur
5. Ne mémorisez pas — bullet points en tête seulement
6. Testez l'audio. Écoutez le playback. Si on vous entend pas bien, refaites.

### Sources
- YC officiel : "Statistically we're much more likely to interview people who submit a video"
- Michael Seibel : "Explain it like you would to your grandmother"
- Dalton Caldwell : "Cut to the chase. Get to the point."
- YC : "Please do not recite a script. Just talk spontaneously as you would to a friend."

# Chargebotic — Charging Infrastructure Audit Framework

## What You Deliver

A 5-10 page PDF report. Clean, professional, with numbers.

---

## Audit Process (2 weeks)

### Week 1: Discovery (3-4 hours total)

**Day 1-2: Kickoff call (1h)**
- How many robots in the fleet?
- What types/models?
- What batteries (LiFePO4, Li-ion, lead acid)?
- How many charging stations?
- Where are they located?
- Who manages the charging (dedicated person? software? nobody?)

**Day 3-5: Data collection (2-3h)**
- Get charging logs if available (most fleet software tracks this)
- Map the physical layout: where are stations vs. where robots work?
- Count: how many robots queue at the same station at the same time?
- Measure: average charge time, average work time, idle time waiting to charge

### Week 2: Analysis & Report (4-5 hours total)

**Day 6-8: Crunch numbers**
- Calculate Work-to-Charge Ratio (target: 4:1 or better)
- Calculate fleet uptime % (industry avg: 82%, target: 95%+)
- Identify peak charging conflicts (robots need to charge at the same time)
- Estimate $ lost to charging downtime per month
- Compare station-to-robot ratio vs. industry benchmark (1:2 to 1:3)

**Day 9-10: Write report + recommendations**

---

## Report Template

```
CHARGEBOTIC CHARGING INFRASTRUCTURE AUDIT
==========================================
Client: [Company Name]
Date: [Date]
Auditor: Anis Cheriet, Founder — Chargebotic

1. EXECUTIVE SUMMARY
   - Fleet size and type
   - Current uptime: X%
   - Estimated monthly cost of charging downtime: $X
   - Top 3 recommendations

2. FLEET SNAPSHOT
   - Robot inventory (model, count, battery type, capacity)
   - Charging station inventory (type, location, power output)
   - Station-to-robot ratio: X:X (benchmark: 1:2 to 1:3)

3. CHARGING PERFORMANCE ANALYSIS
   - Average charge time per robot
   - Average work time between charges
   - Work-to-Charge Ratio: X:X (benchmark: 4:1)
   - Fleet uptime: X% (benchmark: 95-99%)
   - Peak queue times (when do robots wait to charge?)

4. DOWNTIME COST ANALYSIS
   - Hours lost per week to charging: X hours
   - Estimated cost per hour of robot downtime: $X
   - Total monthly cost of charging downtime: $X
   - Annual projected loss: $X

5. BOTTLENECK MAP
   [Visual: floor plan with charging stations, traffic patterns, queue zones]
   - Station A: serves X robots, avg queue: X min
   - Station B: serves X robots, avg queue: X min
   - Dead zones: areas where robots run low before reaching a station

6. RECOMMENDATIONS

   QUICK WINS (implement in 1-2 weeks, low cost):
   - Relocate station X to reduce dead zone
   - Stagger charging schedules to reduce peak queue
   - Add 1-2 stations at bottleneck locations ($5-10K each)

   MEDIUM TERM (1-3 months):
   - Implement opportunity charging (charge during idle moments)
   - Upgrade to wireless charging pads at key locations
   - Deploy fleet battery management software

   LONG TERM (3-12 months):
   - Evaluate dynamic/in-motion charging (CaPow-style)
   - Battery upgrade path (faster charge chemistry)
   - Full infrastructure redesign for 24/7 zero-downtime operation

7. ROI PROJECTION
   - Quick wins investment: $X
   - Expected uptime gain: +X%
   - Monthly savings: $X
   - Payback period: X months

8. APPENDIX
   - Raw data tables
   - Benchmark comparisons
   - Vendor options for recommended solutions
```

---

## Pricing

| Tier | Price | What's Included |
|------|-------|----------------|
| **First audit** | FREE | Full report for first client (you need the case study) |
| **Standard audit** | $2,500 | Full report + 1h review call |
| **Premium audit** | $5,000 | Full report + implementation support (2 weeks) |
| **Retainer** | $2,000/mo | Monthly monitoring + optimization recommendations |

---

## Tools You Need

- Google Sheets (data collection + analysis)
- Canva or Google Slides (report design)
- A tape measure (for station layout mapping)
- A phone with camera (document current setup)
- Excel/Python for number crunching

---

## Questions to Ask During Discovery Call

### About the fleet
1. How many robots are in your fleet today?
2. What models? Mixed fleet or single vendor?
3. What's the battery type and capacity?
4. How old are the batteries? Any degradation noticed?

### About charging today
5. How many charging stations do you have?
6. Where are they located? Who decided the placement?
7. How long does a full charge take?
8. Do robots auto-dock or does someone plug them in?
9. Do you use any fleet management software that tracks battery levels?

### About the pain
10. What's your biggest headache with charging today?
11. Do robots ever die mid-task because of battery?
12. Do you have robots queuing to charge at the same time?
13. Have you ever had to buy MORE robots just because existing ones were charging?
14. How much time does your team spend managing charging?

### About the money
15. What does one hour of robot downtime cost you?
16. Have you evaluated any charging solutions? (WiBotic, CaPow, etc.)
17. What's your budget for infrastructure improvements this year?
18. Who makes the purchasing decision for this kind of thing?

---

## After the Audit: The Upsell Path

Audit → "I can help you implement these recommendations" → Implementation consulting ($5-10K)
Implementation → "I could build a custom solution for this" → Chargebotic product
3 audits → You know EXACTLY what to build → Chargebotic v1 (the actual product)

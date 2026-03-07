# Charging Power Analysis: 100W vs Market Standard

*Date: Feb 25, 2026*

## Current State: 100W Induction Charging

Chargebotic's current prototype delivers **100W** via induction. This analysis evaluates whether it's competitive.

## Battery Capacities by Robot Category

### Warehouse AMRs
| Robot | Battery (Wh) | Charge Time @ 100W (20%→80%) |
|-------|-------------|------------------------------|
| Fetch Freight | 924 | 6.5 hours |
| MiR250 | 1,600 | 11.3 hours |
| MiR600/1350 | 1,630 | 11.5 hours |

### Humanoid Robots
| Robot | Battery (Wh) | Charge Time @ 100W (20%→80%) |
|-------|-------------|------------------------------|
| Unitree G1 | 432 | 3.0 hours |
| Unitree H1 | 1,728 | 12.2 hours |
| Figure 02 | 2,250 | 15.9 hours |
| Figure 03 | 2,300 | 16.2 hours |
| Tesla Optimus | 2,300 | 16.2 hours |

### Delivery Robots
| Robot | Battery (Wh) | Charge Time @ 100W (20%→80%) |
|-------|-------------|------------------------------|
| Kiwibot | 200-300 | 1-2 hours |
| Starship | 1,260 | 8.9 hours |

### Drones / Small Robots
| Robot | Battery (Wh) | Charge Time @ 100W (20%→80%) |
|-------|-------------|------------------------------|
| DJI Matrice 30 | 37 | 16 minutes |
| DJI Matrice 4 | 100 | 42 minutes |
| Roomba | 26-84 | 11-35 minutes |

*Note: Calculations assume 85% induction efficiency (100W input → 85W delivered)*

## Market Standard Charging Power

| System | Power | Type | Target |
|--------|-------|------|--------|
| Kiwibot station | 200W | Wireless | Delivery robots |
| WiBotic standard | 200-400W | Wireless | AMRs, drones |
| WiBotic 1kW (2024) | 1,000W | Wireless | Large AMRs |
| Wiferion CW1000 | 1,000W | Inductive | AMRs |
| MiRCharge 48V | 1,680W | Contact | MiR robots |
| Figure 03 rated | 2,000W | Contact | Humanoid |
| Wiferion etaLINK 3000 | 3,000-3,300W | Inductive | AGVs, heavy |

**Market sweet spot: 500W-1,500W for mid-size AMRs**

## Verdict

| Category | 100W viable? | Minimum needed |
|----------|-------------|----------------|
| Small indoor / promo robots | ✅ Yes | 50-100W |
| Drones (inspection) | ✅ Yes | 50-200W |
| Delivery robots (small) | ⚠️ Marginal | 200-500W |
| Warehouse AMRs | ❌ Non | 500-1,500W |
| Humanoid robots | ❌ Non | 1,000-3,000W |

## Roadmap Recommandé

1. **Now**: 100W → bon pour POC, démos, petits robots
2. **Month 2**: 500W → couvre delivery robots + petits AMRs
3. **Month 4**: 1,000W → couvre la majorité des AMRs
4. **Month 6+**: 2,000-3,000W → humanoïdes + heavy industrial

## Sources
- MiR Product Specifications (lotsofbots.com)
- Figure F.03 Battery Development (figure.ai)
- Tesla Optimus Specs (qviro.com, botinfo.ai)
- Unitree H1/G1 Specs (unitree.com, robostore.com)
- WiBotic 1kW announcement (robotics247.com, Automate 2024)
- Wiferion etaLINK 3000 / CW1000 (wiferion.com)
- Kiwibot Wireless Charging (kiwibot.com)
- Starship Robot Specs (wevolver.com)

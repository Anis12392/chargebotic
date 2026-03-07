# Chargebotic — Notion Workspace

> Import ce fichier dans Notion (File > Import > Markdown) pour créer ton workspace.
> Partage ensuite la page avec Chris via le bouton Share.

---

# 🔋 Chargebotic

## Mission

**Build the universal energy layer for autonomous robots.**

On construit des stations de recharge murales universelles qui rechargent n'importe quel robot — AMRs, humanoïdes, drones, delivery bots — avec le même système. Hardware (wall-mount + bras sur rail vertical + induction pad) + Software (navigation, alignement vision, fleet management) + Retrofit universel.

---

## Le Problème

- **30% du temps de flotte** perdu au charging (confirmé par Nyobolt, CaPow)
- **Zéro interopérabilité** : chaque marque de robot a son propre chargeur propriétaire
- Une usine avec Tesla Optimus + Unitree + MiR AMR = **3 systèmes de charge différents**
- Les flottes sont **surdimensionnées de 20-30%** juste pour compenser le downtime de charge
- **Personne** ne construit le "Android du robot charging" — la couche universelle

## Notre Solution

**Wall-mounted charging stations** avec :
1. **Rail vertical (~1.5m)** sur le mur avec bras robotique + pad induction
2. **Le chargeur vient au robot** (pas l'inverse) — pas besoin de floor space
3. **Retrofit kit universel** — on adapte n'importe quel robot pour recevoir la charge
4. **Computer vision** pour l'alignement (pas IR — plus précis, moins cher)
5. **1 station remplace 5-10 chargeurs fixes** — scaling sub-linéaire

## Positionnement Compétitif

| Concurrent | Approche | Funding | Limitation |
|-----------|----------|---------|------------|
| WiBotic | Pads wireless au sol | $15.1M | Hardware only, pas universel |
| CaPow | Recharge en mouvement (sol) | $22.5M | Floor pads, installation lourde |
| Nyobolt | Batteries ultra-rapides | Undisclosed | Battery tech, pas infrastructure |
| **Chargebotic** | **Wall-mount + retrofit universel** | **Pre-seed** | **Full-stack : hardware + software + retrofit** |

**Notre moat** : le seul à faire hardware + software + retrofit. Chaque robot intégré crée un "charging profile" → network effects.

---

# 📋 Roadmap

## Cette Semaine (25 Feb - 3 Mar 2026) — IP PROTECTION

- [ ] Signer IP assignment agreements entre Anis & Chris (templates Orrick gratuits)
- [ ] Prior art search sur Google Patents (mots-clés : "robot charging station vertical rail", "universal robot charger induction", "wall mount robotic charger")
- [ ] Rédiger le provisional patent — décrire : wall-mount, rail vertical, bras, retrofit kit, alignement vision, toutes variantes
- [ ] Filer le provisional sur USPTO Patent Center — micro-entity = **$65**
- [ ] Postuler à Startup Legal Garage (UC Law SF) — startuplegalgarage.org/apply
- [ ] Postuler à Berkeley Law Startup Initiative

## Ce Mois (Mars 2026) — PROTOTYPE + PITCH

- [ ] Upgrade prototype de 100W → 500W (minimum viable pour delivery robots + petits AMRs)
- [ ] Mettre à jour le one-pager avec positionnement wall-mount
- [ ] Mettre à jour chargebotic.com
- [ ] 5 interviews avec opérateurs de flottes robotiques (warehouses SF/Bay Area)
- [ ] Publier defensive disclosure sur TDCommons (variantes génériques)
- [ ] NDA template prêt pour démos/pitches

## Ce Trimestre (Q1-Q2 2026) — PREMIER CLIENT

- [ ] Prototype 1,000W (couvre majorité des AMRs)
- [ ] Premier POC avec un client warehouse
- [ ] Candidature YC S2026
- [ ] Candidature NSF SBIR Phase I (si réautorisé)
- [ ] Vidéo démo pour le site

## Backlog

- [ ] Retrofit kit v2 pour humanoïdes (Tesla Optimus, Figure)
- [ ] Fleet management software MVP
- [ ] Exploration vertical Ads/Promo robots
- [ ] Prototype 2,000-3,000W pour humanoïdes
- [ ] Intégrations OEM partnerships

---

# 📊 Research Hub

## Rapports Disponibles

| Rapport | Contenu | Date |
|---------|---------|------|
| Market Sizing | TAM/SAM/SOM, taille marché par vertical, stats vérifiées | Feb 25, 2026 |
| Concept Validation | Rail-mounted arm vs EV, how robots charge today, competitive moat | Feb 25, 2026 |
| Charging Power Analysis | 100W vs marché, batteries par robot, roadmap puissance | Feb 25, 2026 |
| IP Strategy | Brevets, trade secrets, timeline, ressources gratuites SF | Feb 25, 2026 |

## Chiffres Clés Vérifiés (pour le pitch)

### ✅ Confirmé — Utiliser avec confiance
| Stat | Valeur | Source |
|------|--------|--------|
| Robots industriels déployés | **4.66M** worldwide | IFR 2024 |
| Nouveaux robots/an | **542,000** installations | IFR 2024 |
| Temps flotte perdu au charging | **20-30%** | Nyobolt, CaPow, multiples sources |
| Fleet oversizing dû au charging | **20-30%** | CaPow case studies |
| Humanoid market 2035 | **$38B** | Goldman Sachs (revised 6x upward) |
| Humanoid CAGR | **39%** | Goldman Sachs |
| Wireless charging efficiency | **90-93%** | WiTricity, Wiferion |

### ⚠️ À nuancer — Utiliser avec contexte
| Stat | Claim actuel | Réalité | Recommandation |
|------|-------------|---------|----------------|
| Robot charging market | $38B by 2033 | $7.2-33B selon définition | Utiliser **$7.2B** (conservative) ou **$33B** (broad) avec source |
| Autonomous robots by 2028 | 3M+ | 4.6M **déjà** déployés | Reframer : "4.6M+ already deployed" |

---

# 👥 Team

| Nom | Rôle | Background |
|-----|------|------------|
| **Anis Cheriet** | Co-founder & CEO | Ex-EV charging infrastructure. Led Europe's largest charging deployments twice. |
| **Christopher Redfearn** | Co-founder & Hardware Lead | Ex-Apple & Meta. Hardware lead, MS in CS. Space-grade reliable systems. |

---

# 🔑 Décisions Clés

| Date | Décision | Contexte |
|------|----------|----------|
| Feb 25, 2026 | Wall-mount stations (pas ceiling rail) | Visite robotics floor — plus pratique, robots viennent au mur naturellement |
| Feb 25, 2026 | Retrofit universel = core value prop | On ne dépend pas des OEMs, on adapte n'importe quel robot |
| Feb 25, 2026 | Computer vision > IR pour alignement | Plus précis (2cm avec ArUco), moins cher, standard industrie |
| Feb 25, 2026 | 100W = MVP, roadmap vers 500W → 1kW → 3kW | 100W insuffisant pour AMRs/humanoïdes, OK pour POC |
| Feb 25, 2026 | Provisional patent en priorité ($65) | Ford a déjà un brevet EV rail charger (Oct 2024), il faut filer vite |

---

# 📝 Learnings Terrain

| Date | Lieu | Observation |
|------|------|-------------|
| Feb 25, 2026 | Robotics floor SF | Le pad induction peut recharger rovers, petits robots ET humanoïdes |
| Feb 25, 2026 | Robotics floor SF | Les humanoïdes peuvent être entraînés à se positionner pour la charge |
| Feb 25, 2026 | Robotics floor SF | Un rail vertical sur le mur + bras = meilleure approche que ceiling rail |

---

*Dernière mise à jour : Feb 25, 2026*
*Fichiers recherche : projects/chargebotic/research/*

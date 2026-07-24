"""
Create the Wirebird Fundraising Strategy Google Sheets document
directly via the Google Sheets API.

Requires credentials.json in ~/claude-code-official-memory/
Run once — it will open a browser for auth if no valid token exists.
"""

import os, sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
ROOT = os.path.expanduser("~/claude-code-official-memory")
CREDS_PATH = os.path.join(ROOT, "credentials.json")
TOKEN_PATH = os.path.join(ROOT, "token.json")


def get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


# ── Colour palette (RGB hex) ──────────────────────────────────────────────────
NAVY   = {"red": 0.067, "green": 0.212, "blue": 0.384}
TEAL   = {"red": 0.180, "green": 0.518, "blue": 0.541}
GREEN  = {"red": 0.180, "green": 0.459, "blue": 0.235}
ORANGE = {"red": 0.898, "green": 0.498, "blue": 0.188}
GOLD   = {"red": 0.984, "green": 0.753, "blue": 0.012}
LTBLUE = {"red": 0.722, "green": 0.878, "blue": 0.996}
LTGRN  = {"red": 0.851, "green": 0.918, "blue": 0.847}
WHITE  = {"red": 1, "green": 1, "blue": 1}
DKGRAY = {"red": 0.2, "green": 0.2, "blue": 0.2}


def rgb(r, g, b):
    return {"red": r/255, "green": g/255, "blue": b/255}


def hdr(text, bg, fg=WHITE, bold=True, size=11, wrap="WRAP", halign="CENTER"):
    return {
        "userEnteredValue": {"stringValue": text},
        "userEnteredFormat": {
            "backgroundColor": bg,
            "textFormat": {"foregroundColor": fg, "bold": bold, "fontSize": size},
            "horizontalAlignment": halign,
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": wrap,
        }
    }


def cell(val, bg=None, bold=False, fg=DKGRAY, wrap="WRAP", halign="LEFT"):
    if val is None:
        v = {"stringValue": ""}
    elif isinstance(val, (int, float)):
        v = {"numberValue": val}
    else:
        v = {"stringValue": str(val)}
    fmt = {
        "textFormat": {"foregroundColor": fg, "bold": bold},
        "horizontalAlignment": halign,
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": wrap,
    }
    if bg:
        fmt["backgroundColor"] = bg
    return {"userEnteredValue": v, "userEnteredFormat": fmt}


def rows(*row_list):
    return [{"values": r} for r in row_list]


# ═══════════════════════════════════════════════════════════════════════════════
# Sheet data builders
# ═══════════════════════════════════════════════════════════════════════════════

def build_vision():
    """Sheet 1: Vision & Roadmap"""
    data = []

    # Title
    data.append({"values": [hdr("WIREBIRD — FUNDRAISING STRATEGY 2026", NAVY, size=14)]})
    data.append({"values": [hdr("Wirebird Aerospace | Energy distribution from power lines", NAVY, size=10)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    # Section header
    data.append({"values": [hdr("FUNDRAISING ROUNDS", TEAL)]})

    # Column headers
    data.append({"values": [
        hdr("Round", TEAL, size=10), hdr("Amount", TEAL, size=10),
        hdr("Valuation", TEAL, size=10), hdr("Target Date", TEAL, size=10),
        hdr("Purpose", TEAL, size=10), hdr("Key Milestones", TEAL, size=10),
        hdr("Status", TEAL, size=10),
    ]})

    rounds = [
        ("Angel SAFE",       "$20K",         "$5M cap",      "This week",  "Immediate bridge",             "—",                                                                         "🔴 To do"),
        ("Bridge",           "$200K",        "$5M cap",      "July 2026",  "Runway to Pre-Seed",           "Angels signed · ADAM $80K pilot covers most of gap",                        "🔴 Launch"),
        ("Pre-Seed",         "$2M",          "$10–15M",      "Oct 2026",   "Production + hangar",          "ADAM deal signed · JIFX demo · Patent · SBIR submitted (Aug)",              "🎯 Oct 2026"),
        ("SBIR DoD Ph.I",    "$150–300K",    "Non-dilutive", "~Mar 2027",  "DoD validation + cash",        "Submit Aug 2026 → ~9 months → award ~March 2027",                           "📅 Submit Aug"),
        ("SBIR SOCOM Ph.I",  "$150–300K",    "Non-dilutive", "~Mar 2027",  "SOCOM validation + cash",      "Parallel track → faster path to SOCOM direct contracts",                    "📅 Submit Aug"),
        ("Seed",             "$8M–$10M",     "TBD",          "May 2027",   "B2B2G scale + ops cell",       "300 units B2B2G · $6.5M–$20M rev · Both SBIR Ph.I awards",                  "📅 May 2027"),
        ("SBIR Ph.II",       "$750K–$2M×2",  "Non-dilutive", "2027–2028",  "Unlocks DoD + SOCOM direct",   "DoD & SOCOM Phase II → direct contracts both tracks",                       "📅 2027–28"),
        ("Series A",         "$50M",         "TBD",          "May 2028",   "Direct DoD + utility scale",   "SOCOM contracts · Utility pilots · $30M+ rev",                              "📅 May 2028"),
        ("Series B+",        "TBD",          "TBD",          "2029–2030",  "Market leadership + Moon",     "$200M+ rev · International · Moon roadmap",                                 "📅 2029+"),
    ]
    colors = [NAVY, TEAL, GREEN, TEAL, TEAL, GREEN, TEAL, ORANGE, ORANGE]
    for i, (r_name, amt, val, dt, purpose, miles, status) in enumerate(rounds):
        bg = rgb(229+i*2, 237+i, 246+i) if i % 2 == 0 else WHITE
        data.append({"values": [
            cell(r_name, bg, bold=True), cell(amt, bg), cell(val, bg),
            cell(dt, bg), cell(purpose, bg), cell(miles, bg), cell(status, bg),
        ]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    # Revenue path header
    data.append({"values": [hdr("REVENUE PATH TO $1B", NAVY)]})
    data.append({"values": [
        hdr("Year", NAVY, size=10), hdr("Phase", NAVY, size=10),
        hdr("Units", NAVY, size=10), hdr("B2B2G Rev", NAVY, size=10),
        hdr("SBIR/Gov", NAVY, size=10), hdr("Commercial", NAVY, size=10),
        hdr("Total Rev", NAVY, size=10), hdr("Notes", NAVY, size=10),
    ]})

    rev = [
        ("2026", "Phase 1 — B2B2G only",      "12",       "$650K\n(ADAM: $80K pilot + $570K order)", "$0",        "$0",         "$650K",              "B2B2G only (ADAM, Chariot)\nSBIR submitted — no money yet\nNo direct DoD yet"),
        ("2027", "Phase 1→2 — B2B2G + SBIR",  "100–300",  "$6.5M–$19.5M",                             "$60K",      "$0",         "$6.5M–$20M",         "300 drones via B2B2G\nSBIR Phase I award ~March 2027\nSeed raise May 2027"),
        ("2028", "Phase 3 — Direct DoD + Utils","300–600", "$19.5M–$39M",                              "$1.5M",     "$5M–$10M",   "$26M–$51M",          "SOCOM + direct DoD contracts\nSBIR Phase II award\nSeries A $50M"),
        ("2029", "Phase 4 — Scale",            "600–1500", "$39M–$97.5M",                              "$5M–$10M",  "$20M–$50M",  "$100M–$200M",        "DoD direct at scale\nUtility commercial rollout\nInternational expansion"),
        ("2030", "Phase 4 — $1B Target",       "2000+",    "$130M+",                                   "$25M+",     "$200M+",     "$1,000,000,000",     "Full scale · Moon roadmap\nIPO / late stage"),
    ]
    for i, row in enumerate(rev):
        bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell(v, bg) for v in row]})

    return data


def build_business():
    """Sheet 2: Business Model"""
    data = []
    data.append({"values": [hdr("WIREBIRD — BUSINESS MODEL & GTM", NAVY, size=13)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    data.append({"values": [hdr("PRICING & UNIT ECONOMICS", TEAL)]})
    pricing = [
        ("Unit price (hardware)",  "$65,000",      "Per drone unit"),
        ("SaaS / maintenance",     "$5,000/yr",    "Per unit per year"),
        ("ADAM pilot contract",    "$80K (2 units)","Pilot; deducted from 10-unit order"),
        ("ADAM full order",        "$650K",         "10 units @ $65K — $80K pilot already paid"),
        ("Gross margin target",    "60–70%",        "Based on BOM + assembly estimates"),
        ("Payback for customer",   "< 12 months",   "Based on saved downtime / uptime gain"),
    ]
    data.append({"values": [hdr("Item", TEAL, size=10), hdr("Value", TEAL, size=10), hdr("Note", TEAL, size=10)]})
    for i, (item, val, note) in enumerate(pricing):
        bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell(item, bg, bold=True), cell(val, bg), cell(note, bg)]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("GO-TO-MARKET — 4 PHASES", NAVY)]})
    gtm = [
        ("Phase 1 — NOW 2026",       "B2B2G Only",             "Sell through ADAM, Chariot & prime contractors\nNOT direct DoD yet · SBIR submitted Aug 2026 (money in 9 months)"),
        ("Phase 2 — 2027",           "Dual SBIR + B2B2G Scale","Both SBIR Phase I awards ~March 2027 (~$300K–$600K non-dilutive)\n300 units B2B2G · Apply SBIR Phase II"),
        ("Phase 3 — 2028",           "Direct DoD / SOCOM",     "SBIR Phase II unlocks DoD & SOCOM direct\nUtility pilots begin (18mo post-Pre-Seed) · Series A $50M"),
        ("Phase 4 — 2029–2030",      "Scale + Space",           "International, full commercial rollout\nMoon roadmap · $1B target"),
    ]
    data.append({"values": [hdr("Phase", NAVY, size=10), hdr("Label", NAVY, size=10), hdr("Key Actions", NAVY, size=10)]})
    for i, (ph, label, actions) in enumerate(gtm):
        bg = LTGRN if i % 2 == 0 else WHITE
        data.append({"values": [cell(ph, bg, bold=True), cell(label, bg), cell(actions, bg)]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("COMPETITIVE BENCHMARKS", TEAL)]})
    comps = [
        ("WindLift",  "$20M raised",    "Persistent aerial platform — similar fundraise trajectory"),
        ("Anduril",   "$1.5B raised",   "Defense autonomy — confirms defense market appetite"),
        ("SpaceX",    "Multi-billion",  "Space + energy distribution — long-term vision alignment"),
        ("Chariot",   "B2B2G model",    "Prime contractor distribution — our GTM partner model"),
    ]
    data.append({"values": [hdr("Company", TEAL, size=10), hdr("Stage", TEAL, size=10), hdr("Relevance", TEAL, size=10)]})
    for i, row in enumerate(comps):
        bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell(v, bg) for v in row]})

    return data


def build_budget():
    """Sheet 3: 6-Month Budget"""
    data = []
    data.append({"values": [hdr("WIREBIRD — 6-MONTH BUDGET (Jun–Nov 2026)", NAVY, size=13)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    headers = ["Category", "Item", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Total", "Notes"]
    data.append({"values": [hdr(h, NAVY, size=10) for h in headers]})

    budget_rows = [
        # (category, item, jun, jul, aug, sep, oct, nov, notes)
        ("Salaries",    "Anis (CEO) — full-time",         7000,  7000,  7000,  7000,  7000,  7000,  "Minimum viable salary"),
        ("Salaries",    "Christopher (HW) — full-time",   7000,  7000,  7000,  7000,  7000,  7000,  "Minimum viable salary"),
        ("Salaries",    "Part-time #1",                   3500,  3500,  3500,  3500,  3500,  3500,  "Software / ops support"),
        ("Salaries",    "Part-time #2",                   3500,  3500,  3500,  3500,  3500,  3500,  "Engineering support"),
        ("Components",  "Hardware / BOM",                 5000,  4000,  5000,  6000,  5000,  5000,  "JIFX prototype + ADAM units"),
        ("Events",      "JIFX (in 2 months)",             0,     8000,  0,     0,     0,     0,     "Travel, logistics, demo setup"),
        ("Events",      "T-REX 26-3",                     0,     0,     0,     15000, 0,     0,     "More commercial / procurement focused"),
        ("Events",      "2 additional events",            0,     0,     0,     5000,  5000,  0,     "Outreach + demos"),
        ("Legal",       "Patent (provisional)",           0,     2000,  0,     0,     0,     0,     "Protect drone energy distribution tech"),
        ("Legal",       "SAFE legal review",              800,   0,     0,     0,     0,     0,     "Clerky SAFEs"),
        ("Software",    "AI subscriptions",               500,   500,   500,   500,   500,   500,   "Claude, Cursor, etc."),
        ("Software",    "Cloud / infra",                  500,   400,   400,   400,   400,   400,   "AWS / GCP / tools"),
        ("SBIR",        "SBIR prep (DoD + SOCOM)",        0,     0,     5000,  2000,  0,     0,     "Proposal writing, review, submission"),
        ("Travel",      "Investor meetings / Bay Area",   1000,  1000,  1000,  1000,  1000,  1000,  "Pre-Seed outreach"),
        ("Misc",        "Insurance / admin",              500,   500,   500,   500,   500,   500,   "Business expenses"),
    ]

    categories = {}
    for row in budget_rows:
        cat = row[0]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(row)

    cat_colors = {
        "Salaries": rgb(173, 216, 230),
        "Components": rgb(144, 238, 144),
        "Events": rgb(255, 218, 185),
        "Legal": rgb(221, 160, 221),
        "Software": rgb(255, 255, 180),
        "SBIR": rgb(200, 230, 200),
        "Travel": rgb(230, 220, 255),
        "Misc": rgb(230, 230, 230),
    }

    col_totals = [0]*6
    grand_total = 0

    for cat, rows_in_cat in categories.items():
        bg = cat_colors.get(cat, WHITE)
        for i, row in enumerate(rows_in_cat):
            cat_label, item, *monthly, notes = row
            total = sum(monthly)
            for j, v in enumerate(monthly):
                col_totals[j] += v
            grand_total += total
            row_bg = bg if i % 2 == 0 else WHITE
            data.append({"values": [
                cell(cat_label if i == 0 else "", row_bg, bold=(i==0)),
                cell(item, row_bg),
                *[cell(f"${v:,}" if v else "—", row_bg, halign="RIGHT") for v in monthly],
                cell(f"${total:,}", row_bg, bold=True, halign="RIGHT"),
                cell(notes, row_bg),
            ]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [
        hdr("MONTHLY TOTALS", TEAL, size=10),
        cell(""),
        *[cell(f"${v:,}", LTBLUE, bold=True, halign="RIGHT") for v in col_totals],
        cell(f"${grand_total:,}", TEAL, bold=True, halign="RIGHT"),
        cell(""),
    ]})

    return data


def build_captable():
    """Sheet 4: Cap Table"""
    data = []
    data.append({"values": [hdr("WIREBIRD — CAP TABLE SIMULATION", NAVY, size=13)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    data.append({"values": [hdr("CURRENT (Pre-Bridge)", TEAL)]})
    data.append({"values": [hdr("Founder", TEAL, size=10), hdr("Shares", TEAL, size=10), hdr("Ownership %", TEAL, size=10), hdr("Notes", TEAL, size=10)]})
    current = [
        ("Anis Cheriet (CEO)",          "4,900,000", "49%", "Co-founder"),
        ("Christopher Redfearn (HW)",    "5,100,000", "51%", "Co-founder"),
        ("Total",                         "10,000,000","100%","Pre-money"),
    ]
    for i, row in enumerate(current):
        bg = LTBLUE if i % 2 == 0 else WHITE
        bold = (i == len(current)-1)
        data.append({"values": [cell(v, bg, bold=bold) for v in row]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("BRIDGE SAFE — $200K at $5M Cap", NAVY)]})
    data.append({"values": [
        cell("Bridge amount", LTBLUE, bold=True), cell("$200,000", LTBLUE),
        cell("Valuation cap", LTBLUE, bold=True), cell("$5,000,000", LTBLUE),
    ]})
    data.append({"values": [
        cell("SAFE converts at Pre-Seed close ($2M at $10–15M)", None, bold=True, fg=TEAL),
    ]})
    data.append({"values": [
        cell("Implied % at conversion: ~1.5–2% per $100K invested", None, bold=False),
    ]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("POST PRE-SEED SIMULATION ($2M raised at $10M cap)", GREEN)]})
    data.append({"values": [hdr("Shareholder", GREEN, size=10), hdr("Shares", GREEN, size=10), hdr("% Post-money", GREEN, size=10)]})
    post = [
        ("Anis Cheriet",            "4,900,000",  "~38%"),
        ("Christopher Redfearn",     "5,100,000",  "~39%"),
        ("Bridge SAFE holders",      "~280,000",   "~2–3%"),
        ("Pre-Seed Investors",        "~2,560,000", "~20%"),
        ("Option Pool (proposed)",    "~0",         "0% now → 10–15% post"),
        ("Total",                     "~12,840,000","100%"),
    ]
    for i, row in enumerate(post):
        bg = LTGRN if i % 2 == 0 else WHITE
        bold = (i == len(post)-1)
        data.append({"values": [cell(v, bg, bold=bold) for v in row]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("⚠️  KEY NOTES FOR INVESTORS", ORANGE)]})
    notes = [
        "• SAFE does not change cap table until it converts at next priced round (Pre-Seed)",
        "• Post-Money Valuation Cap SAFE used (via Clerky)",
        "• Option pool will be created at Pre-Seed close (~10–15%)",
        "• Rafael M. removed from team as of March 2026 — no equity",
        "• Dual co-founder structure: Anis (49%) + Christopher (51%)",
        "• No outside investors yet — 100% founder-owned today",
    ]
    for note in notes:
        data.append({"values": [cell(note, rgb(255, 248, 220))]})

    return data


def build_milestones():
    """Sheet 5: Milestones"""
    data = []
    data.append({"values": [hdr("WIREBIRD — MILESTONES TO PRE-SEED CLOSE", NAVY, size=13)]})
    data.append({"values": [hdr("Retrograde plan from October 2026 target", NAVY, size=10)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    headers = ["When", "Milestone", "Owner", "Dependencies", "Status", "Impact"]
    data.append({"values": [hdr(h, TEAL, size=10) for h in headers]})

    milestones = [
        ("Now (Jun 2026)",     "Close Angel SAFE $20K (Clerky)",        "Anis",       "Investor ready",                 "🔴 This week",   "First check · validates interest"),
        ("Jul 2026",           "Complete ADAM $80K pilot contract",      "Anis",       "Negotiation ongoing",            "🟡 In progress", "First revenue · key Pre-Seed milestone"),
        ("Jul 2026",           "Bridge close $200K @ $5M cap",          "Anis",       "Angel network · JIFX",           "🔴 To do",       "Extends runway to Pre-Seed"),
        ("Aug 2026",           "JIFX demo (2 months from now)",          "Both",       "Prototype ready",                "🟡 Prep",        "Key DoD visibility · investor proof"),
        ("Aug 2026",           "Apply T-REX 26-3 (trex.events)",        "Anis",       "None",                           "🔴 Apply now",   "Commercial DoD procurement exposure"),
        ("Aug 2026",           "Submit SBIR DoD Phase I",               "Both",       "Write proposal",                 "🔴 To do",       "$150K–$300K non-dilutive if awarded"),
        ("Aug 2026",           "Submit SBIR SOCOM Phase I",             "Both",       "Write proposal",                 "🔴 To do",       "$150K–$300K non-dilutive if awarded"),
        ("Sep 2026",           "File provisional patent",               "Anis",       "Patent attorney ~$1,500",        "🔴 To do",       "IP protection before Pre-Seed close"),
        ("Sep 2026",           "ADAM 10-unit order signed ($650K)",     "Anis",       "ADAM deal progression",          "🟡 Ongoing",     "Strongest Pre-Seed proof point"),
        ("Sep 2026",           "Investor deck finalized",               "Anis",       "Metrics + demo video",           "🔴 To do",       "Start Pre-Seed outreach"),
        ("Sep–Oct 2026",       "Pre-Seed investor outreach (20+ VCs)", "Anis",       "Deck, demo, metrics",            "🔴 To do",       "Target $2M at $10–15M valuation"),
        ("Oct 2026",           "PRE-SEED CLOSE — $2M",                  "Anis",       "All above milestones hit",       "🎯 Target",      "18 months runway · Seed in May 2027"),
        ("~Mar 2027",          "SBIR Phase I awards (DoD + SOCOM)",     "Both",       "Submitted Aug 2026",             "📅 Projected",   "$300K–$600K combined non-dilutive"),
        ("May 2027",           "SEED — $8M–$10M",                       "Anis",       "Revenue, SBIR, team",            "📅 Projected",   "Scale B2B2G + hire ops team"),
        ("May 2028",           "SERIES A — $50M",                       "Anis",       "Direct DoD + utility pilots",   "📅 Projected",   "Full scale defense + commercial"),
    ]

    for i, row in enumerate(milestones):
        bg = LTGRN if "Oct 2026" in row[0] and "PRE-SEED" in row[1] else (LTBLUE if i % 2 == 0 else WHITE)
        bold = "PRE-SEED" in row[1] or "SEED" in row[1] or "SERIES" in row[1]
        data.append({"values": [cell(v, bg, bold=bold) for v in row]})

    return data


def build_bridge():
    """Sheet 6: Bridge Tracker"""
    data = []
    data.append({"values": [hdr("WIREBIRD — BRIDGE ROUND TRACKER ($200K TARGET)", NAVY, size=13)]})
    data.append({"values": [hdr("$5M Post-Money Valuation Cap SAFE via Clerky", NAVY, size=10)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    data.append({"values": [hdr("ROUND SUMMARY", TEAL)]})
    summary = [
        ("Target",             "$200,000"),
        ("Instrument",         "Post-Money SAFE (Clerky)"),
        ("Valuation Cap",      "$5,000,000"),
        ("Min check size",     "$10,000"),
        ("Converts at",        "Pre-Seed close (Oct 2026 target)"),
        ("Platform",           "Clerky for docs · Rho bank for wires"),
        ("Status",             "🔴 Launching now"),
    ]
    for i, (k, v) in enumerate(summary):
        bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell(k, bg, bold=True), cell(v, bg)]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("ANGEL TRACKER", NAVY)]})
    headers = ["Investor Name", "Amount Committed", "SAFE Signed?", "Wire Received?", "Date", "Notes"]
    data.append({"values": [hdr(h, NAVY, size=10) for h in headers]})

    # Empty rows for tracking
    for i in range(15):
        bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell("", bg) for _ in headers]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("TOTALS", TEAL)]})
    data.append({"values": [
        cell("Total committed", LTBLUE, bold=True),
        cell("(use SUM formula)", LTBLUE),
        cell(""), cell(""), cell(""), cell(""),
    ]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("HOW TO RECEIVE A WIRE (CHECKLIST)", ORANGE)]})
    steps = [
        "1. Send investor the Clerky SAFE link (Post-Money Valuation Cap, $5M)",
        "2. Both parties sign the SAFE electronically via Clerky",
        "3. Send investor Rho bank wire instructions (account + routing number)",
        "4. Wire arrives in Rho — confirm receipt and log date above",
        "5. Send investor a signed copy of the SAFE + wire receipt confirmation",
        "6. Track in this sheet. Update 'SAFE Signed' and 'Wire Received' columns.",
    ]
    for step in steps:
        data.append({"values": [cell(step, rgb(255, 248, 220))]})

    return data


# ═══════════════════════════════════════════════════════════════════════════════
# Main: build and upload
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import io
    from googleapiclient.http import MediaIoBaseUpload

    creds = get_creds()
    drive_svc = build("drive", "v3", credentials=creds)

    # Upload the Excel file and convert to Google Sheets
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "Desktop",
        "Wirebird_Fundraising_Strategy.xlsx",
    )
    # Fallback: look on actual Desktop
    if not os.path.exists(excel_path):
        excel_path = os.path.expanduser("~/Desktop/Wirebird_Fundraising_Strategy.xlsx")

    if not os.path.exists(excel_path):
        print(f"❌  Excel file not found at {excel_path}")
        print("Run execution/create_fundraising_excel.py first.")
        sys.exit(1)

    file_metadata = {
        "name": "Wirebird — Fundraising Strategy 2026",
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }
    with open(excel_path, "rb") as f:
        content = f.read()

    media = MediaIoBaseUpload(
        io.BytesIO(content),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=False,
    )
    result = drive_svc.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,webViewLink",
    ).execute()

    ss_id = result["id"]
    url = result.get("webViewLink", f"https://docs.google.com/spreadsheets/d/{ss_id}/edit")

    print(f"\n✅  Google Sheet created successfully!")
    print(f"🔗  URL: {url}")
    print(f"📊  6 tabs: Vision, Business Model, Budget, Cap Table, Milestones, Bridge Tracker")


if __name__ == "__main__":
    main()

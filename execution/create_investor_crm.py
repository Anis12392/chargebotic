"""
Wirebird — Angel Investor CRM
Creates a Google Sheet to track all angel investor outreach with pipeline stages.

Stages (Slidebean-inspired):
  Identified → Intro Sent → Responded → First Call → Follow-up → Due Diligence → Committed → Closed → Pass

Run: python3 execution/create_investor_crm.py
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


# ── Colours ──────────────────────────────────────────────────────────────────
def rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}

NAVY   = rgb(17, 54,  98)
TEAL   = rgb(46, 132, 138)
WHITE  = rgb(255, 255, 255)
DKGRAY = rgb(51,  51,  51)
LTBLUE = rgb(220, 235, 252)

# Stage colours (background for the stage badge)
STAGE_COLORS = {
    "Identified":     rgb(220, 220, 220),
    "Intro Sent":     rgb(255, 243, 205),
    "Responded":      rgb(255, 224, 178),
    "First Call":     rgb(179, 229, 252),
    "Follow-up":      rgb(178, 235, 242),
    "Due Diligence":  rgb(209, 196, 233),
    "Committed":      rgb(200, 230, 201),
    "Closed":         rgb(165, 214, 167),
    "Pass":           rgb(255, 205, 210),
}

STAGE_OPTIONS = list(STAGE_COLORS.keys())


def hdr(text, bg=NAVY, fg=WHITE, bold=True, size=10, halign="CENTER"):
    return {
        "userEnteredValue": {"stringValue": text},
        "userEnteredFormat": {
            "backgroundColor": bg,
            "textFormat": {"foregroundColor": fg, "bold": bold, "fontSize": size},
            "horizontalAlignment": halign,
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
        },
    }


def cell(val, bg=None, bold=False, fg=DKGRAY, halign="LEFT", italic=False):
    if val is None:
        v = {"stringValue": ""}
    elif isinstance(val, (int, float)):
        v = {"numberValue": val}
    else:
        v = {"stringValue": str(val)}
    fmt = {
        "textFormat": {"foregroundColor": fg, "bold": bold, "italic": italic},
        "horizontalAlignment": halign,
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": "WRAP",
    }
    if bg:
        fmt["backgroundColor"] = bg
    return {"userEnteredValue": v, "userEnteredFormat": fmt}


# ── Sheet builders ────────────────────────────────────────────────────────────

def build_crm():
    """Main CRM tab."""
    data = []

    # Title rows
    data.append({"values": [hdr("CHARGEBOTIC — INVESTOR CRM", NAVY, size=14)]})
    data.append({"values": [hdr("Track every investor outreach · update Stage as you progress · Slidebean pipeline method", TEAL, size=10)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    # Column headers
    columns = [
        "Investor Name", "Fund / Firm", "Tier",
        "Contact Info", "Stage", "Last Touch",
        "Next Action", "Check Size ($)", "Notes",
    ]
    data.append({"values": [hdr(c, NAVY, size=10) for c in columns]})

    # Real investor data
    TIER1 = rgb(255, 224, 178)   # orange — dream
    TIER2 = rgb(200, 230, 201)   # green — solid fit
    TIER3 = rgb(220, 220, 220)   # gray — backup/inbound

    investors = [
        # ── TIER 1 — ACTIVE / DREAM ──────────────────────────────────────────
        ("Antoine Moyroud",   "Lightspeed Venture Partners", "Tier 1 — Dream",
         "antoine@lsvp.com",       "First Call",  "2026-05-12",
         "Re-engage with Chariot deal + Terna news",    "$250K–$1M",
         "Made Orqa intro, 'make us proud at demo.' Has not seen Chariot contract yet. Warm supporter."),

        ("Christian Keil",    "a16z American Dynamism",     "Tier 1 — Dream",
         "ck@a16z.com",            "First Call",  "2026-05-11",
         "Follow up: Chariot LOI + JIFX Aug invite",   "$500K–$2M",
         "Had intro call May 11. Responded fast to cold X outreach. American Dynamism = defense/hard tech."),

        ("Pietro Rossi",      "Terna Forward (CVC)",        "Tier 1 — Dream",
         "pietro.rossi@terna.it",  "First Call",  "2026-06-23",
         "Deep dive Jun 30, 9AM PT / 6PM Rome",        "$250K–$1M",
         "Head of Terna Venture Fund. 71,000km Italian power lines. Patrick has mutual contacts."),

        ("Luca Scherling",    "Terna Forward (CVC)",        "Tier 1 — Dream",
         "luca.scherling@terna.it","First Call",  "2026-06-23",
         "Deep dive Jun 30 alongside Pietro",          "—",
         "Terna Forward initiating contact. Focus: drone inspection + charging."),

        ("Jamie Gull",        "Wavefunction VC",            "Tier 1 — Dream",
         "—",                      "Identified",  "—",
         "Find contact, cold outreach",                "$250K–$1M",
         "Focus: hardware deep tech — aerospace, defense, energy, robotics. PERFECT sector fit. Pre-seed to Seed."),

        ("Matt Ocko / Zachary Bogue", "DCVC",             "Tier 1 — Dream",
         "info@dcvc.com",           "Identified",  "—",
         "Find warm intro path via LinkedIn",          "$500K–$2M",
         "Deep tech: sensors, AI, robotics. Pre-seed–Series A. Strong portfolio relevance."),

        # ── TIER 2 — SOLID FIT ───────────────────────────────────────────────
        ("Jamie Daudon",      "—",                          "Tier 2 — Solid fit",
         "LinkedIn (via Patrick)",  "Identified",  "2026-06-23",
         "Patrick to make intro — mutual contact w/ Pietro", "$25K–$100K",
         "Patrick flagged Jun 23 as potential early investor. Mutual contact with Pietro Rossi."),

        ("JT (Jagannadham N.)","Independent Angel",         "Tier 2 — Solid fit",
         "jagannadham.ndg@gmail.com","Responded", "2026-05-25",
         "Book 20-min intro call — overdue",           "$25K–$100K",
         "Inbound May 16. 'Infrastructure at intersection of energy + autonomous systems.' Replied May 25. No call yet."),

        ("Avidan Ross / Lee Edwards","Root Ventures",       "Tier 2 — Solid fit",
         "root.vc",                "Identified",  "—",
         "Cold outreach — find partner email",         "$250K–$500K",
         "Deep tech, hardware, robotics, tools for engineers. Pre-seed/Seed hard-tech fund."),

        ("Jeremy Conrad",     "Lemnos VC",                  "Tier 2 — Solid fit",
         "lemnos.vc",              "Identified",  "—",
         "Cold outreach — find warm intro",            "$250K–$500K",
         "Hardware, robotics, sensors, industrial, deep tech. Pre-seed/Seed. Strong alignment."),

        ("Josh Wolfe / Peter Hébert","Lux Capital",         "Tier 2 — Solid fit",
         "partners@lux.vc",        "Identified",  "—",
         "Need warm intro — search LinkedIn network",  "$1M–$5M",
         "Deep tech. Josh Wolfe known for defense/national security. Portfolio: Formlabs, etc."),

        ("Alexis Houssou",    "Hardware Club (HCVC)",       "Tier 2 — Solid fit",
         "hcvc.co",                "Identified",  "—",
         "Apply or cold outreach",                     "$250K–$1M",
         "Dedicated hardware startup ecosystem fund. Seed–Series A. Global network."),

        ("Charly Mwangi",     "Eclipse Ventures",           "Tier 2 — Solid fit",
         "eclipse.capital",        "Identified",  "—",
         "Find intro path",                            "$500K–$2M",
         "Hardware, manufacturing, compute. Seed–Series B. Good for production scale angle."),

        ("Alex Burkardt",     "Lowercase Capital",          "Tier 2 — Solid fit",
         "—",                      "Identified",  "—",
         "Find email — cold outreach with Chariot deal", "$100K–$500K",
         "Pre-seed friendly. Reach out with Chariot contract as proof point."),

        ("Robert McKay",      "Independent Angel/Connector","Tier 2 — Solid fit",
         "+1 802 793 4459 · calendly.com/robertmckayiv/coffee", "Identified", "—",
         "Book coffee via Calendly",                   "$25K–$100K",
         "Connector + investor. In your Google Drive fundraising sheet. Has Calendly."),

        ("Aurelien Gittard",  "Angel — Robotics",           "Tier 2 — Solid fit",
         "—",                      "Identified",  "—",
         "Get email from Patrick or network",          "$25K–$100K",
         "In your fundraising sheet. Investor, entrepreneur first, robotics focus. Strong fit."),

        # ── TIER 3 — EVENTS / PROGRAMS / BACKUP ─────────────────────────────
        ("Ryan Green",        "Antler VC",                  "Tier 3 — Backup",
         "—",                      "Identified",  "—",
         "Meet at SF Hardware Meetup @ Antler — Jul 9",  "$100K–$500K",
         "You're registered for Jul 9 SF Hardware Meetup at Antler VC. Meet Ryan Green in person."),

        ("Ed Dua",            "Tilden Capital",             "Tier 3 — Backup",
         "—",                      "Identified",  "—",
         "Meet at STAK Ventures VIP Lunch Jun 24",    "$100K–$500K",
         "Speaking at STAK event Jun 24 you're registered for. Early stage."),

        ("Bryce Gilleland",   "Cal Innovation Fund II",     "Tier 3 — Backup",
         "—",                      "Identified",  "—",
         "Meet at STAK Ventures VIP Lunch Jun 24",    "$100K–$500K",
         "Speaking at same STAK event Jun 24. Cal Innovation Fund."),

        ("Hiroki",            "goi.bot",                    "Tier 3 — Backup",
         "h@goi.bot",              "Intro Sent",  "2026-06-10",
         "Check if he made any investor intros",       "—",
         "Anis asked Hiroki Jun 10 to make warm investor intro emails on your behalf."),

        ("FoundersInc",       "FoundersInc Program",        "Tier 3 — Backup",
         "adrianna@f.inc",         "Follow-up",   "2026-06-10",
         "Follow up via Adriana if no word by Jun 30","Program",
         "Ask sent Jun 15. Anis also messaged Adriana Jun 10 asking for advice. Saw pitch live May 27."),

        ("Stepan G.",         "cyber.fund (Monastery)",     "Tier 3 — Backup",
         "sg@cyber.fund",          "Responded",   "2026-06-05",
         "Evaluate: AI-native accelerator, assess fit","Accelerator",
         "Inbound Jun 5. AI-native. May not fit defense/hard tech angle."),

        ("Pitch Global — Jun 26", "Event — SJSU",           "Tier 3 — Backup",
         "pitchglobal@luma",       "Identified",  "—",
         "Pitch at SJSU Jun 26, 12:30–5PM — AI/Deeptech CVCs/angels", "—",
         "You're registered for Pitch Global at SJSU Jun 26. Present to AI/Deeptech/CVC/angels."),

        ("Tim Hsia",          "Context VC (Defense Tech)",  "Tier 3 — Backup",
         "timhsia@contextvc.com",  "Identified",  "—",
         "Reach out — Defense Tech Conference Nov 4",  "$100K–$500K",
         "Runs Defense Tech Conference Nov 4 SF. Military veteran startup ecosystem. Defense fit."),

        ("Anoop P.",          "Alientt (NSF SBIR help)",    "Tier 3 — Backup",
         "anoop.p@alientt.com",    "First Call",  "2026-05-21",
         "Non-dilutive only — use for NSF SBIR submission", "Non-dilutive",
         "Grant writing service. Not a VC. Had a call May 21. Loop in when ready for NSF."),

        ("Daniel Paredes",    "Sierra Ventures",            "Tier 2 — Solid fit",
         "daniel@sierraventures.com","Pass",       "2026-06-09",
         "Re-engage in Sep/Oct with Chariot contract signed + JIFX results", "$250K–$1M",
         "Call Jun 3. He replied Jun 9: 'reconnect later this year once you have more traction.' Soft pass — not a no. Follow up with proof points in ~3 months."),

        ("Benjamin Toney",    "Stanford (Power Line Research)","Tier 2 — Solid fit",
         "benjaminrtoney@gmail.com","Responded",  "2026-06-03",
         "Check if Stanford has progressed on powerline testing — loop in for R&D collab", "—",
         "Discussed Stanford powerline testing/research side. Anis shared Jun 3 energy harvesting milestone (3V). He replied positively. Not a VC — valuable for academic validation + Stanford network."),

        ("Ruslan",            "FoundersInc (f.inc)",        "Tier 1 — Dream",
         "ruslan@f.inc",           "Follow-up",   "2026-06-18",
         "Office hours Jun 26 2pm — attend + push for decision", "Program / Check",
         "Decision-maker at FoundersInc. Anis in Off Season II. Followed up Jun 18: 'we've done the business work you asked for.' Office hours: Jun 26, Jul 20, Aug 3. USE Jun 26 slot."),
    ]

    tier_bg_map = {
        "Tier 1 — Dream":    TIER1,
        "Tier 2 — Solid fit": TIER2,
        "Tier 3 — Backup":   TIER3,
    }

    for inv in investors:
        name, firm, tier, contact, stage, last_touch, next_action, check, notes = inv
        bg = tier_bg_map.get(tier, WHITE)
        stage_bg = STAGE_COLORS.get(stage, WHITE)
        data.append({"values": [
            cell(name,        bg,       bold=True),
            cell(firm,        bg),
            cell(tier,        bg,       bold=True),
            cell(contact,     bg),
            cell(stage,       stage_bg, bold=True, halign="CENTER"),
            cell(last_touch,  bg,       halign="CENTER"),
            cell(next_action, bg),
            cell(check,       bg,       halign="CENTER"),
            cell(notes,       bg),
        ]})

    # 20 empty rows for new contacts
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("── ADD NEW CONTACTS BELOW ──", TEAL, size=9)]})
    for i in range(20):
        row_bg = LTBLUE if i % 2 == 0 else WHITE
        data.append({"values": [cell("", row_bg) for _ in columns]})

    return data


def build_legend():
    """Legend / how-to-use tab."""
    data = []
    data.append({"values": [hdr("HOW TO USE THIS CRM", NAVY, size=13)]})
    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})

    data.append({"values": [hdr("PIPELINE STAGES (Slidebean method)", TEAL)]})
    data.append({"values": [
        hdr("Stage", TEAL, size=10),
        hdr("What it means", TEAL, size=10),
        hdr("What to do next", TEAL, size=10),
        hdr("Typical timing", TEAL, size=10),
    ]})

    stages = [
        ("Identified",    "Added to list — not yet contacted",
         "Write personalized intro email or find a warm intro path",
         "Day 0"),
        ("Intro Sent",    "Cold email or warm intro sent",
         "Wait 5–7 days · if no reply, send 1 follow-up with new info",
         "Day 1–7"),
        ("Responded",     "They replied positively",
         "Book a 20-min intro call ASAP — same week if possible",
         "Day 3–10"),
        ("First Call",    "Intro call scheduled or completed",
         "Send deck + one-pager within 24h · ask for a follow-up meeting",
         "Week 1–2"),
        ("Follow-up",     "Had first call · deeper conversation ongoing",
         "Answer questions, share traction, propose next meeting",
         "Week 2–4"),
        ("Due Diligence", "Investor doing deeper research",
         "Share data room link · respond fast · intro to customers/advisors",
         "Week 3–6"),
        ("Committed",     "They said yes · term agreed",
         "Send Clerky SAFE link · wire instructions (Rho bank)",
         "Week 4–8"),
        ("Closed",        "SAFE signed + wire received",
         "Send signed copy + confirmation · log in Bridge Tracker",
         "Done ✅"),
        ("Pass",          "They declined",
         "Ask for a referral to another investor · keep relationship warm",
         "N/A"),
    ]

    colors = list(STAGE_COLORS.values())
    for i, (stage, meaning, action, timing) in enumerate(stages):
        bg = colors[i]
        data.append({"values": [
            cell(stage, bg, bold=True),
            cell(meaning, bg),
            cell(action, bg),
            cell(timing, bg, halign="CENTER"),
        ]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("SLIDEBEAN OUTREACH RULES", NAVY)]})
    rules = [
        "📌  Batch your outreach: send 10–20 intros in the same week so you create momentum and FOMO.",
        "📌  Start with Tier 2/3 investors to practise your pitch before hitting your top targets.",
        "📌  Follow-up exactly once (5–7 days later) with ONE new piece of info (traction, demo, press).",
        "📌  3 touches max: initial + 1 follow-up + 1 final ping. After that, move to Pass.",
        "📌  Always end a meeting with a clear next step agreed in the room.",
        "📌  Update this sheet the same day as any interaction — stale CRMs are useless.",
    ]
    for rule in rules:
        data.append({"values": [cell(rule, rgb(255, 248, 220))]})

    data.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    data.append({"values": [hdr("TIER SYSTEM (how to prioritise)", TEAL)]})
    tiers = [
        ("Tier 1 — Dream",   "Top angels in robotics / defense / deeptech · attack last when pitch is sharp"),
        ("Tier 2 — Solid fit", "Good stage/sector match · use to refine your story · target first"),
        ("Tier 3 — Backup",  "Weaker fit but reachable · fill the round if needed"),
    ]
    data.append({"values": [hdr("Tier", TEAL, size=10), hdr("How to use", TEAL, size=10)]})
    tier_bgs = [rgb(255, 224, 178), rgb(200, 230, 201), rgb(220, 220, 220)]
    for i, (tier, desc) in enumerate(tiers):
        data.append({"values": [cell(tier, tier_bgs[i], bold=True), cell(desc, tier_bgs[i])]})

    return data


# ── Formatting requests ───────────────────────────────────────────────────────

def get_format_requests(sheet_id, num_data_rows=42):
    """Column widths, frozen rows, dropdown validation for Stage column."""
    requests = []

    # Freeze header rows (rows 0-3 = title + headers)
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 4},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Column widths: A=200, B=150, C=130, D=180, E=130, F=110, G=200, H=110, I=260
    widths = [200, 150, 130, 180, 130, 110, 200, 110, 260]
    for col_idx, px in enumerate(widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": px},
                "fields": "pixelSize",
            }
        })

    # Row height for header row (row index 3)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 3,
                "endIndex": 4,
            },
            "properties": {"pixelSize": 45},
            "fields": "pixelSize",
        }
    })

    # Dropdown validation on Stage column (col E = index 4), rows 4 to num_data_rows+4
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 4 + num_data_rows,
                "startColumnIndex": 4,
                "endColumnIndex": 5,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": s} for s in STAGE_OPTIONS],
                },
                "showCustomUi": True,
                "strict": True,
            },
        }
    })

    # Conditional formatting: colour each stage value in col E
    for stage, color in STAGE_COLORS.items():
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 4,
                        "endRowIndex": 4 + num_data_rows,
                        "startColumnIndex": 4,
                        "endColumnIndex": 5,
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "TEXT_EQ",
                            "values": [{"userEnteredValue": stage}],
                        },
                        "format": {"backgroundColor": color},
                    },
                },
                "index": 0,
            }
        })

    return requests


def get_legend_format_requests(sheet_id):
    requests = []
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })
    widths = [160, 320, 320, 120]
    for col_idx, px in enumerate(widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": px},
                "fields": "pixelSize",
            }
        })
    return requests


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    creds = get_creds()
    sheets_svc = build("sheets", "v4", credentials=creds)
    drive_svc  = build("drive",  "v3", credentials=creds)

    print("Creating Google Sheet...")

    # Create spreadsheet with two tabs
    ss = sheets_svc.spreadsheets().create(body={
        "properties": {"title": "Chargebotic — Investor CRM"},
        "sheets": [
            {"properties": {"title": "Investor Pipeline", "index": 0}},
            {"properties": {"title": "How to Use (Stages)", "index": 1}},
        ],
    }).execute()

    ss_id = ss["spreadsheetId"]
    crm_sheet_id    = ss["sheets"][0]["properties"]["sheetId"]
    legend_sheet_id = ss["sheets"][1]["properties"]["sheetId"]

    print(f"  Sheet ID: {ss_id}")

    # Write data
    crm_data    = build_crm()
    legend_data = build_legend()

    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=ss_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": "Investor Pipeline!A1",
                    "values": [],  # written via batchUpdate below
                },
            ],
        },
    ).execute()

    # Use batchUpdate for rich formatting
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={
            "requests": [
                # Write CRM rows
                {
                    "updateCells": {
                        "rows": crm_data,
                        "fields": "userEnteredValue,userEnteredFormat",
                        "start": {"sheetId": crm_sheet_id, "rowIndex": 0, "columnIndex": 0},
                    }
                },
                # Write Legend rows
                {
                    "updateCells": {
                        "rows": legend_data,
                        "fields": "userEnteredValue,userEnteredFormat",
                        "start": {"sheetId": legend_sheet_id, "rowIndex": 0, "columnIndex": 0},
                    }
                },
            ]
        },
    ).execute()

    # Apply formatting + dropdowns
    fmt_requests = get_format_requests(crm_sheet_id)
    fmt_requests += get_legend_format_requests(legend_sheet_id)

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={"requests": fmt_requests},
    ).execute()

    # Make it accessible (optional — skip if Drive API not enabled)
    try:
        drive_svc.permissions().create(
            fileId=ss_id,
            body={"type": "anyone", "role": "writer"},
        ).execute()
    except Exception as e:
        print(f"  (Sharing skipped: {e})")

    url = f"https://docs.google.com/spreadsheets/d/{ss_id}/edit"
    print(f"\n✅  Angel Investor CRM created!")
    print(f"🔗  {url}")
    print(f"\nTabs:")
    print(f"  1. Investor Pipeline  — your main tracking sheet with Stage dropdown")
    print(f"  2. How to Use (Stages) — Slidebean pipeline guide + outreach rules")


if __name__ == "__main__":
    main()

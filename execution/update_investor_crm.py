"""
Update Chargebotic — Investor CRM 1
Overwrites the "Investor Pipeline" tab of an existing sheet with all contacts.
Targets: https://docs.google.com/spreadsheets/d/1uIKaoZwJD1YnDmpJerGIXxIiVRZxqp5tsSY1rSEGqJs

Run: python3 execution/update_investor_crm.py
"""

import os
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
TOKEN_PATH  = os.path.join(ROOT, "token.json")

# ── Target sheet ──────────────────────────────────────────────────────────────
SHEET_ID = "1uIKaoZwJD1YnDmpJerGIXxIiVRZxqp5tsSY1rSEGqJs"


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


# ── Colours ───────────────────────────────────────────────────────────────────
def rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}

NAVY   = rgb(17, 54, 98)
TEAL   = rgb(46, 132, 138)
WHITE  = rgb(255, 255, 255)
DKGRAY = rgb(51, 51, 51)
LTBLUE = rgb(220, 235, 252)

TIER1 = rgb(255, 224, 178)
TIER2 = rgb(200, 230, 201)
TIER3 = rgb(220, 220, 220)

STAGE_COLORS = {
    "Identified":    rgb(220, 220, 220),
    "Intro Sent":    rgb(255, 243, 205),
    "Responded":     rgb(255, 224, 178),
    "First Call":    rgb(179, 229, 252),
    "Follow-up":     rgb(178, 235, 242),
    "Due Diligence": rgb(209, 196, 233),
    "Committed":     rgb(200, 230, 201),
    "Closed":        rgb(165, 214, 167),
    "Pass":          rgb(255, 205, 210),
}
STAGE_OPTIONS = list(STAGE_COLORS.keys())

TIER_BG = {
    "Tier 1 — Dream":     TIER1,
    "Tier 2 — Solid fit": TIER2,
    "Tier 3 — Backup":    TIER3,
}


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
    v = {"stringValue": str(val) if val is not None else ""}
    fmt = {
        "textFormat": {"foregroundColor": fg, "bold": bold, "italic": italic},
        "horizontalAlignment": halign,
        "verticalAlignment": "MIDDLE",
        "wrapStrategy": "WRAP",
    }
    if bg:
        fmt["backgroundColor"] = bg
    return {"userEnteredValue": v, "userEnteredFormat": fmt}


# ── Investor data ─────────────────────────────────────────────────────────────
#
# Format: (name, firm, tier, contact, stage, last_touch, next_action, check_size, notes)

INVESTORS = [
    # ── TIER 1 — DREAM / ACTIVE ──────────────────────────────────────────────
    ("Antoine Moyroud", "Lightspeed Venture Partners", "Tier 1 — Dream",
     "antoine@lsvp.com", "First Call", "2026-05-12",
     "Re-engage with Chariot deal + Terna news", "$250K–$1M",
     "Made Orqa intro, 'make us proud at demo.' Has not seen Chariot contract yet. Warm supporter."),

    ("Christian Keil", "a16z American Dynamism", "Tier 1 — Dream",
     "ck@a16z.com", "First Call", "2026-05-11",
     "Follow up: Chariot LOI + JIFX Aug invite", "$500K–$2M",
     "Had intro call May 11. Responded fast to cold X outreach. American Dynamism = defense/hard tech."),

    ("Pietro Rossi", "Terna Forward (CVC)", "Tier 1 — Dream",
     "pietro.rossi@terna.it", "First Call", "2026-06-23",
     "Deep dive Jun 30, 9AM PT / 6PM Rome", "$250K–$1M",
     "Head of Terna Venture Fund. 71,000km Italian power lines. Patrick has mutual contacts."),

    ("Luca Scherling", "Terna Forward (CVC)", "Tier 1 — Dream",
     "luca.scherling@terna.it", "First Call", "2026-06-23",
     "Deep dive Jun 30 alongside Pietro", "—",
     "Terna Forward initiating contact. Focus: drone inspection + charging."),

    ("Ruslan", "FoundersInc (f.inc)", "Tier 1 — Dream",
     "ruslan@f.inc", "Follow-up", "2026-06-18",
     "Office hours Jun 26 2pm — attend + push for decision", "Program / Check",
     "Decision-maker at FoundersInc. In Off Season II. Followed up Jun 18: 'we've done the business work you asked for.' Use Jun 26 / Jul 20 / Aug 3 office hours slots."),

    ("Jamie Gull", "Wavefunction VC", "Tier 1 — Dream",
     "—", "Identified", "—",
     "Find contact, cold outreach", "$250K–$1M",
     "Hardware deep tech — aerospace, defense, energy, robotics. PERFECT sector fit. Pre-seed to Seed."),

    ("Matt Ocko / Zachary Bogue", "DCVC", "Tier 1 — Dream",
     "info@dcvc.com", "Identified", "—",
     "Find warm intro path via LinkedIn", "$500K–$2M",
     "Deep tech: sensors, AI, robotics. Pre-seed–Series A. Strong portfolio relevance."),

    # ── TIER 2 — SOLID FIT ───────────────────────────────────────────────────
    ("Jamie Daudon", "—", "Tier 2 — Solid fit",
     "LinkedIn (via Patrick)", "Identified", "2026-06-23",
     "Patrick to make intro — mutual contact w/ Pietro", "$25K–$100K",
     "Patrick flagged Jun 23 as potential early investor. Mutual contact with Pietro Rossi."),

    ("JT (Jagannadham N.)", "Independent Angel", "Tier 2 — Solid fit",
     "jagannadham.ndg@gmail.com", "Responded", "2026-05-25",
     "Book 20-min intro call — overdue", "$25K–$100K",
     "Inbound May 16. 'Infrastructure at intersection of energy + autonomous systems.' Replied May 25. No call booked yet."),

    ("Daniel Paredes", "Sierra Ventures", "Tier 2 — Solid fit",
     "daniel@sierraventures.com", "Pass", "2026-06-09",
     "Re-engage Sep/Oct with Chariot signed + JIFX results", "$250K–$1M",
     "Call Jun 3. Replied Jun 9: 'reconnect later this year once you have more traction.' Soft pass — not a no. Follow up in ~3 months."),

    ("Benjamin Toney", "Stanford (Power Line Research)", "Tier 2 — Solid fit",
     "benjaminrtoney@gmail.com", "Responded", "2026-06-03",
     "Loop in for R&D collab — Stanford powerline testing", "—",
     "Discussed Stanford powerline testing. Anis shared Jun 3 energy harvesting milestone (3V). Replied positively. Not a VC — academic validation + Stanford network."),

    ("Avidan Ross / Lee Edwards", "Root Ventures", "Tier 2 — Solid fit",
     "root.vc", "Identified", "—",
     "Cold outreach — find partner email", "$250K–$500K",
     "Deep tech, hardware, robotics, tools for engineers. Pre-seed/Seed hard-tech fund."),

    ("Jeremy Conrad", "Lemnos VC", "Tier 2 — Solid fit",
     "lemnos.vc", "Identified", "—",
     "Cold outreach — find warm intro", "$250K–$500K",
     "Hardware, robotics, sensors, industrial, deep tech. Pre-seed/Seed. Strong alignment."),

    ("Josh Wolfe / Peter Hébert", "Lux Capital", "Tier 2 — Solid fit",
     "partners@lux.vc", "Identified", "—",
     "Need warm intro — search LinkedIn network", "$1M–$5M",
     "Deep tech. Josh Wolfe known for defense/national security."),

    ("Alexis Houssou", "Hardware Club (HCVC)", "Tier 2 — Solid fit",
     "hcvc.co", "Identified", "—",
     "Apply or cold outreach", "$250K–$1M",
     "Dedicated hardware startup ecosystem fund. Seed–Series A. Global network."),

    ("Charly Mwangi", "Eclipse Ventures", "Tier 2 — Solid fit",
     "eclipse.capital", "Identified", "—",
     "Find intro path", "$500K–$2M",
     "Hardware, manufacturing, compute. Seed–Series B. Good for production scale angle."),

    ("Alex Burkardt", "Lowercase Capital", "Tier 2 — Solid fit",
     "—", "Identified", "—",
     "Find email — cold outreach with Chariot deal", "$100K–$500K",
     "Pre-seed friendly. Reach out with Chariot contract as proof point."),

    ("Robert McKay", "Independent Angel/Connector", "Tier 2 — Solid fit",
     "+1 802 793 4459 · calendly.com/robertmckayiv/coffee", "Identified", "—",
     "Book coffee via Calendly", "$25K–$100K",
     "Connector + investor. In your Google Drive fundraising sheet. Has Calendly."),

    ("Aurelien Gittard", "Angel — Robotics", "Tier 2 — Solid fit",
     "—", "Identified", "—",
     "Get email from Patrick or network", "$25K–$100K",
     "In your fundraising sheet. Investor, entrepreneur first, robotics focus. Strong fit."),

    ("Liam Maniscalco", "F-Prime Capital (Fidelity VC)", "Tier 2 — Solid fit",
     "lmaniscalco@fprimecapital.com", "First Call", "2026-05-30",
     "Follow up on Zoom call — send deck + traction update", "$250K–$1M",
     "Reached out May 30 for a Zoom. F-Prime is Fidelity's VC arm. Scheduled meeting proactively — warm signal."),

    # ── TIER 3 — EVENTS / PROGRAMS / BACKUP ──────────────────────────────────
    ("Adrianna Lakatos", "FoundersInc (f.inc)", "Tier 3 — Backup",
     "adrianna@f.inc", "Follow-up", "2026-04-14",
     "Ask for warm intro to Adrianna's father (Stanford-connected) — he was to follow up with info", "Program",
     "Accepted Anis + Bo into Canopy Apr 14. Investment role at f.inc ($100K–$250K checks). Father is Stanford-connected investor who promised to get back with info — needs follow-up."),

    ("Père d'Adrianna Lakatos", "Stanford (network)", "Tier 3 — Backup",
     "— (ask Adrianna for intro)", "Identified", "—",
     "Get name + email from Adrianna — he was supposed to reach out with info", "—",
     "Met via Adrianna Lakatos (f.inc). Stanford-connected. Promised to get back to Anis with information. Has not followed up. Need to chase via Adrianna."),

    ("Hubert", "FoundersInc (f.inc)", "Tier 3 — Backup",
     "hubert@f.inc", "Follow-up", "2026-06-15",
     "Follow up — sent pitch Jun 15, no response yet", "Program / Check",
     "Sent full traction pitch Jun 15: Chariot $6.5M/year + Cupertino LOI. No reply yet. Escalate via Ruslan if needed."),

    ("Ryan Green", "Antler VC", "Tier 3 — Backup",
     "—", "Identified", "—",
     "Meet at SF Hardware Meetup @ Antler — Jul 9", "$100K–$500K",
     "Registered for Jul 9 SF Hardware Meetup at Antler VC. Meet Ryan Green in person."),

    ("Ed Dua", "Tilden Capital", "Tier 3 — Backup",
     "ed@virtussolis.space", "Responded", "2026-05-29",
     "Follow up on intro Ed was working on", "$100K–$500K",
     "Had call May 12. May 29: 'meeting next week with the guy I'm working an intro for — will update.' Chase for update."),

    ("Bryce Gilleland", "Cal Innovation Fund II", "Tier 3 — Backup",
     "—", "Identified", "—",
     "Meet at STAK Ventures VIP Lunch Jun 24", "$100K–$500K",
     "Speaking at STAK event Jun 24. Cal Innovation Fund."),

    ("Hiroki", "goi.bot", "Tier 3 — Backup",
     "h@goi.bot", "Intro Sent", "2026-06-10",
     "Check if he made any investor intros", "—",
     "Anis asked Hiroki Jun 10 to make warm investor intro emails on your behalf."),

    ("Stepan G.", "cyber.fund (Monastery)", "Tier 3 — Backup",
     "sg@cyber.fund", "Responded", "2026-06-05",
     "Evaluate: AI-native accelerator, assess fit", "Accelerator",
     "Inbound Jun 5. AI-native accelerator. May not fit defense/hard tech angle."),

    ("Tim Hsia", "Context VC (Defense Tech)", "Tier 3 — Backup",
     "timhsia@contextvc.com", "Identified", "—",
     "Reach out — Defense Tech Conference Nov 4", "$100K–$500K",
     "Runs Defense Tech Conference Nov 4 SF. Military veteran startup ecosystem. Defense fit."),

    ("Pitch Global — Jun 26", "Event — SJSU", "Tier 3 — Backup",
     "pitchglobal@luma", "Identified", "—",
     "Pitch at SJSU Jun 26, 12:30–5PM — AI/Deeptech CVCs/angels", "—",
     "Registered for Pitch Global at SJSU Jun 26. Present to AI/Deeptech/CVC/angels."),

    ("Anoop P.", "Alientt (NSF SBIR help)", "Tier 3 — Backup",
     "anoop.p@alientt.com", "First Call", "2026-05-21",
     "Non-dilutive only — use for NSF SBIR submission", "Non-dilutive",
     "Grant writing service. Not a VC. Had a call May 21. Loop in when ready for NSF."),
]


def build_crm_rows():
    columns = [
        "Investor Name", "Fund / Firm", "Tier",
        "Contact Info", "Stage", "Last Touch",
        "Next Action", "Check Size ($)", "Notes",
    ]

    rows = []
    rows.append({"values": [hdr("CHARGEBOTIC — INVESTOR CRM", NAVY, size=14)]})
    rows.append({"values": [hdr("Track every investor · update Stage as you progress · Slidebean pipeline method", TEAL, size=10)]})
    rows.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    rows.append({"values": [hdr(c, NAVY, size=10) for c in columns]})

    for inv in INVESTORS:
        name, firm, tier, contact, stage, last_touch, next_action, check, notes = inv
        bg = TIER_BG.get(tier, WHITE)
        stage_bg = STAGE_COLORS.get(stage, WHITE)
        rows.append({"values": [
            cell(name,        bg, bold=True),
            cell(firm,        bg),
            cell(tier,        bg, bold=True),
            cell(contact,     bg),
            cell(stage,       stage_bg, bold=True, halign="CENTER"),
            cell(last_touch,  bg, halign="CENTER"),
            cell(next_action, bg),
            cell(check,       bg, halign="CENTER"),
            cell(notes,       bg),
        ]})

    rows.append({"values": [{"userEnteredValue": {"stringValue": ""}}]})
    rows.append({"values": [hdr("── ADD NEW CONTACTS BELOW ──", TEAL, size=9)]})
    for i in range(20):
        row_bg = LTBLUE if i % 2 == 0 else WHITE
        rows.append({"values": [cell("", row_bg) for _ in columns]})

    return rows


def get_format_requests(sheet_id, num_data_rows):
    requests = []

    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 4},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    widths = [200, 165, 140, 200, 130, 110, 210, 120, 280]
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

    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 4 + num_data_rows + 20,
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

    for stage, color in STAGE_COLORS.items():
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 4,
                        "endRowIndex": 4 + num_data_rows + 20,
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


def main():
    creds = get_creds()
    svc = build("sheets", "v4", credentials=creds)

    # Get current sheet info (need sheetId for the "Investor Pipeline" tab)
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    crm_sheet_id = None
    for sh in meta["sheets"]:
        if sh["properties"]["title"] == "Investor Pipeline":
            crm_sheet_id = sh["properties"]["sheetId"]
            break

    if crm_sheet_id is None:
        print("ERROR: 'Investor Pipeline' tab not found.")
        return

    print(f"Updating sheet {SHEET_ID} (tab sheetId={crm_sheet_id})...")

    rows = build_crm_rows()
    num_data_rows = len(INVESTORS)

    # Clear existing content first
    svc.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range="Investor Pipeline!A1:Z200",
    ).execute()

    # Write new content
    svc.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            "requests": [
                {
                    "updateCells": {
                        "rows": rows,
                        "fields": "userEnteredValue,userEnteredFormat",
                        "start": {"sheetId": crm_sheet_id, "rowIndex": 0, "columnIndex": 0},
                    }
                }
            ]
        },
    ).execute()

    # Apply formatting + dropdowns
    fmt = get_format_requests(crm_sheet_id, num_data_rows)
    svc.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": fmt},
    ).execute()

    print(f"\n✅  CRM updated — {num_data_rows} investors")
    print(f"🔗  https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()

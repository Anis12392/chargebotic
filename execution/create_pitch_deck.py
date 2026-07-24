"""
Chargebotic Inc — Investor Pitch Deck (Pre-Seed, June 2026)
7 slides: Cover, Problem, Opportunity, Solution, Team, Traction, Milestones.
Creates PPTX locally, then uploads to Google Slides.

Usage:
    python3 execution/create_pitch_deck.py
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── Palette ───────────────────────────────────────────────────────────────────
DEEP_SPACE  = RGBColor(0x05, 0x08, 0x14)
CARD_BG     = RGBColor(0x0D, 0x11, 0x1C)
GRID_LINE   = RGBColor(0x22, 0x26, 0x33)
ELECTRIC    = RGBColor(0x00, 0xB4, 0xFF)
AMBER       = RGBColor(0xF9, 0x73, 0x16)
DANGER_RED  = RGBColor(0xFC, 0x3D, 0x21)
GREEN_CHECK = RGBColor(0x22, 0xC5, 0x5E)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xD4, 0xD4, 0xD4)
MID_GRAY    = RGBColor(0x9A, 0x9A, 0x9A)
DARK_GRAY   = RGBColor(0x55, 0x55, 0x55)

HEAD_FONT    = "Helvetica"
BODY_FONT    = "Helvetica"
TOTAL_SLIDES = 7
COMPANY      = "CHARGEBOTIC INC"
EMAIL        = "anis@chargebotic.com"
DOMAIN       = "chargebotic.com"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SW = prs.slide_width
SH = prs.slide_height


# ── Helpers ───────────────────────────────────────────────────────────────────
def blank():
    return prs.slides.add_slide(prs.slide_layouts[6])


def bg(slide, color=DEEP_SPACE):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def txt(slide, left, top, w, h, text,
        size=14, color=WHITE, bold=False,
        align=PP_ALIGN.LEFT, font=BODY_FONT):
    box = slide.shapes.add_textbox(left, top, w, h)
    tf  = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = text
    p.font.size      = Pt(size)
    p.font.color.rgb = color
    p.font.bold      = bold
    p.font.name      = font
    p.alignment      = align
    return box


def rect(slide, left, top, w, h, fill=CARD_BG, line=None, lw=0.75):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def footer(slide, n):
    rect(slide, Inches(0.5), Inches(6.95), Inches(12.333), Pt(0.75), fill=GRID_LINE)
    txt(slide, Inches(0.5), Inches(7.05), Inches(3), Inches(0.3),
        COMPANY, size=8, color=MID_GRAY, bold=True, font=HEAD_FONT)
    txt(slide, Inches(4.5), Inches(7.05), Inches(4.3), Inches(0.3),
        f"{EMAIL}  ·  {DOMAIN}",
        size=8, color=DARK_GRAY, align=PP_ALIGN.CENTER)
    txt(slide, Inches(10.5), Inches(7.05), Inches(2.333), Inches(0.3),
        f"{n:02d} / {TOTAL_SLIDES:02d}",
        size=8, color=MID_GRAY, bold=True, align=PP_ALIGN.RIGHT, font=HEAD_FONT)


def bullet_row(slide, x, y, dot_color, text, size=12):
    rect(slide, x, y + Inches(0.13), Inches(0.05), Inches(0.32), fill=dot_color)
    txt(slide, x + Inches(0.2), y + Inches(0.06),
        Inches(12.0 - x.inches if hasattr(x, 'inches') else 11.5), Inches(0.45),
        text, size=size, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — COVER
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.55), Inches(9), Inches(0.25),
    "PRE-SEED  ·  JUNE 2026  ·  CONFIDENTIAL",
    size=9, color=MID_GRAY, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.3), Inches(12.1), Inches(2.0),
    "CHARGEBOTIC\nINC",
    size=66, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(3.55), Inches(12.1), Inches(0.5),
    "Perch on power lines. Harvest energy. Deliver it anywhere.",
    size=18, color=ELECTRIC, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(4.2), Inches(9.5), Inches(0.5),
    "A drone that lands on power lines, extracts energy inductively, and powers "
    "defense systems or inspects the grid — with zero infrastructure changes.",
    size=12, color=LIGHT_GRAY)

rect(slide, 0, Inches(5.3), SW, Inches(1.25), fill=RGBColor(0x06, 0x10, 0x24))
stats = [
    ("$6.5M/yr",  "Active defense deal"),
    ("$30B+/yr",  "Inspection market"),
    ("7.3M km",   "Power lines worldwide"),
    ("0",         "Direct competitors"),
]
for i, (v, l) in enumerate(stats):
    x = Inches(1.0 + i * 3.0)
    txt(slide, x, Inches(5.42), Inches(2.6), Inches(0.44),
        v, size=24, color=WHITE, bold=True, font=HEAD_FONT)
    txt(slide, x, Inches(5.88), Inches(2.8), Inches(0.32),
        l, size=9, color=LIGHT_GRAY)

footer(slide, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "PROBLEM", size=9, color=DANGER_RED, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(1.3),
    "Two industries. Same\nunsolved problem.",
    size=48, bold=True, font=HEAD_FONT)

# Defense card
rect(slide, Inches(0.6), Inches(2.6), Inches(5.85), Inches(3.7),
     fill=CARD_BG, line=DANGER_RED, lw=1.2)
txt(slide, Inches(0.88), Inches(2.82), Inches(5.3), Inches(0.3),
    "DEFENSE", size=12, color=DANGER_RED, bold=True, font=HEAD_FONT)
txt(slide, Inches(0.88), Inches(3.25), Inches(5.35), Inches(0.8),
    "Autonomous systems go dark when batteries die. "
    "There is no silent, persistent way to recharge them in the field.",
    size=12, color=LIGHT_GRAY)
for j, b in enumerate([
    "$400/gal fuel cost at forward operating bases",
    "1 in 24 fuel convoy casualties (US Army study)",
    "250,000 Army vehicles, no field recharge solution",
]):
    txt(slide, Inches(0.88), Inches(4.35 + j * 0.6), Inches(5.35), Inches(0.5),
        f"·  {b}", size=12, color=WHITE)

# Utility card
rect(slide, Inches(6.88), Inches(2.6), Inches(5.85), Inches(3.7),
     fill=CARD_BG, line=AMBER, lw=1.2)
txt(slide, Inches(7.16), Inches(2.82), Inches(5.3), Inches(0.3),
    "UTILITY INSPECTION", size=12, color=AMBER, bold=True, font=HEAD_FONT)
txt(slide, Inches(7.16), Inches(3.25), Inches(5.35), Inches(0.8),
    "7.3M km of power lines, aging fast. Inspection is still done "
    "by helicopter or manual crew — slow, expensive, dangerous.",
    size=12, color=LIGHT_GRAY)
for j, b in enumerate([
    "Helicopter inspection: $500–1,000 per mile",
    "Vegetation encroachment causes 60%+ of outages",
    "$30B/year spent — mostly manual, not preventive",
]):
    txt(slide, Inches(7.16), Inches(4.35 + j * 0.6), Inches(5.35), Inches(0.5),
        f"·  {b}", size=12, color=WHITE)

footer(slide, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — THE OPPORTUNITY
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "OPPORTUNITY", size=9, color=ELECTRIC, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(0.8),
    "Two $30B markets. Nobody has touched them.",
    size=40, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.95), Inches(11.5), Inches(0.4),
    "Power lines run through every battlefield, every grid, every disaster zone. "
    "They carry enormous energy — and nobody is tapping it.",
    size=12, color=LIGHT_GRAY)

# Two TAM cards
markets = [
    ("$30B+", DANGER_RED, "Defense TAM",
     "Military field power for UGVs, sensors, and\nforward operating bases — US + NATO forces."),
    ("$30B+", AMBER, "Utility TAM",
     "Power line inspection market worldwide —\n7.3M km of lines, aging fast."),
]
for i, (value, color, label, desc) in enumerate(markets):
    x = Inches(0.6 + i * 6.2)
    rect(slide, x, Inches(2.6), Inches(5.85), Inches(2.0), fill=CARD_BG, line=color, lw=1.5)
    txt(slide, x + Inches(0.3), Inches(2.82), Inches(3.5), Inches(0.8),
        value, size=52, color=color, bold=True, font=HEAD_FONT)
    txt(slide, x + Inches(0.3), Inches(3.72), Inches(5.2), Inches(0.28),
        label, size=12, color=WHITE, bold=True, font=HEAD_FONT)
    txt(slide, x + Inches(0.3), Inches(4.05), Inches(5.3), Inches(0.5),
        desc, size=11, color=LIGHT_GRAY)

# SAM / SOM as text rows, not cards
txt(slide, Inches(0.6), Inches(5.0), Inches(11), Inches(0.3),
    "OUR PATH IN", size=9, color=MID_GRAY, bold=True, font=HEAD_FONT)
for i, (label, val) in enumerate([
    ("SAM — 5 years", "$50–200M  ·  B2B2G via Chariot + direct DoD; utility via Cupertino and Terna"),
    ("SOM — Year 3", "$25M  ·  30–100 units across both markets at $150–250K blended ASP"),
]):
    y = Inches(5.4 + i * 0.6)
    rect(slide, Inches(0.6), y + Inches(0.13), Inches(0.05), Inches(0.3), fill=ELECTRIC)
    txt(slide, Inches(0.85), y + Inches(0.06), Inches(2.6), Inches(0.4),
        label, size=12, color=WHITE, bold=True)
    txt(slide, Inches(3.3), y + Inches(0.06), Inches(9.3), Inches(0.4),
        val, size=11, color=LIGHT_GRAY)

footer(slide, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE SOLUTION
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "SOLUTION", size=9, color=GREEN_CHECK, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(1.1),
    "One drone.\nTwo markets.",
    size=52, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(2.3), Inches(11), Inches(0.38),
    "Chargebotic perches on any power line, harvests energy via magnetic induction, "
    "and uses it for two missions — with the same hardware.",
    size=12, color=LIGHT_GRAY)

# Steps — text rows, no boxes
steps = [
    (ELECTRIC,    "DEPLOY",   "Launch from any ground vehicle. No permits. No infrastructure changes."),
    (AMBER,       "PERCH",    "Computer vision locks onto the line. The drone clamps on and holds indefinitely."),
    (GREEN_CHECK, "HARVEST",  "Induction coil extracts AC energy from the line. No wire contact."),
    (WHITE,       "DELIVER",  "Defense: DC power down the tether to robots, sensors, comms.  "
                              "Utility: AI inspection data in real time."),
]

for i, (color, title, desc) in enumerate(steps):
    y = Inches(3.0 + i * 0.92)
    txt(slide, Inches(0.6), y, Inches(0.7), Inches(0.55),
        f"0{i+1}", size=26, color=color, bold=True, font=HEAD_FONT)
    txt(slide, Inches(1.45), y + Inches(0.08), Inches(1.7), Inches(0.3),
        title, size=13, color=color, bold=True, font=HEAD_FONT)
    txt(slide, Inches(3.3), y + Inches(0.08), Inches(9.4), Inches(0.7),
        desc, size=13, color=LIGHT_GRAY)
    if i < 3:
        rect(slide, Inches(0.6), y + Inches(0.78), Inches(12.1), Pt(0.75), fill=GRID_LINE)

footer(slide, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — THE TEAM
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "WHO WE ARE", size=9, color=AMBER, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(0.75),
    "Built to prototype, sell, and win contracts.",
    size=40, bold=True, font=HEAD_FONT)

team = [
    (ELECTRIC,    "ANIS CHERIET",              "Co-Founder & CEO",
     ["EV charging infrastructure background",
      "Fundraising, BD, investor relations",
      "Driving Chariot deal, Cupertino LOI, Terna deep dive"]),
    (AMBER,       "BO CHRISTOPHER REDFEARN",   "Co-Founder & CTO — Formerly Apple",
     ["Hardware and electrical engineering",
      "Leads prototype: inductive harvesting + tether",
      "BOM, suppliers, bench validation, certs roadmap"]),
    (GREEN_CHECK, "ARMIN FOROUGHI",             "Co-Founder — AI/ML",
     ["Computer vision and autonomy",
      "Power line detection and perch algorithms",
      "Real-time inspection data pipeline"]),
    (MID_GRAY,    "STEVE MACENSKI",             "Technical Advisor",
     ["Maintainer of Nav2 — most deployed open-source",
      "robotics navigation stack worldwide",
      "Autonomy and defense ecosystem access"]),
]

for i, (color, name, title, bullets) in enumerate(team):
    x = Inches(0.6 + i * 3.15)
    rect(slide, x, Inches(2.1), Inches(3.0), Inches(4.5),
         fill=CARD_BG, line=color, lw=1.0)
    txt(slide, x + Inches(0.18), Inches(2.25), Inches(2.75), Inches(0.32),
        name, size=11, color=WHITE, bold=True, font=HEAD_FONT)
    txt(slide, x + Inches(0.18), Inches(2.62), Inches(2.75), Inches(0.35),
        title, size=9, color=color, bold=True, font=HEAD_FONT)
    for j, b in enumerate(bullets):
        txt(slide, x + Inches(0.18), Inches(3.1 + j * 0.8), Inches(2.78), Inches(0.72),
            f"·  {b}", size=10, color=LIGHT_GRAY)

rect(slide, Inches(0.6), Inches(6.72), Inches(11.7), Inches(0.42),
     fill=RGBColor(0x0D, 0x1F, 0x0D), line=GREEN_CHECK, lw=0.75)
txt(slide, Inches(0.88), Inches(6.82), Inches(11.0), Inches(0.26),
    "Founders Inc Accelerator  ·  NVIDIA Inception  ·  Demo Day completed May 2026",
    size=11, color=WHITE)

footer(slide, 5)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — TRACTION
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "TRACTION", size=9, color=GREEN_CHECK, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(12), Inches(0.75),
    "Three live deals. One demo secured.",
    size=40, bold=True, font=HEAD_FONT)

traction_items = [
    (AMBER,       "Chariot Defense",
     "$6.5M/year commercial order pending JIFX pilot success. Adam Warmoth, CEO: "
     "\"The hardest part is keeping them charged.\" $41M raised, a16z Series A."),
    (ELECTRIC,    "Cupertino — Letter of Interest confirmed",
     "Largest utility inspector in the US. Power line inspection use case. "
     "Pilot scope in discussion."),
    (ELECTRIC,    "Terna Forward — Italian national grid CVC",
     "Italy's national power grid operator reached out. Deep dive scheduled Jun 30, 2026."),
    (GREEN_CHECK, "JIFX 26-4 secured — Aug 10–14, Camp Roberts CA",
     "Joint demo with Chariot Defense. Hardware ordered from ORQA, delivery Jul 1. "
     "Goal: energy harvest → Chariot Amphora ground system."),
]

for i, (color, title, desc) in enumerate(traction_items):
    y = Inches(2.15 + i * 1.12)
    rect(slide, Inches(0.6), y + Inches(0.05), Inches(0.05), Inches(0.78), fill=color)
    txt(slide, Inches(0.85), y, Inches(11.5), Inches(0.32),
        title, size=15, color=WHITE, bold=True)
    txt(slide, Inches(0.85), y + Inches(0.42), Inches(11.5), Inches(0.5),
        desc, size=12, color=LIGHT_GRAY)
    if i < 3:
        rect(slide, Inches(0.6), y + Inches(0.95), Inches(12.1), Pt(0.75), fill=GRID_LINE)

footer(slide, 6)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — NEXT MILESTONES + ASK
# ══════════════════════════════════════════════════════════════════════════════
slide = blank()
bg(slide, DEEP_SPACE)

txt(slide, Inches(0.6), Inches(0.5), Inches(9), Inches(0.25),
    "WHAT'S NEXT", size=9, color=ELECTRIC, bold=True, font=HEAD_FONT)

txt(slide, Inches(0.6), Inches(1.0), Inches(8), Inches(0.7),
    "18 months to seed-raise ready.",
    size=40, bold=True, font=HEAD_FONT)

milestones = [
    ("Aug 2026",   AMBER,       "JIFX 26-4 demo",
     "Energy harvest → Chariot Amphora. Camp Roberts CA."),
    ("Oct 2026",   AMBER,       "TRL 6 — working prototype",
     "Bench-validated. First real power line test."),
    ("Q4 2026",    ELECTRIC,    "First paid pilots",
     "2–3 units deployed — defense + utility."),
    ("Q1 2027",    ELECTRIC,    "SBIR Phase I",
     "$250K non-dilutive. Army + SOCOM applications."),
    ("Q3 2027",    GREEN_CHECK, "$100–200K ARR",
     "5–8 units contracted. Seed round launched."),
]

for i, (date, color, title, desc) in enumerate(milestones):
    y = Inches(2.1 + i * 0.82)
    rect(slide, Inches(0.62), y + Inches(0.04), Inches(0.16), Inches(0.16), fill=color)
    txt(slide, Inches(1.0), y, Inches(1.4), Inches(0.28),
        date, size=10, color=color, bold=True, font=HEAD_FONT)
    txt(slide, Inches(2.5), y, Inches(5.4), Inches(0.28),
        title, size=13, color=WHITE, bold=True)
    txt(slide, Inches(2.5), y + Inches(0.32), Inches(5.6), Inches(0.3),
        desc, size=11, color=LIGHT_GRAY)

# Ask box
rect(slide, Inches(8.5), Inches(1.85), Inches(4.25), Inches(4.75),
     fill=CARD_BG, line=ELECTRIC, lw=1.5)
txt(slide, Inches(8.75), Inches(2.05), Inches(3.75), Inches(0.28),
    "THE ASK", size=10, color=ELECTRIC, bold=True, font=HEAD_FONT)
txt(slide, Inches(8.75), Inches(2.45), Inches(3.75), Inches(0.75),
    "Raising $2M", size=36, color=WHITE, bold=True, font=HEAD_FONT)
txt(slide, Inches(8.75), Inches(3.28), Inches(3.75), Inches(0.28),
    "$10M cap SAFE  ·  18 months runway", size=10, color=LIGHT_GRAY)

ask_items = [
    (GREEN_CHECK, "JIFX demo + pilot units"),
    (GREEN_CHECK, "TRL 6 prototype by Oct 2026"),
    (GREEN_CHECK, "Utility pilots: Cupertino + Terna"),
    (GREEN_CHECK, "SBIR Phase I submitted"),
    (ELECTRIC,   "Seed-raise ready at $20–30M"),
]
for i, (color, item) in enumerate(ask_items):
    y = Inches(3.72 + i * 0.5)
    rect(slide, Inches(8.75), y + Inches(0.1), Inches(0.05), Inches(0.28), fill=color)
    txt(slide, Inches(8.95), y + Inches(0.06), Inches(3.6), Inches(0.38),
        item, size=11,
        color=ELECTRIC if color == ELECTRIC else WHITE,
        bold=(color == ELECTRIC))

txt(slide, Inches(0.6), Inches(6.25), Inches(4), Inches(0.26),
    "Anis Cheriet — anis@chargebotic.com", size=11, color=MID_GRAY)

footer(slide, 7)


# ── Save PPTX ─────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pptx_path = os.path.join(ROOT, "chargebotic-pitch-deck.pptx")
prs.save(pptx_path)
print(f"PPTX saved: {pptx_path}")


# ── Upload to Google Slides ────────────────────────────────────────────────────
def upload_to_google_slides(local_pptx_path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds_root  = os.path.dirname(os.path.dirname(ROOT))
    token_path  = os.path.join(creds_root, "token.json")
    creds_path  = os.path.join(creds_root, "credentials.json")

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    drive = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": "Chargebotic Inc — Investor Pitch Deck (June 2026)",
        "mimeType": "application/vnd.google-apps.presentation",
    }
    media = MediaFileUpload(
        local_pptx_path,
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation"
        ),
        resumable=True,
    )

    print("Uploading to Google Slides...")
    file = (
        drive.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    url = file.get("webViewLink")
    print(f"Google Slides URL: {url}")
    return url


upload_to_google_slides(pptx_path)

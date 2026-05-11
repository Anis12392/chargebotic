"""
Chargebotic Pitch Deck — NASA Ignition aesthetic, Serve-Robotics-level substance.
14 slides with unit economics, traction, competition, why-now, moon business.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree
import os

# NASA-inspired palette
BLACK        = RGBColor(0x00, 0x00, 0x00)
DEEP_SPACE   = RGBColor(0x05, 0x08, 0x14)
NASA_BLUE    = RGBColor(0x0B, 0x3D, 0x91)
NASA_RED     = RGBColor(0xFC, 0x3D, 0x21)
IGNITION_AMB = RGBColor(0xF9, 0x73, 0x16)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xD4, 0xD4, 0xD4)
MID_GRAY     = RGBColor(0x9A, 0x9A, 0x9A)
DARK_GRAY    = RGBColor(0x55, 0x55, 0x55)
GRID_LINE    = RGBColor(0x22, 0x26, 0x33)
CARD_BG      = RGBColor(0x0D, 0x11, 0x1C)
PLACEHOLDER  = RGBColor(0xFF, 0xB0, 0x40)  # orange highlight for TBD fields

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tmp", "deck-assets")
TOTAL_SLIDES = 14

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW = Inches(13.333)
SH = Inches(7.5)

HEAD_FONT = "Helvetica"
BODY_FONT = "Helvetica"


# ───────────────────────── helpers ─────────────────────────
def set_bg(slide, color=DEEP_SPACE):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, left, top, width, height, text,
             font_size=18, color=WHITE, bold=False,
             alignment=PP_ALIGN.LEFT, font_name=BODY_FONT,
             letter_spacing=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    if letter_spacing is not None:
        rPr = p.runs[0].font._rPr
        rPr.set("spc", str(letter_spacing))
    return box


def add_rect(slide, left, top, width, height,
             fill_color=CARD_BG, line_color=None, line_width_pt=None,
             alpha_pct=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if alpha_pct is not None:
        sp = shape.fill._xPr
        solidFill = sp.find(qn("a:solidFill"))
        srgbClr = solidFill.find(qn("a:srgbClr"))
        alpha_el = etree.SubElement(srgbClr, qn("a:alpha"))
        alpha_el.set("val", str(int((100 - alpha_pct) * 1000)))
    if line_color is not None:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width_pt or 0.75)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_fullbleed_image(slide, image_filename):
    path = os.path.join(ASSET_DIR, image_filename)
    slide.shapes.add_picture(path, 0, 0, width=SW, height=SH)


def add_mission_badge(slide, left, top, mission_id, label, color=NASA_RED):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  left, top, Inches(0.05), Inches(0.4))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    add_text(slide, left + Inches(0.18), top - Inches(0.02),
             Inches(3.0), Inches(0.25),
             mission_id, font_size=10, color=color, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    add_text(slide, left + Inches(0.18), top + Inches(0.2),
             Inches(8), Inches(0.3),
             label, font_size=11, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)


def add_footer(slide, page_num):
    add_rect(slide, Inches(0.5), Inches(6.95),
             Inches(12.333), Pt(0.75), fill_color=GRID_LINE)
    add_text(slide, Inches(0.5), Inches(7.05), Inches(3), Inches(0.3),
             "CHARGEBOTIC", font_size=8, color=MID_GRAY, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, Inches(4.5), Inches(7.05), Inches(4.3), Inches(0.3),
             "anis@chargebotic.com  ·  chargebotic.com",
             font_size=8, color=DARK_GRAY, alignment=PP_ALIGN.CENTER,
             font_name=BODY_FONT)
    add_text(slide, Inches(10.5), Inches(7.05), Inches(2.333), Inches(0.3),
             f"{page_num:02d} / {TOTAL_SLIDES:02d}", font_size=8, color=MID_GRAY,
             bold=True, alignment=PP_ALIGN.RIGHT, font_name=HEAD_FONT,
             letter_spacing=400)


def add_blank():
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_section_header(slide, mission_id, label, title, subtitle,
                       badge_color=IGNITION_AMB):
    """Standard top-of-slide header: badge + big title + subtitle."""
    add_mission_badge(slide, Inches(0.6), Inches(0.6),
                      mission_id, label, color=badge_color)
    add_text(slide, Inches(0.6), Inches(1.3), Inches(12), Inches(1.2),
             title, font_size=34, color=WHITE, bold=True, font_name=HEAD_FONT)
    if subtitle:
        add_text(slide, Inches(0.6), Inches(2.7), Inches(12), Inches(0.7),
                 subtitle, font_size=13, color=LIGHT_GRAY, font_name=BODY_FONT)


# ══════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE (Earthrise)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)
add_fullbleed_image(slide, "hero_earthrise.jpg")
add_rect(slide, 0, 0, SW, Inches(3.2), fill_color=BLACK, alpha_pct=35)
add_rect(slide, 0, Inches(5.8), SW, Inches(1.7), fill_color=BLACK, alpha_pct=60)

add_mission_badge(slide, Inches(0.6), Inches(0.5),
                   "MISSION BRIEF — 2026", "PRE-SEED · SAN FRANCISCO, CA")

add_text(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.4),
         "CHARGEBOTIC",
         font_size=92, color=WHITE, bold=True,
         alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT, letter_spacing=600)

add_rect(slide, Inches(5.4), Inches(2.75), Inches(2.5), Pt(2),
          fill_color=NASA_RED)

add_text(slide, Inches(0.5), Inches(2.9), Inches(12.3), Inches(0.6),
         "EMPOWERING ROBOTS ON THE MOON",
         font_size=22, color=WHITE, bold=True,
         alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT, letter_spacing=500)

add_text(slide, Inches(0.5), Inches(6.05), Inches(12.3), Inches(0.3),
         "BACKED BY",
         font_size=10, color=MID_GRAY, bold=True, alignment=PP_ALIGN.CENTER,
         font_name=HEAD_FONT, letter_spacing=500)
add_text(slide, Inches(0.5), Inches(6.35), Inches(12.3), Inches(0.5),
         "FOUNDERS INC.     ·     NVIDIA INCEPTION",
         font_size=20, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER,
         font_name=HEAD_FONT, letter_spacing=400)

add_footer(slide, 1)


# ══════════════════════════════════════════════════════════════
# SLIDE 2 — PROBLEM
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)

img_w = Inches(6.5)
slide.shapes.add_picture(os.path.join(ASSET_DIR, "problem_terminator.jpg"),
                          0, 0, width=img_w, height=SH)
add_rect(slide, Inches(5.5), 0, Inches(1.5), SH,
          fill_color=BLACK, alpha_pct=70)

add_mission_badge(slide, Inches(7.0), Inches(0.6),
                   "HAZARD — 01", "THE ENERGY BOTTLENECK", color=NASA_RED)

add_text(slide, Inches(7.0), Inches(1.4), Inches(6), Inches(2.2),
         "Energy kills\nlunar missions.",
         font_size=46, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(7.0), Inches(3.6), Inches(6), Inches(1.0),
         "Humanity must establish a lunar presence within 5 years. "
         "Robots get there first — but without reliable power, they "
         "freeze, stall, and strand operations within days.",
         font_size=13, color=LIGHT_GRAY, font_name=BODY_FONT)

stats = [
    ("14 DAYS",  "Max rover survival during lunar night"),
    ("−173 °C",  "Temperature extremes that kill batteries"),
    ("LIMITED",  "Exploration range — tethered to landers"),
]
for i, (stat, desc) in enumerate(stats):
    y = Inches(5.0 + i * 0.55)
    add_text(slide, Inches(7.0), y, Inches(1.8), Inches(0.4),
             stat, font_size=16, color=NASA_RED, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    add_text(slide, Inches(9.0), y, Inches(4), Inches(0.4),
             desc, font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

add_footer(slide, 2)


# ══════════════════════════════════════════════════════════════
# SLIDE 3 — WHY NOW (basecamp image, three converging trends)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)
add_fullbleed_image(slide, "basecamp_surface.jpg")
add_rect(slide, 0, 0, SW, SH, fill_color=BLACK, alpha_pct=55)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "CONTEXT — 02", "WHY NOW", color=IGNITION_AMB)

add_text(slide, Inches(0.6), Inches(1.3), Inches(12), Inches(1.0),
         "Three trends just converged.",
         font_size=38, color=WHITE, bold=True, font_name=HEAD_FONT)

trends = [
    ("01", "COMMERCIAL LUNAR",
     "NASA CLPS: $2.6B\ncommercial cargo to Moon.\nArtemis base camp target:\nlate 2020s."),
    ("02", "ROBOT FLEETS EXPLODE",
     "3M+ autonomous mobile\nrobots shipping by 2028.\nEnergy = the unsolved\nbottleneck."),
    ("03", "OPEN-STACK STANDARDIZED",
     "Nav2 / ROS 2 is now the\nde-facto navigation stack.\nOne integration target\ninstead of hundreds."),
]
for i, (num, title, body) in enumerate(trends):
    x = Inches(0.6 + i * 4.2)
    y = Inches(2.8)
    add_rect(slide, x, y, Inches(3.9), Inches(3.8),
              fill_color=CARD_BG, alpha_pct=15,
              line_color=GRID_LINE, line_width_pt=0.75)
    add_text(slide, x + Inches(0.3), y + Inches(0.25),
             Inches(3.3), Inches(0.6),
             num, font_size=36, color=IGNITION_AMB, bold=True,
             font_name=HEAD_FONT)
    add_text(slide, x + Inches(0.3), y + Inches(1.1),
             Inches(3.3), Inches(0.4),
             title, font_size=13, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    add_text(slide, x + Inches(0.3), y + Inches(1.6),
             Inches(3.3), Inches(2.0),
             body, font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

add_footer(slide, 3)


# ══════════════════════════════════════════════════════════════
# SLIDE 4 — SOLUTION (Orion + Moon)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)
add_fullbleed_image(slide, "solution_earth_moon.jpg")
add_rect(slide, Inches(3.4), 0, Inches(6.5), SH,
          fill_color=BLACK, alpha_pct=30)

add_mission_badge(slide, Inches(3.8), Inches(0.6),
                   "DIRECTIVE — 03", "THE SOLUTION", color=IGNITION_AMB)

add_text(slide, Inches(3.8), Inches(1.3), Inches(6.2), Inches(1.8),
         "Energy delivery\nfor any robot,\nanywhere.",
         font_size=40, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(3.8), Inches(4.1), Inches(6.2), Inches(1.0),
         "We are the last-mile logistics layer for energy — "
         "pulling from any generation source and delivering it "
         "to any robot, rover, or habitat that needs it.",
         font_size=13, color=LIGHT_GRAY, font_name=BODY_FONT)

pipe_y = Inches(5.5)
pipeline = [
    ("GENERATION",  "Solar  ·  Nuclear  ·  Regolith"),
    ("DELIVERY",    "Autonomous charging fleet"),
    ("CONSUMPTION", "Rovers  ·  Bases  ·  Drones"),
]
for i, (label, sub) in enumerate(pipeline):
    x = Inches(0.6 + i * 4.2)
    add_rect(slide, x, pipe_y, Inches(3.9), Inches(0.9),
              fill_color=CARD_BG, alpha_pct=20,
              line_color=GRID_LINE, line_width_pt=0.75)
    color = IGNITION_AMB if i == 1 else NASA_BLUE
    add_text(slide, x + Inches(0.2), pipe_y + Inches(0.12),
             Inches(3.5), Inches(0.3),
             label, font_size=10, color=color, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, x + Inches(0.2), pipe_y + Inches(0.45),
             Inches(3.5), Inches(0.4),
             sub, font_size=13, color=WHITE, bold=True, font_name=BODY_FONT)

for i in range(2):
    x = Inches(4.4 + i * 4.2)
    add_text(slide, x, pipe_y + Inches(0.25), Inches(0.4), Inches(0.5),
             "▸", font_size=22, color=IGNITION_AMB, bold=True,
             alignment=PP_ALIGN.CENTER)

add_footer(slide, 4)


# ══════════════════════════════════════════════════════════════
# SLIDE 5 — THE HOPPER (spec sheet)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)

img_w = Inches(6.8)
img_left = SW - img_w
slide.shapes.add_picture(os.path.join(ASSET_DIR, "how_crater.jpg"),
                          img_left, 0, width=img_w, height=SH)
add_rect(slide, img_left, 0, Inches(1.5), SH,
          fill_color=BLACK, alpha_pct=70)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "VEHICLE — 04", "THE HOPPER", color=IGNITION_AMB)

add_text(slide, Inches(0.6), Inches(1.4), Inches(6.0), Inches(1.5),
         "A charging station\nthat comes to you.",
         font_size=36, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(0.6), Inches(3.2), Inches(6.0), Inches(0.7),
         "Lightweight, foldable, self-returning. "
         "Delivers power to any robot at any site.",
         font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

# Spec sheet — 6 rows
specs = [
    ("RANGE",        "50 km",                "Per mission"),
    ("ENVIRONMENT",  "HARSH TERRAIN",        "Lunar-grade design"),
    ("DUTY CYCLE",   "SELF-RETURN",          "Recharges at base, infinite reuse"),
    ("FORM FACTOR",  "FOLDABLE",             "Minimal payload volume"),
    ("POWER OUTPUT", "[ TBD kW ]",           "Induction charging standard"),
    ("UNIT COST",    "$35K",                 "Plug-and-play, Earth SKU"),
]
for i, (label, value, desc) in enumerate(specs):
    y = Inches(4.1 + i * 0.45)
    add_rect(slide, Inches(0.6), y, Inches(6.0), Pt(0.5),
              fill_color=GRID_LINE)
    add_text(slide, Inches(0.6), y + Inches(0.05),
             Inches(1.6), Inches(0.35),
             label, font_size=10, color=MID_GRAY, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    is_tbd = "TBD" in value
    add_text(slide, Inches(2.3), y + Inches(0.05),
             Inches(2.2), Inches(0.35),
             value, font_size=14, color=PLACEHOLDER if is_tbd else IGNITION_AMB,
             bold=True, font_name=HEAD_FONT)
    add_text(slide, Inches(4.3), y + Inches(0.08),
             Inches(2.3), Inches(0.35),
             desc, font_size=10, color=LIGHT_GRAY, font_name=BODY_FONT)

add_footer(slide, 5)


# ══════════════════════════════════════════════════════════════
# SLIDE 6 — PRODUCT & TRACTION
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_section_header(slide,
                    "STATUS — 05", "PRODUCT & TRACTION",
                    "What we've built.",
                    "Prototype in hand. Partnerships signed. Capital aligned.")

# Left column — what's built
add_rect(slide, Inches(0.6), Inches(3.6), Inches(6.0), Inches(3.1),
          fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(0.9), Inches(3.75), Inches(5.4), Inches(0.3),
         "BUILT & DEMONSTRATED", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)

built = [
    ("✓", "Working hardware prototype"),
    ("✓", "Autonomous docking demo on video"),
    ("✓", "Nav2 / ROS 2 integration in progress"),
    ("✓", "Induction charging operational"),
    ("→", "[ FIRST PILOT CUSTOMER IN DISCUSSION ]"),
]
for i, (mark, label) in enumerate(built):
    y = Inches(4.2 + i * 0.45)
    color = NASA_RED if mark == "→" else IGNITION_AMB
    add_text(slide, Inches(0.9), y, Inches(0.35), Inches(0.35),
             mark, font_size=14, color=color, bold=True, font_name=HEAD_FONT)
    is_placeholder = "[" in label
    add_text(slide, Inches(1.25), y + Inches(0.02),
             Inches(5.1), Inches(0.35),
             label, font_size=12,
             color=PLACEHOLDER if is_placeholder else WHITE,
             font_name=BODY_FONT)

# Right column — validation / backers
add_rect(slide, Inches(6.8), Inches(3.6), Inches(5.9), Inches(3.1),
          fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(7.1), Inches(3.75), Inches(5.3), Inches(0.3),
         "VALIDATION", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)

validations = [
    ("FOUNDERS INC.",     "Pre-seed backer"),
    ("NVIDIA INCEPTION",  "Accepted — compute + GTM"),
    ("STEVE MACENSKI",    "Nav2 maintainer — active collaboration"),
    ("Y COMBINATOR",      "[ APPLIED — PENDING ]"),
    ("SPEEDRUN (A16Z)",   "[ APPLIED — PENDING ]"),
]
for i, (name, status) in enumerate(validations):
    y = Inches(4.2 + i * 0.45)
    add_text(slide, Inches(7.1), y, Inches(2.8), Inches(0.35),
             name, font_size=12, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    is_placeholder = "[" in status
    add_text(slide, Inches(10.0), y + Inches(0.02),
             Inches(2.6), Inches(0.35),
             status, font_size=11,
             color=PLACEHOLDER if is_placeholder else LIGHT_GRAY,
             font_name=BODY_FONT)

add_footer(slide, 6)


# ══════════════════════════════════════════════════════════════
# SLIDE 7 — BUSINESS MODEL & UNIT ECONOMICS
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_section_header(slide,
                    "MODEL — 06", "BUSINESS MODEL",
                    "Hardware margin today. Software compounding tomorrow.",
                    "Every Hopper sold becomes a recurring-revenue endpoint.")

# Three revenue columns
streams = [
    ("HARDWARE SALE",
     "$35K",
     "Per unit",
     [
         "Plug-and-play station",
         "One-time revenue",
         "~43% gross margin",
         "[ COGS ≈ $20k target ]",
     ],
     IGNITION_AMB),
    ("SOFTWARE (SaaS)",
     "$2K",
     "Per station / year",
     [
         "Fleet energy management",
         "Charging optimization",
         "Recurring, high margin",
         "Scales with every unit sold",
     ],
     NASA_BLUE),
    ("SERVICES",
     "$5K",
     "Per deployment",
     [
         "Install + integration",
         "Nav2 onboarding",
         "Pilot support",
         "Conversion engine for SaaS",
     ],
     NASA_RED),
]

for i, (title, price, unit, bullets, color) in enumerate(streams):
    x = Inches(0.6 + i * 4.2)
    y = Inches(3.6)
    add_rect(slide, x, y, Inches(3.9), Inches(3.1),
              fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
    # color strip top
    add_rect(slide, x, y, Inches(3.9), Inches(0.08), fill_color=color)
    add_text(slide, x + Inches(0.3), y + Inches(0.25),
             Inches(3.3), Inches(0.3),
             title, font_size=10, color=color, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, x + Inches(0.3), y + Inches(0.6),
             Inches(3.3), Inches(0.6),
             price, font_size=36, color=WHITE, bold=True,
             font_name=HEAD_FONT)
    add_text(slide, x + Inches(0.3), y + Inches(1.25),
             Inches(3.3), Inches(0.3),
             unit, font_size=10, color=MID_GRAY, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    for j, b in enumerate(bullets):
        is_p = "[" in b
        add_text(slide, x + Inches(0.3), y + Inches(1.7 + j * 0.3),
                 Inches(3.3), Inches(0.3),
                 f"·  {b}", font_size=11,
                 color=PLACEHOLDER if is_p else LIGHT_GRAY,
                 font_name=BODY_FONT)

add_footer(slide, 7)


# ══════════════════════════════════════════════════════════════
# SLIDE 8 — EARTH BEACHHEAD (GTM)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_section_header(slide,
                    "OPERATION — 07", "EARTH BEACHHEAD",
                    "Become the charging standard on Earth.",
                    "A multipurpose station co-designed with the Nav2 ecosystem — "
                    "the de facto navigation stack for mobile robots.")

add_rect(slide, Inches(0.6), Inches(3.8), Inches(6.0), Inches(2.9),
          fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(0.9), Inches(3.95), Inches(5.4), Inches(0.3),
         "2026 MILESTONES", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
milestones = [
    "30 charging stations produced & sold",
    "Deep Nav2 / ROS 2 integration shipped",
    "Active collaboration: Steve Macenski",
    "Paying pilots across 3 verticals",
    "$1M revenue run-rate by Q4 2026",
]
for i, m in enumerate(milestones):
    y = Inches(4.4 + i * 0.42)
    add_text(slide, Inches(0.9), y, Inches(0.3), Inches(0.35),
             "▸", font_size=13, color=NASA_RED, bold=True)
    add_text(slide, Inches(1.25), y + Inches(0.02), Inches(5.1), Inches(0.35),
             m, font_size=12, color=WHITE, font_name=BODY_FONT)

add_rect(slide, Inches(6.8), Inches(3.8), Inches(5.9), Inches(2.9),
          fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(7.1), Inches(3.95), Inches(5.3), Inches(0.3),
         "STRATEGIC WEDGE", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
add_text(slide, Inches(7.1), Inches(4.35), Inches(5.3), Inches(0.5),
         "NAV2 / ROS 2", font_size=20, color=WHITE, bold=True,
         font_name=HEAD_FONT, letter_spacing=300)
add_text(slide, Inches(7.1), Inches(4.85), Inches(5.3), Inches(1.8),
         "Nav2 powers robots across agriculture, logistics, "
         "and defense — hundreds of fleets, one open stack.\n\n"
         "Co-development with Steve Macenski (Nav2 lead "
         "maintainer) embeds Chargebotic charging inside the "
         "navigation stack itself.",
         font_size=11, color=LIGHT_GRAY, font_name=BODY_FONT)

add_footer(slide, 8)


# ══════════════════════════════════════════════════════════════
# SLIDE 9 — MARKET / TAM
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_section_header(slide,
                    "MARKET — 08", "TAM & VERTICALS",
                    "$35K plug-and-play.\nEvery robotics vertical.",
                    "One charging standard cuts integration cost for every "
                    "robotics company shipping hardware today.")

verticals = [
    ("AGRICULTURE",      Inches(0.6),  Inches(3.9)),
    ("LAST-MILE",        Inches(2.75), Inches(3.9)),
    ("AMR / WAREHOUSE",  Inches(4.9),  Inches(3.9)),
    ("UAV / DRONES",     Inches(0.6),  Inches(5.0)),
    ("DEFENSE",          Inches(2.75), Inches(5.0)),
    ("INDUSTRIAL",       Inches(4.9),  Inches(5.0)),
]
for name, x, y in verticals:
    add_rect(slide, x, y, Inches(2.05), Inches(0.95),
              fill_color=CARD_BG, line_color=NASA_BLUE, line_width_pt=1.0)
    add_text(slide, x, y + Inches(0.3), Inches(2.05), Inches(0.4),
             name, font_size=12, color=WHITE, bold=True,
             alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT,
             letter_spacing=300)

big_x = Inches(8.2)
big_y = Inches(3.5)
big_w = Inches(4.5)
big = slide.shapes.add_shape(MSO_SHAPE.OVAL, big_x, big_y, big_w, big_w)
big.fill.solid()
big.fill.fore_color.rgb = IGNITION_AMB
big.line.color.rgb = WHITE
big.line.width = Pt(2)

tf = big.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.2)
tf.margin_right = Inches(0.2)
p = tf.paragraphs[0]
p.text = "$38B"
p.font.size = Pt(68)
p.font.color.rgb = BLACK
p.font.bold = True
p.font.name = HEAD_FONT
p.alignment = PP_ALIGN.CENTER
p2 = tf.add_paragraph()
p2.text = "ROBOT CHARGING TAM"
p2.font.size = Pt(12)
p2.font.color.rgb = BLACK
p2.font.bold = True
p2.font.name = HEAD_FONT
p2.alignment = PP_ALIGN.CENTER
p3 = tf.add_paragraph()
p3.text = "BY 2033"
p3.font.size = Pt(10)
p3.font.color.rgb = BLACK
p3.font.name = HEAD_FONT
p3.alignment = PP_ALIGN.CENTER

add_footer(slide, 9)


# ══════════════════════════════════════════════════════════════
# SLIDE 10 — COMPETITION (matrix)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_section_header(slide,
                    "LANDSCAPE — 09", "COMPETITION",
                    "One product. Every axis.",
                    "Existing charging tech is proprietary, fixed, or Earth-only. "
                    "Chargebotic is the only universal + autonomous + moon-grade stack.")

# Matrix headers
cols = ["UNIVERSAL", "AUTONOMOUS", "SW PLATFORM", "MOON-GRADE"]
rows = [
    ("CHARGEBOTIC",       [True,  True,  True,  True],  IGNITION_AMB),
    ("WiBotic",           [True,  False, False, False], MID_GRAY),
    ("InductEV",          [False, False, False, False], MID_GRAY),
    ("OEM Docking",       [False, True,  False, False], MID_GRAY),
    ("Manual Plug-in",    [True,  False, False, False], MID_GRAY),
]

table_left = Inches(0.6)
table_top = Inches(3.8)
row_h = Inches(0.55)
name_w = Inches(3.2)
col_w = Inches(2.35)

# Header row
add_text(slide, table_left, table_top, name_w, row_h,
         "PLAYER", font_size=10, color=MID_GRAY, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
for i, col in enumerate(cols):
    x = table_left + name_w + col_w * i
    add_text(slide, x, table_top, col_w, row_h,
             col, font_size=10, color=MID_GRAY, bold=True,
             alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT,
             letter_spacing=400)

# Divider under header
add_rect(slide, table_left, table_top + Inches(0.4),
          Inches(12.1), Pt(1), fill_color=GRID_LINE)

for r, (player, checks, color) in enumerate(rows):
    y = table_top + Inches(0.55) + row_h * r
    is_us = r == 0
    if is_us:
        add_rect(slide, table_left, y, Inches(12.1), row_h,
                  fill_color=CARD_BG, alpha_pct=0)
    add_text(slide, table_left + Inches(0.1), y + Inches(0.12),
             name_w, row_h,
             player, font_size=13, color=color,
             bold=is_us, font_name=HEAD_FONT,
             letter_spacing=300 if is_us else None)
    for i, ok in enumerate(checks):
        x = table_left + name_w + col_w * i
        mark = "●" if ok else "○"
        mark_color = IGNITION_AMB if (ok and is_us) else (
            WHITE if ok else DARK_GRAY)
        add_text(slide, x, y + Inches(0.1), col_w, row_h,
                 mark, font_size=22, color=mark_color, bold=True,
                 alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT)

add_footer(slide, 10)


# ══════════════════════════════════════════════════════════════
# SLIDE 11 — REVENUE TRAJECTORY
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

img_w = Inches(3.0)
img_h = Inches(3.0)
slide.shapes.add_picture(os.path.join(ASSET_DIR, "market_crescent_earth.jpg"),
                          SW - img_w - Inches(0.4), Inches(0.5),
                          width=img_w, height=img_h)
add_rect(slide, SW - img_w - Inches(0.4), Inches(0.5), img_w, img_h,
          fill_color=BLACK, alpha_pct=45)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "TRAJECTORY — 10", "REVENUE FORECAST", color=IGNITION_AMB)

add_text(slide, Inches(0.6), Inches(1.3), Inches(9), Inches(1.0),
         "Earth today. Moon\nby 2029.",
         font_size=34, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(0.6), Inches(3.1), Inches(12), Inches(0.5),
         "Earth SKU compounds hardware + SaaS. Lunar activation "
         "multiplies the curve by 30×.",
         font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

chart_top = Inches(4.0)
baseline_y = Inches(6.5)
add_rect(slide, Inches(1.0), baseline_y,
          Inches(11.3), Pt(1), fill_color=GRID_LINE)

points = [
    ("2026", "$1M",    1.5, 0.20, NASA_BLUE),
    ("2027", "$8M",    3.0, 0.50, NASA_BLUE),
    ("2028", "$30M",   4.5, 0.90, NASA_BLUE),
    ("2029", "$100M",  6.3, 1.35, IGNITION_AMB),
    ("2030", "$800M",  8.5, 1.85, IGNITION_AMB),
    ("2031", "$3B",    10.8, 2.35, NASA_RED),
]
for year, label, x_in, h_in, color in points:
    bar_w = Inches(1.1)
    bar_h = Inches(h_in)
    bar_top = baseline_y - bar_h
    bar_left = Inches(x_in - 0.55)
    add_rect(slide, bar_left, bar_top, bar_w, bar_h, fill_color=color)
    add_text(slide, Inches(x_in - 1.0), bar_top - Inches(0.38),
             Inches(2.0), Inches(0.35),
             label, font_size=13, color=WHITE, bold=True,
             alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT)
    add_text(slide, Inches(x_in - 1.0), baseline_y + Inches(0.08),
             Inches(2.0), Inches(0.3),
             year, font_size=10, color=MID_GRAY, bold=True,
             alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT,
             letter_spacing=200)

add_text(slide, Inches(1.5), Inches(3.7), Inches(3.5), Inches(0.3),
         "◆ EARTH PHASE", font_size=9, color=NASA_BLUE, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
add_text(slide, Inches(5.8), Inches(3.7), Inches(5.0), Inches(0.3),
         "◆ LUNAR ACTIVATION",
         font_size=9, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)

add_footer(slide, 11)


# ══════════════════════════════════════════════════════════════
# SLIDE 12 — MOON ACTIVATION (basecamp image)
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)
add_fullbleed_image(slide, "basecamp_surface.jpg")
add_rect(slide, 0, 0, SW, SH, fill_color=BLACK, alpha_pct=40)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "ACTIVATION — 11", "LUNAR MARKET (2029+)", color=NASA_RED)

add_text(slide, Inches(0.6), Inches(1.3), Inches(12), Inches(1.0),
         "The Moon is now a market.",
         font_size=38, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(0.6), Inches(2.6), Inches(12), Inches(0.7),
         "NASA's CLPS program is buying commercial cargo to the lunar surface. "
         "Lunar night power is a NASA-declared priority gap.",
         font_size=13, color=LIGHT_GRAY, font_name=BODY_FONT)

# Three moon-economy cards
moon_cards = [
    ("$2.6B",       "NASA CLPS",
     "Commercial payload\nservices already\nprocured."),
    ("$1.2M / kg",  "PAYLOAD COST",
     "Foldable + lightweight\ndesign = ideal\npayload economics."),
    ("$10B+",       "LUNAR SURFACE TAM",
     "Surface logistics &\npower delivery\nby 2035."),
]
for i, (stat, title, body) in enumerate(moon_cards):
    x = Inches(0.6 + i * 4.2)
    y = Inches(3.8)
    add_rect(slide, x, y, Inches(3.9), Inches(2.7),
              fill_color=CARD_BG, alpha_pct=20,
              line_color=GRID_LINE, line_width_pt=0.75)
    add_text(slide, x + Inches(0.3), y + Inches(0.25),
             Inches(3.3), Inches(0.8),
             stat, font_size=34, color=IGNITION_AMB, bold=True,
             font_name=HEAD_FONT)
    add_text(slide, x + Inches(0.3), y + Inches(1.1),
             Inches(3.3), Inches(0.35),
             title, font_size=11, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, x + Inches(0.3), y + Inches(1.55),
             Inches(3.3), Inches(1.0),
             body, font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

# Bottom: business model for moon
add_text(slide, Inches(0.6), Inches(6.65), Inches(12.1), Inches(0.3),
         "LUNAR MODEL — HARDWARE SALE TO OPERATORS  ·  $/kWh DELIVERED  ·  NASA + COMMERCIAL PRIMES",
         font_size=10, color=IGNITION_AMB, bold=True,
         alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT, letter_spacing=400)

add_footer(slide, 12)


# ══════════════════════════════════════════════════════════════
# SLIDE 13 — TEAM
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, DEEP_SPACE)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "PERSONNEL — 12", "THE TEAM", color=IGNITION_AMB)

add_text(slide, Inches(0.6), Inches(1.3), Inches(12), Inches(0.9),
         "Operators, builders & advisors.",
         font_size=34, color=WHITE, bold=True, font_name=HEAD_FONT)

core = [
    ("ANIS CHERIET",    "CO-FOUNDER · CEO",           "Energy systems &\ngo-to-market."),
    ("BO",              "ENGINEERING (EX-APPLE)",     "Left Apple to build\nChargebotic hardware."),
    ("STEVE MACENSKI",  "NAV2 COLLABORATION",         "Lead maintainer — ROS 2\nnavigation stack."),
]
for i, (name, role, bio) in enumerate(core):
    x = Inches(0.6 + i * 4.2)
    y = Inches(2.6)
    add_rect(slide, x, y, Inches(3.9), Inches(2.2),
              fill_color=CARD_BG, line_color=NASA_BLUE, line_width_pt=1.0)
    add_rect(slide, x, y, Inches(3.9), Inches(0.08), fill_color=NASA_RED)
    add_text(slide, x + Inches(0.3), y + Inches(0.3),
             Inches(3.3), Inches(0.45),
             name, font_size=18, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    add_text(slide, x + Inches(0.3), y + Inches(0.85),
             Inches(3.3), Inches(0.3),
             role, font_size=10, color=IGNITION_AMB, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, x + Inches(0.3), y + Inches(1.25),
             Inches(3.3), Inches(0.8),
             bio, font_size=12, color=LIGHT_GRAY, font_name=BODY_FONT)

advisors = [
    ("ARNE",    "ADVISOR"),
    ("PATRICK", "ADVISOR"),
    ("HADI",    "ADVISOR"),
]
for i, (name, role) in enumerate(advisors):
    x = Inches(0.6 + i * 4.2)
    y = Inches(5.0)
    add_rect(slide, x, y, Inches(3.9), Inches(1.4),
              fill_color=CARD_BG, line_color=GRID_LINE, line_width_pt=0.75)
    add_text(slide, x + Inches(0.3), y + Inches(0.25),
             Inches(3.3), Inches(0.45),
             name, font_size=16, color=WHITE, bold=True,
             font_name=HEAD_FONT, letter_spacing=300)
    add_text(slide, x + Inches(0.3), y + Inches(0.72),
             Inches(3.3), Inches(0.3),
             role, font_size=10, color=NASA_RED, bold=True,
             font_name=HEAD_FONT, letter_spacing=400)
    add_text(slide, x + Inches(0.3), y + Inches(1.05),
             Inches(3.3), Inches(0.3),
             "Strategic guidance", font_size=11, color=LIGHT_GRAY,
             font_name=BODY_FONT)

add_text(slide, Inches(0.6), Inches(6.55), Inches(12), Inches(0.3),
         "LET'S POWER THE NEXT CIVILIZATION   ·   anis@chargebotic.com",
         font_size=11, color=IGNITION_AMB, bold=True,
         alignment=PP_ALIGN.CENTER, font_name=HEAD_FONT, letter_spacing=400)

add_footer(slide, 13)


# ══════════════════════════════════════════════════════════════
# SLIDE 14 — THE ASK
# ══════════════════════════════════════════════════════════════
slide = add_blank()
set_bg(slide, BLACK)
add_fullbleed_image(slide, "ask_hertzsprung.jpg")
add_rect(slide, 0, 0, SW, SH, fill_color=BLACK, alpha_pct=45)
add_rect(slide, 0, Inches(2.5), SW, Inches(4.0),
          fill_color=BLACK, alpha_pct=25)

add_mission_badge(slide, Inches(0.6), Inches(0.6),
                   "REQUEST — 13", "THE ASK", color=NASA_RED)

add_text(slide, Inches(0.6), Inches(1.3), Inches(12), Inches(1.0),
         "Raising $2.2M.",
         font_size=64, color=WHITE, bold=True, font_name=HEAD_FONT)

add_text(slide, Inches(0.6), Inches(2.5), Inches(12), Inches(0.6),
         "6–12 months to production and go-to-market.",
         font_size=20, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=300)

add_rect(slide, Inches(0.6), Inches(3.4), Inches(6.0), Inches(3.1),
          fill_color=CARD_BG, alpha_pct=15,
          line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(0.9), Inches(3.55), Inches(5.4), Inches(0.3),
         "USE OF CAPITAL", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
uses = [
    ("Hardware R&D & production",       "45%"),
    ("Pilot deployments & field tests", "25%"),
    ("Engineering hires (HW + SW)",     "20%"),
    ("Operations & G&A",                "10%"),
]
for i, (label, pct) in enumerate(uses):
    y = Inches(4.0 + i * 0.55)
    add_text(slide, Inches(0.9), y, Inches(4.2), Inches(0.4),
             label, font_size=13, color=WHITE, font_name=BODY_FONT)
    add_text(slide, Inches(5.1), y, Inches(1.3), Inches(0.4),
             pct, font_size=15, color=NASA_RED, bold=True,
             alignment=PP_ALIGN.RIGHT, font_name=HEAD_FONT)

add_rect(slide, Inches(6.8), Inches(3.4), Inches(5.9), Inches(3.1),
          fill_color=CARD_BG, alpha_pct=15,
          line_color=GRID_LINE, line_width_pt=0.75)
add_text(slide, Inches(7.1), Inches(3.55), Inches(5.3), Inches(0.3),
         "WHAT $2.2M DELIVERS", font_size=10, color=IGNITION_AMB, bold=True,
         font_name=HEAD_FONT, letter_spacing=400)
wins = [
    "Production-ready charging station",
    "30 units built & deployed in 2026",
    "Pre-orders from 3+ robotics OEMs",
    "Pilot data: agriculture + AMR",
    "Line of sight to Series A",
]
for i, w in enumerate(wins):
    y = Inches(4.0 + i * 0.45)
    add_text(slide, Inches(7.1), y, Inches(0.3), Inches(0.35),
             "▸", font_size=13, color=NASA_RED, bold=True)
    add_text(slide, Inches(7.45), y + Inches(0.02), Inches(5.0), Inches(0.35),
             w, font_size=13, color=WHITE, font_name=BODY_FONT)

add_footer(slide, 14)


# ══════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "chargebotic-pitch-deck.pptx")
prs.save(output_path)
print(f"Pitch deck saved: {output_path}")

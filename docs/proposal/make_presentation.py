"""Build the MCQM proposal deck from SCRIPT_ChatGPT.md.

Run with the bundled Python that provides python-pptx, or any Python with
python-pptx installed.  The script only writes beside this source file.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


HERE = Path(__file__).resolve().parent
ASSETS = HERE / "presentation_assets"
LOGOS = ASSETS / "logos"
OUT = HERE / "MCQM_Final_Proposal_GoogleMeet_2026-10-26.pptx"
SCRIPT = HERE / "SCRIPT_ChatGPT.md"

SW, SH = 13.333, 7.5
NAVY = "F8FAF9"
PANEL = "FFFFFF"
PANEL2 = "EAF3F1"
WHITE = "172B28"
MUTED = "52625E"
CYAN = "00897B"  # Google Meet teal
AMBER = "FBBC04"
GREEN = "34A853"
LINE = "D5E0DD"
TEAL_PANEL = "DDF3EF"
AMBER_PANEL = "FEF5DC"
PURPLE_PANEL = "EFE8FA"
BLUE_PANEL = "E8F0FE"
GOOGLE_BLUE = "4285F4"
GOOGLE_RED = "EA4335"


def col(hex_rgb: str) -> RGBColor:
    return RGBColor.from_string(hex_rgb)


def rect(slide, x, y, w, h, fill, radius=False, line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = col(fill)
    shape.line.fill.background() if line is None else None
    if line is not None:
        shape.line.color.rgb = col(line)
        shape.line.width = Pt(1)
    if radius:
        shape.adjustments[0] = 0.12
    return shape


def txt(slide, text, x, y, w, h, size=18, color=WHITE, bold=False,
        align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, font="Aptos"):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.01)
    tf.margin_top = tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = valign
    for index, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = col(color)
    return box


def line(slide, x1, y1, x2, y2, color=LINE, width=1.4):
    shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                       Inches(x2), Inches(y2))
    shape.line.color.rgb = col(color)
    shape.line.width = Pt(width)
    return shape


def circle(slide, x, y, d, fill, label="", color=NAVY, size=14):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid(); s.fill.fore_color.rgb = col(fill); s.line.fill.background()
    if label:
        txt(slide, label, x, y, d, d, size, color, True, PP_ALIGN.CENTER)
    return s


def add_image_crop(slide, path, x, y, w, h):
    with Image.open(path) as im:
        iw, ih = im.size
    target = w / h
    aspect = iw / ih
    if aspect > target:
        crop = (iw - ih * target) / (2 * iw)
        picture = slide.shapes.add_picture(str(path), Inches(x), Inches(y),
                                           width=Inches(w), height=Inches(h))
        picture.crop_left = picture.crop_right = crop
    else:
        crop = (ih - iw / target) / (2 * ih)
        picture = slide.shapes.add_picture(str(path), Inches(x), Inches(y),
                                           width=Inches(w), height=Inches(h))
        picture.crop_top = picture.crop_bottom = crop


def add_image_contain(slide, path, x, y, w, h):
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - pw) / 2),
                             Inches(y + (h - ph) / 2),
                             width=Inches(pw), height=Inches(ph))


def base(prs, no, section, title, subtitle=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, SW, SH, NAVY)
    rect(s, 0, 0, SW, 0.075, CYAN)
    txt(s, title, 0.60, 0.52, 12.05, 0.69, 32, WHITE, True)
    if subtitle:
        txt(s, subtitle, 0.62, 1.21, 12.02, 0.37, 18, MUTED)
    return s


def card(slide, x, y, w, h, kicker, title, body, accent=CYAN, title_size=19, body_size=13):
    rect(slide, x, y, w, h, PANEL, True)
    rect(slide, x, y, 0.055, h, accent)
    txt(slide, kicker.upper(), x + 0.24, y + 0.20, w - 0.46, 0.24, 9.5, accent, True)
    txt(slide, title, x + 0.24, y + 0.55, w - 0.48, 0.58, title_size, WHITE, True)
    txt(slide, body, x + 0.24, y + 1.22, w - 0.48, h - 1.37, body_size, MUTED,
        valign=MSO_ANCHOR.TOP)


def notes_for(number):
    raw = SCRIPT.read_text(encoding="utf-8")
    m = re.search(rf"(?ms)^## Slide {number} — .*?\n(.*?)(?=^## Slide \d+ — |^---\s*$)", raw)
    if not m:
        raise ValueError(f"Missing script for slide {number}")
    body = re.sub(r"^\*\d:\d+–\d+:\d+\*\s*", "", m.group(1).strip())
    return body.strip()


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)

    # 1 — typographic cover with the core project question.
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, SW, SH, NAVY)
    rect(s, 0, 0, 0.12, SH, CYAN)
    txt(s, "MCQM     /     CSE 310 FINAL PROJECT PROPOSAL", 0.82, 0.55, 11.7, 0.38, 15, CYAN, True)
    txt(s, "Is it the network\nor my laptop?", 0.82, 1.48, 8.9, 1.85, 43, WHITE, True)
    rect(s, 0.86, 3.77, 1.05, 0.08, GOOGLE_BLUE)
    rect(s, 1.91, 3.77, 0.70, 0.08, GOOGLE_RED)
    rect(s, 2.61, 3.77, 0.70, 0.08, AMBER)
    rect(s, 3.31, 3.77, 1.05, 0.08, GREEN)
    txt(s, "Real-time call quality from packet headers", 0.86, 4.18, 8.9, 0.58, 24, MUTED)
    txt(s, "Multi-layer Call Quality Monitor", 0.86, 4.82, 8.9, 0.40, 17, MUTED)
    txt(s, "Sungmin Choo  ·  Yerim Cho", 0.86, 6.15, 6.4, 0.40, 18, WHITE, True)
    txt(s, "01    MOTIVATION       02    METHOD       03    EVIDENCE", 8.25, 6.15, 4.2, 0.40, 12, MUTED, True)

    # 2 — agenda, in the order used by the presentation script.
    s = base(prs, 2, "00 / Overview", "Today’s route")
    agenda = [
        ("01", "Motivation", "The question we are trying to answer"),
        ("02", "Background", "vcaml and existing platform tools"),
        ("03", "Our approach", "What MCQM adds and how it works"),
        ("04", "Evidence", "Pilots, evaluation plan, and risks"),
        ("05", "Demo + conclusion", "What we aim to show and learn"),
    ]
    for i, (number, heading, detail) in enumerate(agenda):
        y = 1.70 + i * 0.96
        txt(s, number, 0.86, y, 0.72, 0.44, 18, CYAN, True)
        txt(s, heading, 1.82, y - 0.02, 3.6, 0.48, 22, WHITE, True)
        txt(s, detail, 5.25, y, 6.8, 0.44, 17, MUTED)
        if i < 4:
            rect(s, 1.82, y + 0.62, 10.2, 0.015, LINE)

    # 3 — the method uses packet metadata instead of payload content.
    s = base(prs, 2, "01 / Background", "vcaml reads the packet—not the video")
    stages = [
        ("01", "Encrypted call", "Payload hidden"),
        ("02", "Packet metadata", "Size + timing"),
        ("03", "Random Forest", "1-second windows"),
        ("04", "Quality estimate", "fps · bitrate · jitter · size"),
    ]
    for i, (n, title, detail) in enumerate(stages):
        x = 0.60 + i * 3.18
        rect(s, x, 1.67, 2.76, 1.32, PANEL, True)
        txt(s, n, x + 0.19, 1.81, 0.45, 0.30, 17, CYAN, True)
        txt(s, title, x + 0.19, 2.12, 2.43, 0.39, 19.5, WHITE, True)
        txt(s, detail, x + 0.19, 2.57, 2.43, 0.30, 15.5, MUTED)
        if i < 3:
            txt(s, "→", x + 2.78, 2.14, 0.34, 0.38, 22, CYAN, True, PP_ALIGN.CENTER)
    rect(s, 0.60, 3.30, 5.86, 2.24, TEAL_PANEL, True)
    txt(s, "BEFORE ENCRYPTION", 0.87, 3.62, 5.32, 0.42, 21, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "H.264 frame #124\n1920×1080", 0.92, 4.21, 5.24, 0.96,
        24, WHITE, True, PP_ALIGN.CENTER, font="Consolas")
    rect(s, 6.75, 3.30, 5.96, 2.24, AMBER_PANEL, True)
    txt(s, "AFTER ENCRYPTION", 7.02, 3.62, 5.42, 0.42, 21, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "0x8F  0xA3  0x11  0x7E\n0x9C  0xF4  0x02  …", 7.04, 4.21, 5.36, 0.96,
        21, WHITE, True, PP_ALIGN.CENTER, font="Consolas")
    txt(s, "Illustrative example", 0.66, 5.62, 4.30, 0.32, 16, MUTED)
    txt(s, "1.50 → 1.49", 0.62, 6.03, 5.47, 0.63, 31, CYAN, True)
    txt(s, "fps error  ·  paper → our reproduction", 0.64, 6.70, 5.70, 0.31, 16, MUTED)
    txt(s, "VCAML LIMITS", 6.80, 5.89, 5.31, 0.36, 18, AMBER, True)
    for j, label in enumerate(["OFFLINE", "LINUX LAB", "NO CAUSE"]):
        x = 6.80 + j * 1.95
        rect(s, x, 6.37, 1.79, 0.63, PANEL2, True)
        txt(s, label, x + 0.06, 6.50, 1.67, 0.31, 16.4, WHITE, True, PP_ALIGN.CENTER)

    # 3 — current industry offerings, with the distinction between user/admin views.
    s = base(prs, 3, "02 / Existing solutions", "Platforms already help users")
    txt(s, "IN-CALL VIEW", 4.63, 1.59, 3.72, 0.34, 17, CYAN, True)
    txt(s, "ADMIN VIEW", 8.65, 1.59, 3.92, 0.34, 17, CYAN, True)
    rows = [
        ("Google Meet", "CPU · network · actions", "Meet Quality Tool", "google_meet.png"),
        ("Microsoft Teams", "Call health · 15 s", "CQD · Real-Time Analytics", "microsoft_teams.png"),
        ("Zoom", "Statistics window", "Zoom Dashboard", "zoom_logo.png"),
        ("Webex", "Not reviewed", "Control Hub · ThousandEyes", "webex.png"),
    ]
    for i, (platform, user, admin, image_name) in enumerate(rows):
        y = 1.98 + i * 1.28
        rect(s, 0.59, y, 12.13, 1.16, PANEL if i % 2 == 0 else PANEL2, True)
        rect(s, 0.76, y + 0.13, 1.36, 0.90, "E8F1F7", True)
        add_image_contain(s, LOGOS / image_name, 0.87, y + 0.20, 1.14, 0.75)
        txt(s, platform, 2.35, y + 0.27, 2.09, 0.61, 20, WHITE, True)
        txt(s, user, 4.62, y + 0.25, 3.85, 0.65, 18, WHITE)
        txt(s, admin, 8.65, y + 0.25, 3.80, 0.65, 18, MUTED)

    # 4 — concise gap statement.
    s = base(prs, 4, "02 / Existing solutions", "Three gaps remain")
    gaps = [
        (0.60, "One app at a time", "Each view stays inside its own app.", CYAN),
        (4.76, "Different views", "Numbers and hints vary by platform.", AMBER),
        (8.92, "Unverified hints", "Cause and recovery are not independently checked.", GREEN),
    ]
    for x, title, body, accent in gaps:
        rect(s, x, 1.65, 3.81, 5.27, PANEL, True)
        rect(s, x, 1.65, 3.81, 0.09, accent)
        txt(s, title, x + 0.26, 1.99, 3.28, 0.65, 22, WHITE, True, PP_ALIGN.CENTER)
        txt(s, body, x + 0.32, 5.29, 3.17, 1.24, 18.6, WHITE, align=PP_ALIGN.CENTER)
    # Three compact illustrations sit between each title and explanation.
    for i in range(3):
        x = 1.06 + i * 0.76
        rect(s, x, 3.20, 0.62, 1.06, BLUE_PANEL, True, CYAN)
        circle(s, x + 0.21, 3.58, 0.20, CYAN)
    for j, (height, accent) in enumerate([(0.82, CYAN), (1.45, AMBER), (1.07, GREEN)]):
        rect(s, 5.36 + j * 0.79, 4.48 - height, 0.49, height, accent, True)
    circle(s, 10.10, 3.04, 1.48, PURPLE_PANEL)
    txt(s, "?", 10.10, 3.09, 1.48, 1.35, 57, GREEN, True, PP_ALIGN.CENTER)

    # The two measurements cover different scopes; each compares only to the update budget.
    s = base(prs, 5, "03 / Opportunity", "Measured timing vs one-second updates")
    rect(s, 0.60, 1.67, 5.86, 2.78, TEAL_PANEL, True)
    txt(s, "36 ms", 0.92, 2.02, 5.22, 0.89, 48, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "P95 · LAB", 0.92, 3.00, 5.22, 0.41, 20, CYAN, True, PP_ALIGN.CENTER)
    txt(s, "Full tick: packets + 4 models + diagnosis", 0.91, 3.59, 5.24, 0.49,
        18.2, WHITE, align=PP_ALIGN.CENTER)
    rect(s, 6.75, 1.67, 5.96, 2.78, AMBER_PANEL, True)
    txt(s, "126 ms", 7.07, 2.02, 5.32, 0.89, 48, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "P95 · REAL CALL", 7.07, 3.00, 5.32, 0.41, 20, AMBER, True, PP_ALIGN.CENTER)
    txt(s, "Model inference on battery power", 7.06, 3.59, 5.34, 0.49,
        18.2, WHITE, align=PP_ALIGN.CENTER)
    txt(s, "↓", 2.95, 4.56, 1.17, 0.57, 29, CYAN, True, PP_ALIGN.CENTER)
    txt(s, "↓", 9.30, 4.56, 1.17, 0.57, 29, AMBER, True, PP_ALIGN.CENTER)
    rect(s, 0.60, 5.12, 12.11, 1.03, PANEL2, True)
    txt(s, "1,000 ms  ·  update interval", 0.93, 5.31, 11.44, 0.63,
        32, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "Timing looks feasible. Real-call accuracy remains hard.",
        0.63, 6.51, 12.05, 0.49, 22, CYAN, True, PP_ALIGN.CENTER)

    # 6 — five contributions, explicit implementation status.
    s = base(prs, 6, "04 / Our contribution", "MCQM connects five capabilities")
    rect(s, 0.60, 1.65, 4.45, 5.31, BLUE_PANEL, True)
    for x1, y1, x2, y2 in [(2.82, 3.40, 1.36, 2.49), (2.82, 3.40, 4.18, 2.48),
                            (2.82, 3.40, 1.45, 4.02), (2.82, 3.40, 4.08, 4.03)]:
        line(s, x1, y1, x2, y2, CYAN, 2.0)
    circle(s, 2.37, 2.95, 0.90, CYAN)
    for x, y, c in [(1.19, 2.31, AMBER), (3.95, 2.31, GREEN),
                     (1.29, 3.88, GREEN), (3.83, 3.88, AMBER)]:
        circle(s, x, y, 0.34, c)
    txt(s, "MCQM", 0.90, 4.79, 3.85, 0.71, 38, WHITE, True, PP_ALIGN.CENTER)
    txt(s, "Multi-layer Call Quality Monitor", 0.78, 5.55, 4.08, 0.37,
        14.7, MUTED, align=PP_ALIGN.CENTER)
    txt(s, "DESIGNED TO ADD", 0.86, 6.24, 3.93, 0.34, 17, CYAN, True, PP_ALIGN.CENTER)
    line(s, 5.06, 4.30, 5.53, 4.30, CYAN, 2.0)
    line(s, 5.53, 2.16, 5.53, 6.47, CYAN, 2.0)
    items = [
        ("01", "Real time", "Every second", CYAN),
        ("02", "Real-world accuracy", "Windows calls + retraining", AMBER),
        ("03", "Cause diagnosis", "Network vs device CPU", GREEN),
        ("04", "Action + recovery", "Guidance, then verification", CYAN),
        ("05", "Dashboard + widget", "PiP beside the call", AMBER),
    ]
    for i, (n, title, detail, accent) in enumerate(items):
        y = 1.68 + i * 1.07
        line(s, 5.53, y + 0.46, 5.94, y + 0.46, CYAN, 1.8)
        rect(s, 5.93, y, 6.78, 0.92, PANEL if i % 2 == 0 else PANEL2, True)
        circle(s, 6.13, y + 0.20, 0.50, accent, n, NAVY, 12)
        txt(s, title, 6.81, y + 0.12, 3.11, 0.37, 21, WHITE, True)
        txt(s, detail, 6.81, y + 0.48, 5.56, 0.28, 16.8, MUTED)

    # 7 — architecture plus near-term plan.
    s = base(prs, 7, "05 / System and plan", "From packets to a useful decision")
    for i, (label, detail) in enumerate([
        ("Capture", "own traffic"), ("Estimate", "1-second quality"),
        ("Diagnose", "packets + CPU"), ("Advise + verify", "action + recovery"),
    ]):
        x = 0.60 + i * 3.10
        rect(s, x, 1.67, 2.83, 1.46, PANEL2, True)
        txt(s, label, x + 0.17, 1.91, 2.49, 0.43, 21, WHITE, True, PP_ALIGN.CENTER)
        txt(s, detail, x + 0.17, 2.46, 2.49, 0.37, 16.5, MUTED, align=PP_ALIGN.CENTER)
        if i < 3:
            txt(s, "→", x + 2.84, 2.16, 0.25, 0.45, 21, CYAN, True, PP_ALIGN.CENTER)
    txt(s, "NEXT: COLLECT REAL CALLS", 0.63, 3.45, 10.50, 0.45, 21, CYAN, True)
    for i, (label, count, logo) in enumerate([
        ("Google Meet", "FIRST", "google_meet.png"),
        ("Teams · Chrome", "NEXT", "microsoft_teams.png"),
    ]):
        x = 1.24 + i * 5.60
        rect(s, x, 3.99, 5.03, 2.30, PANEL, True)
        rect(s, x + 0.21, 4.20, 1.12, 0.98, "E8F1F7", True)
        add_image_contain(s, LOGOS / logo, x + 0.31, 4.30, 0.92, 0.76)
        txt(s, label, x + 1.51, 4.38, 3.18, 0.59, 20, WHITE, True)
        txt(s, count, x + 0.25, 5.30, 2.56, 0.71, 30, CYAN, True)
        txt(s, "COLLECT", x + 2.43, 5.51, 1.35, 0.39, 16, MUTED, True)
    txt(s, "COLLECTION ORDER: MEET FIRST  →  TEAMS THROUGH CHROME", 0.63, 6.62,
        12.10, 0.42, 18, GREEN, True, PP_ALIGN.CENTER)

    # 8 — every pilot is labelled as a single call.
    s = base(prs, 8, "05 / Pilot evidence", "Three pilots. One call each.")
    x1, x2, x3 = 0.60, 4.76, 8.92
    for x, accent in [(x1, CYAN), (x2, AMBER), (x3, GREEN)]:
        rect(s, x, 1.67, 3.81, 5.30, PANEL, True)
        rect(s, x, 1.67, 3.81, 0.09, accent)
    txt(s, "9.09", x1 + 0.26, 2.08, 3.28, 0.81, 43, CYAN, True)
    txt(s, "FPS ERROR", x1 + 0.29, 2.94, 3.25, 0.37, 19, WHITE, True)
    txt(s, "Original model on a\nreal Windows Meet call", x1 + 0.29, 3.43, 3.25, 0.78, 18.2, MUTED)
    txt(s, "Repeated", x2 + 0.26, 2.08, 3.28, 0.81, 31, AMBER, True)
    txt(s, "FREEZES", x2 + 0.29, 2.94, 3.25, 0.37, 19, WHITE, True)
    txt(s, "Two CPU cores; packets\nlooked normal", x2 + 0.29, 3.43, 3.25, 0.78, 18.2, MUTED)
    txt(s, "~1.3%", x3 + 0.26, 2.08, 3.28, 0.81, 43, GREEN, True)
    txt(s, "MONITOR CPU", x3 + 0.29, 2.94, 3.25, 0.37, 19, WHITE, True)
    txt(s, "Monitor on/off: no call\nmetric change observed", x3 + 0.29, 3.43, 3.25, 0.78, 18.2, MUTED)
    # Minimal explanatory images below each pilot statement.
    line(s, 1.08, 6.37, 3.96, 6.37, LINE, 1.5)
    rect(s, 1.32, 5.80, 0.67, 0.57, BLUE_PANEL, True)
    rect(s, 2.71, 4.77, 0.67, 1.60, CYAN, True)
    txt(s, "1.33", 1.07, 6.50, 1.18, 0.31, 17, MUTED, True, PP_ALIGN.CENTER)
    txt(s, "9.09", 2.47, 6.50, 1.18, 0.31, 17, CYAN, True, PP_ALIGN.CENTER)
    rect(s, 5.34, 4.83, 2.63, 1.54, BLUE_PANEL, True, AMBER)
    rect(s, 5.54, 5.02, 2.22, 0.96, PANEL2, True)
    txt(s, "Ⅱ", 5.54, 5.01, 2.22, 0.96, 41, AMBER, True, PP_ALIGN.CENTER)
    line(s, 5.60, 6.56, 7.72, 6.56, AMBER, 2.5)
    rect(s, 9.98, 5.02, 1.67, 1.39, BLUE_PANEL, True, GREEN)
    txt(s, "✓", 9.98, 5.13, 1.67, 1.11, 46, GREEN, True, PP_ALIGN.CENTER)

    # 9 — measure exactly what the experiment can establish.
    s = base(prs, 9, "06 / Evaluation", "Four questions for evaluation")
    questions = [
        ("Accurate?", "Error before vs after retraining"),
        ("Right cause?", "Precision + recall, with vs without OS data"),
        ("Recovered?", "Detection delay + false recovery rate"),
        ("Light enough?", "CPU + call quality, monitor on vs off"),
    ]
    for i, (q, measure) in enumerate(questions):
        x = 0.60 if i % 2 == 0 else 6.75
        y = 1.67 if i < 2 else 3.58
        rect(s, x, y, 5.91, 1.72, PANEL if i % 2 == 0 else PANEL2, True)
        txt(s, q, x + 0.27, y + 0.28, 5.37, 0.43, 23, CYAN, True)
        txt(s, measure, x + 0.27, y + 0.86, 5.37, 0.58, 18.3, WHITE)
    rect(s, 0.60, 5.66, 12.06, 1.24, PANEL2, True)
    txt(s, "CONTROLLED: LOSS · BANDWIDTH · CPU", 0.88, 5.84, 11.45, 0.44,
        21, AMBER, True, PP_ALIGN.CENTER)
    txt(s, "Labels = injected conditions  ·  We test recovery detection, not advice efficacy", 0.89, 6.40,
        11.43, 0.33, 17.5, WHITE, align=PP_ALIGN.CENTER)

    # 11 — a proposed final-demo sequence, explicitly future tense.
    s = base(prs, 11, "07 / Final demonstration", "Planned final demo")
    steps = [
        ("1", "Normal call", "Live quality estimate", CYAN),
        ("2", "Inject problem", "Network loss or CPU limit", AMBER),
        ("3", "Explain + advise", "Likely cause, confidence, action", GOOGLE_BLUE),
        ("4", "Check recovery", "Problem removed; status confirmed", GREEN),
    ]
    for i, (number, title, detail, accent) in enumerate(steps):
        y = 1.72 + i * 1.20
        circle(s, 0.92, y + 0.15, 0.62, accent, number, WHITE, 16)
        txt(s, title, 1.86, y + 0.05, 4.25, 0.40, 21, WHITE, True)
        txt(s, detail, 1.86, y + 0.49, 4.65, 0.32, 16, MUTED)
        if i < 3:
            rect(s, 1.22, y + 0.80, 0.025, 0.35, LINE)
    rect(s, 7.10, 1.82, 5.15, 3.95, PANEL2, True)
    txt(s, "WHAT WE WILL REPORT", 7.48, 2.18, 4.4, 0.36, 15, CYAN, True)
    for j, (label, color) in enumerate([
        ("Estimation error", GOOGLE_BLUE), ("Cause diagnosis", GOOGLE_RED),
        ("Recovery detection", GREEN), ("Monitoring overhead", AMBER),
    ]):
        y = 2.88 + j * 0.62
        rect(s, 7.49, y + 0.10, 0.14, 0.14, color, True)
        txt(s, label, 7.83, y, 3.95, 0.36, 18, WHITE)
    txt(s, "These are goals, not results yet.", 7.49, 5.21, 4.25, 0.33, 15, MUTED)

    # 12 — conclusion: direct statement of the study and its limits.
    s = base(prs, 12, "08 / Conclusion", "Measure what packet-only monitoring can really do")
    txt(s, "vcaml showed that encrypted packet sizes and timing can estimate call quality.",
        0.86, 1.72, 10.9, 0.86, 25, WHITE, True)
    txt(s, "MCQM builds on that idea to test quality, likely cause, and recovery from outside the app.",
        0.86, 2.92, 10.9, 0.94, 24, WHITE)
    rect(s, 0.86, 4.22, 11.45, 0.02, LINE)
    txt(s, "Our contribution is measured verification, including where the method fails.",
        0.86, 4.58, 10.9, 0.70, 21, CYAN, True)
    txt(s, "We have tested video calls only. Other encrypted services remain a direction, not a result.",
        0.86, 5.55, 10.9, 0.63, 17, MUTED)
    txt(s, "Thank you.  Questions?", 0.86, 6.44, 10.9, 0.40, 19, GOOGLE_BLUE, True)

    # Preserve the user's full checked script as editable PowerPoint speaker notes.
    for i, slide in enumerate(prs.slides, 1):
        note = slide.notes_slide.notes_text_frame
        note.text = notes_for(i)
        if i == 3:
            note.text += ("\n\nIllustrative visual, not a captured packet. Say: "
                          "'Before encryption, an encoded video frame contains meaningful data. "
                          "After encryption, its payload appears as opaque bytes. "
                          "We do not decrypt it; we use only packet size and timing.' "
                          "The actual codec and bytes vary by call.")
        if i in (4, 5):
            note.text += "\n\nProduct descriptions: official sources listed in SCRIPT_ChatGPT.md (checked 2026-10-25)."
        if i == 6:
            note.text += ("\n\nThe 36 ms number measures our full in-lab tick; 126 ms is model inference "
                          "during one battery-powered real call. They are different scopes and conditions. "
                          "The 1,000 ms figure is the update interval, not a measured end-to-end delay. "
                          "The vcaml paper does not report a directly comparable live runtime.")
        if i == 11:
            note.text += "\n\nNext steps on the slide are planned work, not completed results."

    prs.save(OUT)
    print(f"Saved {OUT} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    build()

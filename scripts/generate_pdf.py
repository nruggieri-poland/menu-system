"""
generate_pdf.py
Generates printable monthly menu calendar PDFs from the JSON data files, in
the newsletter layout used by the district's previous Nutrislice PDFs:
a header banner, a left info sidebar (director contact, "what makes a meal",
a la carte options, fruit/veg choices, prices, USDA notice), and the Mon-Fri
grid on the right.

Sidebar copy comes from menu_content.py — edit that file when prices or
option lists change. Banner images are optional; see menu_content.py's
docstring for the expected file paths.

Output: site/pdfs/{year}-{month:02d}-{menutype}-{school}.pdf
"""

import calendar
import json
from datetime import date, datetime
from pathlib import Path

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from menu_content import get_content, DIRECTOR, USDA_NOTICE

# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------
NAVY        = colors.HexColor("#1a3e9c")
INK         = colors.HexColor("#222222")
MUTED       = colors.HexColor("#555555")
WHITE       = colors.white
BORDER      = colors.HexColor("#c9d2e0")
GRID_HEAD   = colors.HexColor("#1a3e9c")

BOX_BLUE    = colors.HexColor("#dbe9fb")
BOX_PINK    = colors.HexColor("#fbdbdb")
BOX_TAN     = colors.HexColor("#fdf1cf")
BOX_PURPLE  = colors.HexColor("#e3ddf5")
HEAD_BLUE   = colors.HexColor("#1a3e9c")
HEAD_RED    = colors.HexColor("#a33333")

# ---------------------------------------------------------------------------
# Layout constants  (landscape letter = 11 × 8.5 in)
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = landscape(letter)
MARGIN      = 0.4 * inch

HEADER_H    = 1.15 * inch
SIDEBAR_W   = 2.55 * inch
GAP         = 0.16 * inch

GRID_X      = MARGIN + SIDEBAR_W + GAP
GRID_TOP    = PAGE_H - MARGIN - HEADER_H
GRID_BOT    = MARGIN
GRID_H      = GRID_TOP - GRID_BOT
GRID_W      = PAGE_W - MARGIN - GRID_X

DAYS        = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
NUM_COLS    = 5
COL_W       = GRID_W / NUM_COLS

DATA_DIR    = Path(__file__).parent.parent / "data"
ASSETS_DIR  = Path(__file__).parent / "assets"
# PDFs live under site/ so GitHub Pages actually publishes them (site/ is the
# only path uploaded by the Pages deploy workflow).
PDF_DIR     = Path(__file__).parent.parent / "site" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_rollup(school: str, menutype: str) -> dict | None:
    path = DATA_DIR / f"{menutype}-{school}.json"
    if not path.exists():
        print(f"  ⚠ Missing rollup file: {path.name}")
        return None
    with open(path) as f:
        return json.load(f)


def build_week_grid(data: dict, year: int, month: int) -> list[list]:
    """
    Returns a list of weeks; each week is a list of 5 slots (Mon–Fri).
    Each slot is either None or a list of item strings.
    """
    items_by_date: dict[str, list[str]] = {}
    for day in data.get("days", []):
        items_by_date[day["date"]] = day["items"]

    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])

    week_start = first - __import__('datetime').timedelta(days=first.weekday())

    weeks = []
    current = week_start
    while current <= last:
        week = []
        for i in range(5):
            d = current + __import__('datetime').timedelta(days=i)
            key = d.strftime("%Y-%m-%d")
            if d.month == month:
                week.append((d.day, items_by_date.get(key, [])))
            else:
                week.append((None, []))
        weeks.append(week)
        current += __import__('datetime').timedelta(days=7)

    return weeks


def wrap_text_lines(text: str, max_chars: int) -> list[str]:
    """Simple word-wrap into lines of at most max_chars."""
    words = text.split()
    lines, current = [], ""
    for w in words:
        if current and len(current) + 1 + len(w) > max_chars:
            lines.append(current)
            current = w
        else:
            current = (current + " " + w).strip() if current else w
    if current:
        lines.append(current)
    return lines


def load_image(path: Path) -> ImageReader | None:
    if not path.exists():
        return None
    try:
        return ImageReader(str(path))
    except Exception as e:
        print(f"  ⚠ Could not load image {path.name}: {e}")
        return None


# ---------------------------------------------------------------------------
# Header banner
# ---------------------------------------------------------------------------

def draw_header(c: canvas.Canvas, school: str, menutype: str, year: int, month: int,
                 banner_title: str):
    top = PAGE_H - MARGIN
    left = MARGIN

    # School name / meal type / month
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(left, top - 16, banner_title)

    c.setFont("Helvetica-Bold", 22)
    c.drawString(left, top - 38, f"{menutype.upper()} - {MONTH_NAMES[month].upper()} {year}")

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#c00000"))
    subject = "MENUS SUBJECT TO CHANGE"
    c.drawString(left, top - 53, subject)
    text_w = c.stringWidth(subject, "Helvetica-Bold", 10)
    c.setLineWidth(0.75)
    c.line(left, top - 55, left + text_w, top - 55)

    # Banner photo strip (optional), centered between the title block and the
    # director info block on the right.
    banner_img = load_image(ASSETS_DIR / f"banner-{school}.jpg") or load_image(ASSETS_DIR / f"banner-{school}.png")
    photo_x = left + 2.9 * inch
    photo_w = PAGE_W - MARGIN - 1.9 * inch - photo_x
    photo_h = 0.62 * inch
    photo_y = top - HEADER_H + (HEADER_H - photo_h) / 2 - 0.05 * inch
    if banner_img is not None and photo_w > 0:
        try:
            c.saveState()
            c.rect(photo_x, photo_y, photo_w, photo_h, stroke=0, fill=0)
            c.drawImage(banner_img, photo_x, photo_y, width=photo_w, height=photo_h,
                        preserveAspectRatio=True, anchor='c', mask='auto')
            c.restoreState()
        except Exception as e:
            print(f"  ⚠ Could not draw banner image: {e}")

    # Director contact block (top-right)
    dx = PAGE_W - MARGIN
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(INK)
    c.drawRightString(dx, top - 10, "Food Service Director:")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(dx, top - 20, DIRECTOR["name"])
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawRightString(dx, top - 29, DIRECTOR["email"])
    c.drawRightString(dx, top - 38, DIRECTOR["phone"])

    logo_img = load_image(ASSETS_DIR / "logo-nutrition-group.png")
    if logo_img is not None:
        try:
            logo_w, logo_h = 0.55 * inch, 0.55 * inch
            c.drawImage(logo_img, dx - logo_w, top - 38 - logo_h, width=logo_w, height=logo_h,
                        preserveAspectRatio=True, anchor='c', mask='auto')
        except Exception as e:
            print(f"  ⚠ Could not draw logo: {e}")

    # Divider under the whole header band
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(MARGIN, top - HEADER_H, PAGE_W - MARGIN, top - HEADER_H)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def wrap_box_lines(w: float, heading: str, lines: list[str], font_size: float,
                    pad: float) -> tuple[list[str], list[str]]:
    max_chars = max(8, int((w - 2 * pad) / (font_size * 0.52)))
    heading_lines = wrap_text_lines(heading, max_chars) or [heading]
    wrapped: list[str] = []
    for item in lines:
        wrapped.extend(wrap_text_lines(item, max_chars) or [""])
    return heading_lines, wrapped


def box_height(w: float, heading: str, lines: list[str], font_size: float,
                heading_size: float, pad: float) -> float:
    heading_lines, wrapped = wrap_box_lines(w, heading, lines, font_size, pad)
    line_h = font_size + 2.6
    return pad + len(heading_lines) * (heading_size + 2) + 4 + len(wrapped) * line_h + pad


def draw_box(c: canvas.Canvas, x: float, y_top: float, w: float, bg, heading: str,
             heading_color, lines: list[str], font_size: float,
             heading_size: float, pad: float = 0.09 * inch) -> float:
    """Draws a rounded info box starting at y_top, returns the y of its bottom edge."""
    heading_lines, wrapped = wrap_box_lines(w, heading, lines, font_size, pad)
    line_h = font_size + 2.6
    content_h = box_height(w, heading, lines, font_size, heading_size, pad)
    y_bot = y_top - content_h

    c.setFillColor(bg)
    c.roundRect(x, y_bot, w, content_h, radius=4, fill=1, stroke=0)

    ty = y_top - pad - heading_size
    c.setFont("Helvetica-BoldOblique", heading_size)
    c.setFillColor(heading_color)
    for hl in heading_lines:
        c.drawString(x + pad, ty, hl)
        ty -= heading_size + 2

    ty -= 2
    c.setFont("Helvetica", font_size)
    c.setFillColor(INK)
    for line in wrapped:
        ty -= line_h
        c.drawString(x + pad, ty + (line_h - font_size), line)

    return y_bot


SIDEBAR_GAP = 0.09 * inch
SIDEBAR_PAD = 0.09 * inch


def sidebar_content_height(content: dict, font_size: float, heading_size: float) -> float:
    w = SIDEBAR_W
    h = box_height(w, "What makes a meal?", content["what_makes_a_meal"], font_size, heading_size, SIDEBAR_PAD)
    h += SIDEBAR_GAP
    h += box_height(w, content["options_heading"], content["options"], font_size, heading_size, SIDEBAR_PAD)
    h += SIDEBAR_GAP
    h += box_height(w, "fruit and vegetable choices may include:", content["fruit_veg_choices"],
                     font_size, heading_size, SIDEBAR_PAD)
    h += SIDEBAR_GAP
    h += 22  # milk choices line
    price_lines = [f"{label}: {amount}" for label, amount in content["prices"]]
    h += box_height(w, "Prices", price_lines, font_size + 0.4, heading_size + 0.5, SIDEBAR_PAD)
    h += SIDEBAR_GAP
    h += 20  # USDA notice
    if content.get("placeholder"):
        h += 20
    return h


def fit_sidebar_font_size(content: dict) -> float:
    """Shrinks the sidebar font until everything fits between the header and
    the bottom margin — a long a la carte options list (PSHS has ~12 items)
    otherwise runs the boxes off the bottom of the page."""
    available = GRID_TOP - GRID_BOT
    for font_size in (7.2, 6.8, 6.4, 6.0, 5.6, 5.2, 4.8):
        heading_size = font_size + 1.3
        if sidebar_content_height(content, font_size, heading_size) <= available:
            return font_size
    return 4.8


def draw_sidebar(c: canvas.Canvas, school: str, menutype: str):
    content = get_content(school, menutype)
    x = MARGIN
    w = SIDEBAR_W
    y = GRID_TOP
    gap = SIDEBAR_GAP

    font_size = fit_sidebar_font_size(content)
    heading_size = font_size + 1.3

    y = draw_box(c, x, y, w, BOX_BLUE, "What makes a meal?", HEAD_BLUE,
                 content["what_makes_a_meal"], font_size, heading_size) - gap
    y = draw_box(c, x, y, w, BOX_PINK, content["options_heading"], HEAD_RED,
                 content["options"], font_size, heading_size) - gap
    y = draw_box(c, x, y, w, BOX_TAN, f"{menutype.capitalize()} fruit and vegetable choices may include:",
                 HEAD_BLUE, content["fruit_veg_choices"], font_size, heading_size) - gap

    # Milk choices (plain line, not boxed)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(INK)
    c.drawString(x, y - 10, "Daily Milk Choices")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED)
    c.drawString(x + c.stringWidth("Daily Milk Choices  ", "Helvetica-Bold", 8), y - 10, content["milk_choices"])
    y -= 22

    price_lines = [f"{label}: {amount}" for label, amount in content["prices"]]
    y = draw_box(c, x, y, w, BOX_PURPLE, f"{menutype.capitalize()} Prices", HEAD_BLUE,
                 price_lines, font_size + 0.4, heading_size + 0.5) - gap

    if content.get("placeholder"):
        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(colors.HexColor("#a33333"))
        for l in wrap_text_lines(
            "Pricing/options for this menu are placeholders — update menu_content.py.", 60
        ):
            y -= 8
            c.drawString(x, y, l)
        y -= 4

    # USDA notice, bottom of sidebar
    c.setFont("Helvetica", 6.5)
    c.setFillColor(MUTED)
    usda_lines = wrap_text_lines(USDA_NOTICE, 62)
    uy = GRID_BOT + len(usda_lines) * 8
    for line in usda_lines:
        c.drawString(x, uy, line)
        uy -= 8


# ---------------------------------------------------------------------------
# Grid (Mon–Fri calendar)
# ---------------------------------------------------------------------------

def draw_grid(c: canvas.Canvas, data: dict, year: int, month: int):
    weeks = build_week_grid(data, year, month)
    num_rows = len(weeks)
    row_h = GRID_H / num_rows
    subhead_h = 0.24 * inch
    grid_top = GRID_TOP - subhead_h
    grid_h = grid_top - GRID_BOT
    row_h = grid_h / num_rows

    # Day-name header row
    c.setFillColor(GRID_HEAD)
    c.rect(GRID_X, GRID_TOP - subhead_h, GRID_W, subhead_h, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    for col, day_name in enumerate(DAYS):
        cx = GRID_X + col * COL_W + COL_W / 2
        c.drawCentredString(cx, GRID_TOP - subhead_h + 0.07 * inch, day_name)

    for row_idx, week in enumerate(weeks):
        row_top = grid_top - row_idx * row_h
        row_bot = row_top - row_h

        for col_idx, (day_num, items) in enumerate(week):
            cell_x = GRID_X + col_idx * COL_W
            if day_num is None:
                c.setFillColor(colors.HexColor("#f2f4f8"))
                c.rect(cell_x, row_bot, COL_W, row_h, fill=1, stroke=0)
                continue

            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(cell_x + 5, row_top - 11, str(day_num))

            if items:
                font_size = 6.6
                c.setFont("Helvetica", font_size)
                line_h = font_size + 2
                avail_h = row_h - 16
                max_lines = max(1, int(avail_h / line_h))
                text_y = row_top - 20
                lines_drawn = 0
                for item in items:
                    wrapped = wrap_text_lines(item, int(COL_W / 3.6))
                    for line in wrapped:
                        if lines_drawn >= max_lines:
                            break
                        c.setFillColor(MUTED)
                        c.drawString(cell_x + 5, text_y, line)
                        text_y -= line_h
                        lines_drawn += 1
                    if lines_drawn >= max_lines:
                        break

    # Grid lines
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    for col in range(NUM_COLS + 1):
        x = GRID_X + col * COL_W
        c.line(x, GRID_BOT, x, grid_top)
    for row in range(num_rows + 1):
        y = grid_top - row * row_h
        c.line(GRID_X, y, PAGE_W - MARGIN, y)
    c.setStrokeColor(GRID_HEAD)
    c.setLineWidth(1)
    c.line(GRID_X, GRID_TOP, PAGE_W - MARGIN, GRID_TOP)


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def draw_page(c: canvas.Canvas, data: dict, year: int, month: int,
              school_display: str, menutype: str, school: str):
    content = get_content(school, menutype)
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    draw_header(c, school, menutype, year, month, content["banner_title"])
    draw_sidebar(c, school, menutype)
    draw_grid(c, data, year, month)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_all(year: int, month: int):
    import csv

    csv_path = Path(__file__).parent / "menu-list.csv"
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        school       = row["school"].strip()
        display_name = row["display_name"].strip()
        menutype     = row["menutype"].strip()

        print(f"\n→ PDF: {display_name} / {menutype}")
        data = load_rollup(school, menutype)
        if data is None:
            continue

        out_path = PDF_DIR / f"{year}-{month:02d}-{menutype}-{school}.pdf"
        c = canvas.Canvas(str(out_path), pagesize=landscape(letter))
        draw_page(c, data, year, month, display_name, menutype, school)
        c.showPage()
        c.save()
        print(f"  ✓ {out_path.name}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int, default=datetime.now().year)
    parser.add_argument("--month", type=int, default=datetime.now().month)
    args = parser.parse_args()
    generate_all(args.year, args.month)
    print("\n✅ PDFs generated.")

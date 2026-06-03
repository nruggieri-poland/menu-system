"""
generate_pdf.py
Generates printable monthly menu calendar PDFs from the JSON data files.
Matches the Poland Schools branding: dark navy background, bold white headers.

Output: pdfs/{year}-{month:02d}-{menutype}-{school}.pdf
"""

import json
import calendar
from datetime import datetime, date
from pathlib import Path

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------
NAVY       = colors.HexColor("#0D2A6B")
WHITE      = colors.white
GOLD       = colors.HexColor("#F5A623")
LIGHT_BLUE = colors.HexColor("#E8F0FC")
CELL_BG    = colors.white
HEADER_FG  = colors.white
DAY_HEADER = colors.HexColor("#1A3E9C")

# ---------------------------------------------------------------------------
# Layout constants  (landscape letter = 11 × 8.5 in)
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = landscape(letter)
MARGIN_X = 0.45 * inch
MARGIN_Y = 0.35 * inch

HEADER_H   = 1.05 * inch   # top banner
SUBHEAD_H  = 0.30 * inch   # day-name row
FOOTER_H   = 0.22 * inch

GRID_TOP   = PAGE_H - MARGIN_Y - HEADER_H - SUBHEAD_H
GRID_BOT   = MARGIN_Y + FOOTER_H
GRID_H     = GRID_TOP - GRID_BOT

DAYS        = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
NUM_COLS    = 5
COL_W       = (PAGE_W - 2 * MARGIN_X) / NUM_COLS

DATA_DIR    = Path(__file__).parent.parent / "data"
PDF_DIR     = Path(__file__).parent.parent / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(school: str, menutype: str, year: int, month: int) -> dict | None:
    path = DATA_DIR / f"{year}-{month:02d}-{menutype}-{school}.json"
    if not path.exists():
        print(f"  ⚠ Missing data file: {path.name}")
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

    # Figure out which weeks to show
    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])

    # Start from Monday of the week containing the 1st
    week_start = first - __import__('datetime').timedelta(days=first.weekday())

    weeks = []
    current = week_start
    while current <= last:
        week = []
        for i in range(5):  # Mon–Fri only
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


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_page(c: canvas.Canvas, data: dict, year: int, month: int,
              school_display: str, menutype: str):

    weeks = build_week_grid(data, year, month)
    num_rows = len(weeks)
    row_h = GRID_H / num_rows

    # ── Background ──────────────────────────────────────────────────────────
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ── Top header band ─────────────────────────────────────────────────────
    banner_y = PAGE_H - MARGIN_Y - HEADER_H
    c.setFillColor(NAVY)
    c.rect(MARGIN_X, banner_y, PAGE_W - 2 * MARGIN_X, HEADER_H, fill=1, stroke=0)

    # Menu type (large)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 38)
    label = menutype.upper()
    c.drawCentredString(PAGE_W / 2, banner_y + 0.48 * inch, label)

    # School name (smaller, below)
    c.setFont("Helvetica", 14)
    c.setFillColor(GOLD)
    c.drawCentredString(PAGE_W / 2, banner_y + 0.24 * inch, school_display)

    # Month + Year (right-aligned)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 16)
    month_label = f"{MONTH_NAMES[month].upper()} {year}"
    c.drawRightString(PAGE_W - MARGIN_X - 0.1 * inch,
                      banner_y + 0.52 * inch, month_label)

    # Gold accent line under header
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(MARGIN_X, banner_y, PAGE_W - MARGIN_X, banner_y)

    # ── Day-name subheader ───────────────────────────────────────────────────
    sub_y = banner_y - SUBHEAD_H
    c.setFillColor(DAY_HEADER)
    c.rect(MARGIN_X, sub_y, PAGE_W - 2 * MARGIN_X, SUBHEAD_H, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    for col, day_name in enumerate(DAYS):
        x = MARGIN_X + col * COL_W + COL_W / 2
        c.drawCentredString(x, sub_y + 0.08 * inch, day_name.upper())

    # ── Calendar grid ────────────────────────────────────────────────────────
    for row_idx, week in enumerate(weeks):
        row_top = GRID_TOP - row_idx * row_h
        row_bot = row_top - row_h

        for col_idx, (day_num, items) in enumerate(week):
            cell_x = MARGIN_X + col_idx * COL_W
            cell_y = row_bot

            # Cell background
            bg = CELL_BG if day_num else colors.HexColor("#0A2060")
            c.setFillColor(bg)
            c.roundRect(cell_x + 2, cell_y + 2,
                        COL_W - 4, row_h - 4,
                        radius=4, fill=1, stroke=0)

            if day_num is None:
                continue

            # Date number
            c.setFillColor(NAVY)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(cell_x + 8, row_top - 14, str(day_num))

            # Menu items
            if items:
                item_font_size = 7.5
                c.setFont("Helvetica", item_font_size)
                line_h = item_font_size + 2.2
                # Available height below date number
                avail_h = row_h - 22
                max_lines = int(avail_h / line_h)

                text_y = row_top - 26
                lines_drawn = 0
                for item in items:
                    wrapped = wrap_text_lines(item, int(COL_W / 4.4))
                    for line in wrapped:
                        if lines_drawn >= max_lines:
                            break
                        c.setFillColor(colors.HexColor("#1a1a2e"))
                        c.drawString(cell_x + 8, text_y, line)
                        text_y -= line_h
                        lines_drawn += 1
                    if lines_drawn >= max_lines:
                        break
            else:
                c.setFillColor(colors.HexColor("#aaaaaa"))
                c.setFont("Helvetica-Oblique", 7)
                c.drawString(cell_x + 8, row_top - 26, "No menu")

    # ── Grid lines ───────────────────────────────────────────────────────────
    c.setStrokeColor(colors.HexColor("#3A5AB0"))
    c.setLineWidth(0.5)
    # Vertical
    for col in range(NUM_COLS + 1):
        x = MARGIN_X + col * COL_W
        c.line(x, GRID_BOT, x, GRID_TOP)
    # Horizontal
    for row in range(num_rows + 1):
        y = GRID_TOP - row * row_h
        c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)

    # ── Footer ───────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#aaaacc"))
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN_X, MARGIN_Y,
                 "Menu subject to change  •  Poland Local School District")
    c.drawRightString(PAGE_W - MARGIN_X, MARGIN_Y,
                      f"Generated {datetime.utcnow().strftime('%B %d, %Y')}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_pdfs(year: int, month: int):
    from scripts_helper import load_menu_list  # inline below
    pass


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
        data = load_json(school, menutype, year, month)
        if data is None:
            continue

        out_path = PDF_DIR / f"{year}-{month:02d}-{menutype}-{school}.pdf"
        c = canvas.Canvas(str(out_path), pagesize=landscape(letter))
        draw_page(c, data, year, month, display_name, menutype)
        c.showPage()
        c.save()
        print(f"  ✓ {out_path.name}")


if __name__ == "__main__":
    year  = int(input("Year (YYYY): "))
    month = int(input("Month (1-12): "))
    generate_all(year, month)
    print("\n✅ PDFs generated.")

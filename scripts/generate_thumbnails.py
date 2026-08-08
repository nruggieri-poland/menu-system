"""
generate_thumbnails.py
Builds a preview image for each generated PDF calendar: a large "MONTH
YEAR" banner on top (like a button — the most prominent element) with an
actual preview of the calendar page underneath (~55-60% of the image),
meant for a Finalsite "photo" component that links to the PDF.

Requires poppler (the `pdftoppm` binary) on PATH — installed via
`apt-get install poppler-utils` in CI, or `brew install poppler` locally.

Output: site/pdfs/thumbnails/{same-stem-as-pdf}.png
"""

import csv
from datetime import date
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

ROOT      = Path(__file__).parent.parent
PDF_DIR   = ROOT / "site" / "pdfs"
THUMB_DIR = PDF_DIR / "thumbnails"

CARD_W    = 900
BANNER_H  = 300   # ~42% of the card — the prominent month/year banner
CAL_H     = 440   # ~58% of the card — the calendar preview beneath it

SCHOOL_BLUE = (0, 50, 143)     # #00328f
WHITE       = (255, 255, 255)
LIGHT_BLUE  = (190, 210, 245)
BORDER      = (215, 220, 232)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for base in ("/usr/share/fonts/truetype/dejavu", "/System/Library/Fonts/Supplemental"):
        path = Path(base) / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    arial = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    if Path(arial).exists():
        return ImageFont.truetype(arial, size)
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def centered_text(draw: ImageDraw.ImageDraw, cx: float, cy: float, text: str,
                   font: ImageFont.FreeTypeFont, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]), text, font=font, fill=fill)


def render_calendar_preview(pdf_path: Path) -> Image.Image:
    """Rasterizes PDF page 1 at CARD_W wide, then crops (top-anchored) to
    CAL_H tall — a landscape-letter page is proportionally taller than
    CAL_H at this width, so this keeps the header row + first couple weeks
    (the most informative part) and trims the bottom."""
    pages = convert_from_path(str(pdf_path), first_page=1, last_page=1, size=(CARD_W, None))
    page = pages[0].convert("RGB")
    if page.height > CAL_H:
        page = page.crop((0, 0, CARD_W, CAL_H))
    elif page.height < CAL_H:
        canvas = Image.new("RGB", (CARD_W, CAL_H), WHITE)
        canvas.paste(page, (0, 0))
        page = canvas
    return page


def build_card(pdf_path: Path, month_label: str, menutype: str) -> Image.Image:
    calendar_preview = render_calendar_preview(pdf_path)

    card = Image.new("RGB", (CARD_W, BANNER_H + CAL_H), WHITE)
    draw = ImageDraw.Draw(card)

    draw.rectangle([0, 0, CARD_W, BANNER_H], fill=SCHOOL_BLUE)

    month_font = load_font(72)
    centered_text(draw, CARD_W / 2, BANNER_H * 0.42, month_label, month_font, WHITE)

    sub_font = load_font(24)
    centered_text(draw, CARD_W / 2, BANNER_H * 0.74,
                   f"{menutype.upper()} CALENDAR  •  DOWNLOAD PDF", sub_font, LIGHT_BLUE)

    card.paste(calendar_preview, (0, BANNER_H))

    draw.line([0, BANNER_H, CARD_W, BANNER_H], fill=WHITE, width=2)
    draw.rectangle([0, 0, CARD_W - 1, BANNER_H + CAL_H - 1], outline=BORDER, width=1)
    return card


def load_menu_list() -> list[dict]:
    with open(Path(__file__).parent / "menu-list.csv", newline="") as f:
        return list(csv.DictReader(f))


def generate_all():
    """Builds current-{menutype}-{school}.png and next-...png directly from
    the matching current-/next- PDFs generate_pdf.py writes — there's no
    dated file and no copy step, this IS the only preview card for that
    label, matching the PDF side one-to-one."""
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today()
    this_month = (today.year, today.month)
    next_month = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    labeled_months = {"current": this_month, "next": next_month}

    pdfs = sorted(p for p in PDF_DIR.glob("*.pdf") if p.stem.split("-", 1)[0] in labeled_months)
    if not pdfs:
        print("  No PDFs found — run generate_pdf.py first.")
        return

    count = 0
    for pdf_path in pdfs:
        label, menutype, school = pdf_path.stem.split("-", 2)
        year, month = labeled_months[label]
        month_label = f"{MONTH_NAMES[month].upper()} {year}"

        card = build_card(pdf_path, month_label, menutype)
        out_path = THUMB_DIR / f"{pdf_path.stem}.png"
        card.save(out_path, "PNG")
        count += 1
        print(f"  ✓ {out_path.name}")

    print(f"  Generated {count} preview card(s) → site/pdfs/thumbnails/")


if __name__ == "__main__":
    generate_all()
    print("✅ Preview cards generated.")

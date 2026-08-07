"""
generate_thumbnails.py
Rasterizes page 1 of each generated calendar PDF into a PNG preview image
with a "DOWNLOAD" banner overlaid at the bottom, so the image itself reads
as a download call-to-action — meant for a Finalsite "photo" component that
links to the PDF hosted in this repo.

Requires poppler (the `pdftoppm` binary) on PATH — installed via
`apt-get install poppler-utils` in CI, or `brew install poppler` locally.

Output: site/pdfs/thumbnails/{same-stem-as-pdf}.png
"""

from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

PDF_DIR   = Path(__file__).parent.parent / "site" / "pdfs"
THUMB_DIR = PDF_DIR / "thumbnails"

THUMB_WIDTH = 900  # px — sharp enough for a clickable card, small enough to keep the repo light

SCHOOL_BLUE = (0, 50, 143)   # #00328f
WHITE       = (255, 255, 255)
BANNER_TEXT = "DOWNLOAD"
BANNER_H    = 64  # px


def load_banner_font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Ubuntu (CI)
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",     # macOS
        "/Library/Fonts/Arial Bold.ttf",                          # macOS (older)
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def add_download_banner(page: Image.Image) -> Image.Image:
    page = page.convert("RGB")
    w, h = page.size
    canvas = Image.new("RGB", (w, h + BANNER_H), WHITE)
    canvas.paste(page, (0, 0))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, h, w, h + BANNER_H], fill=SCHOOL_BLUE)

    font = load_banner_font(int(BANNER_H * 0.5))
    bbox = draw.textbbox((0, 0), BANNER_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = (w - text_w) / 2 - bbox[0]
    ty = h + (BANNER_H - text_h) / 2 - bbox[1]
    draw.text((tx, ty), BANNER_TEXT, font=font, fill=WHITE)

    return canvas


def generate_all():
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("  No PDFs found — run generate_pdf.py first.")
        return

    count = 0
    for pdf_path in pdfs:
        out_path = THUMB_DIR / f"{pdf_path.stem}.png"
        pages = convert_from_path(str(pdf_path), first_page=1, last_page=1, size=(THUMB_WIDTH, None))
        add_download_banner(pages[0]).save(out_path, "PNG")
        count += 1
        print(f"  ✓ {out_path.name}")

    print(f"  Generated {count} thumbnail(s) → site/pdfs/thumbnails/")


if __name__ == "__main__":
    generate_all()
    print("✅ Thumbnails generated.")

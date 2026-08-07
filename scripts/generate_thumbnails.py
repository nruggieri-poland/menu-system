"""
generate_thumbnails.py
Rasterizes page 1 of each generated calendar PDF into a PNG preview image, so
the PDF can be presented on Finalsite as a clickable image ("click the
calendar image to download the PDF") instead of an inert file link.

Requires poppler (the `pdftoppm` binary) on PATH — installed via
`apt-get install poppler-utils` in CI, or `brew install poppler` locally.

Output: site/pdfs/thumbnails/{same-stem-as-pdf}.png
"""

from pathlib import Path

from pdf2image import convert_from_path

PDF_DIR   = Path(__file__).parent.parent / "site" / "pdfs"
THUMB_DIR = PDF_DIR / "thumbnails"

THUMB_WIDTH = 900  # px — sharp enough for a clickable card, small enough to keep the repo light


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
        pages[0].save(out_path, "PNG")
        count += 1
        print(f"  ✓ {out_path.name}")

    print(f"  Generated {count} thumbnail(s) → site/pdfs/thumbnails/")


if __name__ == "__main__":
    generate_all()
    print("✅ Thumbnails generated.")

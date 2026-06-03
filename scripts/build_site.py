"""
build_site.py
Copies data JSON files into the site/ directory so the static TV display
pages can fetch them with a relative path (no CORS issues on GitHub Pages).
Also regenerates the per-school/per-mealtype index HTML stubs if needed.
"""

import json
import shutil
import csv
from pathlib import Path
from datetime import datetime

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / "data"
SITE   = ROOT / "site"


def copy_data():
    dest = SITE / "data"
    dest.mkdir(exist_ok=True)
    count = 0
    for src in DATA.glob("*.json"):
        shutil.copy2(src, dest / src.name)
        count += 1
    print(f"  Copied {count} JSON files → site/data/")


def build_manifest():
    """Write site/data/manifest.json listing all available data files."""
    files = sorted(p.name for p in (SITE / "data").glob("*.json"))
    manifest = {"files": files, "updated": datetime.utcnow().isoformat() + "Z"}
    out = SITE / "data" / "manifest.json"
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest: {len(files)} entries")


def ensure_tv_pages():
    """Make sure each school/mealtype index.html exists (created once by template)."""
    csv_path = Path(__file__).parent / "menu-list.csv"
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            school   = row["school"].strip()
            menutype = row["menutype"].strip()
            page_dir = SITE / school / menutype
            page_dir.mkdir(parents=True, exist_ok=True)
            page = page_dir / "index.html"
            if not page.exists():
                print(f"  ⚠  Missing TV page: {page} — generating stub")
                page.write_text(
                    f'<!DOCTYPE html><html><head>'
                    f'<meta http-equiv="refresh" content="0;url=../../tv.html'
                    f'?school={school}&type={menutype}">'
                    f'</head><body></body></html>'
                )


if __name__ == "__main__":
    copy_data()
    build_manifest()
    ensure_tv_pages()
    print("✅ Site built.")

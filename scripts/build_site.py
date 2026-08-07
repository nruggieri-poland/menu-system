"""
build_site.py
site/ is pure build output (gitignored, regenerated every run) — nothing in
it is hand-edited directly. This script copies the hand-authored static
assets that DO live under version control (assets/) into site/, copies data
JSON into site/ so the static TV display pages can fetch them with a
relative path (no CORS issues on GitHub Pages), and regenerates the
per-school/per-mealtype TV redirect stubs.
"""

import json
import shutil
import csv
from pathlib import Path
from datetime import datetime, timezone

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / "data"
SITE   = ROOT / "site"
ASSETS = ROOT / "assets"


def copy_static_assets():
    """Hand-authored files that live in assets/ (tracked in git) get copied
    straight into site/ (untracked, CI-generated) at the same relative path."""
    if not ASSETS.exists():
        return
    count = 0
    for src in ASSETS.rglob("*"):
        if src.is_file():
            dest = SITE / src.relative_to(ASSETS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            count += 1
    print(f"  Copied {count} static asset(s) from assets/ → site/")


def copy_data():
    dest = SITE / "data"
    if dest.exists():
        shutil.rmtree(dest)  # clear stale files (e.g. old per-month rollups) before copying
    dest.mkdir(parents=True)
    count = 0
    for src in DATA.glob("*.json"):
        shutil.copy2(src, dest / src.name)
        count += 1
    print(f"  Copied {count} JSON files → site/data/")


def build_manifest():
    """Write site/data/manifest.json listing all available data files."""
    files = sorted(p.name for p in (SITE / "data").glob("*.json"))
    manifest = {"files": files, "updated": datetime.now(timezone.utc).isoformat()}
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
    copy_static_assets()
    copy_data()
    build_manifest()
    ensure_tv_pages()
    print("✅ Site built.")

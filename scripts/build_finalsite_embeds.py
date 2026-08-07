"""
build_finalsite_embeds.py
Generates four fully self-contained paste-into-Finalsite embed files, one
per school/menutype feed — everything (CSS, markup, JS) inlined into a
single block with no external <script src>, no third-party library CDNs
(no FullCalendar/PapaParse/moment — accessible semantic HTML/CSS instead),
and no iframe. The only network call at runtime is a fetch() straight to
this repo's data/ JSON on GitHub, so the calendar always shows live data.

Each file is meant to be copy-pasted whole into that school+menutype's
Finalsite "Custom HTML" component.

Output: site/embed/finalsite/{school}-{menutype}.html
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"
WIDGET_JS = SITE / "embed" / "menu-widget.js"
OUT_DIR = SITE / "embed" / "finalsite"


def load_menu_list() -> list[dict]:
    with open(Path(__file__).parent / "menu-list.csv", newline="") as f:
        return list(csv.DictReader(f))


def widget_js_body() -> str:
    """Strip the file's leading /* ... */ doc comment (it contains a literal
    </script> inside a code sample, which would prematurely close an inline
    <script> tag) and return everything from the IIFE onward."""
    text = WIDGET_JS.read_text()
    marker = "(function ()"
    idx = text.index(marker)
    return text[idx:]


def build():
    body = widget_js_body()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for row in load_menu_list():
        school = row["school"].strip()
        menutype = row["menutype"].strip()
        display_name = row["display_name"].strip()

        out = f"""<!-- Poland Schools menu embed — {display_name} {menutype.capitalize()}
     Paste this entire block into the Finalsite Custom HTML component for
     this page. No external script/library dependencies — the only network
     request it makes is to fetch this month's menu JSON from the repo.
     Source: scripts/build_finalsite_embeds.py (do not hand-edit; regenerate
     instead if menu-widget.js changes). -->
<div data-psmenu data-school="{school}" data-menutype="{menutype}" data-display-name="{display_name}"></div>
<script>
{body}
</script>
"""
        out_path = OUT_DIR / f"{school}-{menutype}.html"
        out_path.write_text(out)
        count += 1
        print(f"  ✓ {out_path.relative_to(SITE)}")

    print(f"  Finalsite embed files built: {count}")


if __name__ == "__main__":
    build()
    print("✅ Finalsite embeds generated.")

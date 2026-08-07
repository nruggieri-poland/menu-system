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
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"
WIDGET_JS = ROOT / "assets" / "embed" / "menu-widget.js"
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

        # No HTML markup at all — just the <script> tag. Config is hardcoded
        # as JS values (not HTML attributes), and the script creates its own
        # container via document.currentScript, so there's nothing for a CMS
        # sanitizer to strip except the script tag itself.
        footer = (
            "(function(){"
            "var s=document.currentScript;"
            "var c=document.createElement('div');"
            "s.parentNode.insertBefore(c,s.nextSibling);"
            f"new PSMenuWidget.Widget(c,{{school:{json.dumps(school)},"
            f"menutype:{json.dumps(menutype)},displayName:{json.dumps(display_name)}}}).init();"
            "})();"
        )

        out = f"""<!-- Poland Schools menu embed — {display_name} {menutype.capitalize()}
     Paste this entire block into the Finalsite Custom HTML component for
     this page. No external script/library dependencies, no HTML markup
     needed (the script creates its own container) — the only network
     request it makes is to fetch this month's menu JSON from the repo.
     Source: scripts/build_finalsite_embeds.py (do not hand-edit; regenerate
     instead if menu-widget.js changes). -->
<script>
{body}
{footer}
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

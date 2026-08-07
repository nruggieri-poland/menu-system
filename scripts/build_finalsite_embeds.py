"""
build_finalsite_embeds.py
Generates four fully self-contained paste-into-Finalsite widget files, one
per school/menutype feed — CSS, markup, and JS all hardcoded/inlined into a
single <script> block with no external dependencies (no <script src>, no
third-party library CDN, no iframe). The MENU DATA is never hardcoded: the
only network call at runtime is a fetch() straight to this repo's data/
JSON on GitHub, so the calendar always shows live, current data.

Every class name, id, and data-attribute in each file is namespaced to that
specific school+menutype (e.g. .psmenu-pshs-lunch-head), so any combination
of these four files can be pasted onto the same Finalsite page with zero
risk of CSS or JS collision between them, or with anything else on the
page. Each file creates its own container element automatically — there's
no HTML markup to paste beyond the <script> tag itself.

Each file is meant to be copy-pasted whole into that school+menutype's
Finalsite "Custom HTML" component.

Output: widgets/{school}-{menutype}.html
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIDGET_JS = ROOT / "assets" / "embed" / "menu-widget.js"
OUT_DIR = ROOT / "widgets"

BOOT_MARKER = "\n  // ── Boot"


def load_menu_list() -> list[dict]:
    with open(Path(__file__).parent / "menu-list.csv", newline="") as f:
        return list(csv.DictReader(f))


def engine_body() -> str:
    """The shared widget's helpers, stylesheet, and Widget class — everything
    except the auto-boot scanning logic (bootFromScriptTags/bootFromDataAttr),
    which is irrelevant here since each generated file hardcodes its own
    config and mounts its own container directly. Also strips the leading
    /* ... */ doc comment, which contains a literal </script> inside a code
    sample that would prematurely close an inline <script> tag."""
    text = WIDGET_JS.read_text()
    start = text.index("(function ()")
    end = text.index(BOOT_MARKER)
    return text[start:end]


def namespaced_engine(school: str, menutype: str) -> str:
    """Every class/id/data-attribute in the engine is literally the string
    'psmenu' or 'psmenu-something' — a single global find/replace scopes the
    whole stylesheet and DOM API calls to a namespace unique to this feed."""
    namespace = f"psmenu-{school}-{menutype}"
    return engine_body().replace("psmenu", namespace)


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for row in load_menu_list():
        school = row["school"].strip()
        menutype = row["menutype"].strip()
        display_name = row["display_name"].strip()

        body = namespaced_engine(school, menutype)

        # No HTML markup at all — just the <script> tag. The container is
        # created here, at the point this script executes, via
        # document.currentScript — reliable for an inline synchronous script.
        footer = (
            "\n  var __script = document.currentScript;\n"
            "  var __container = document.createElement('div');\n"
            "  __script.parentNode.insertBefore(__container, __script.nextSibling);\n"
            f"  new Widget(__container, {{\n"
            f"    school: {json.dumps(school)},\n"
            f"    menutype: {json.dumps(menutype)},\n"
            f"    displayName: {json.dumps(display_name)}\n"
            f"  }}).init();\n"
            "})();\n"
        )

        out = f"""<!-- Poland Schools menu widget — {display_name} {menutype.capitalize()}
     Paste this entire block into the Finalsite Custom HTML component for
     this page. No external script/library dependencies, no HTML markup
     needed (the script creates its own container). All CSS/JS in this file
     is namespaced to this specific feed, so it's safe to paste alongside
     any of the other three widget files on the same page. The MENU DATA is
     never hardcoded — the only network request this makes is to fetch the
     current menu JSON from the repo, so it always shows live data.
     Source: scripts/build_finalsite_embeds.py (do not hand-edit; regenerate
     instead if assets/embed/menu-widget.js changes). -->
<script>
{body}
{footer}</script>
"""
        out_path = OUT_DIR / f"{school}-{menutype}.html"
        out_path.write_text(out)
        count += 1
        print(f"  ✓ widgets/{out_path.name}")

    print(f"  Widget files built: {count}")


if __name__ == "__main__":
    build()
    print("✅ Finalsite widgets generated.")

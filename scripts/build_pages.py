"""
build_pages.py
Generates WCAG 2.1 AA accessible, responsive, static HTML for each school/menutype:

  {school}/{menutype}/calendar/index.html   <- default / recommended embed target
      Live copy of the current month's grid calendar (same data as the PDF),
      a real <table> with proper headers/captions, real prev/next links to
      adjacent months (no JS required), and a responsive "stacked" layout on
      narrow screens. Also written per-month at calendar/{year}-{month:02d}.html.

  {school}/{menutype}/week/index.html
      Current week's menu as a simple day-by-day list — an alternate view,
      linked from the calendar page as "List View". Also written per-week at
      week/{YYYY-MM-DD}.html with real prev/next navigation.

  {school}/{menutype}/embed.html
      The current month's calendar as a bare fragment (no <html>/<head>/<body>
      wrapper), for pasting directly into a Finalsite "Custom HTML" component
      if iframes aren't an option there. Re-generated daily, but a pasted copy
      will only reflect data as of the last paste — the iframe route is
      preferred because it always shows live data.

Both view types have no fixed dimensions, no motion, and no client-side data
fetching required — meant to be dropped into an <iframe> on the school
website or Finalsite.

Run after fetch_menus.py (and generate_pdf.py, if PDF links should resolve).
"""

import csv
import html
import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

REPO_SLUG = "nruggieri-poland/menus"
PAGES_BASE = "https://nruggieri-poland.github.io/menus"


# ── Data helpers ──────────────────────────────────────────────────────────

def load_menu_list() -> list[dict]:
    with open(Path(__file__).parent / "menu-list.csv", newline="") as f:
        return list(csv.DictReader(f))


_rollup_cache: dict[tuple[str, str], dict | None] = {}


def load_rollup(school: str, menutype: str) -> dict | None:
    key = (school, menutype)
    if key not in _rollup_cache:
        path = DATA / f"{menutype}-{school}.json"
        _rollup_cache[key] = json.loads(path.read_text()) if path.exists() else None
    return _rollup_cache[key]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def fmt_date(d: date) -> str:
    return d.strftime("%b ") + str(d.day)


def fmt_date_long(d: date) -> str:
    return d.strftime("%A, %B ") + str(d.day)


def fmt_date_full(d: date) -> str:
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


def item_map(school: str, menutype: str) -> dict[str, list[str]]:
    """The whole rollup's days as a single date -> items lookup — the rollup
    holds full history, so no per-month filtering is needed to use it."""
    data = load_rollup(school, menutype)
    if not data:
        return {}
    return {day["date"]: day["items"] for day in data.get("days", [])}


# How far to generate browsable week/month pages, independent of which of
# those months actually have published menu data yet (Nutrislice publishes
# incrementally — most of this range will just show "No menu" until closer
# to the date, same as the old per-month-file site did).
SITE_MONTHS_BACK = 12
SITE_MONTHS_AHEAD = 12


def browsable_months() -> list[tuple[int, int]]:
    today = date.today()
    months = []
    for delta in range(-SITE_MONTHS_BACK, SITE_MONTHS_AHEAD + 1):
        m = today.month - 1 + delta
        y = today.year + m // 12
        m = m % 12 + 1
        months.append((y, m))
    return months


def browsable_mondays() -> list[date]:
    months = browsable_months()
    start_year, start_month = months[0]
    end_year, end_month = months[-1]
    start = get_monday(date(start_year, start_month, 1))
    last_day_of_end_month = (
        date(end_year, end_month + 1, 1) - timedelta(days=1)
        if end_month < 12 else date(end_year, 12, 31)
    )
    end = get_monday(last_day_of_end_month)

    mondays = []
    current = start
    while current <= end:
        mondays.append(current)
        current += timedelta(days=7)
    return mondays


# ── Shared styling ───────────────────────────────────────────────────────

BASE_CSS = """
:root{
  --navy:#07194a; --navy-mid:#0d2870; --brand-blue:#1a3e9c; --ink:#1a1a2e; --muted:#475569;
  --white:#ffffff; --paper:#ffffff; --border:#d8dee9; --row-bg:#eef0f2; --row-bg-today:#dce6fb;
  --pill-bg:#2d3748; --pill-bg-hover:#1c2536;
  --gold-bg:#f5a623; --gold-ink:#5c3d00; --focus:#0b57d0;
}
.menu-embed *,.menu-embed *::before,.menu-embed *::after{box-sizing:border-box;}
.menu-embed{
  font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink); background:var(--paper); line-height:1.5; margin:0;
}
.menu-embed a{color:var(--navy-mid);}
.menu-embed a:focus-visible,.menu-embed button:focus-visible{outline:3px solid var(--focus);outline-offset:2px;}
.menu-embed .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}
.menu-embed .skip-link{position:absolute;left:-999px;top:auto;background:var(--navy);color:#fff;padding:.75rem 1rem;z-index:100;text-decoration:none;border-radius:0 0 6px 0;}
.menu-embed .skip-link:focus{left:0;top:0;}

/* Legacy banner header, still used by the embed-guide reference page */
.menu-embed .site-header{background:var(--navy);color:#fff;padding:1.25rem 1.5rem;}
.menu-embed .site-header h1{margin:0;font-size:clamp(1.3rem,4vw,1.9rem);}
.menu-embed .site-header p{margin:.3rem 0 0;color:#cfe0ff;font-size:.95rem;}

.menu-embed main{padding:0 1.25rem 2rem;max-width:1100px;margin:0 auto;}

/* Page head: eyebrow + big date heading + today/prev/next nav */
.menu-embed .page-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.75rem 1rem;max-width:1100px;margin:0 auto;padding:1.25rem 1.25rem 0;}
.menu-embed .eyebrow{font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:0 0 .2rem;}
.menu-embed .page-head h1{color:var(--brand-blue);font-size:clamp(1.4rem,4vw,2rem);margin:0;line-height:1.2;}
.menu-embed .nav-controls{display:flex;gap:.5rem;flex-shrink:0;align-items:center;}
.menu-embed .nav-pill,.menu-embed .nav-btn{background:var(--pill-bg);color:#fff;border:0;border-radius:8px;padding:.55rem .95rem;font-size:.85rem;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;font-weight:600;min-height:44px;min-width:44px;}
.menu-embed .nav-pill:hover,.menu-embed .nav-btn:hover{background:var(--pill-bg-hover);}
.menu-embed .nav-btn[aria-disabled="true"]{opacity:.35;pointer-events:none;}
.menu-embed .print-link{font-size:.85rem;color:var(--navy-mid);background:none;border:0;text-decoration:underline;cursor:pointer;padding:.5rem;}

/* Week / list view */
.menu-embed .day-list{max-width:1100px;margin:1rem auto 0;border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.menu-embed .day-row + .day-row{border-top:1px solid var(--border);}
.menu-embed .day-row-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:.35rem .75rem;background:var(--row-bg);padding:.7rem 1.25rem;}
.menu-embed .day-row.today .day-row-head{background:var(--row-bg-today);}
.menu-embed .day-row-head h2{font-size:1.05rem;color:var(--brand-blue);margin:0;display:inline-flex;align-items:center;gap:.5rem;}
.menu-embed .day-row-head .date{font-weight:700;color:var(--brand-blue);font-size:1rem;}
.menu-embed .today-flag{font-size:.65rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#3d2a00;background:var(--gold-bg);padding:.15rem .5rem;border-radius:999px;}
.menu-embed .day-row-body{padding:1rem 1.25rem 1.25rem;background:#fff;}
.menu-embed ul.items{list-style:none;margin:0;padding:0;}
.menu-embed ul.items li{padding-left:1.1rem;position:relative;margin-bottom:.4rem;color:#333;}
.menu-embed ul.items li:first-child::before{content:"";position:absolute;left:0;top:.55em;width:8px;height:8px;border-radius:50%;background:var(--brand-blue);}
.menu-embed .no-menu{color:var(--muted);font-style:italic;margin:0;}

.menu-embed .view-toggle{display:flex;justify-content:center;margin:1.5rem auto 0;max-width:1100px;}
.menu-embed .view-toggle a{background:var(--brand-blue);color:#fff;padding:.65rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;min-height:44px;display:inline-flex;align-items:center;}
.menu-embed .view-toggle a:hover{background:var(--navy-mid);}

.menu-embed .site-footer{padding:1.5rem 1.25rem 1rem;color:var(--muted);font-size:.85rem;text-align:center;}

/* Monthly calendar table */
.menu-embed table.cal{border-collapse:collapse;width:100%;margin-top:1rem;table-layout:fixed;}
.menu-embed table.cal caption{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}
.menu-embed table.cal th,.menu-embed table.cal td{border:1px solid var(--border);vertical-align:top;padding:.5rem;}
.menu-embed table.cal thead th{background:var(--brand-blue);color:#fff;text-align:center;padding:.6rem;font-size:.9rem;}
.menu-embed table.cal td{width:20%;}
.menu-embed table.cal td.empty{background:#f2f4f8;}
.menu-embed .cal-daynum{font-weight:700;color:var(--brand-blue);display:block;text-align:right;margin-bottom:.3rem;font-size:.85rem;}
.menu-embed table.cal ul{list-style:none;margin:0;padding:0;font-size:.8rem;}
.menu-embed table.cal ul li{margin-bottom:.25rem;color:#333;}
.menu-embed table.cal .no-menu{font-size:.78rem;}

@media (max-width: 700px){
  .menu-embed table.cal thead{position:absolute;left:-9999px;top:-9999px;}
  .menu-embed table.cal, .menu-embed table.cal tbody, .menu-embed table.cal tr, .menu-embed table.cal td{display:block;width:100%;}
  .menu-embed table.cal tr{margin-bottom:1rem;border:1px solid var(--border);border-radius:8px;overflow:hidden;}
  .menu-embed table.cal td{border:none;border-bottom:1px solid var(--border);}
  .menu-embed table.cal td:last-child{border-bottom:none;}
  .menu-embed table.cal td.empty{display:none;}
  .menu-embed table.cal td::before{content:attr(data-day);font-weight:700;color:var(--brand-blue);display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem;}
  .menu-embed .cal-daynum{text-align:left;}
  .menu-embed .page-head{padding:1rem 1rem 0;}
}

@media print{
  .menu-embed .view-toggle,.menu-embed .skip-link,.menu-embed .nav-controls,.menu-embed .print-link{display:none !important;}
  .menu-embed .site-header{background:#fff !important;color:#000 !important;border-bottom:3px solid #000;}
  .menu-embed .site-header p{color:#333 !important;}
  .menu-embed{background:#fff !important;}
  .menu-embed table.cal thead th{background:#e5e5e5 !important;color:#000 !important;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
  .menu-embed .today-flag{border:1px solid #000;}
  @page{size:landscape;margin:0.4in;}
}
""".strip()


def page_shell(title: str, description: str, body: str, canonical: str | None = None) -> str:
    canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{canonical_tag}
<style>
html,body{{margin:0;padding:0;}}
{BASE_CSS}
</style>
</head>
<body class="menu-embed">
<a class="skip-link" href="#main">Skip to main content</a>
{body}
</body>
</html>
"""


# ── Week view ─────────────────────────────────────────────────────────────

def render_week_body(school: str, display_name: str, menutype: str, monday: date,
                      nav: tuple[date | None, date | None] | None = None,
                      with_chrome: bool = True) -> str:
    """nav = (prev_monday, next_monday), each None if out of the browsable page range."""
    friday = monday + timedelta(days=4)
    day_items = item_map(school, menutype)

    today = date.today()

    rows = []
    for i, day_name in enumerate(DAYS):
        d = monday + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        items = day_items.get(key, [])
        is_today = d == today
        flag = '<span class="today-flag">Today</span>' if is_today else ""
        heading_id = f"day-{i}"
        if items:
            items_html = "<ul class=\"items\">" + "".join(f"<li>{esc(it)}</li>" for it in items) + "</ul>"
        else:
            items_html = '<p class="no-menu">No menu available</p>'
        rows.append(f"""
      <section class="day-row{' today' if is_today else ''}" aria-labelledby="{heading_id}">
        <div class="day-row-head">
          <h2 id="{heading_id}">{esc(day_name)}{flag}</h2>
          <span class="date">{esc(fmt_date_full(d))}</span>
        </div>
        <div class="day-row-body">{items_html}</div>
      </section>""")

    head = f"""
<p class="eyebrow">{esc(display_name)} &middot; {esc(menutype.capitalize())}</p>
<h1>{esc(fmt_date(monday))} &ndash; {esc(fmt_date(friday))}, {monday.year}</h1>"""

    nav_html = ""
    view_toggle = ""
    if with_chrome:
        prev_monday, next_monday = nav or (None, None)
        prev_el = (f'<a class="nav-btn" href="{prev_monday.isoformat()}.html" aria-label="Previous week">&larr;</a>'
                   if prev_monday else
                   '<span class="nav-btn" aria-disabled="true" aria-hidden="true">&larr;</span>')
        next_el = (f'<a class="nav-btn" href="{next_monday.isoformat()}.html" aria-label="Next week">&rarr;</a>'
                   if next_monday else
                   '<span class="nav-btn" aria-disabled="true" aria-hidden="true">&rarr;</span>')
        nav_html = f"""
  <nav class="nav-controls" aria-label="Week navigation">
    <a class="nav-pill" href="./">Today</a>
    {prev_el}
    {next_el}
    <button type="button" class="print-link" onclick="window.print()">Print</button>
  </nav>"""
        view_toggle = '\n  <div class="view-toggle"><a href="../calendar/">Month View</a></div>'

    return f"""
<div class="page-head">
  <div>{head}</div>{nav_html}
</div>
<main id="main">
  <div class="day-list">
    {''.join(rows)}
  </div>{view_toggle}
</main>
<footer class="site-footer">Menu subject to change &middot; Poland Local School District &middot; Data sourced from Nutrislice</footer>
""".strip()


def build_week_pages():
    for row in load_menu_list():
        school, display_name, menutype = row["school"].strip(), row["display_name"].strip(), row["menutype"].strip()
        mondays = browsable_mondays()
        current_monday = get_monday(date.today())
        if current_monday not in mondays:
            mondays = sorted(set(mondays) | {current_monday})

        out_dir = SITE / school / menutype / "week"
        out_dir.mkdir(parents=True, exist_ok=True)

        for i, monday in enumerate(mondays):
            prev_monday = mondays[i - 1] if i > 0 else None
            next_monday = mondays[i + 1] if i < len(mondays) - 1 else None
            body = render_week_body(school, display_name, menutype, monday, nav=(prev_monday, next_monday))
            canonical = f"{PAGES_BASE}/{school}/{menutype}/week/{monday.isoformat()}.html"
            page = page_shell(
                f"{menutype.capitalize()} Menu — {display_name} — Week of {fmt_date(monday)}",
                f"{menutype.capitalize()} menu for {display_name}, week of {fmt_date(monday)}.",
                body,
                canonical=canonical,
            )
            (out_dir / f"{monday.isoformat()}.html").write_text(page)

        # index.html = a live copy of the current week's page (not a redirect,
        # so it loads instantly when used as an iframe src).
        current_file = out_dir / f"{current_monday.isoformat()}.html"
        if current_file.exists():
            (out_dir / "index.html").write_text(current_file.read_text())

    print(f"  Week pages built for {len(load_menu_list())} feeds")


# ── Monthly calendar view ───────────────────────────────────────────────

def build_week_grid(item_map: dict[str, list[str]], year: int, month: int) -> list[list[tuple[int | None, list[str]]]]:
    first = date(year, month, 1)
    last_day = (date(year, month + 1, 1) - timedelta(days=1)) if month < 12 else date(year, 12, 31)
    week_start = first - timedelta(days=first.weekday())

    weeks = []
    current = week_start
    while current <= last_day:
        week = []
        for i in range(5):
            d = current + timedelta(days=i)
            key = d.strftime("%Y-%m-%d")
            if d.month == month:
                week.append((d.day, item_map.get(key, [])))
            else:
                week.append((None, []))
        weeks.append(week)
        current += timedelta(days=7)
    return weeks


def render_calendar_body(school: str, display_name: str, menutype: str, year: int, month: int,
                          nav: tuple[tuple[int, int] | None, tuple[int, int] | None] | None = None,
                          with_chrome: bool = True) -> str:
    day_items = item_map(school, menutype)
    weeks = build_week_grid(day_items, year, month)

    header_cells = "".join(f'<th scope="col">{esc(d)}</th>' for d in DAYS)

    rows = []
    for week in weeks:
        cells = []
        for day_name, (day_num, items) in zip(DAYS, week):
            if day_num is None:
                cells.append(f'<td class="empty" data-day="{esc(day_name)}"></td>')
                continue
            if items:
                items_html = "<ul>" + "".join(f"<li>{esc(it)}</li>" for it in items) + "</ul>"
            else:
                items_html = '<p class="no-menu">No menu</p>'
            d_full = date(year, month, day_num)
            cells.append(
                f'<td data-day="{esc(day_name)}">'
                f'<span class="sr-only">{esc(fmt_date_long(d_full))}: </span>'
                f'<span class="cal-daynum" aria-hidden="true">{day_num}</span>{items_html}</td>'
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")

    month_label = f"{MONTH_NAMES[month]} {year}"
    caption = f"{esc(menutype.capitalize())} menu &mdash; {esc(display_name)} &mdash; {esc(month_label)}"

    nav_html = ""
    view_toggle = ""
    if with_chrome:
        prev_ym, next_ym = nav or (None, None)
        prev_el = (f'<a class="nav-btn" href="{prev_ym[0]}-{prev_ym[1]:02d}.html" aria-label="Previous month">&larr;</a>'
                   if prev_ym else
                   '<span class="nav-btn" aria-disabled="true" aria-hidden="true">&larr;</span>')
        next_el = (f'<a class="nav-btn" href="{next_ym[0]}-{next_ym[1]:02d}.html" aria-label="Next month">&rarr;</a>'
                   if next_ym else
                   '<span class="nav-btn" aria-disabled="true" aria-hidden="true">&rarr;</span>')
        nav_html = f"""
  <nav class="nav-controls" aria-label="Month navigation">
    <a class="nav-pill" href="index.html">Today</a>
    {prev_el}
    {next_el}
    <button type="button" class="print-link" onclick="window.print()">Print</button>
  </nav>"""
        view_toggle = '\n  <div class="view-toggle"><a href="../week/">List View</a></div>'

    return f"""
<div class="page-head">
  <div>
    <p class="eyebrow">{esc(menutype.capitalize())} &middot; {esc(display_name)}</p>
    <h1>{esc(month_label)}</h1>
  </div>{nav_html}
</div>
<main id="main">
  <table class="cal">
    <caption>{caption}</caption>
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>{view_toggle}
</main>
<footer class="site-footer">Menu subject to change &middot; Poland Local School District &middot; Data sourced from Nutrislice</footer>
""".strip()


def build_calendar_pages():
    built = 0
    for row in load_menu_list():
        school, display_name, menutype = row["school"].strip(), row["display_name"].strip(), row["menutype"].strip()
        cal_dir = SITE / school / menutype / "calendar"
        cal_dir.mkdir(parents=True, exist_ok=True)

        months = browsable_months()

        for i, (year, month) in enumerate(months):
            prev_ym = months[i - 1] if i > 0 else None
            next_ym = months[i + 1] if i < len(months) - 1 else None
            body = render_calendar_body(school, display_name, menutype, year, month, nav=(prev_ym, next_ym))
            canonical = f"{PAGES_BASE}/{school}/{menutype}/calendar/{year}-{month:02d}.html"
            page = page_shell(
                f"{menutype.capitalize()} Calendar — {MONTH_NAMES[month]} {year} — {display_name}",
                f"Printable {menutype} calendar for {display_name}, {MONTH_NAMES[month]} {year}.",
                body,
                canonical=canonical,
            )
            (cal_dir / f"{year}-{month:02d}.html").write_text(page)
            built += 1

        # index.html = a live copy of the current month's page (not a
        # redirect, so it loads instantly when used as an iframe src). Falls
        # back to the most recent available month if the current one has no
        # data yet.
        today = date.today()
        current_ym = (today.year, today.month)
        if current_ym not in months and months:
            current_ym = months[-1]
        current_file = cal_dir / f"{current_ym[0]}-{current_ym[1]:02d}.html"
        if current_file.exists():
            (cal_dir / "index.html").write_text(current_file.read_text())

        # Bare fragment (month view, the default) — for pasting into a
        # Finalsite Custom HTML block if iframes aren't an option there.
        if current_file.exists():
            fragment_body = render_calendar_body(school, display_name, menutype,
                                                  current_ym[0], current_ym[1], with_chrome=False)
            embed_url = f"{PAGES_BASE}/{school}/{menutype}/embed.html"
            fragment = f"<!-- Poland Schools menu embed — {esc(display_name)} {esc(menutype)}. " \
                       f"Regenerated daily; re-copy from {embed_url} to stay current if " \
                       f"pasted as static HTML instead of used via iframe. -->\n" \
                       f"<div class=\"menu-embed\">\n<style>{BASE_CSS}</style>\n{fragment_body}\n</div>\n"
            (SITE / school / menutype / "embed.html").write_text(fragment)

    print(f"  Calendar pages built: {built}")


# ── Embed guide ───────────────────────────────────────────────────────────

def build_embed_guide():
    """A human-facing page listing ready-to-copy embed snippets for whoever
    manages the Finalsite pages — not linked from anywhere automatically
    consumed by CI, just a convenience reference."""
    widget_url = f"{PAGES_BASE}/embed/menu-widget.js"
    sections = []
    for row in load_menu_list():
        school, display_name, menutype = row["school"].strip(), row["display_name"].strip(), row["menutype"].strip()
        week_url = f"{PAGES_BASE}/{school}/{menutype}/week/"
        cal_url = f"{PAGES_BASE}/{school}/{menutype}/calendar/"
        embed_url = f"{PAGES_BASE}/{school}/{menutype}/embed.html"

        widget_snippet = f'<div data-psmenu data-school="{esc(school)}" data-menutype="{esc(menutype)}"></div>'
        finalsite_file_url = f"{PAGES_BASE}/embed/finalsite/{school}-{menutype}.html"

        cal_iframe_snippet = (
            f'<iframe src="{cal_url}" title="{esc(display_name)} {esc(menutype)} calendar" '
            f'style="width:100%;max-width:900px;border:0;min-height:800px" loading="lazy"></iframe>'
        )
        iframe_snippet = (
            f'<iframe src="{week_url}" title="{esc(display_name)} {esc(menutype)} menu" '
            f'style="width:100%;max-width:900px;border:0;min-height:900px" loading="lazy"></iframe>'
        )

        sections.append(f"""
    <section aria-labelledby="h-{esc(school)}-{esc(menutype)}">
      <h2 id="h-{esc(school)}-{esc(menutype)}">{esc(display_name)} &mdash; {esc(menutype.capitalize())}</h2>

      <h3>Recommended for Finalsite: self-contained paste block</h3>
      <p>Open <a href="{esc(finalsite_file_url)}">{esc(finalsite_file_url)}</a>, select all, copy,
      and paste the whole thing into this page's Custom HTML component. It's one complete block
      &mdash; CSS, markup, and JS all inline, no external script tag, no third-party library CDN,
      no iframe. The only network request it makes at runtime is fetching this month's JSON
      straight from the repo, so it always shows live data. Includes working prev/next month
      navigation and a List View / Month View toggle, built on semantic HTML (a real
      <code>&lt;table&gt;</code> for the grid, proper headings, focus-visible states, 44px touch
      targets) rather than a calendar library's non-semantic div grid.</p>

      <h3>Lighter option: div + shared script</h3>
      <p>If the site can load an external script fine, this is less to paste per page &mdash;
      functionally identical, just not self-contained:</p>
      <pre><code>{esc(widget_snippet)}</code></pre>
      <pre><code>&lt;script src="{esc(widget_url)}" defer&gt;&lt;/script&gt;</code></pre>
      <p>Defaults to month view; add <code>data-view="week"</code> to start in list view instead.</p>

      <h3>Alternative: iframe</h3>
      <p>Simpler, but some Finalsite CSP configurations block framed content outright (that's
      what happened when we first tried this route) &mdash; use one of the options above if this
      gets silently blocked.</p>
      <pre><code>{esc(cal_iframe_snippet)}</code></pre>
      <pre><code>{esc(iframe_snippet)}</code></pre>

      <h3>Fallback: static fragment</h3>
      <p>Only if none of the above works. Copy the contents of
      <a href="{esc(embed_url)}">{esc(embed_url)}</a> directly into the Custom HTML block
      (renders the monthly calendar as of the last rebuild). It is regenerated daily, but a
      pasted copy freezes at paste time &mdash; you'd need to re-copy it each time the menu
      changes to stay current.</p>

      <h3>PDF calendar (clickable image)</h3>
      <p>Link the current month's thumbnail image at
      <code>{esc(PAGES_BASE)}/pdfs/thumbnails/{{year}}-{{month}}-{esc(menutype)}-{esc(school)}.png</code>
      to the PDF at <code>{esc(PAGES_BASE)}/pdfs/{{year}}-{{month}}-{esc(menutype)}-{esc(school)}.pdf</code>.</p>
    </section>""")

    body = f"""
<header class="site-header">
  <h1>Embedding These Menus</h1>
  <p>Copy-paste snippets for the school website / Finalsite</p>
</header>
<main id="main">
  <p>The <strong>JS widget</strong> is the recommended approach: it fetches the menu JSON
  straight from this repo client-side and renders it in the page, so it always shows live data
  without needing to frame external content &mdash; which avoids the CSP <code>frame-src</code>
  blocks some Finalsite configurations apply to iframes. The monthly calendar is the default
  view everywhere; every page links to the alternate list view too.</p>
  {''.join(sections)}
</main>
<footer class="site-footer">Internal reference page &mdash; not linked from the public menu pages.</footer>
""".strip()

    extra_css = """
.menu-embed pre{background:#0d1330;color:#e8edff;padding:1rem;border-radius:8px;overflow-x:auto;font-size:.85rem;}
.menu-embed code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;}
.menu-embed section{border-top:1px solid var(--border);padding-top:1.25rem;margin-top:1.5rem;}
"""
    page = page_shell(
        "Embedding These Menus — Reference",
        "Copy-paste iframe and fallback embed snippets for Finalsite.",
        body,
    ).replace("</style>", extra_css + "</style>")

    out_dir = SITE / "embed-guide"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page)
    print("  Embed guide built: site/embed-guide/index.html")


# ── Landing page ─────────────────────────────────────────────────────────

MEAL_ICONS = {"breakfast": "🥞", "lunch": "🍕"}


def latest_pdf_for(school: str, menutype: str) -> tuple[int, int] | None:
    """Most recent (year, month) with a generated PDF on disk, preferring the
    current month if it exists."""
    pdf_dir = SITE / "pdfs"
    months = sorted({
        (int(p.stem.split("-")[0]), int(p.stem.split("-")[1]))
        for p in pdf_dir.glob(f"*-{menutype}-{school}.pdf")
    })
    if not months:
        return None
    today = date.today()
    if (today.year, today.month) in months:
        return (today.year, today.month)
    return months[-1]


def build_index_page():
    feed_cards = []
    pdf_cards = []
    for row in load_menu_list():
        school, display_name, menutype = row["school"].strip(), row["display_name"].strip(), row["menutype"].strip()
        icon = MEAL_ICONS.get(menutype, "🍽️")

        feed_cards.append(f"""
      <a class="card" href="{school}/{menutype}/calendar/">
        <span class="card-icon" aria-hidden="true">{icon}</span>
        <span class="card-school">{esc(display_name)}</span>
        <span class="card-type">{esc(menutype.capitalize())}</span>
        <span class="card-desc">Monthly calendar — accessible, mobile-friendly, iframe-ready</span>
      </a>""")

        ym = latest_pdf_for(school, menutype)
        if ym:
            year, month = ym
            stem = f"{year}-{month:02d}-{menutype}-{school}"
            pdf_cards.append(f"""
      <a class="card pdf-card" href="pdfs/{stem}.pdf">
        <img src="pdfs/thumbnails/{stem}.png" alt="{esc(MONTH_NAMES[month])} {year} {esc(menutype)} calendar for {esc(display_name)} (PDF)" loading="lazy">
        <span class="card-school">{esc(display_name)}</span>
        <span class="card-type">{esc(MONTH_NAMES[month])} {year} &middot; {esc(menutype.capitalize())} PDF</span>
      </a>""")

    tv_cards = "".join(f"""
      <a class="card" href="tv.html?school={esc(row['school'].strip())}&type={esc(row['menutype'].strip())}" target="_blank" rel="noopener">
        <span class="card-icon" aria-hidden="true">{MEAL_ICONS.get(row['menutype'].strip(), '📺')}</span>
        <span class="card-school">{esc(row['display_name'].strip())}</span>
        <span class="card-type">{esc(row['menutype'].strip().capitalize())}</span>
        <span class="card-desc">Fullscreen TV display</span>
      </a>""" for row in load_menu_list())

    week_cards = "".join(f"""
      <a class="card" href="{esc(row['school'].strip())}/{esc(row['menutype'].strip())}/week/">
        <span class="card-icon" aria-hidden="true">📋</span>
        <span class="card-school">{esc(row['display_name'].strip())}</span>
        <span class="card-type">{esc(row['menutype'].strip().capitalize())}</span>
        <span class="card-desc">This week as a simple list</span>
      </a>""" for row in load_menu_list())

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poland Schools Menu System</title>
<meta name="description" content="Weekly and monthly school breakfast/lunch menus for Poland Local Schools.">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
  :root{{ --navy:#07194a; --gold:#f5a623; --white:#fff; --gray:#7a9cc6; --ink:#1a1a2e; }}
  body{{ font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; background:var(--navy); color:var(--white);
    min-height:100vh; display:flex; flex-direction:column; align-items:center; padding:40px 20px 60px; }}
  a{{ color:inherit; }}
  a:focus-visible{{ outline:3px solid var(--gold); outline-offset:2px; }}
  h1{{ font-size:clamp(32px,5vw,52px); letter-spacing:1px; margin-bottom:6px; }}
  h1 span{{ color:var(--gold); }}
  .subtitle{{ font-size:16px; color:var(--gray); margin-bottom:40px; letter-spacing:1px; text-transform:uppercase; }}
  .section-label{{ font-size:14px; color:var(--gray); letter-spacing:2px; text-transform:uppercase;
    margin:40px 0 16px; align-self:flex-start; max-width:900px; width:100%; }}
  .grid{{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; max-width:900px; width:100%; }}
  .card{{ background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15); border-radius:14px;
    padding:24px; text-decoration:none; display:flex; flex-direction:column; gap:6px;
    transition:transform .15s, border-color .15s; }}
  .card:hover{{ transform:translateY(-3px); border-color:var(--gold); }}
  .card-icon{{ font-size:32px; }}
  .card-school{{ font-size:13px; color:var(--gold); font-weight:600; letter-spacing:1px; text-transform:uppercase; }}
  .card-type{{ font-size:20px; font-weight:600; }}
  .card-desc{{ font-size:13px; color:var(--gray); line-height:1.4; }}
  .pdf-card img{{ width:100%; border-radius:8px; border:1px solid rgba(255,255,255,0.2); margin-bottom:4px; }}
  footer{{ margin-top:56px; font-size:13px; color:var(--gray); opacity:.7; text-align:center; }}
  footer a{{ color:var(--gold); }}
</style>
</head>
<body>
  <h1>Poland <span>Schools</span></h1>
  <p class="subtitle">Menu Display System</p>

  <p class="section-label">🗓️ Monthly Calendars</p>
  <div class="grid">{''.join(feed_cards)}</div>

  <p class="section-label">📋 Weekly List View</p>
  <div class="grid">{week_cards}</div>

  <p class="section-label">📄 Monthly PDF Calendars</p>
  <div class="grid">{''.join(pdf_cards) if pdf_cards else '<p style="color:var(--gray)">PDFs are generated by the daily build — check back soon.</p>'}</div>

  <p class="section-label">📺 TV Displays</p>
  <div class="grid">{tv_cards}</div>

  <footer>
    Poland Local School District &middot; Menu data sourced from Nutrislice<br>
    <a href="embed-guide/">Embedding these menus on Finalsite &rarr;</a>
  </footer>
</body>
</html>
"""
    (SITE / "index.html").write_text(page)
    print("  Landing page built: site/index.html")


if __name__ == "__main__":
    build_week_pages()
    build_calendar_pages()
    build_embed_guide()
    build_index_page()
    print("Accessible pages built.")

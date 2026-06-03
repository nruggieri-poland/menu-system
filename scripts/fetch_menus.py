"""
fetch_menus.py
Pulls menu data from Nutrislice for all schools/mealtypes defined in menu-list.csv
and writes clean JSON files to the data/ directory.

Default mode: fetches a 25-month window — 12 months back, current month, 12 months ahead.
Manual mode: pass --year YYYY --month MM to fetch a single specific month.

Output format: data/{year}-{month:02d}-{menutype}-{school}.json
"""

import argparse
import csv
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SchoolMenuBot/1.0)",
    "Accept": "application/json",
}

# ── Date helpers ──────────────────────────────────────────────────────────────

def get_sundays_for_menu(year: int, month: int) -> list[datetime]:
    """Return all Sundays needed to cover every week that touches the given month."""
    first_day = datetime(year, month, 1)
    days_to_sunday = (6 - first_day.weekday()) % 7
    first_sunday = first_day + timedelta(days=days_to_sunday)
    sunday_before = first_sunday - timedelta(days=7)

    sundays = [sunday_before]
    current = first_sunday
    while current.month == month:
        sundays.append(current)
        current += timedelta(days=7)
    sundays.append(current)  # one Sunday past the end of the month

    return sundays


def month_range(center: datetime, months_back: int, months_ahead: int) -> list[tuple[int, int]]:
    """
    Return a list of (year, month) tuples spanning from `months_back` before
    `center` to `months_ahead` after it, inclusive.
    """
    results = []
    for delta in range(-months_back, months_ahead + 1):
        month = center.month + delta
        year  = center.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        results.append((year, month))
    return results


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_week(api_url: str, sunday: datetime) -> list[dict]:
    """Fetch one week of menu data starting on sunday. Returns list of day dicts."""
    url = f"{api_url}/{sunday.strftime('%Y/%m/%d')}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    ⚠ Failed {url}: {e}")
        return []

    days = []
    for day in resp.json().get("days", []):
        date_str = day.get("date", "")
        items = []
        for entry in day.get("menu_items", []):
            food = entry.get("food")
            if food and food.get("name"):
                name = food["name"].strip()
                if name and name.lower() not in ("", "none"):
                    items.append(name)

        # De-duplicate while preserving order
        seen: set[str] = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)

        if unique_items:
            days.append({"date": date_str, "items": unique_items})
        else:
            print(f"    – No items for {date_str}")

    return days


def fetch_month(api_url: str, year: int, month: int) -> list[dict]:
    """Fetch all menu days for the given month."""
    sundays = get_sundays_for_menu(year, month)
    print(f"    Sundays: {[s.strftime('%Y-%m-%d') for s in sundays]}")

    all_days: dict[str, list[str]] = {}
    for sunday in sundays:
        for day in fetch_week(api_url, sunday):
            try:
                day_dt = datetime.strptime(day["date"], "%Y-%m-%d")
            except ValueError:
                continue
            if day_dt.year == year and day_dt.month == month:
                all_days[day["date"]] = day["items"]
        time.sleep(0.8)  # be polite to Nutrislice

    return [{"date": d, "items": i} for d, i in sorted(all_days.items())]


# ── Saving ────────────────────────────────────────────────────────────────────

def save_json(days: list[dict], school: str, display_name: str,
              menutype: str, year: int, month: int) -> Path:
    payload = {
        "school":       school,
        "display_name": display_name,
        "menutype":     menutype,
        "year":         year,
        "month":        month,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days":         days,
    }
    filename = DATA_DIR / f"{year}-{month:02d}-{menutype}-{school}.json"
    with open(filename, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"    ✓ Saved {filename.name} ({len(days)} days)")
    return filename


# ── Orchestration ─────────────────────────────────────────────────────────────

def process_school(school: str, display_name: str, menutype: str,
                   api_url: str, months: list[tuple[int, int]]) -> None:
    print(f"\n{'─'*60}")
    print(f"  {display_name} / {menutype}")
    print(f"  {len(months)} months to fetch")
    print(f"{'─'*60}")

    for year, month in months:
        label = datetime(year, month, 1).strftime("%B %Y")
        print(f"\n  [{label}]")
        days = fetch_month(api_url, year, month)
        save_json(days, school, display_name, menutype, year, month)


def process_all(input_csv: Path, months: list[tuple[int, int]]) -> None:
    with open(input_csv, newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows) * len(months)
    print(f"\n🗓  Fetching {len(months)} months × {len(rows)} feeds = {total} requests\n")

    for row in rows:
        process_school(
            school       = row["school"].strip(),
            display_name = row["display_name"].strip(),
            menutype     = row["menutype"].strip(),
            api_url      = row["api"].strip(),
            months       = months,
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Nutrislice menu data")
    parser.add_argument("--year",  type=int, help="Fetch a single year (requires --month)")
    parser.add_argument("--month", type=int, help="Fetch a single month 1-12 (requires --year)")
    parser.add_argument("--back",  type=int, default=1,
                        help="Months to look back from today (default: 12)")
    parser.add_argument("--ahead", type=int, default=1,
                        help="Months to look ahead from today (default: 12)")
    args = parser.parse_args()

    csv_path = Path(__file__).parent / "menu-list.csv"

    if args.year and args.month:
        # Single-month mode
        months = [(args.year, args.month)]
        print(f"Single-month mode: {args.year}-{args.month:02d}")
    else:
        # Rolling window mode (default)
        today  = datetime.today()
        months = month_range(today, months_back=args.back, months_ahead=args.ahead)
        print(f"Rolling window mode: {months[0][0]}-{months[0][1]:02d} → "
              f"{months[-1][0]}-{months[-1][1]:02d}")

    process_all(csv_path, months)
    print("\n✅ Done.")


if __name__ == "__main__":
    main()

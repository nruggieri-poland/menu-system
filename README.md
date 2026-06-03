# Poland Schools Menu System

Automated school menu pipeline: pulls from Nutrislice → stores clean JSON → generates printable PDFs → deploys animated TV display via GitHub Pages.

## Live URLs (after GitHub Pages is enabled)

| Display | URL |
|---|---|
| PSHS Breakfast | `https://<your-org>.github.io/<repo>/pshs/breakfast/` |
| PSHS Lunch | `https://<your-org>.github.io/<repo>/pshs/lunch/` |
| McKinley Breakfast | `https://<your-org>.github.io/<repo>/mckinley-middle/breakfast/` |
| McKinley Lunch | `https://<your-org>.github.io/<repo>/mckinley-middle/lunch/` |

Each URL renders a **1920×1080 animated weekly menu display** — just point a browser in fullscreen at any of these on a cafeteria TV.

---

## Project Structure

```
menu-system/
├── .github/workflows/
│   ├── fetch-menus.yml        # Daily 6am: pull from Nutrislice → data/
│   └── generate-outputs.yml  # After fetch: build PDFs + deploy site
├── scripts/
│   ├── menu-list.csv          # Schools + Nutrislice API URLs (edit this!)
│   ├── fetch_menus.py         # Nutrislice → JSON
│   ├── generate_pdf.py        # JSON → monthly PDF
│   └── build_site.py          # Copies data into site/, builds manifest
├── data/                      # Auto-generated JSON (committed by CI)
│   └── {year}-{month}-{type}-{school}.json
├── pdfs/                      # Auto-generated PDFs (committed by CI)
├── site/                      # GitHub Pages static site
│   ├── index.html             # Dashboard / link hub
│   ├── tv.html                # TV display (reads ?school= & ?type= params)
│   ├── pshs/breakfast/        # Redirect → tv.html
│   ├── pshs/lunch/
│   ├── mckinley-middle/breakfast/
│   └── mckinley-middle/lunch/
```

---

## Setup

### 1. Fork / create repo

Push this directory to a new GitHub repository.

### 2. Update `scripts/menu-list.csv`

Verify the Nutrislice API URLs for each school/meal type. The format Nutrislice uses is typically:

```
https://<district>.nutrislice.com/menu/<school-slug>/<meal-type>
```

To find the correct slug, open the Nutrislice menu page for your school in a browser, open DevTools → Network, and look for requests to `/menu/<slug>/breakfast/YYYY/MM/DD/`.

### 3. Enable GitHub Pages

- Repo Settings → Pages
- Source: **Deploy from a branch**
- Branch: `gh-pages` / root
- Save

### 4. Enable Actions permissions

- Repo Settings → Actions → General
- Set **Workflow permissions** to **Read and write**

### 5. Run manually the first time

Go to Actions → **Fetch Menus** → Run workflow → enter current year/month.  
Then Actions → **Generate Outputs & Deploy** → Run workflow.

After that, everything runs automatically every day at 6 AM.

---

## TV Display Setup

1. Open the TV display URL in Chrome/Edge on the cafeteria computer.
2. Press **F11** for fullscreen.
3. The display will auto-refresh at midnight to show the current week.
4. Today's column is highlighted in gold automatically.

### Tips
- Each TV only needs one URL bookmarked.
- Use Chrome's "Open on startup" feature for always-on displays.
- The display works offline if the browser has the page cached (it re-fetches data from GitHub Pages, not Nutrislice directly).

---

## Running Locally

```bash
pip install requests reportlab

# Fetch menus
cd scripts
python fetch_menus.py
# → Enter 2026 and 5

# Generate PDFs
python generate_pdf.py
# → Enter 2026 and 5

# Build site (copies data into site/)
python build_site.py

# Serve site locally
cd ../site
python -m http.server 8000
# Open http://localhost:8000/tv.html?school=pshs&type=breakfast
```

---

## Customization

### Add a school
Add a row to `scripts/menu-list.csv` and create a redirect stub under `site/<school>/<type>/index.html`.

### Change the fetch schedule
Edit the `cron:` line in `.github/workflows/fetch-menus.yml`. Current default: `0 11 * * *` (11:00 UTC = 6:00 AM Eastern).

### Change PDF branding
Edit the color constants at the top of `scripts/generate_pdf.py`.

---

## Dependencies

| Package | Use |
|---|---|
| `requests` | Nutrislice API calls |
| `reportlab` | PDF generation |

Both are installed by the GitHub Actions workflows automatically.

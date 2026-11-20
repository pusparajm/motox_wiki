# MotoX Wiki

A fast, lightweight motorcycle technical reference — engine and performance specifications, dimensions, service data, torque values, oil quantities, fork seal sizes, fastener dimensions, and more. Built for [GitHub Pages](https://pages.github.com/) with zero heavy frameworks.

📖 **[Complete setup & workflow guide](docs/GUIDE.md)** — local admin, publishing, data model, troubleshooting.

## Coverage

The catalogue currently contains **409 mass-produced motorcycles from 36 manufacturers**, spanning:

- Commuters, scooters and mini-bikes
- Naked bikes, retro roadsters and scramblers
- Supersports, sportbikes and hyper-nakeds
- Adventure, dual-sport, enduro and motocross models
- Cruisers, baggers and touring bikes
- Electric motorcycles

Every entry has a **General Specifications** section (engine, power, torque, transmission, suspension, brakes, tyres, weight, seat height, fuel capacity and more) and a **Torque Specifications** section. Where reliable model-specific data is available, the torque table shows exact component values; otherwise the page shows a clearly labelled general fastener reference instead of inventing figures. Where reliable data is available, entries also include **Service Data** (oil capacity and grade, chain size, spark plug, brake pad codes, wheel and steering bearing kits, fork oil and seal sizes).

Manufacturers covered include Aprilia, Ather, Bajaj, Benelli, BMW, BSA, CFMOTO, Ducati, Energica, Harley-Davidson, Hero, Honda, Husqvarna, Indian, Jawa, Kawasaki, KTM, Kove, Kymco, LiveWire, Moto Guzzi, Ola, Piaggio, QJMotor, Royal Enfield, Stark, Suzuki, SYM, Triumph, TVS, Ultraviolette, Vespa, Voge, Yamaha, Zero and Zontes.

> Specifications are manufacturer-claimed, compiled from public model data, and can vary by model year and market. Always confirm service limits and torque values against the owner's or workshop manual before working on a motorcycle. The site shows service data only where a reliable figure is available rather than filling gaps with generic values.

## Features

- **Lightweight** — vanilla HTML/CSS/JS with [Pico CSS](https://picocss.com/). No React, Vue, or runtime framework.
- **Complete catalogue** — browse all 409 models with make, category, text, and sort filters.
- **Smart search** — tokenized multi-word matching, common nicknames and aliases (Fireblade, Busa, Gixxer), typo tolerance, and suggested searches when nothing matches.
- **Expandable specs** — JSON-driven sections for key-value fields, tables and custom HTML blocks.
- **Related models** — each detail page links to other variants and models in the same family.
- **SEO pages** — static model specification pages under `motorcycle/` and oil capacity, seat height, weight, horsepower, parts fitment, A2, beginner and comparison guides under `guides/`.
- **Advertisements** — configurable ad slots (placeholder, custom HTML, Google AdSense).
- **Responsive** — mobile-friendly layout with collapsible spec sections.
- **SEO** — generated sitemap, per-model canonical URLs and Motorcycle structured data.

## Quick Start

### Local preview

```bash
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080).

### Rebuild data after editing `data/motorcycles.json`

```bash
npm run build:data
```

This regenerates `motorcycles-index.json`, per-bike files under `data/motorcycles/`, the search index, page indexes and the popular-model cache.

To rebuild the static SEO guides and sitemap as well:

```bash
npm run build:seo
```

Or run the full pipeline:

```bash
npm run build
```

### Deploy to GitHub Pages

1. Push this repository to GitHub.
2. Go to **Settings → Pages**.
3. Set **Source** to `Deploy from a branch`.
4. Select branch `main` (or `master`) and folder `/ (root)`.
5. Save. Your site will be live at `https://pusparajm.github.io/motox_wiki/` (or your [custom domain via Cloudflare](docs/GUIDE.md#custom-domain-with-cloudflare)).

**Note:** This repo contains only the public site. No admin code is included.

### Anti-scrape protection (optional hardening)

The public site includes a client-side **`js/shield.js`** layer that:

- Randomizes CSS class names on every page load (session-specific)
- Remaps `main.css` selectors to match obfuscated classes
- Adds honeypot links and bot heuristics for headless browsers
- Weaves dynamic HTML structure: dead markup removed at runtime, session-encoded text, parser traps for strict HTML/XML scrapers

For stronger protection before deploy, obfuscate the public JavaScript:

```bash
npm install
npm run build:web          # one-off build → js/dist/
npm run watch:web          # rebuild automatically when js/*.js changes
npm run preview            # build + watch + http://localhost:8765
npm run setup:hooks        # install git hooks (also runs on npm install)
```

Git hooks (auto-rebuild `js/dist/`):

- **pre-commit** — runs `npm run build:web` when `js/shield.js`, `js/core.js`, or `js/search.js` are staged or newer than `js/dist/`, then stages `js/dist/*.js`
- **post-merge** — rebuilds after `git pull` if sources are newer than dist

Enable once per clone:

```bash
npm run setup:hooks
```

(Happens automatically on `npm install` via the `prepare` script.)

**Limitation:** JSON files under `data/` remain directly fetchable on static hosting. Class obfuscation raises the bar for HTML scrapers; blocking bulk JSON export requires a server or edge worker.

## Editing content

### Option A — edit JSON directly

Edit files in `data/`:
- `motorcycles.json` — source of truth for bike specs
- `pages.json` — wiki articles
- `settings.json` — site title, ads, navigation, featured models

Then regenerate the derived files:

```bash
npm run build:data
```

### Option B — local admin tool (recommended)

Use the separate **`motox_wiki_admin`** folder (sibling to this repo, not committed here):

```bash
cd ../motox_wiki_admin
./setup.sh          # one-time: links to this repo's data/
./scripts/preview-wiki.sh   # terminal 1 — wiki at :8765
./start.sh          # terminal 2 — admin at :8766
```

Export JSON from the admin dashboard, copy into `motox_wiki/data/`, then rebuild and commit.

## Project Structure

```
motox_wiki/              # This repo (public, GitHub Pages)
├── index.html           # Browse all models
├── motorcycle.html      # Model detail page
├── pages.html           # Wiki reference pages
├── search.html          # Full search results
├── guides/              # Static SEO charts, buying guides and comparisons
├── motorcycle/          # Static, crawlable model specification pages
├── sitemap.xml
├── robots.txt
├── css/main.css
├── js/
│   ├── core.js
│   ├── search.js
│   └── shield.js
├── scripts/
│   ├── build-data.py    # Generate derived JSON from motorcycles.json
│   ├── build-seo-pages.py # Generate static guides and sitemap
│   └── build-web.mjs    # Obfuscate public JS into js/dist/
└── data/
    ├── motorcycles.json
    ├── motorcycles-index.json
    ├── motorcycles/<id>.json
    ├── pages.json
    └── settings.json
```

## Data Model

Motorcycles use flexible, expandable spec sections. A typical entry:

```json
{
  "id": "yamaha-mt-07-2018",
  "make": "Yamaha",
  "model": "MT-07",
  "year": "2018–Present",
  "region": "Global",
  "category": "Naked",
  "displacement": "689 cc",
  "summary": "Yamaha's hugely popular CP2 naked…",
  "sections": {
    "general_specs": {
      "label": "General Specifications",
      "fields": [
        { "key": "engine", "label": "Engine", "value": "689 cc liquid-cooled DOHC parallel twin" },
        { "key": "power", "label": "Max Power", "value": "74 hp (55 kW) @ 9,000 rpm" },
        { "key": "torque", "label": "Max Torque", "value": "68 Nm (50 lb-ft) @ 6,500 rpm" },
        { "key": "weight", "label": "Kerb Weight", "value": "184 kg" }
      ]
    },
    "service": {
      "label": "Service Data",
      "fields": [
        { "key": "oil_capacity", "label": "Engine Oil (with filter)", "value": "2.9 L (3.1 US qt)" },
        { "key": "oil_grade", "label": "Oil Grade", "value": "SAE 10W-40, JASO MA2" }
      ]
    },
    "torque_specs": {
      "label": "Torque Specifications",
      "table": [
        { "component": "Oil drain plug", "torque": "43 Nm", "notes": "Replace crush washer" }
      ]
    }
  }
}
```

Field keys in `general_specs` (`power`, `torque`, `weight`, `seat_height`, `engine`, `fuel_capacity`) are extracted into the compact index so browse cards and search results stay fast.

## SEO

The search strategy and page map are documented in [docs/SEO.md](docs/SEO.md). Static guide pages target oil capacity, seat height, weight, horsepower, torque, A2, beginner, 125cc, scooter, adventure, cruiser, electric and comparison queries.

## Data Sources & Accuracy

The catalogue was rebuilt from public manufacturer specifications and model data. It deliberately avoids filling every bike with the same generic values.

- Where a reliable service figure (oil capacity, chain size, fork seal) was available, it is included.
- Where it was not, the field is omitted and the page displays a verification note.
- Model-year and market differences exist. Treat the figures as a starting point and verify against the official workshop manual.

## Advertisements

Configure ad slots in `data/settings.json` under `ads.slots`:

| Slot ID | Location |
|---------|----------|
| `header-banner` | Below site header |
| `sidebar` | Right sidebar on detail pages |
| `content-top` | Above spec content |
| `content-bottom` | Below spec content |
| `footer-banner` | Above site footer on every page |
| `in-article` | Between spec sections |

## License

MIT — use freely for your own motorcycle wiki.

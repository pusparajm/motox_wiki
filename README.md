# MotoX Wiki

A fast, lightweight motorcycle technical reference wiki — torque specs, oil quantities, fork seal sizes, fastener dimensions, and more. Built for [GitHub Pages](https://pages.github.com/) with zero heavy frameworks.

📖 **[Complete setup & workflow guide](docs/GUIDE.md)** — local admin, publishing, data model, troubleshooting.

## Features

- **Lightweight** — Vanilla HTML/CSS/JS with [Pico CSS](https://picocss.com/) (~10 KB). No React, Vue, or build step.
- **Search** — Instant client-side search across motorcycles and wiki pages.
- **Expandable specs** — JSON-driven sections (key-value fields, tables, custom HTML blocks).
- **Advertisements** — Configurable ad slots (placeholder, custom HTML, Google AdSense).
- **Responsive** — Mobile-friendly layout with collapsible spec sections.

## Quick Start

### Local preview

```bash
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080)

### Deploy to GitHub Pages

1. Push this repository to GitHub.
2. Go to **Settings → Pages**.
3. Set **Source** to `Deploy from a branch`.
4. Select branch `main` (or `master`) and folder `/ (root)`.
5. Save. Your site will be live at `https://pusparajm.github.io/motox_wiki/` (or your [custom domain via Cloudflare](docs/GUIDE.md#custom-domain-with-cloudflare)).

**Note:** This repo contains only the public site. No admin code is included.

## Editing content

### Option A — Edit JSON directly

Edit files in `data/`:
- `motorcycles.json` — bike specs
- `pages.json` — wiki articles
- `settings.json` — site title, ads, navigation

### Option B — Local admin tool (recommended)

Use the separate **`motox_wiki_admin`** folder (sibling to this repo, not committed here):

```bash
cd ../motox_wiki_admin
./setup.sh          # one-time: links to this repo's data/
./scripts/preview-wiki.sh   # terminal 1 — wiki at :8765
./start.sh          # terminal 2 — admin at :8766
```

Export JSON from the admin dashboard, copy into `motox_wiki/data/`, then commit and push this repo.

## Project Structure

```
motox_wiki/              # This repo (public, GitHub Pages)
├── index.html
├── motorcycle.html
├── pages.html
├── search.html
├── css/main.css
├── js/
│   ├── core.js
│   └── search.js
└── data/
    ├── motorcycles.json
    ├── pages.json
    └── settings.json

motox_wiki_admin/        # Local only — NOT in this repo
├── index.html
├── js/admin.js
└── setup.sh
```

## Data Model

Motorcycles support flexible, expandable spec sections:

```json
{
  "id": "yamaha-mt-07-2018",
  "make": "Yamaha",
  "model": "MT-07",
  "sections": {
    "engine_oil": {
      "label": "Engine Oil",
      "fields": [
        { "key": "capacity", "label": "Oil Capacity", "value": "2.91 L" }
      ]
    },
    "torque_specs": {
      "label": "Torque Specifications",
      "table": [
        { "component": "Oil drain plug", "torque": "43 Nm", "notes": "" }
      ]
    }
  }
}
```

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

# MotoX Wiki — Complete Setup & Workflow Guide

This document covers everything you need to run, edit, and publish the MotoX Wiki — a lightweight, static motorcycle technical reference site.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Public Site vs Local Admin](#public-site-vs-local-admin)
4. [Local Preview (Public Site)](#local-preview-public-site)
5. [Local Admin Dashboard](#local-admin-dashboard)
6. [How Admin Login Works (Static Sites)](#how-admin-login-works-static-sites)
7. [Publishing Changes to GitHub](#publishing-changes-to-github)
8. [Deploy to GitHub Pages](#deploy-to-github-pages)
9. [Editing Content](#editing-content)
10. [Data Model](#data-model)
11. [Advertisements](#advertisements)
12. [Search](#search)
13. [Mobile & Responsive Design](#mobile--responsive-design)
14. [Layout & Spacing Notes](#layout--spacing-notes)
15. [Troubleshooting](#troubleshooting)

---

## Overview

MotoX Wiki is a **static website** for motorcycle technical reference:

- Torque specs
- Engine oil quantities
- Fork seal sizes
- Bolt & nut dimensions
- Custom expandable spec sections

**Tech stack (kept intentionally light):**

| Layer | Choice |
|-------|--------|
| HTML/CSS/JS | Vanilla — no React, Vue, or build step |
| CSS framework | [Pico CSS](https://picocss.com/) (~10 KB) |
| Data | JSON files in `data/` |
| Hosting | GitHub Pages |
| Admin | Separate local-only tool (`motox_wiki_admin`) |

---

## Project Structure

Two folders live side by side on your computer:

```
~/motox_wiki/              ← PUBLIC — commit & push to GitHub
├── index.html             # Homepage (browse motorcycles)
├── motorcycle.html        # Motorcycle detail page
├── pages.html             # Wiki reference pages
├── search.html            # Full search results
├── css/main.css           # Site styles
├── js/
│   ├── core.js            # Data loading, header, footer, ads
│   └── search.js          # Client-side search
├── data/
│   ├── motorcycles.json   # All motorcycle specs
│   ├── pages.json         # Wiki articles
│   └── settings.json      # Site title, nav, ads, search config
├── docs/
│   └── GUIDE.md           # This file
├── .gitignore             # Excludes admin/ if ever re-added
├── .nojekyll              # Required for GitHub Pages
└── README.md

~/motox_wiki_admin/        ← LOCAL ONLY — never deployed to GitHub Pages
├── index.html             # Admin dashboard UI
├── css/admin.css
├── js/
│   ├── config.js          # Paths to wiki repo (edit if needed)
│   └── admin.js           # CMS logic
├── data/                  # Symlink → ../motox_wiki/data/
├── exports/               # Drop exported JSON here (optional)
├── scripts/
│   ├── preview-wiki.sh    # Start wiki preview on :8765
│   └── apply-to-wiki.sh   # Copy exports/ into wiki data/
├── setup.sh               # One-time symlink setup
├── start.sh               # Start admin on :8766
└── README.md
```

---

## Public Site vs Local Admin

| | `motox_wiki` | `motox_wiki_admin` |
|---|---|---|
| **Purpose** | Public website visitors see this | You edit content locally |
| **Git** | Yes — push to GitHub | No — keep off public repo |
| **GitHub Pages** | Deployed | Never deployed |
| **URL (local)** | `http://localhost:8765` | `http://localhost:8766` |
| **Password** | None (public) | `motox2026` (default) |

The public site has **no admin link** in the footer and **no admin folder** in the repository.

---

## Local Preview (Public Site)

### Option A — simple

```bash
cd ~/motox_wiki
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080)

### Option B — via admin scripts (port 8765)

```bash
cd ~/motox_wiki_admin
./scripts/preview-wiki.sh
```

Open [http://localhost:8765](http://localhost:8765)

---

## Local Admin Dashboard

### One-time setup

```bash
cd ~/motox_wiki_admin
chmod +x setup.sh start.sh scripts/*.sh
./setup.sh
```

`setup.sh` creates a symlink:

```
motox_wiki_admin/data  →  ../motox_wiki/data/
```

This lets the admin dashboard read the same JSON files the public site uses.

### Run both site and admin

Use **two terminal windows**:

**Terminal 1 — Wiki preview:**
```bash
cd ~/motox_wiki_admin
./scripts/preview-wiki.sh
# → http://localhost:8765
```

**Terminal 2 — Admin dashboard:**
```bash
cd ~/motox_wiki_admin
./start.sh
# → http://localhost:8766
```

### Admin login

| Field | Value |
|-------|-------|
| URL | [http://localhost:8766](http://localhost:8766) |
| Default password | `motox2026` |

Change the password in **Admin → Site Settings → Admin Password**. The new password is stored in your browser's `localStorage` on your machine only.

### Admin sections

| Section | What you can do |
|---------|-----------------|
| **Dashboard** | Stats, quick actions, recent motorcycles |
| **Motorcycles** | Add, edit, delete bikes and spec sections |
| **Wiki Pages** | Manage reference articles |
| **Advertisements** | Configure ad slots |
| **Site Settings** | Title, tagline, footer, password |
| **Export / Import** | Download/upload JSON files |

### Configuration (`motox_wiki_admin/js/config.js`)

Edit if your wiki repo is not at `../motox_wiki/`:

```javascript
const AdminConfig = {
  dataBase: 'data/',                        // symlinked data folder
  wikiSiteUrl: 'http://localhost:8765',     // preview URL for "View Site"
  wikiDataPath: '../motox_wiki/data/'       // shown in export instructions
};
```

---

## How Admin Login Works (Static Sites)

There is **no server** on GitHub Pages. Login is entirely **client-side**:

```
You enter password
       ↓
JavaScript compares to default (motox2026) or localStorage password
       ↓
Match → sessionStorage flag set ("logged in" for this browser tab)
       ↓
Dashboard loads; edits saved to localStorage
       ↓
Export JSON → copy to motox_wiki/data/ → git commit → GitHub Pages updates
```

### What this means

| Aspect | Reality |
|--------|---------|
| **Security** | Not real authentication — password is in client-side code |
| **Protection** | Keeps casual visitors out of the dashboard UI only |
| **Edits** | Stored in your browser until you export |
| **Public site** | Unaffected — serves static JSON from GitHub |

Because admin is **local-only and not deployed**, the login gate only protects your own machine's editing session.

---

## Publishing Changes to GitHub

### Workflow (admin dashboard)

1. Make changes in the admin dashboard at `http://localhost:8766`
2. Go to **Export / Import**
3. Click **Export All** (or export individual files)
4. Copy the downloaded JSON files into `motox_wiki/data/`:

```bash
# Manual copy
cp ~/Downloads/motorcycles.json ~/motox_wiki/data/
cp ~/Downloads/pages.json      ~/motox_wiki/data/
cp ~/Downloads/settings.json   ~/motox_wiki/data/
```

**Or use the helper script:**

```bash
# Save exports to motox_wiki_admin/exports/ first, then:
cd ~/motox_wiki_admin
./scripts/apply-to-wiki.sh
```

5. Commit and push **only** the `motox_wiki` repo:

```bash
cd ~/motox_wiki
git add data/
git commit -m "Update motorcycle specs"
git push
```

6. GitHub Pages rebuilds automatically (usually within 1–2 minutes)

### Workflow (edit JSON directly)

```bash
cd ~/motox_wiki
# Edit data/motorcycles.json, data/pages.json, or data/settings.json
git add data/
git commit -m "Add Yamaha R1 torque specs"
git push
```

---

## Deploy to GitHub Pages

1. Create a GitHub repository and push `motox_wiki`:

```bash
cd ~/motox_wiki
git init
git add .
git commit -m "Initial MotoX Wiki"
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

2. On GitHub: **Settings → Pages**
3. **Source:** Deploy from a branch
4. **Branch:** `main` (or `master`)
5. **Folder:** `/ (root)`
6. Save

Your site will be live at:

```
https://<username>.github.io/<repo>/
```

> **Important:** Only push `motox_wiki`. Do **not** add `motox_wiki_admin` to this repository.

---

## Editing Content

### Motorcycles (`data/motorcycles.json`)

Each motorcycle entry supports:

- Basic info: make, model, year, category, displacement, tags, summary
- **Spec sections** — expandable groups (engine oil, torque, fork seals, fasteners, etc.)
- **Custom sections** — free-form HTML blocks

### Wiki pages (`data/pages.json`)

Reference articles (e.g. torque conversion chart, oil grades guide).

### Site settings (`data/settings.json`)

- Site title, tagline, description, footer
- Navigation links
- Ad slot configuration
- Search settings (`minChars`, `maxResults`)

---

## Data Model

### Motorcycle example

```json
{
  "id": "yamaha-mt-07-2018",
  "make": "Yamaha",
  "model": "MT-07",
  "year": "2018–2024",
  "category": "Naked",
  "displacement": "689 cc",
  "published": true,
  "tags": ["yamaha", "mt-07", "naked"],
  "summary": "Popular middleweight naked bike.",
  "sections": {
    "engine_oil": {
      "label": "Engine Oil",
      "fields": [
        { "key": "capacity", "label": "Oil Capacity", "value": "2.91 L" },
        { "key": "type", "label": "Grade", "value": "SAE 10W-40" }
      ]
    },
    "torque_specs": {
      "label": "Torque Specifications",
      "table": [
        { "component": "Oil drain plug", "torque": "43 Nm", "notes": "M12×1.25" }
      ]
    }
  },
  "custom_sections": [
    { "title": "Chain & Sprocket", "content": "525 chain, 114 links..." }
  ]
}
```

### Section types

| Type | Use for | Structure |
|------|---------|-----------|
| **fields** | Key-value specs (oil capacity, seal size) | `fields: [{ key, label, value }]` |
| **table** | Tabular data (torque specs, fasteners) | `table: [{ column1, column2, ... }]` |

Add new section keys freely — the site renderer handles any `fields` or `table` structure.

---

## Advertisements

Configured in `data/settings.json` under `ads`:

```json
{
  "ads": {
    "enabled": true,
    "slots": [
      {
        "id": "header-banner",
        "label": "Header Banner",
        "enabled": true,
        "type": "placeholder",
        "content": "<div class=\"ad-placeholder\">Advertisement — 728×90</div>"
      }
    ]
  }
}
```

### Ad slot locations

| Slot ID | Where it appears |
|---------|------------------|
| `header-banner` | Full-width bar below the top navigation |
| `sidebar` | Right sidebar on detail pages (desktop) |
| `content-top` | Above spec content |
| `content-bottom` | Below spec content |
| `in-article` | Between spec sections |

### Ad types

| Type | Description |
|------|-------------|
| `placeholder` | Dashed-border placeholder div (for development) |
| `html` | Custom HTML / ad network code |
| `adsense` | Google AdSense (`client` + `slotId` fields) |

---

## Search

Client-side search — no server or external library.

- Searches motorcycles and wiki pages
- Header search bar with instant dropdown results
- Full results page at `search.html?q=...`
- Config in `data/settings.json`:

```json
{
  "search": {
    "minChars": 2,
    "maxResults": 20
  }
}
```

---

## Mobile & Responsive Design

The site is responsive across screen sizes:

| Width | Behavior |
|-------|----------|
| **< 360px** | Compact brand, minimal padding |
| **< 768px** | Hamburger menu, stacked filters, single-column cards |
| **480px+** | Multi-column bike grid |
| **768px+** | Desktop header with inline navigation |
| **900px+** | Sidebar ad layout on detail pages |

### Mobile navigation

On phones, tap the **☰ menu button** (top right) to open Home / Browse / Pages links.

### Touch-friendly

Inputs use 44px+ tap targets on touch devices. Tables scroll horizontally on narrow screens.

---

## Layout & Spacing Notes

| Element | Setting |
|---------|---------|
| Side padding | `clamp(0.75rem, 3vw, 1rem)` on `body` |
| Content width | Full viewport (no max-width cap) |
| Footer | Sticks to bottom of viewport on short pages |
| Ad bar | Full-width strip below header |
| Header | Compact sticky bar |

---

## Troubleshooting

### Admin can't load data

```bash
cd ~/motox_wiki_admin
./setup.sh   # Re-create symlink
ls -la data  # Should point to ../motox_wiki/data
```

### Changes in admin don't appear on public site

Admin saves to **browser localStorage** first. You must **export JSON** and copy into `motox_wiki/data/`, then commit and push.

### Port already in use

```bash
# Use a different port
cd ~/motox_wiki
python3 -m http.server 9000
```

Update `wikiSiteUrl` in `motox_wiki_admin/js/config.js` if you change the preview port.

### CSS/JS changes not visible

Hard refresh: `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)

### GitHub Pages shows 404

- Ensure `.nojekyll` exists in the repo root
- Check Pages settings: branch `main`, folder `/ (root)`
- Wait 1–2 minutes after pushing

### Forgot admin password

Default is always `motox2026` unless you changed it in Site Settings.

To reset a custom password, open browser DevTools → Application → Local Storage → delete `motox_admin_password`.

---

## Quick Reference

```bash
# Preview public site
cd ~/motox_wiki && python3 -m http.server 8080

# Or via admin toolkit
cd ~/motox_wiki_admin && ./scripts/preview-wiki.sh   # :8765

# Start admin
cd ~/motox_wiki_admin && ./start.sh                   # :8766

# Publish
# 1. Export JSON from admin
# 2. Copy to ~/motox_wiki/data/
# 3. git add data/ && git commit && git push

# Admin password (default)
motox2026
```

---

## Summary

| Task | Where | Command / URL |
|------|-------|---------------|
| View public site locally | `motox_wiki` | `python3 -m http.server 8080` |
| Edit content | `motox_wiki_admin` | `http://localhost:8766` |
| Preview while editing | `motox_wiki_admin` | `http://localhost:8765` |
| Publish | `motox_wiki` git repo | Export → copy JSON → `git push` |
| Live site | GitHub Pages | `https://<user>.github.io/<repo>/` |

**Golden rule:** Only `motox_wiki` goes to GitHub. `motox_wiki_admin` stays on your computer.

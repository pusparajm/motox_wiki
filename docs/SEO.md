# SEO Strategy — MotoX Wiki

## Objective

Rank for high-intent motorcycle specification, service and buying queries, then funnel search visitors into model pages and the full catalogue.

The site already has a large structured dataset (409 models, 36 manufacturers, service data for 290 models). The SEO opportunity is not more generic text — it is **turning that data into pages that answer the exact things people search for**.

---

## Research method

Keyword demand was collected from **Google Autocomplete** for motorcycle seed terms, model names, service terms, buying intents and comparisons. Autocomplete reflects real query patterns and long-tail phrasing, though not volume.

Seed groups included:

- Model queries: `cbr600rr`, `mt 07`, `ninja 400`, `classic 350`, `himalayan 450`, `zx10r`, `panigale v4`
- Service queries: `motorcycle torque specs`, `motorcycle oil capacity`, `motorcycle seat height`, `motorcycle weight`, `motorcycle horsepower`, `motorcycle valve clearance`, `motorcycle chain slack`, `motorcycle tire pressure`
- Buying queries: `best beginner motorcycle`, `best a2 motorcycle`, `best 125cc motorcycle`, `best scooter`, `best adventure motorcycle`, `best cruiser motorcycle`, `best electric motorcycle`, `best commuter motorcycle`, `best retro motorcycle`
- Fit queries: `motorcycle seat height for short riders`, `motorcycle for short riders`, `a2 compliant motorcycles`
- Comparison queries: `cbr600rr vs cbr650r`, `mt 07 vs mt 09`, `ninja 400 vs ninja 500`, `classic 350 vs hunter 350`, `himalayan 450 vs 411`, `interceptor 650 vs continental gt 650`

---

## What people search for

### 1. Model-name + a specific attribute

Examples:

- `cbr600rr top speed`
- `cbr600rr seat height`
- `himalayan 450 weight`
- `interceptor 650 mileage`
- `mt 07 cc`
- `ninja 400 price`
- `harley sportster s seat height`

**Intent:** quick specification check, often on mobile.

**MotoX answer:** model pages with power, torque, weight, seat height, fuel capacity, oil capacity and service data. Titles and meta descriptions now include these attributes.

### 2. Service and maintenance lookups

Examples:

- `motorcycle torque specs`
- `motorcycle oil capacity chart`
- `engine oil capacity of classic 350`
- `motorcycle seat height chart`
- `motorcycle weight chart`
- `motorcycle horsepower chart`
- `motorcycle chain slack`
- `motorcycle valve clearance`
- `motorcycle tire pressure chart`

**Intent:** DIY maintenance, pre-purchase research or workshop reference.

**MotoX answer:** static data pages for oil capacity, seat height, weight, horsepower and torque, plus model-level service data and torque tables.

### 3. Buying-intent shortlists

Examples:

- `best beginner motorcycle`
- `best a2 motorcycles`
- `best 125cc motorcycle`
- `best scooter`
- `best adventure motorcycle`
- `best cruiser motorcycle`
- `best electric motorcycle`
- `best commuter motorcycle`
- `best retro motorcycle`

**Intent:** shortlist before a test ride or purchase.

**MotoX answer:** data-driven shortlists with transparent criteria (power, seat height, weight, category). These are not subjective rankings and say so.

### 4. Fit and accessibility

Examples:

- `motorcycle seat height for short riders`
- `motorcycle for short riders`
- `low seat height motorcycles`
- `motorcycle seat height calculator`

**Intent:** find a bike the rider can confidently handle.

**MotoX answer:** seat height chart and a low-seat page filtered to 800 mm or less, with weight and power context.

### 5. Direct comparisons

Examples:

- `cbr600rr vs cbr650r`
- `mt 07 vs mt 09`
- `ninja 400 vs ninja 500`
- `classic 350 vs hunter 350`
- `himalayan 450 vs 411`
- `interceptor 650 vs continental gt 650`

**Intent:** choose between two shortlisted models.

**MotoX answer:** side-by-side specification tables and on-paper differences, with links to both model pages.

---

## Keyword clusters and page map

| Cluster | Example queries | Target page |
|---|---|---|
| Model specs | `cbr600rr specs`, `mt 07 top speed`, `himalayan 450 weight` | `motorcycle.html?id=...` |
| Oil capacity | `motorcycle oil capacity chart`, `classic 350 engine oil capacity` | `guides/oil-capacity-chart.html` |
| Seat height | `motorcycle seat height chart`, `low seat height motorcycles` | `guides/seat-height-chart.html`, `guides/low-seat-height-motorcycles.html` |
| Weight | `motorcycle weight chart`, `ninja 400 weight` | `guides/weight-chart.html` |
| Horsepower | `motorcycle horsepower chart`, `cbr600rr hp` | `guides/horsepower-chart.html` |
| Torque | `motorcycle torque specs`, `zx10r torque specs` | `guides/torque-specs.html`, model pages |
| Beginner | `best beginner motorcycle` | `guides/best-beginner-motorcycles.html` |
| A2 | `best a2 motorcycle`, `a2 compliant motorcycles` | `guides/a2-motorcycles.html` |
| 125cc | `best 125cc motorcycle` | `guides/best-125cc-motorcycles.html` |
| Scooters | `best scooter`, `best scooter in india` | `guides/best-scooters.html` |
| Adventure | `best adventure motorcycle` | `guides/best-adventure-motorcycles.html` |
| Cruisers | `best cruiser motorcycle` | `guides/best-cruiser-motorcycles.html` |
| Electric | `best electric motorcycle` | `guides/best-electric-motorcycles.html` |
| Commuters | `best commuter motorcycle` | `guides/best-commuter-motorcycles.html` |
| Retro | `best retro motorcycle` | `guides/best-retro-motorcycles.html` |
| Comparisons | `cbr600rr vs cbr650r` | `guides/cbr600rr-vs-cbr650r.html` |
| Comparisons | `mt 07 vs mt 09` | `guides/mt-07-vs-mt-09.html` |
| Comparisons | `ninja 400 vs ninja 500` | `guides/ninja-400-vs-ninja-500.html` |
| Comparisons | `classic 350 vs hunter 350` | `guides/classic-350-vs-hunter-350.html` |
| Comparisons | `himalayan 450 vs 411` | `guides/himalayan-450-vs-411.html` |
| Comparisons | `interceptor 650 vs continental gt 650` | `guides/interceptor-650-vs-continental-gt-650.html` |

---

## On-page changes implemented

### Homepage

- Title targets **“Motorcycle Specifications Database”** and model count.
- Meta description includes power, torque, weight, seat height, oil capacity and torque specs.
- H1 changed from “Browse Motorcycles” to **“Motorcycle Specifications Database”**.
- Added a keyword-rich intro paragraph.
- Added popular guide links: oil capacity, seat height, beginner, A2, torque.
- Added `WebSite` + `SearchAction` structured data.
- Added Open Graph and Twitter meta tags.
- Added canonical and robots meta.

### Model pages

- Dynamic title: **“[Make] [Model] ([Year]) Specs & Torque”**.
- Meta description includes power, torque, weight, seat height and oil capacity.
- Added **“Also known as”** aliases (Fireblade, Busa, CP2, etc.).
- Added an H2 **Specifications** section.
- Added a **Frequently Asked Questions** section generated from real data:
  - power, torque, seat height, weight, oil capacity/grade, top speed, fuel capacity
- Added `FAQPage`, `Motorcycle` and `BreadcrumbList` structured data.
- Added **Related Guides** links based on category.
- Added canonical, Open Graph and Twitter meta.

### Guide pages

22 static, indexable HTML pages were added under `guides/`. They contain real HTML content instead of client-rendered placeholders:

- Oil capacity chart
- Seat height chart
- Weight chart
- Horsepower chart
- Torque specifications
- Best beginner motorcycles
- A2 motorcycles
- Best 125cc motorcycles
- Best scooters
- Best adventure motorcycles
- Best cruiser motorcycles
- Best electric motorcycles
- Best commuter motorcycles
- Best retro motorcycles
- Low seat height motorcycles
- Six model comparisons

Each guide includes:

- Unique title and meta description
- Canonical URL
- `Article` and `BreadcrumbList` JSON-LD
- Real tables with internal links to model pages
- Related guide links
- Mobile-friendly layout

### Technical SEO

- `sitemap.xml` now includes all models, reference pages, guides and the homepage.
- `robots.txt` points to the sitemap.
- `search.html` is `noindex,follow` to avoid indexing thin search-result pages.
- Guide pages are static HTML so they do not depend on JavaScript rendering.
- Internal links from guides and model pages help crawlers discover the catalogue.

---

## Internal linking strategy

- **Homepage → guides** via “Popular guides”.
- **Model pages → guides** via “Related Guides”.
- **Guides → model pages** through every table row.
- **Guides → other guides** via “Related guides”.
- **Header → Guides** via the main navigation.
- **Footer** carries the site-wide data disclaimer.

Future links to add:

- Category hub links from every model page (e.g. “More adventure bikes”).
- “Compare with…” links between popular models.
- Guide links from the reference pages.

---

## Content gaps and next phase

These are high-demand areas that need reliable data before publishing:

### 1. Price and mileage

Queries such as `cbr600rr price in india`, `classic 350 mileage` and `ninja 400 on road price` are extremely common. Prices and fuel economy are market-specific and change frequently.

Recommendation: add price and mileage only with a **market, currency and source date** for each value. Do not publish one global price.

### 2. Top speed and 0–60 / quarter-mile

`cbr600rr top speed` is a major query. We have top speed for only a few models and no 0–60 or quarter-mile data.

Recommendation: add top speed only from manufacturer or verified test data; add 0–60 and quarter-mile only with a cited test source.

### 3. Reliability and common problems

`motorcycle reliability by brand` and `common motorcycle problems` are large clusters, but they require sourced, model-specific evidence.

Recommendation: publish brand-level reliability pages only when supported by recall data, owner surveys or documented failure patterns. Avoid generic listicles.

### 4. More comparisons

The six comparison pages should be expanded to the top 20–30 head-to-head queries, for example:

- `cbr650r vs ninja 650`
- `mt 07 vs sv650`
- `classic 350 vs meteor 350`
- `himalayan 450 vs scram 411`
- `g310r vs duke 390`
- `trident 660 vs mt 07`

### 5. Service-procedure pages

Queries like `motorcycle chain slack`, `valve clearance` and `fork seal replacement` are informational. A guide explaining the procedure, tools and typical intervals would complement the model data.

### 6. Static model pages

Model pages are currently client-rendered. Google can render JavaScript, but static HTML would be more robust. If Search Console shows indexing or rendering problems, generate `motorcycle/<id>.html` pages from the same data and link to them as canonical.

---

## Measurement

Track in Google Search Console:

- Indexed pages and coverage errors
- Queries and impressions by cluster
- Click-through rate for model vs guide pages
- Core Web Vitals
- Top landing pages

Priority KPIs:

1. Model pages indexed and ranking for `[model] specs`, `[model] top speed`, `[model] seat height`, `[model] weight`.
2. Guide pages ranking for `motorcycle oil capacity chart`, `seat height chart`, `best beginner motorcycle`, `a2 motorcycles`.
3. Comparison pages ranking for `[model A] vs [model B]`.
4. Internal click-through from guides to model pages.

---

## Editorial rules

- Do not invent specifications. Omit a field rather than fill it with a generic value.
- Keep model-year and market context visible.
- Use “manufacturer-claimed” language for power, torque, weight and top speed.
- Torque and service values must include a verification note.
- Buying guides must state their criteria and avoid pretending to be subjective road tests.
- Every new page needs a unique title, description, H1 and internal links.

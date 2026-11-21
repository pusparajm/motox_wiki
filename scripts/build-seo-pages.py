#!/usr/bin/env python3
"""Generate static, indexable SEO guide pages and the sitemap.

The public browse and model pages are client-rendered. These static guide
pages give search engines real HTML content and internal links to the
catalogue, while targeting the search clusters found in Google Autocomplete:
model specs, oil capacity, seat height, weight, horsepower, torque,
A2/beginner/125cc/scooter/adventure/cruiser buying guides, low-seat bikes and
popular model comparisons.
"""
from __future__ import annotations

import html
import json
import os
import re
from urllib.parse import quote

from search_aliases import aliases_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
GUIDES = os.path.join(ROOT, "guides")
REFERENCE = os.path.join(ROOT, "reference")
MODELS = os.path.join(ROOT, "motorcycle")
SITE = "https://motoxref.com"
LAST_MOD = "2026-11-22"


def read_json(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


SETTINGS = read_json("settings.json", {})
OPTIONS = SETTINGS.get("options") or {}
FEATURES = OPTIONS.get("features") or {}
FAQ_OPTIONS = OPTIONS.get("faq") or {}
IMAGE_OPTIONS = OPTIONS.get("images") or {}
THIRD_PARTY = SETTINGS.get("third_party") or {}
REFERENCE_OVERRIDES = read_json("reference-pages.json", {}).get("pages", {})
REFERENCE_PAGE_META = {}
ADS_ENABLED = (SETTINGS.get("ads") or {}).get("enabled", True)

ADSENSE_HEAD = """  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3716738858398465"
     crossorigin="anonymous"></script>""" if ADS_ENABLED else ""


def load_bike_images():
    path = os.path.join(DATA, "bike-images.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("images", {})


BIKE_IMAGES = load_bike_images()
BRAKE_INTERCHANGE = read_json("brake-interchange.json", {})
SBS_INTERCHANGE = {}
for _ebc, _item in BRAKE_INTERCHANGE.items():
    for _code in _item.get("sbs") or []:
        for _part in re.split(r"[/,]", str(_code)):
            _base = re.sub(r"[^0-9]", "", _part)
            if _base:
                SBS_INTERCHANGE.setdefault(_base, []).append(_item)


def esc(value):
    return html.escape(str(value or ""), quote=True)


def load():
    with open(os.path.join(DATA, "motorcycles.json"), encoding="utf-8") as fh:
        bikes = [b for b in json.load(fh)["motorcycles"] if b.get("published") is not False]
    with open(os.path.join(DATA, "pages.json"), encoding="utf-8") as fh:
        pages = [p for p in json.load(fh)["pages"] if p.get("published") is not False]
    return bikes, pages


def field(bike, key):
    section = (bike.get("sections") or {}).get("general_specs") or {}
    for item in section.get("fields") or []:
        if item.get("key") == key:
            return item.get("value", "")
    return ""


def service(bike, key):
    section = (bike.get("sections") or {}).get("service") or {}
    for item in section.get("fields") or []:
        if item.get("key") == key:
            return item.get("value", "")
    return ""


def brake_shape_crossref_html(front, rear):
    lines = []
    for label, value in (("Front", front), ("Rear", rear)):
        if not value:
            continue
        matches = []
        seen = set()
        for match in re.finditer(r"SBS\s+([0-9/]+)", str(value), re.I):
            for part in match.group(1).split("/"):
                base = re.sub(r"[^0-9]", "", part)
                for item in SBS_INTERCHANGE.get(base, []):
                    ebc = item.get("ebc") or ""
                    if ebc and ebc not in seen:
                        seen.add(ebc)
                        matches.append(item)
        if not matches:
            continue
        pieces = []
        for item in matches[:2]:
            piece = f"EBC {esc(item.get('ebc', ''))}"
            for key, brand in (("ferodo", "Ferodo"), ("dunlopad", "Dunlopad"), ("vesrah", "Vesrah")):
                values = [str(entry) for entry in item.get(key) or [] if entry]
                if values:
                    piece += f" · {brand} {esc(' / '.join(values[:3]))}"
            pieces.append(piece)
        lines.append(f"<strong>{label} {esc(value)}:</strong> {' · '.join(pieces)}")
    if not lines:
        return ""
    return (
        '<p class="data-note"><strong>Shape-family cross-reference:</strong> '
        + "<br>".join(lines)
        + ". Cross-reference values describe the backing-plate shape family; "
        "confirm the compound and exact model year before ordering.</p>"
    )


def battery_value(bike):
    return service(bike, "battery") or service(bike, "battery_rating")


def numeric(value):
    if not value:
        return 0.0
    found = re.sub(r"[^0-9.]", "", str(value).split("(")[0].split("@")[0])
    try:
        return float(found)
    except ValueError:
        return 0.0


def hp(bike):
    return numeric(field(bike, "power"))


def kw(bike):
    return hp(bike) * 0.7457


def weight(bike):
    return numeric(field(bike, "weight"))


def seat(bike):
    return numeric(field(bike, "seat_height"))


def displacement(bike):
    return numeric(bike.get("displacement") or field(bike, "displacement"))


def name(bike):
    make = str(bike.get("make") or "").strip()
    model = str(bike.get("model") or "").strip()
    if not model:
        return f"{make} Brake Pad Fitment".strip()
    return f"{make} {model}".strip()


def title(bike):
    return f"{name(bike)} ({bike.get('year', '')})"


def bike_url(bike):
    return f"../motorcycle/{quote(bike['id'])}.html"


def bike_link(bike):
    return f'<a href="{bike_url(bike)}">{esc(title(bike))}</a>'


def spec_strip(bike):
    bits = [bike.get("category", ""), bike.get("displacement", "")]
    if hp(bike):
        bits.append(field(bike, "power").split("@")[0].strip())
    if weight(bike):
        bits.append(field(bike, "weight"))
    return " · ".join(bit for bit in bits if bit)


def table(headers, rows):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell if str(cell).strip() else '—'}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f'<div class="spec-table-wrap"><table class="spec-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def related_guides(links):
    return '<h2>Related guides</h2><ul>' + "".join(
        f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in links
    ) + "</ul>"


def guide_page(slug, page_title, description, h1, subtitle, content, breadcrumb, extra_json=None, parents=None):
    canonical = f"{SITE}/guides/{slug}.html" if slug != "index" else f"{SITE}/guides/"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": h1,
        "description": description,
        "url": canonical,
        "dateModified": LAST_MOD,
        "author": {"@type": "Organization", "name": "MotoX Wiki", "url": SITE},
        "publisher": {"@type": "Organization", "name": "MotoX Wiki", "url": SITE}
    }
    breadcrumb_items = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
    ]
    for label, href in parents or []:
        breadcrumb_items.append({
            "@type": "ListItem",
            "position": len(breadcrumb_items) + 1,
            "name": label,
            "item": href if str(href).startswith("http") else f"{SITE}/guides/{href}",
        })
    breadcrumb_items.append({
        "@type": "ListItem",
        "position": len(breadcrumb_items) + 1,
        "name": h1,
        "item": canonical,
    })
    graph = [jsonld, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumb_items
    }]
    if extra_json:
        graph.extend(extra_json)
    template = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{esc(page_title)} | MotoX Wiki</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="MotoX Wiki">
  <meta property="og:title" content="{esc(page_title)} | MotoX Wiki">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(page_title)} | MotoX Wiki">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="theme-color" content="#c2410c">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/site.min.css?v=10" id="mx-main-css" data-mx-shield-css="../css/main.css?v=39" fetchpriority="high">
  <script type="application/ld+json">{json.dumps(graph, ensure_ascii=False)}</script>
  {ADSENSE_HEAD}
</head>
<body>
  <header class="site-header static-header">
    <div class="container">
      <div class="header-row">
        <a class="brand" href="../index.html"><span class="brand-icon">⚙</span><span>MotoX Wiki</span></a>
      </div>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="index.html" class="active">Guides</a>
        <a href="../pages.html">Reference</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <div class="bike-header">
      <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="index.html">Guides</a>{''.join(f' / <a href="{href}">{esc(label)}</a>' for label, href in (parents or []))} / {esc(breadcrumb)}</div>
      <h1>{h1}</h1>
      <p class="bike-subtitle">{subtitle}</p>
    </div>
    <article class="page-content article-content">
      {content}
    </article>
    <p class="data-note">Specifications are manufacturer-claimed and can vary by model year and market. Confirm service limits and torque values against your owner's or workshop manual. Data updated {LAST_MOD}.</p>
  </main>

  <footer class="site-footer">
    <div class="container site-footer-inner">
      <span class="footer-text">© 2026 MotoX Wiki. Community-maintained motorcycle technical reference.</span>
    </div>
  </footer>
</body>
</html>
"""
    path = os.path.join(GUIDES, "index.html" if slug == "index" else f"{slug}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(template)
    return canonical


def reference_group(slug):
    if slug.startswith("brand-"):
        return "Brand hub"
    if slug in {
        "all-models", "brands", "battery-finder", "brake-pad-fitment",
        "pad-shape-cross-reference", "tyre-size-finder", "fork-seal-finder",
    }:
        return "Reference tool"
    return "Reference"


def reference_page(slug, page_title, description, h1, subtitle, content, breadcrumb, extra_json=None):
    override = REFERENCE_OVERRIDES.get(slug) or {}
    page_title = override.get("title") or page_title
    description = override.get("description") or description
    h1 = override.get("h1") or h1
    subtitle = override.get("subtitle") or subtitle
    breadcrumb = override.get("breadcrumb") or breadcrumb
    content = f"{override.get('intro') or ''}{content}{override.get('footer') or ''}"
    REFERENCE_PAGE_META[slug] = {
        "slug": slug,
        "title": page_title,
        "description": description,
        "h1": h1,
        "subtitle": subtitle,
        "group": reference_group(slug),
        "hasOverride": bool(override),
        "path": f"reference/{slug}.html",
    }
    canonical = f"{SITE}/reference/{slug}.html"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": h1,
        "description": description,
        "url": canonical,
        "dateModified": LAST_MOD,
        "author": {"@type": "Organization", "name": "MotoX Wiki", "url": SITE},
        "publisher": {"@type": "Organization", "name": "MotoX Wiki", "url": SITE}
    }
    graph = [jsonld, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Reference", "item": SITE + "/pages.html"},
            {"@type": "ListItem", "position": 3, "name": h1, "item": canonical}
        ]
    }]
    if extra_json:
        graph.extend(extra_json)
    template = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{esc(page_title)} | MotoX Wiki</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="MotoX Wiki">
  <meta property="og:title" content="{esc(page_title)} | MotoX Wiki">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(page_title)} | MotoX Wiki">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="theme-color" content="#c2410c">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/site.min.css?v=10" id="mx-main-css" data-mx-shield-css="../css/main.css?v=39" fetchpriority="high">
  <script type="application/ld+json">{json.dumps(graph, ensure_ascii=False)}</script>
  {ADSENSE_HEAD}
</head>
<body>
  <header class="site-header static-header">
    <div class="container">
      <div class="header-row">
        <a class="brand" href="../index.html"><span class="brand-icon">⚙</span><span>MotoX Wiki</span></a>
      </div>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="../guides/index.html">Guides</a>
        <a href="../pages.html" class="active">Reference</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <div class="bike-header">
      <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="../pages.html">Reference</a> / {esc(breadcrumb)}</div>
      <h1>{h1}</h1>
      <p class="bike-subtitle">{subtitle}</p>
    </div>
    <article class="page-content article-content">
      {content}
    </article>
    <p class="data-note">Specifications and part references can vary by model year and market. Confirm the exact part against your machine before ordering. Data updated {LAST_MOD}.</p>
  </main>

  <footer class="site-footer">
    <div class="container site-footer-inner">
      <span class="footer-text">© 2026 MotoX Wiki. Community-maintained motorcycle technical reference.</span>
    </div>
  </footer>
</body>
</html>
"""
    os.makedirs(REFERENCE, exist_ok=True)
    path = os.path.join(REFERENCE, f"{slug}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(template)
    return canonical


def build_index(bikes):
    cards = [
        ("oil-capacity-chart", "Motorcycle Oil Capacity Chart", "Engine oil capacity and oil grade for every model with verified service data."),
        ("seat-height-chart", "Motorcycle Seat Height Chart", "Seat heights across the catalogue, including a low-seat section for shorter riders."),
        ("weight-chart", "Motorcycle Weight Chart", "Kerb weights across every model, useful for A2, garage and touring decisions."),
        ("horsepower-chart", "Motorcycle Horsepower Chart", "Power and torque figures sorted from highest to lowest."),
        ("torque-specs", "Motorcycle Torque Specifications", "Fastener torque tables and links to model-specific torque data."),
        ("parts-fitment-codes", "Motorcycle Parts & Fitment Codes", "Spark plug, battery, brake pad, wheel bearing, steering head bearing and fork seal codes by model."),
        ("best-beginner-motorcycles", "Best Beginner Motorcycles", "A data-driven shortlist based on power, seat height and weight."),
        ("a2-motorcycles", "A2 Motorcycles", "Motorcycles within the 35 kW / 0.2 kW-per-kg A2 envelope."),
        ("best-125cc-motorcycles", "Best 125cc Motorcycles", "125–155 cc commuters, sportbikes and mini-bikes."),
        ("best-scooters", "Best Scooters", "Every scooter in the catalogue, from 110 cc commuters to 560 cc maxi-scooters."),
        ("best-adventure-motorcycles", "Best Adventure Motorcycles", "Adventure and dual-sport models by engine size and weight."),
        ("best-cruiser-motorcycles", "Best Cruiser Motorcycles", "Cruisers and baggers from Harley-Davidson, Indian, Royal Enfield, Honda and more."),
        ("best-electric-motorcycles", "Best Electric Motorcycles", "Electric sport, commuter and off-road models."),
        ("low-seat-height-motorcycles", "Low Seat Height Motorcycles", "Bikes with a seat height of 800 mm or less, for shorter riders."),
        ("best-commuter-motorcycles", "Best Commuter Motorcycles", "Practical, economical bikes for daily transport."),
        ("best-retro-motorcycles", "Best Retro Motorcycles", "Modern classics, retro roadsters and scramblers."),
    ]
    items = "".join(f'<a class="page-item" href="{slug}.html"><h2>{esc(t)}</h2><p>{esc(d)}</p></a>' for slug, t, d in cards)
    segment_cards = "".join(
        f'<a class="page-item" href="{item["slug"]}.html"><h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p></a>'
        for item in SEGMENT_COMPARISONS
    )
    pair_groups = {}
    for item in COMPARISONS:
        pair_groups.setdefault(item["group"], []).append(item)
    pair_sections = []
    for group, group_items in pair_groups.items():
        cards_html = "".join(
            f'<a class="page-item" href="{item["slug"]}.html"><h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p></a>'
            for item in group_items
        )
        pair_sections.append(f'<h4>{esc(group)}</h4><div class="page-list">{cards_html}</div>')
    content = f"""
      <p>These guides turn the MotoX Wiki catalogue into practical answers: oil capacities, seat heights, weights, horsepower, torque data, buying shortlists and direct model comparisons.</p>
      <p>Brand hubs, the all-model index, brake fitment and parts finders are in the <a href="../pages.html">Reference section</a>.</p>
      <div class="page-list">{items}</div>
      <h2>Motorcycle comparisons</h2>
      <p><a href="comparisons.html">Comparison hub</a> · {len(SEGMENT_COMPARISONS)} segment comparisons · {len(COMPARISONS)} head-to-head comparisons.</p>
      <h3>Segment comparisons</h3>
      <div class="page-list">{segment_cards}</div>
      <h3>Head-to-head comparisons</h3>
      {''.join(pair_sections)}
    """
    return guide_page(
        "index", "Motorcycle Specs Guides, Charts & Comparisons",
        "Motorcycle oil capacity charts, seat height charts, weight and horsepower lists, A2 and beginner guides, and model comparisons.",
        "Motorcycle Guides, Charts & Comparisons",
        f"Data-driven guides built from {len(bikes)} motorcycle specifications.",
        content, "All guides"
    )


def build_oil_chart(bikes):
    rows = []
    for bike in sorted(bikes, key=name):
        capacity = service(bike, "oil_capacity")
        if not capacity:
            continue
        rows.append([bike_link(bike), esc(bike.get("displacement", "")), esc(capacity), esc(service(bike, "oil_grade"))])
    content = f"""
      <p>This chart lists published engine-oil capacities and recommended oil grades for {len(rows)} motorcycles. Oil capacity is shown with a filter change where specified; always confirm the exact fill procedure in the workshop manual.</p>
      {table(["Model", "Displacement", "Oil capacity", "Oil grade"], rows)}
      <h2>How to use the chart</h2>
      <ul>
        <li>Use the model link to see the full service data, torque values and specifications.</li>
        <li>Do not mix oil grades blindly. JASO MA/MA2 is for wet-clutch motorcycles; JASO MB is for many scooters.</li>
        <li>Fill to the level specified in the manual, not only to the nominal capacity.</li>
      </ul>
      {related_guides([("torque-specs.html", "Motorcycle torque specifications"), ("seat-height-chart.html", "Motorcycle seat height chart"), ("best-beginner-motorcycles.html", "Best beginner motorcycles")])}
    """
    return guide_page(
        "oil-capacity-chart", "Motorcycle Oil Capacity Chart",
        f"Engine oil capacity and oil grade for {len(rows)} motorcycles, including CBR, MT, Ninja, Royal Enfield, KTM and scooter models.",
        "Motorcycle Oil Capacity Chart",
        f"Oil capacities and grades for {len(rows)} models.",
        content, "Oil Capacity Chart"
    )


def build_seat_chart(bikes):
    rows = []
    for bike in sorted([b for b in bikes if seat(b)], key=lambda b: (seat(b), name(b))):
        rows.append([bike_link(bike), esc(field(bike, "seat_height")), esc(field(bike, "weight")), esc(field(bike, "power")), esc(bike.get("category", ""))])
    content = f"""
      <p>Seat height is one of the most searched motorcycle specifications. This chart lists {len(rows)} models sorted from lowest to highest seat height so you can compare bikes for inseam, confidence and stop-start traffic.</p>
      <h2>Low-seat motorcycles for shorter riders</h2>
      <p>Bikes under 800 mm are generally easier to flat-foot for riders around 5'2\"–5'6\". The model pages list kerb weight, power and service data as well.</p>
      {table(["Model", "Seat height", "Kerb weight", "Power", "Category"], rows)}
      {related_guides([("low-seat-height-motorcycles.html", "Low seat height motorcycles"), ("best-beginner-motorcycles.html", "Best beginner motorcycles"), ("weight-chart.html", "Motorcycle weight chart")])}
    """
    return guide_page(
        "seat-height-chart", "Motorcycle Seat Height Chart",
        f"Seat heights for {len(rows)} motorcycles sorted from low to high, including low-seat bikes for short riders.",
        "Motorcycle Seat Height Chart",
        f"{len(rows)} models sorted by seat height.",
        content, "Seat Height Chart"
    )


def build_weight_chart(bikes):
    rows = []
    for bike in sorted([b for b in bikes if weight(b)], key=lambda b: (weight(b), name(b))):
        rows.append([bike_link(bike), esc(field(bike, "weight")), esc(field(bike, "power")), esc(field(bike, "seat_height")), esc(bike.get("category", ""))])
    content = f"""
      <p>Kerb weight affects low-speed confidence, A2 power-to-weight calculations, garage space and touring load. This chart sorts {len(rows)} models from lightest to heaviest.</p>
      {table(["Model", "Kerb weight", "Power", "Seat height", "Category"], rows)}
      {related_guides([("horsepower-chart.html", "Motorcycle horsepower chart"), ("seat-height-chart.html", "Motorcycle seat height chart"), ("a2-motorcycles.html", "A2 motorcycles")])}
    """
    return guide_page(
        "weight-chart", "Motorcycle Weight Chart",
        f"Kerb weights for {len(rows)} motorcycles sorted from lightest to heaviest.",
        "Motorcycle Weight Chart",
        f"{len(rows)} models sorted by kerb weight.",
        content, "Weight Chart"
    )


def build_hp_chart(bikes):
    rows = []
    for bike in sorted([b for b in bikes if hp(b)], key=lambda b: (-hp(b), name(b))):
        rows.append([bike_link(bike), esc(field(bike, "power")), esc(field(bike, "torque")), esc(field(bike, "weight")), esc(bike.get("category", ""))])
    content = f"""
      <p>This horsepower chart lists {len(rows)} motorcycles by manufacturer-claimed peak power, with torque and kerb weight for context. Power figures are not directly comparable across markets or dyno types, but they are useful for shortlisting.</p>
      {table(["Model", "Max power", "Max torque", "Kerb weight", "Category"], rows)}
      {related_guides([("weight-chart.html", "Motorcycle weight chart"), ("a2-motorcycles.html", "A2 motorcycles"), ("best-beginner-motorcycles.html", "Best beginner motorcycles")])}
    """
    return guide_page(
        "horsepower-chart", "Motorcycle Horsepower Chart",
        f"Motorcycle horsepower and torque figures for {len(rows)} models, sorted from highest to lowest.",
        "Motorcycle Horsepower Chart",
        f"{len(rows)} models sorted by peak power.",
        content, "Horsepower Chart"
    )


def build_torque_page(bikes):
    rows = []
    for bike in sorted(bikes, key=name):
        section = (bike.get("sections") or {}).get("torque_specs") or {}
        note = next((f.get("value", "") for f in section.get("fields") or [] if f.get("key") == "note"), "")
        if "not yet available" in note:
            continue
        count = len(section.get("table") or [])
        if not count:
            continue
        rows.append([bike_link(bike), esc(bike.get("category", "")), str(count), esc(bike.get("displacement", ""))])
    content = f"""
      <p>Motorcycle “torque specs” can mean two different things: engine torque (the performance figure) and fastener torque (the tightening value for bolts and nuts). This page is about the second: service-manual torque values for axles, brakes, engine covers and other fasteners.</p>
      <h2>Model-specific torque tables</h2>
      <p>The catalogue currently has researched fastener tables for {len(rows)} models. Each model page shows the components, torque values and a verification note.</p>
      {table(["Model", "Category", "Table rows", "Displacement"], rows)}
      <h2>General fastener reference</h2>
      <p>If a model is not listed above, its page still shows a single-value general fastener reference. For safety-critical fasteners, always use the official workshop manual and the specified tightening sequence.</p>
      {related_guides([("oil-capacity-chart.html", "Motorcycle oil capacity chart"), ("seat-height-chart.html", "Seat height chart"), ("best-beginner-motorcycles.html", "Best beginner motorcycles")])}
    """
    return guide_page(
        "torque-specs", "Motorcycle Torque Specifications",
        f"Fastener torque tables for {len(rows)} motorcycles, plus links to model-specific torque specs.",
        "Motorcycle Torque Specifications",
        f"Fastener torque data for {len(rows)} models.",
        content, "Torque Specifications"
    )


def build_parts_fitment(bikes):
    brake_rows = []
    bearing_rows = []
    for bike in sorted(bikes, key=name):
        if bike.get("fitment_only"):
            continue
        spark = service(bike, "spark_plug")
        front = service(bike, "front_brake_pads")
        rear = service(bike, "rear_brake_pads")
        if spark or front or rear:
            brake_rows.append([bike_link(bike), esc(spark), esc(front), esc(rear)])
        front_bearing = service(bike, "front_wheel_bearings")
        rear_bearing = service(bike, "rear_wheel_bearings")
        steering = service(bike, "steering_head_bearings")
        fork = service(bike, "fork_seal")
        if front_bearing or rear_bearing or steering or fork:
            bearing_rows.append([
                bike_link(bike), esc(front_bearing), esc(rear_bearing),
                esc(steering), esc(fork)
            ])
    content = f"""
      <p>Part numbers are not universal. A pad or bearing that fits one model year can miss the next, and ABS, market and mid-year running changes all matter. This page collects the spark plug, brake pad, wheel bearing, steering head bearing and fork seal codes we have been able to verify for individual models.</p>
      <p>Where a cell is blank, we have not confirmed a code for that model. A blank is deliberate: it is better than a plausible-looking guess.</p>
      <p>For model-by-model brake pad fitment and the cross-brand pad shape reference, see the <a href="../reference/brake-pad-fitment.html">brake pad fitment table</a> and <a href="../reference/pad-shape-cross-reference.html">pad shape cross-reference</a>.</p>
      <h2>Brake pad and spark plug codes</h2>
      <p>The table lists the codes shown on each model page. Brake-pad entries combine the shape references recorded for each model; spark plug codes are shown where a verified plug is listed. Treat the codes as shape references, not as a guarantee that every compound or model year uses the same part.</p>
      <p>Where a brake-pad entry contains several numbers separated by slashes, those are shape references for the same backing plate. Pick the compound for your riding and confirm the seller's fitment data for your exact model year.</p>
      {table(["Model", "Spark plug", "Front brake pads", "Rear brake pads"], brake_rows)}
      <h2>Wheel bearing, steering head and fork seal codes</h2>
      <p>Bearing kit numbers are shown where fitment is confirmed. A kit number is not a bearing dimension: it identifies a set of bearings and seals. Fork seal sizes are oil-seal dimensions in millimetres (inner diameter × outer diameter × thickness).</p>
      {table(["Model", "Front wheel bearings", "Rear wheel bearings", "Steering head bearings", "Fork seal"], bearing_rows)}
      <h2>What the codes mean</h2>
      {table(["Code", "What it identifies", "Notes"], [
        ["EBC FA252 / FA252HH", "EBC brake pad shape", "The number identifies the backing-plate shape; letters such as HH denote the compound."],
        ["SBS 634HS", "SBS brake pad shape", "The base number identifies the shape; HS/LS and similar suffixes identify the compound."],
        ["Vesrah VD-274", "Vesrah brake pad shape", "Vesrah uses its own shape numbers; confirm the compound suffix for your application."],
        ["Brembo 07YA23", "Brembo brake pad code", "Brembo may add a compound suffix such as .SA or .LA. One blister normally does one caliper."],
        ["All Balls 25-1659", "Wheel bearing kit", "25-xxxx is a wheel bearing kit; confirm front or rear fitment."],
        ["Pivot Works PWRWS-H68-000", "Wheel bearing kit", "Pivot Works is part of the All Balls Racing group; the PW prefix identifies a Pivot Works kit."],
        ["All Balls 22-1004", "Steering head bearing kit", "22-xxxx is a steering bearing kit, usually supplied with seals."],
        ["41 × 53 × 8/10.5 mm", "Fork oil seal", "Inner diameter × outer diameter × thickness. The dust wiper is a separate part."],
        ["41 × 54 × 11 mm", "Fork oil seal", "Inner diameter × outer diameter × thickness. Check the fork model, not just the bike model."],
      ])}
      <h2>Cross-reference example: Yamaha MT-07</h2>
      <p>The MT-07 is the model where we have the strongest multi-brand brake cross-reference. The front caliper uses EBC FA252, SBS 634HS, Brembo 07YA23 and Vesrah VD-274; the rear uses EBC FA174, SBS 657LS, Brembo 07HO36 and Vesrah VD-163. These are shape equivalences, not identical friction compounds. Pick the compound for your riding and confirm fitment for your exact year.</p>
      {table(["Position", "EBC", "SBS", "Brembo", "Vesrah"], [
        ["Front", "FA252", "634HS", "07YA23", "VD-274"],
        ["Rear", "FA174", "657LS", "07HO36", "VD-163"],
      ])}
      <p>Bearing and seal examples: the MT-07 uses All Balls 25-1659 front, 25-1703 rear and 22-1004 steering head kits, with a 41 × 53 × 8/10.5 mm fork oil seal. The CBR600RR uses All Balls 25-1562 front, Pivot Works PWRWS-H68-000 rear and All Balls 22-1020 steering head kits, with a 41 × 54 × 11 mm fork oil seal. The Ninja 400 uses All Balls 25-1104 front and 25-1780 rear kits.</p>
      <h2>Why some models have no bearing or seal code</h2>
      <p>Bearing and seal fitment is harder to verify than a spark plug code. The same bearing bore can use different widths, seals and spacers, and fitment can change between model years and variants. We only publish a kit number or seal size when fitment is confirmed. If your bike is not in the table, measure the old bearing or seal and use the OEM part number as the primary reference.</p>
      <h2>How to verify a part for your bike</h2>
      <ol>
        <li>Identify the exact model year, market and ABS/non-ABS variant. “MT-07” alone is not enough.</li>
        <li>Look up the OEM part number on a parts fiche for your VIN or model code.</li>
        <li>Cross-check the seller's fitment data, not only the product title.</li>
        <li>For bearings and seals, measure the old part or read the marking on the bearing race.</li>
        <li>For brake pads, compare the pad shape and backing plate; a different compound code can share the same shape.</li>
        <li>Use the workshop manual for torque values, fluid volumes and bed-in procedure.</li>
      </ol>
      <p>Codes can change when a manufacturer revises a compound or kit. Treat this page as a starting point and confirm the part against your exact machine before ordering.</p>
      {related_guides([("oil-capacity-chart.html", "Motorcycle oil capacity chart"), ("torque-specs.html", "Motorcycle torque specifications"), ("seat-height-chart.html", "Motorcycle seat height chart"), ("../reference/brake-pad-fitment.html", "Brake pad fitment table"), ("../reference/battery-finder.html", "Motorcycle battery code finder"), ("../reference/pad-shape-cross-reference.html", "Brake pad shape cross-reference")])}
    """
    return guide_page(
        "parts-fitment-codes", "Motorcycle Parts & Fitment Codes",
        "Spark plug, brake pad, wheel bearing, steering head bearing and fork seal codes by model, with cross-reference guidance.",
        "Motorcycle Parts & Fitment Codes",
        "Spark plugs, brake pads, wheel bearings, steering head bearings and fork seals by model.",
        content, "Parts & Fitment Codes"
    )


def list_page(slug, page_title, description, h1, subtitle, intro, bikes, sort_key, columns, breadcrumb, extra_links=None):
    rows = []
    for bike in sorted(bikes, key=sort_key):
        row = [bike_link(bike)] + [fn(bike) for _, fn in columns]
        rows.append(row)
    content = f"""
      <p>{intro}</p>
      <p>{len(rows)} models match this list. Specifications are manufacturer-claimed; use the linked model pages for service data and torque values.</p>
      {table(["Model"] + [h for h, _ in columns], rows)}
      {related_guides(extra_links or [("best-beginner-motorcycles.html", "Best beginner motorcycles"), ("a2-motorcycles.html", "A2 motorcycles"), ("seat-height-chart.html", "Seat height chart")])}
    """
    return guide_page(slug, page_title, description, h1, subtitle, content, breadcrumb)


def brake_crossref_tables(bikes):
    with open(os.path.join(DATA, "brake-crossref.json"), encoding="utf-8") as fh:
        crossref = json.load(fh)
    with open(os.path.join(DATA, "brake-interchange.json"), encoding="utf-8") as fh:
        interchange = json.load(fh)

    by_id = {b["id"]: b for b in bikes}
    model_rows = []
    for mid, pads in crossref.items():
        bike = by_id.get(mid)
        if not bike or bike.get("fitment_only"):
            continue
        front = pads.get("front_brake_pads", "") or service(bike, "front_brake_pads")
        rear = pads.get("rear_brake_pads", "") or service(bike, "rear_brake_pads")
        if not front and not rear:
            continue
        model_rows.append([bike_link(bike), esc(front), esc(rear)])
    model_rows.sort(key=lambda row: row[0].lower())

    def ebc_key(item):
        code = item[0]
        m = re.match(r"^(FA|SFA|EPFA|GPFAX|MXS|SXR)(\d+)", code)
        if not m:
            return (99, 9999, code)
        prefix_order = {"FA": 0, "SFA": 1, "EPFA": 2, "GPFAX": 3, "MXS": 4, "SXR": 5}
        return (prefix_order.get(m.group(1), 9), int(m.group(2)), code)

    shape_rows = []
    for ebc, item in sorted(interchange.items(), key=ebc_key):
        shape_rows.append([
            esc(ebc),
            esc(", ".join(item.get("sbs", []))),
            esc(", ".join(item.get("ferodo", []))),
            esc(", ".join(item.get("dunlopad", []))),
            esc(", ".join(item.get("emgo_s", []))),
            esc(", ".join(item.get("emgo_fm", []))),
            esc(", ".join(item.get("vesrah", []))),
        ])
    return model_rows, shape_rows


def build_brake_fitment(bikes):
    model_rows, _ = brake_crossref_tables(bikes)
    content = f"""
      <p>This table lists the front and rear brake-pad shapes recorded for individual MotoX Wiki models. The pad code identifies the backing-plate shape; suffixes such as HH, HS or LS identify the friction compound.</p>
      <p>{len(model_rows)} models currently have a verified front or rear fitment entry. Several models can share one shape, so the same code may appear on more than one row.</p>
      <p>For the cross-brand equivalents of each shape, use the <a href="pad-shape-cross-reference.html">pad shape cross-reference</a>.</p>

      <h2 id="model-fitments">Motorcycle fitment table</h2>
      {table(["Model", "Front brake pads", "Rear brake pads"], model_rows)}

      <h2>How to use the table</h2>
      <ul>
        <li>Match the exact model year, market and ABS or non-ABS variant.</li>
        <li>A pad code identifies a shape, not a compound. Check the suffix before ordering.</li>
        <li>Use the model link for full specifications and service data.</li>
        <li>Confirm the seller's fitment data or the OEM parts fiche for your exact machine.</li>
      </ul>

      <h2>Related reference</h2>
      <ul>
        <li><a href="pad-shape-cross-reference.html">Brake pad shape cross-reference</a></li>
        <li><a href="../guides/parts-fitment-codes.html">Parts and fitment codes by model</a></li>
        <li><a href="../pages.html">All reference pages</a></li>
      </ul>
    """
    return reference_page(
        "brake-pad-fitment",
        "Motorcycle Brake Pad Fitment Table",
        "Front and rear brake pad fitment codes for individual motorcycle models, with links to the matching pad shape cross-reference.",
        "Motorcycle Brake Pad Fitment Table",
        "Front and rear brake pad codes by motorcycle model.",
        content,
        "Brake Pad Fitment Table",
    )


def build_pad_shape_crossref(bikes):
    _, shape_rows = brake_crossref_tables(bikes)
    content = f"""
      <p>This table cross-references the brake-pad backing-plate shapes used across the catalogue. The same plate can be sold in several friction compounds, and one shape can fit several models, model years and even several brands.</p>
      <p>For the motorcycle models that use these shapes, see the <a href="brake-pad-fitment.html">brake pad fitment table</a>.</p>

      <h2 id="shape-cross-reference">Pad shape cross-reference</h2>
      <p>The table lists the EBC shape against the equivalent SBS, Ferodo, Dunlopad, Emgo and Vesrah references. A single EBC shape can list several numbers when the same backing plate is offered in different thicknesses or compounds. Treat those as shape-family references, not as “any of these will fit every model”.</p>
      {table(["EBC", "SBS", "Ferodo", "Dunlopad", "Emgo sintered", "Emgo full metal", "Vesrah"], shape_rows)}

      <h2>Why one shape fits several models</h2>
      <p>Brake calipers are often shared across a model family or even across manufacturers. A pad shape is defined by the backing-plate outline, hole spacing, thickness and locating tabs. Once a caliper is used on several bikes, the same shape appears under many model names. The friction compound is separate: a commuter may use an organic or semi-sintered pad, while a sport or race model uses a sintered or race compound in the same shape.</p>
      <p>That is why a cross-reference list can show several models from one brand against one code. The compound can still differ by model or model year, so check the suffix and the intended use before mixing a touring pad into a track application or vice versa.</p>

      <h2>Related reference</h2>
      <ul>
        <li><a href="brake-pad-fitment.html">Motorcycle brake pad fitment table</a></li>
        <li><a href="../guides/parts-fitment-codes.html">Parts and fitment codes by model</a></li>
        <li><a href="../pages.html">All reference pages</a></li>
      </ul>
    """
    return reference_page(
        "pad-shape-cross-reference",
        "Brake Pad Shape Cross-Reference",
        "Cross-compatible motorcycle brake pad shapes from EBC, SBS, Ferodo, Dunlopad, Emgo and Vesrah.",
        "Brake Pad Shape Cross-Reference",
        "EBC, SBS, Ferodo, Dunlopad, Emgo and Vesrah shape equivalents.",
        content,
        "Brake Pad Shape Cross-Reference",
    )


def build_brake_redirect():
    target = "../reference/brake-pad-fitment.html"
    template = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Brake Pad Cross-Reference — Moved | MotoX Wiki</title>
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="{SITE}/reference/brake-pad-fitment.html">
  <meta http-equiv="refresh" content="0; url={target}">
  {ADSENSE_HEAD}
</head>
<body>
  <p>This page has moved to the <a href="{target}">motorcycle brake pad fitment table</a>.</p>
</body>
</html>
"""
    with open(os.path.join(GUIDES, "brake-pad-cross-reference.html"), "w", encoding="utf-8") as fh:
        fh.write(template)


def make_slug(make):
    return re.sub(r"[^a-z0-9]+", "-", str(make).lower()).strip("-")


def sync_reference_index(bikes, pages):
    """Keep the static Reference index in sync with generated brand and reference pages."""
    path = os.path.join(ROOT, "pages.html")
    with open(path, encoding="utf-8") as fh:
        page_html = fh.read()

    makes = sorted({bike.get("make", "") for bike in bikes if bike.get("make")}, key=str.lower)
    brand_links = "\n".join(
        f'      <a href="reference/brand-{make_slug(make)}.html">{esc(make)}</a>'
        for make in makes
    )
    brand_block = (
        '    <div class="home-guide-links" aria-label="Motorcycle brands">\n'
        f'      <strong>{len(makes)} brands:</strong>\n'
        f'{brand_links}\n'
        '    </div>'
    )

    general_cards = "\n".join(
        f'      <a class="page-item" href="pages.html?slug={quote(page.get("slug") or page["id"])}">'
        f'<h2>{esc(page.get("title", ""))}</h2><p>{esc(page.get("summary", ""))}</p></a>'
        for page in sorted(pages, key=lambda item: (item.get("order", 0), item.get("title", "")))
    )

    for start, end, block, indent in (
        ("<!-- BRAND-INDEX:START -->", "<!-- BRAND-INDEX:END -->", brand_block, "    "),
        ("<!-- GENERAL-REFERENCE:START -->", "<!-- GENERAL-REFERENCE:END -->", general_cards, "      "),
    ):
        if start not in page_html or end not in page_html:
            raise SystemExit(f"Reference index markers missing: {start}")
        before, rest = page_html.split(start, 1)
        _, after = rest.split(end, 1)
        page_html = before + start + "\n" + block + "\n" + indent + end + after

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page_html)


def build_brand_pages(bikes):
    by_make = {}
    for bike in bikes:
        by_make.setdefault(bike.get("make", ""), []).append(bike)

    urls = []
    brand_links = {}
    brand_cards = []
    for make in sorted(by_make, key=str.lower):
        items = sorted(by_make[make], key=name)
        slug = make_slug(make)
        page_slug = f"brand-{slug}"
        href = f"../reference/{page_slug}.html"
        brand_links[make] = href
        rows = []
        for bike in items:
            rows.append([
                bike_link(bike),
                esc(bike.get("year", "")),
                esc(bike.get("category", "")),
                esc(bike.get("displacement", "")),
                esc(field(bike, "power")),
                esc(field(bike, "weight")),
                esc(field(bike, "seat_height")),
                esc(service(bike, "oil_capacity")),
            ])
        content = f"""
          <p>Browse every {esc(make)} model in the catalogue. Each row links to the full specification page with engine data, dimensions, service capacities, torque values and FAQs.</p>
          <p><a href="brands.html">All motorcycle brands</a> · <a href="all-models.html">All models A–Z</a> · <a href="../guides/oil-capacity-chart.html">Oil capacity chart</a> · <a href="../guides/seat-height-chart.html">Seat height chart</a></p>
          <h2>{esc(make)} models</h2>
          {table(["Model", "Year", "Category", "Engine", "Power", "Weight", "Seat", "Oil capacity"], rows)}
          <h2>Related reference</h2>
          <ul>
            <li><a href="tyre-size-finder.html">Motorcycle tyre size finder</a></li>
            <li><a href="fork-seal-finder.html">Fork seal and suspension finder</a></li>
            <li><a href="battery-finder.html">Motorcycle battery code finder</a></li>
            <li><a href="brake-pad-fitment.html">Motorcycle brake pad fitment table</a></li>
          </ul>
        """
        urls.append(reference_page(
            page_slug,
            f"{make} Motorcycles — Specs, Oil Capacity & Service Data",
            f"All {make} motorcycle models with engine specifications, power, weight, seat height and oil capacity.",
            f"{make} Motorcycles",
            f"Every {make} model in the MotoX Wiki database.",
            content,
            f"{make}",
        ))
        brand_cards.append((make, page_slug, len(items)))

    cards_html = "".join(
        f'<a class="page-item" href="{page_slug}.html"><h2>{esc(make)}</h2><p>{count} models · specs, oil capacity and service data.</p></a>'
        for make, page_slug, count in brand_cards
    )
    urls.append(reference_page(
        "brands",
        "Motorcycle Brand Directory",
        "Motorcycle manufacturers and model counts, with links to every brand hub and model specification page.",
        "Motorcycle Brand Directory",
        f"{len(brand_cards)} motorcycle manufacturers in the catalogue.",
        f"""
          <p>Choose a manufacturer to browse every model, engine specification, oil capacity and service data entry.</p>
          <p><a href="all-models.html">All models A–Z</a> · <a href="tyre-size-finder.html">Tyre size finder</a> · <a href="fork-seal-finder.html">Fork seal finder</a></p>
          <div class="page-list">{cards_html}</div>
        """,
        "Brands",
    ))

    model_groups = []
    for make in sorted(by_make, key=str.lower):
        slug = make_slug(make)
        models = "".join(
            f'<li><a href="{bike_url(bike)}">{esc(title(bike))}</a></li>'
            for bike in sorted(by_make[make], key=name)
        )
        model_groups.append(f'<h2 id="make-{slug}"><a href="brand-{slug}.html">{esc(make)}</a> <small>{len(by_make[make])} models</small></h2><ul>{models}</ul>')
    urls.append(reference_page(
        "all-models",
        "All Motorcycle Models A–Z",
        f"Complete index of {len(bikes)} motorcycle models by manufacturer, linking to specifications, oil capacity and service data.",
        "All Motorcycle Models",
        f"{len(bikes)} models from {len(by_make)} manufacturers.",
        f"""
          <p>Every published model in the catalogue, grouped by manufacturer. Use the <a href="brands.html">brand directory</a> for manufacturer hubs, or the finders for <a href="tyre-size-finder.html">tyre sizes</a> and <a href="fork-seal-finder.html">fork and shock data</a>.</p>
          {''.join(model_groups)}
        """,
        "All Models",
    ))
    return urls, brand_links


def build_tyre_finder(bikes):
    rows = []
    for bike in sorted(bikes, key=name):
        tyres = field(bike, "tyres")
        if not tyres:
            continue
        match = re.match(r"(.+?)\s+front,\s*(.+?)\s+rear", str(tyres), re.I)
        if match:
            front, rear = match.group(1).strip(), match.group(2).strip()
        else:
            front, rear = str(tyres), ""
        rows.append([bike_link(bike), esc(front), esc(rear)])
    content = f"""
      <p>Find the listed front and rear tyre sizes for {len(rows)} motorcycle models. Tyre dimensions can change by model year, market and wheel option, so confirm the size on the machine before ordering.</p>
      <p><a href="all-models.html">All models</a> · <a href="fork-seal-finder.html">Fork seal finder</a> · <a href="brake-pad-fitment.html">Brake pad fitment</a> · <a href="../guides/parts-fitment-codes.html">Parts and fitment codes</a></p>
      {table(["Model", "Front tyre", "Rear tyre"], rows)}
    """
    return reference_page(
        "tyre-size-finder",
        "Motorcycle Tyre Size Finder",
        f"Front and rear tyre sizes for {len(rows)} motorcycle models, with links to full specifications and service data.",
        "Motorcycle Tyre Size Finder",
        "Front and rear tyre sizes by model.",
        content,
        "Tyre Size Finder",
    )


def build_fork_seal_finder(bikes):
    rows = []
    for bike in sorted(bikes, key=name):
        seal = service(bike, "fork_seal")
        dust = service(bike, "fork_dust_seal")
        bushes = service(bike, "fork_slide_bushes")
        circlip = service(bike, "fork_seal_circlip")
        shock = service(bike, "rear_shock")
        if not any((seal, dust, bushes, circlip, shock)):
            continue
        rows.append([
            bike_link(bike), esc(seal), esc(dust), esc(bushes), esc(circlip), esc(shock)
        ])
    content = f"""
      <p>Fork seal, dust seal, slide-bush, circlip and rear-shock data for {len(rows)} models. Sizes are listed in millimetres. Confirm the exact fork or shock variant before ordering.</p>
      <p><a href="all-models.html">All models</a> · <a href="tyre-size-finder.html">Tyre size finder</a> · <a href="brake-pad-fitment.html">Brake pad fitment</a> · <a href="../guides/parts-fitment-codes.html">Parts and fitment codes</a></p>
      {table(["Model", "Fork oil seal", "Dust seal", "Slide bushes", "Seal circlip", "Rear shock"], rows)}
    """
    return reference_page(
        "fork-seal-finder",
        "Motorcycle Fork Seal & Rear Shock Finder",
        f"Fork oil seal, dust seal, slide bush, circlip and rear shock sizes for {len(rows)} motorcycle models.",
        "Motorcycle Fork Seal & Rear Shock Finder",
        "Fork seal, dust seal, bush and rear-shock data by model.",
        content,
        "Fork Seal & Suspension Finder",
    )


def build_battery_finder(bikes):
    rows = []
    for bike in sorted(bikes, key=name):
        code = service(bike, "battery")
        options = service(bike, "battery_options")
        rating = service(bike, "battery_rating")
        if not (code or rating):
            continue
        rows.append([
            bike_link(bike),
            esc(bike.get("year", "")),
            esc(bike.get("category", "")),
            esc(code),
            esc(options),
            esc(rating),
        ])
    content = f"""
      <p>Battery codes for {len(rows)} motorcycle models, from verified fitment data. Codes are listed only where a fitment has been confirmed for the model entry; blank cells are deliberate.</p>
      <p>Battery case dimensions, terminal layout and hold-down can differ within the same model family. Confirm the code, dimensions and polarity against the battery fitted to your machine before ordering.</p>
      <p><a href="all-models.html">All models</a> · <a href="tyre-size-finder.html">Tyre size finder</a> · <a href="fork-seal-finder.html">Fork seal finder</a> · <a href="../guides/parts-fitment-codes.html">Parts and fitment codes</a></p>
      {table(["Model", "Year", "Category", "Battery", "Options", "Rating"], rows)}
      <h2>Reading a battery code</h2>
      <p>Codes such as YTX9-BS, YTZ10S and GYZ16H identify case size, terminal layout and performance class. They are not interchangeable just because the voltage matches. A larger-capacity code may not fit the battery box, and a different terminal layout can prevent the leads from reaching.</p>
      <p>For models without a listed code, use the battery currently fitted as the primary reference, then check the owner's or workshop manual for the specified capacity and dimensions.</p>
    """
    return reference_page(
        "battery-finder",
        "Motorcycle Battery Code Finder",
        f"Battery codes for {len(rows)} motorcycle models, with alternative codes and battery ratings where verified.",
        "Motorcycle Battery Code Finder",
        f"{len(rows)} models with verified battery data.",
        content,
        "Battery Code Finder",
    )


def build_beginner(bikes):
    candidates = [
        b for b in bikes
        if hp(b) and hp(b) <= 50 and seat(b) and seat(b) <= 800 and weight(b) and weight(b) <= 200
        and (b.get("category") or "") not in ("Supersport", "Sport", "Motocross", "Enduro")
    ]
    return list_page(
        "best-beginner-motorcycles", "Best Beginner Motorcycles",
        "Data-driven beginner motorcycle shortlist based on power under 50 hp, seat height under 800 mm and kerb weight under 200 kg.",
        "Best Beginner Motorcycles",
        "A data-driven shortlist for new riders.",
        "Beginner-friendly is not a marketing label. This shortlist uses three practical filters: peak power of 50 hp or less, a seat height of 800 mm or less, and a kerb weight of 200 kg or less. It is a starting point for test rides, not a substitute for training.",
        candidates, lambda b: (hp(b), weight(b), name(b)),
        [("Power", lambda b: esc(field(b, "power"))), ("Kerb weight", lambda b: esc(field(b, "weight"))), ("Seat height", lambda b: esc(field(b, "seat_height"))), ("Category", lambda b: esc(b.get("category", "")))],
        "Best Beginner Motorcycles"
    )


def build_a2(bikes):
    candidates = [
        b for b in bikes
        if hp(b) and hp(b) <= 47 and weight(b) and (kw(b) / weight(b)) <= 0.2
    ]
    return list_page(
        "a2-motorcycles", "A2 Motorcycles",
        "Motorcycles within the A2 licence envelope: 35 kW / 47 hp or less and no more than 0.2 kW per kg.",
        "A2 Motorcycles",
        "35 kW / 47 hp bikes with an A2-friendly power-to-weight ratio.",
        "A2 rules limit power to 35 kW (47 hp) and power-to-weight to 0.2 kW per kg, and the bike must not be derived from a machine above 70 kW. This list filters the catalogue by claimed power and kerb weight; always check the exact model-year A2 approval for your market.",
        candidates, lambda b: (hp(b), weight(b), name(b)),
        [("Power", lambda b: esc(field(b, "power"))), ("Power-to-weight", lambda b: f"{kw(b)/weight(b):.2f} kW/kg"), ("Kerb weight", lambda b: esc(field(b, "weight"))), ("Seat height", lambda b: esc(field(b, "seat_height")))],
        "A2 Motorcycles"
    )


def build_125(bikes):
    candidates = [b for b in bikes if not b.get("fitment_only") and displacement(b) and displacement(b) <= 155]
    return list_page(
        "best-125cc-motorcycles", "Best 125cc Motorcycles",
        "125–155 cc commuters, sportbikes, mini-bikes and scooters with specifications and links.",
        "Best 125cc Motorcycles",
        "125–155 cc models from the catalogue.",
        "The 125 cc class covers commuters, mini-bikes, learner sportbikes and scooters. This page groups every 125–155 cc model in the catalogue so you can compare power, weight, seat height and service data.",
        candidates, lambda b: (hp(b), name(b)),
        [("Power", lambda b: esc(field(b, "power"))), ("Weight", lambda b: esc(field(b, "weight"))), ("Seat height", lambda b: esc(field(b, "seat_height"))), ("Category", lambda b: esc(b.get("category", "")))],
        "Best 125cc Motorcycles"
    )


def category_page(slug, page_title, description, h1, subtitle, intro, category, breadcrumb):
    candidates = [b for b in bikes if not b.get("fitment_only") and (b.get("category") or "").lower() == category.lower()]
    return list_page(
        slug, page_title, description, h1, subtitle, intro, candidates,
        lambda b: (-hp(b), name(b)),
        [("Power", lambda b: esc(field(b, "power"))), ("Torque", lambda b: esc(field(b, "torque"))), ("Weight", lambda b: esc(field(b, "weight"))), ("Seat height", lambda b: esc(field(b, "seat_height")))],
        breadcrumb
    )


def build_low_seat(bikes):
    candidates = [b for b in bikes if seat(b) and seat(b) <= 800]
    return list_page(
        "low-seat-height-motorcycles", "Low Seat Height Motorcycles",
        "Motorcycles with a seat height of 800 mm or less, sorted for shorter riders.",
        "Low Seat Height Motorcycles",
        "Bikes with a seat height of 800 mm or less.",
        "Seat height is only one part of the fit equation — seat width, suspension sag and footpeg position matter too — but 800 mm and below is a useful starting point for riders around 5'2\"–5'6\". This list is sorted from lowest seat to highest.",
        candidates, lambda b: (seat(b), weight(b), name(b)),
        [("Seat height", lambda b: esc(field(b, "seat_height"))), ("Weight", lambda b: esc(field(b, "weight"))), ("Power", lambda b: esc(field(b, "power"))), ("Category", lambda b: esc(b.get("category", "")))],
        "Low Seat Height Motorcycles"
    )


def comparison_facts(a, b):
    facts = []

    def add(label, value_a, value_b, num_a, num_b, higher_wins, phrase, unit):
        if not num_a or not num_b or num_a == num_b:
            return
        leader = a if (num_a > num_b) == higher_wins else b
        delta = abs(num_a - num_b)
        facts.append(
            f"<li><strong>{label}:</strong> {esc(value_a)} vs {esc(value_b)}. "
            f"The {esc(name(leader))} lists the {phrase} ({delta:g} {unit}).</li>"
        )

    add("Power", field(a, "power"), field(b, "power"), hp(a), hp(b), True, "higher claimed power", "hp")
    add("Torque", field(a, "torque"), field(b, "torque"), numeric(field(a, "torque")), numeric(field(b, "torque")), True, "higher claimed torque", "Nm")
    add("Kerb weight", field(a, "weight"), field(b, "weight"), weight(a), weight(b), False, "lower kerb weight", "kg")
    add("Seat height", field(a, "seat_height"), field(b, "seat_height"), seat(a), seat(b), False, "lower seat height", "mm")
    add("Fuel capacity", field(a, "fuel_capacity"), field(b, "fuel_capacity"), numeric(field(a, "fuel_capacity")), numeric(field(b, "fuel_capacity")), True, "larger fuel capacity", "L")

    if hp(a) and weight(a) and hp(b) and weight(b):
        ratio_a = hp(a) * 1000 / weight(a)
        ratio_b = hp(b) * 1000 / weight(b)
        if round(ratio_a) != round(ratio_b):
            leader = a if ratio_a > ratio_b else b
            facts.append(
                f"<li><strong>Power-to-weight:</strong> about {ratio_a:,.0f} vs {ratio_b:,.0f} hp per tonne. "
                f"The {esc(name(leader))} has the higher calculated ratio.</li>"
            )
    if field(a, "tyres") and field(a, "tyres") == field(b, "tyres"):
        facts.append(f"<li><strong>Tyres:</strong> both list {esc(field(a, 'tyres'))}.</li>")
    if field(a, "transmission") and field(a, "transmission") == field(b, "transmission"):
        facts.append(f"<li><strong>Transmission:</strong> both list {esc(field(a, 'transmission'))}.</li>")
    return facts


def comparison_faqs(a, b):
    faqs = []

    def addq(question, answer):
        if question and answer:
            faqs.append((question, answer))

    def leader_for(value_a, value_b, higher_wins):
        return a if (value_a > value_b) == higher_wins else b

    if hp(a) and hp(b) and hp(a) != hp(b):
        leader = leader_for(hp(a), hp(b), True)
        other = b if leader is a else a
        addq(
            f"Which has more power, the {name(a)} or the {name(b)}?",
            f"The {name(leader)} lists {field(leader, 'power')}, compared with {field(other, 'power')} for the {name(other)}."
        )
    if weight(a) and weight(b) and weight(a) != weight(b):
        leader = leader_for(weight(a), weight(b), False)
        other = b if leader is a else a
        addq(
            f"Which is lighter, the {name(a)} or the {name(b)}?",
            f"The {name(leader)} lists {field(leader, 'weight')}, compared with {field(other, 'weight')} for the {name(other)}."
        )
    if seat(a) and seat(b) and seat(a) != seat(b):
        leader = leader_for(seat(a), seat(b), False)
        other = b if leader is a else a
        addq(
            f"Which has a lower seat height, the {name(a)} or the {name(b)}?",
            f"The {name(leader)} lists {field(leader, 'seat_height')}, compared with {field(other, 'seat_height')} for the {name(other)}."
        )
    if numeric(field(a, "fuel_capacity")) and numeric(field(b, "fuel_capacity")) and numeric(field(a, "fuel_capacity")) != numeric(field(b, "fuel_capacity")):
        leader = leader_for(numeric(field(a, "fuel_capacity")), numeric(field(b, "fuel_capacity")), True)
        other = b if leader is a else a
        addq(
            f"Which has more fuel capacity, the {name(a)} or the {name(b)}?",
            f"The {name(leader)} lists {field(leader, 'fuel_capacity')}, compared with {field(other, 'fuel_capacity')} for the {name(other)}."
        )
    if hp(a) and weight(a) and hp(b) and weight(b):
        ratio_a = hp(a) * 1000 / weight(a)
        ratio_b = hp(b) * 1000 / weight(b)
        if round(ratio_a) != round(ratio_b):
            leader = a if ratio_a > ratio_b else b
            addq(
                f"What is the power-to-weight ratio of the {name(a)} and {name(b)}?",
                f"Using the listed power and kerb weight, the calculated ratios are about {ratio_a:,.0f} hp per tonne for the {name(a)} "
                f"and {ratio_b:,.0f} hp per tonne for the {name(b)}. The {name(leader)} has the higher listed ratio."
            )
    if a.get("category") and a.get("category") == b.get("category"):
        addq(
            f"Are the {name(a)} and {name(b)} both {a.get('category').lower()} motorcycles?",
            f"Yes. Both are listed in the {a.get('category')} category in the catalogue."
        )
    if field(a, "tyres") and field(a, "tyres") == field(b, "tyres"):
        addq(
            f"Do the {name(a)} and {name(b)} use the same tyre sizes?",
            f"Yes. Both list {field(a, 'tyres')}."
        )
    return faqs


def comparison(item, a, b):
    slug = item["slug"]
    h1 = item["title"]
    fields = [
        ("Category", lambda x: x.get("category", "")),
        ("Engine", lambda x: field(x, "engine")),
        ("Displacement", lambda x: x.get("displacement", "")),
        ("Max power", lambda x: field(x, "power")),
        ("Max torque", lambda x: field(x, "torque")),
        ("Kerb weight", lambda x: field(x, "weight")),
        ("Seat height", lambda x: field(x, "seat_height")),
        ("Fuel capacity", lambda x: field(x, "fuel_capacity")),
        ("Transmission", lambda x: field(x, "transmission")),
        ("Front suspension", lambda x: field(x, "front_suspension")),
        ("Rear suspension", lambda x: field(x, "rear_suspension")),
        ("Front brake", lambda x: field(x, "front_brake")),
        ("Rear brake", lambda x: field(x, "rear_brake")),
        ("Tyres", lambda x: field(x, "tyres")),
        ("Oil capacity", lambda x: service(x, "oil_capacity")),
        ("Battery", lambda x: battery_value(x)),
    ]
    rows = "".join(
        f"<tr><th>{esc(label)}</th><td>{esc(fn(a))}</td><td>{esc(fn(b))}</td></tr>"
        for label, fn in fields
    )
    facts = comparison_facts(a, b)
    faqs = comparison_faqs(a, b)
    faq_html = "".join(
        f'<div class="faq-item"><h3 class="faq-question">{esc(question)}</h3><p class="faq-answer">{esc(answer)}</p></div>'
        for question, answer in faqs
    )
    faq_json = {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in faqs
        ],
    } if faqs else None
    brand_links = " · ".join(dict.fromkeys(
        f'<a href="../reference/brand-{make_slug(bike.get("make", ""))}.html">All {esc(bike.get("make", ""))} models</a>'
        for bike in (a, b)
    ))
    content = f"""
      <p>{esc(item["verdict"])}</p>
      <p class="data-note">This is a specification comparison using the catalogue entries for {esc(name(a))} ({esc(a.get("year", ""))}) and {esc(name(b))} ({esc(b.get("year", ""))}). It is not a ride review; specifications can change by model year and market.</p>
      <div class="spec-table-wrap"><table class="spec-table"><thead><tr><th>Specification</th><th>{bike_link(a)}</th><th>{bike_link(b)}</th></tr></thead><tbody>{rows}</tbody></table></div>
      <h2>What the numbers say</h2>
      <ul>{''.join(facts) if facts else '<li>The listed fields do not provide enough comparable numbers for a difference summary.</li>'}</ul>
      <h2>Full specifications and service data</h2>
      <p>{bike_link(a)} · {bike_link(b)}</p>
      <p>{brand_links} · <a href="../reference/tyre-size-finder.html">Tyre size finder</a> · <a href="../reference/fork-seal-finder.html">Fork seal finder</a></p>
      {f'<section class="faq-section"><h2>Frequently Asked Questions</h2>{faq_html}</section>' if faq_html else ''}
      {related_guides([("comparisons.html", "All model comparisons"), ("parts-fitment-codes.html", "Parts and fitment codes"), ("torque-specs.html", "Motorcycle torque specs"), ("seat-height-chart.html", "Motorcycle seat height chart")])}
    """
    return guide_page(
        slug,
        f"{h1} — Specs & Comparison",
        item["description"],
        h1,
        f"{a.get('category', '')} comparison · {a.get('year', '')} vs {b.get('year', '')}",
        content,
        h1,
        [faq_json] if faq_json else None,
        parents=[("Model Comparisons", "comparisons.html")],
    )


def segment_leaders(models, electric=False):
    leaders = []

    def pick(label, value_fn, value_text, higher=True):
        candidates = [(value_fn(model), model) for model in models if value_fn(model)]
        if not candidates:
            return
        best_value, best_model = (max(candidates, key=lambda pair: pair[0]) if higher else min(candidates, key=lambda pair: pair[0]))
        leaders.append(f"<li><strong>{label}:</strong> {bike_link(best_model)} — {esc(value_text(best_model))}.</li>")

    pick("Most power", hp, lambda model: field(model, "power"))
    pick("Most torque", lambda model: numeric(field(model, "torque")), lambda model: field(model, "torque"))
    pick("Lightest", weight, lambda model: field(model, "weight"), higher=False)
    pick("Lowest seat", seat, lambda model: field(model, "seat_height"), higher=False)
    if electric:
        pick("Largest battery capacity", lambda model: numeric(field(model, "fuel_capacity")), lambda model: field(model, "fuel_capacity"))
    else:
        pick("Largest fuel tank", lambda model: numeric(field(model, "fuel_capacity")), lambda model: field(model, "fuel_capacity"))

    ratios = [(hp(model) * 1000 / weight(model), model) for model in models if hp(model) and weight(model)]
    if ratios:
        ratio, best_model = max(ratios, key=lambda pair: pair[0])
        leaders.append(f"<li><strong>Highest power-to-weight:</strong> {bike_link(best_model)} — about {ratio:,.0f} hp per tonne (calculated).</li>")

    low_seat = [model for model in models if seat(model) and seat(model) <= 800]
    if low_seat:
        leaders.append("<li><strong>800 mm seat or lower:</strong> " + " · ".join(bike_link(model) for model in low_seat) + ".</li>")

    a2 = [
        model for model in models
        if hp(model) and weight(model)
        and hp(model) * 0.7457 <= 35
        and (hp(model) * 0.7457) / weight(model) <= 0.2
    ]
    if a2:
        leaders.append("<li><strong>A2-friendly on listed figures:</strong> " + " · ".join(bike_link(model) for model in a2) + ".</li>")

    travel_values = []
    for model in models:
        numbers = [int(value) for value in re.findall(r"(\d{2,3})\s*mm\s+travel", field(model, "front_suspension"), re.I)]
        if numbers:
            travel_values.append(max(numbers))
    if len(travel_values) >= 2:
        leaders.append(f"<li><strong>Listed front suspension travel:</strong> {min(travel_values)}–{max(travel_values)} mm across the group.</li>")

    return leaders


def segment_faqs(models, electric=False):
    faqs = []

    def addq(question, answer):
        if question and answer:
            faqs.append((question, answer))

    power = [(hp(model), model) for model in models if hp(model)]
    if power:
        _, best = max(power, key=lambda pair: pair[0])
        addq("Which model has the most power?", f"The {name(best)} lists {field(best, 'power')}.")
    torque = [(numeric(field(model, "torque")), model) for model in models if numeric(field(model, "torque"))]
    if torque:
        _, best = max(torque, key=lambda pair: pair[0])
        addq("Which model has the most torque?", f"The {name(best)} lists {field(best, 'torque')}.")
    weights = [(weight(model), model) for model in models if weight(model)]
    if weights:
        _, best = min(weights, key=lambda pair: pair[0])
        addq("Which model is the lightest?", f"The {name(best)} lists {field(best, 'weight')}.")
    seats = [(seat(model), model) for model in models if seat(model)]
    if seats:
        _, best = min(seats, key=lambda pair: pair[0])
        addq("Which model has the lowest seat?", f"The {name(best)} lists {field(best, 'seat_height')}.")
    tanks = [(numeric(field(model, "fuel_capacity")), model) for model in models if numeric(field(model, "fuel_capacity"))]
    if tanks:
        _, best = max(tanks, key=lambda pair: pair[0])
        if electric:
            addq("Which model has the largest battery capacity?", f"The {name(best)} lists {field(best, 'fuel_capacity')}.")
        else:
            addq("Which model has the largest fuel tank?", f"The {name(best)} lists {field(best, 'fuel_capacity')}.")
    a2 = [
        model for model in models
        if hp(model) and weight(model)
        and hp(model) * 0.7457 <= 35
        and (hp(model) * 0.7457) / weight(model) <= 0.2
    ]
    if a2:
        addq(
            "Which models are A2-friendly on listed figures?",
            ", ".join(name(model) for model in a2) + ". Market-specific approval and restricted variants can differ."
        )
    addq(
        "How were these models selected?",
        "They are catalogue entries in this segment with listed power, torque, weight, seat height and chassis data. The table uses those listed figures; model years and market variants can differ."
    )
    return faqs


def segment_comparison(item, models):
    models = sorted(models, key=lambda model: (displacement(model), name(model)))
    engine_rows = []
    chassis_rows = []
    for model in models:
        model_cell = bike_link(model)
        engine_rows.append([
            model_cell,
            esc(model.get("year", "")),
            esc(field(model, "engine")),
            esc(field(model, "power")),
            esc(field(model, "torque")),
            esc(field(model, "weight")),
            esc(field(model, "seat_height")),
            esc(field(model, "fuel_capacity")),
        ])
        chassis_rows.append([
            model_cell,
            esc(field(model, "front_suspension")),
            esc(field(model, "rear_suspension")),
            esc(field(model, "front_brake")),
            esc(field(model, "rear_brake")),
            esc(battery_value(model)),
            esc(field(model, "tyres")),
        ])
    electric = item["slug"] == "electric-motorcycles"
    engine_headers = ["Model", "Year", "Engine", "Power", "Torque", "Weight", "Seat", "Battery" if electric else "Fuel"]
    chassis_headers = ["Model", "Front suspension", "Rear suspension", "Front brake", "Rear brake", "Battery", "Tyres"]
    leaders = segment_leaders(models, electric)
    faqs = segment_faqs(models, electric)
    faq_html = "".join(
        f'<div class="faq-item"><h3 class="faq-question">{esc(question)}</h3><p class="faq-answer">{esc(answer)}</p></div>'
        for question, answer in faqs
    )
    faq_json = {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in faqs
        ],
    } if faqs else None
    related = [(f"{segment['slug']}.html", segment["title"]) for segment in SEGMENT_COMPARISONS if segment["slug"] != item["slug"]][:3]
    related += [
        ("comparisons.html", "All model comparisons"),
        ("seat-height-chart.html", "Motorcycle seat height chart"),
        ("parts-fitment-codes.html", "Parts and fitment codes"),
    ]
    content = f"""
      <p>{esc(item["intro"])}</p>
      <p class="data-note">This is a segment comparison using listed catalogue data, not a ride review. Model years and market variants can differ; confirm the exact machine before ordering parts.</p>
      <h2>Engine, weight and dimensions</h2>
      <p>Sorted by engine size, then model name.</p>
      {table(engine_headers, engine_rows)}
      <h2>Chassis and running gear</h2>
      {table(chassis_headers, chassis_rows)}
      <h2>Segment leaders</h2>
      <ul>{''.join(leaders) if leaders else '<li>Not enough listed data for a leader summary.</li>'}</ul>
      <h2>How to shortlist</h2>
      <p>Start with seat height and kerb weight, then compare {'battery capacity' if electric else 'tank size'} and listed power. For off-road use, check front suspension travel, tyre sizes and brake specification; for touring, prioritise {'battery capacity' if electric else 'fuel capacity'}, seat height and weather protection. The table links every model to its full specification and service data.</p>
      {f'<section class="faq-section"><h2>Frequently Asked Questions</h2>{faq_html}</section>' if faq_html else ''}
      {related_guides(related)}
    """
    return guide_page(
        item["slug"],
        f"{item['title']} — Specs & Comparison",
        item["description"],
        item["title"],
        f"{len(models)} models compared · listed specifications",
        content,
        item["title"],
        [faq_json] if faq_json else None,
        parents=[("Model Comparisons", "comparisons.html")],
    )


def build_comparisons_hub():
    segment_cards = "".join(
        f'<a class="page-item" href="{item["slug"]}.html"><h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p></a>'
        for item in SEGMENT_COMPARISONS
    )
    groups = {}
    for item in COMPARISONS:
        groups.setdefault(item["group"], []).append(item)
    sections = [f'<h2>Segment comparisons</h2><div class="page-list">{segment_cards}</div>', '<h2>Head-to-head comparisons</h2>']
    for group, items in groups.items():
        cards = "".join(
            f'<a class="page-item" href="{item["slug"]}.html"><h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p></a>'
            for item in items
        )
        sections.append(f'<h3>{esc(group)}</h3><div class="page-list">{cards}</div>')
    content = f"""
      <p>Segment comparisons and head-to-head pages built from the catalogue's listed specifications. Each page shows power, torque, weight, seat height, suspension, brakes, tyres and service data, followed by the main on-paper differences.</p>
      <p>These are specification comparisons, not ride reviews. Model-year and market variants can differ, so confirm the exact machine before ordering parts.</p>
      {''.join(sections)}
      {related_guides([("parts-fitment-codes.html", "Parts and fitment codes"), ("seat-height-chart.html", "Seat height chart"), ("torque-specs.html", "Torque specifications"), ("oil-capacity-chart.html", "Oil capacity chart")])}
    """
    return guide_page(
        "comparisons",
        "Motorcycle Comparisons — Segments & Head-to-Head",
        f"{len(SEGMENT_COMPARISONS)} segment comparisons and {len(COMPARISONS)} head-to-head comparisons for adventure, touring, sport, motocross and retro motorcycles.",
        "Motorcycle Comparisons",
        f"{len(SEGMENT_COMPARISONS)} segment comparisons and {len(COMPARISONS)} head-to-head comparisons.",
        content,
        "Model Comparisons",
    )


def property_table(rows):
    body = "".join(
        f'<div class="spec-field"><span class="field-label">{esc(label)}</span><span class="field-value">{esc(value)}</span></div>'
        for label, value in rows if value
    )
    return f'<div class="spec-fields">{body}</div>'


def bike_faq(bike):
    if not FEATURES.get("modelFaq", True):
        return []
    try:
        max_faq = max(0, min(50, int(FAQ_OPTIONS.get("maxPerModel", 26))))
    except (TypeError, ValueError):
        max_faq = 26
    if not max_faq:
        return []
    full = name(bike)
    faq = []

    def usable(value):
        return bool(value and str(value).strip().lower() not in {"none", "-", "n/a", "na"})
    power = field(bike, "power")
    torque = field(bike, "torque")
    seat_height = field(bike, "seat_height")
    kerb = field(bike, "weight")
    oil = service(bike, "oil_capacity")
    oil_grade = service(bike, "oil_grade")
    battery = service(bike, "battery")
    battery_options = service(bike, "battery_options")
    battery_rating = service(bike, "battery_rating")
    top = field(bike, "top_speed")
    fuel = field(bike, "fuel_capacity")
    disp = bike.get("displacement") or field(bike, "displacement")
    tyres = field(bike, "tyres")
    abs_value = field(bike, "abs")
    front_susp = field(bike, "front_suspension")
    rear_susp = field(bike, "rear_suspension")
    front_brake = field(bike, "front_brake")
    rear_brake = field(bike, "rear_brake")
    interval = service(bike, "service_interval")
    front_pads = service(bike, "front_brake_pads")
    rear_pads = service(bike, "rear_brake_pads")
    spark = service(bike, "spark_plug")
    chain_value = service(bike, "chain") or field(bike, "chain")
    final_drive = service(bike, "final_drive")
    subject = faq_alias(bike) if FAQ_OPTIONS.get("aliasVariants", True) else full

    if power:
        faq.append((f"How much horsepower (BHP) does the {subject} make?", f"The {full} is rated at {power}."))
    if torque:
        faq.append((f"What is the torque of the {full}?", f"Manufacturer-claimed peak torque is {torque}."))
    if top:
        faq.append((f"What is the top speed of the {subject}?", f"The listed top speed is {top}."))
    if disp:
        faq.append((f"What is the engine displacement of the {full}?", f"The {full} is listed with a {disp} engine."))
    if seat_height:
        faq.append((f"What is the seat height of the {full}?", f"The seat height is listed as {seat_height}. Seat width and suspension sag also affect reach."))
    if kerb:
        faq.append((f"How much does the {full} weigh?", f"The kerb weight is listed as {kerb}."))

    hp_value = hp(bike)
    kg_value = weight(bike)
    if hp_value and kg_value:
        per_tonne = round(hp_value * 1000 / kg_value)
        kw_per_kg = round(hp_value * 0.7457 / kg_value, 2)
        power_for_ratio = re.sub(r"\s*@.*$", "", power).strip() or power
        faq.append((
            f"What is the power-to-weight ratio of the {full}?",
            f"Using the listed {power_for_ratio} and {kerb}, the calculated ratio is about {per_tonne:,} hp per tonne ({kw_per_kg:.2f} kW/kg)."
        ))

    if hp_value and kg_value and seat_height:
        beginner_categories = {"Supersport", "Sport", "Motocross", "Enduro"}
        fits_power = hp_value <= 50
        fits_weight = kg_value <= 200
        fits_seat = seat(bike) <= 800
        category_ok = (bike.get("category") or "") not in beginner_categories
        if fits_power and fits_weight and fits_seat and category_ok:
            faq.append((
                f"Is the {full} suitable for beginners?",
                f"On the site's beginner shortlist criteria (50 hp or less, 200 kg or less and an 800 mm seat or lower), "
                f"the {full} qualifies at {power}, {kerb} and {seat_height}. Rider training and individual fit still matter."
            ))
        else:
            reasons = []
            if not fits_power:
                reasons.append(f"{power} is above the 50 hp limit")
            if not fits_weight:
                reasons.append(f"{kerb} is above the 200 kg limit")
            if not fits_seat:
                reasons.append(f"{seat_height} is above the 800 mm seat limit")
            if not category_ok:
                reasons.append(f"its {bike.get('category')} category is excluded from the shortlist")
            faq.append((
                f"Is the {full} suitable for beginners?",
                "It falls outside the site's beginner shortlist criteria: " + "; ".join(reasons) +
                ". The criteria are 50 hp or less, 200 kg or less, an 800 mm seat or lower, and a non-sport, non-competition category."
            ))

    if hp_value and kg_value:
        kw_value = hp_value * 0.7457
        kw_per_kg = kw_value / kg_value
        fits_a2 = kw_value <= 35 and kw_per_kg <= 0.2
        if fits_a2:
            faq.append((
                f"Is the {full} A2-legal?",
                f"On the listed figures it fits the European A2 limits: about {kw_value:.1f} kW and {kw_per_kg:.2f} kW/kg. "
                "Market-specific approval and restricted variants can differ."
            ))
        else:
            faq.append((
                f"Is the {full} A2-legal?",
                f"On the listed figures it exceeds the European A2 limits: about {kw_value:.1f} kW and {kw_per_kg:.2f} kW/kg "
                "(limits: 35 kW and 0.2 kW/kg). A restricted version may be available; check local approval."
            ))

    if seat_height:
        seat_mm = seat(bike)
        if seat_mm <= 760:
            band = "low"
        elif seat_mm <= 800:
            band = "moderate"
        elif seat_mm <= 830:
            band = "tall"
        else:
            band = "very tall"
        faq.append((
            f"Is the {full} suitable for shorter riders?",
            f"The seat is listed at {seat_height}, which is {band} by the site's seat-height bands "
            "(760 mm or lower low, 761–800 mm moderate, 801–830 mm tall, above 830 mm very tall). "
            "Seat width, suspension sag and rider inseam also affect reach."
        ))

    if fuel:
        faq.append((f"What is the fuel capacity of the {full}?", f"Fuel capacity is listed as {fuel}."))
    if usable(tyres):
        faq.append((f"What tyres does the {subject} use?", f"Tyre sizes are listed as {tyres}."))
    if usable(abs_value):
        abs_lower = abs_value.lower()
        if abs_value.strip().lower() in ("yes", "no"):
            faq.append((f"Does the {full} have ABS?", f"ABS: {abs_value.strip()}."))
        elif "abs" in abs_lower:
            faq.append((f"Does the {full} have ABS?", f"The {full} is listed with {abs_value}."))
        elif "combined" in abs_lower or "cbs" in abs_lower:
            faq.append((f"What braking system does the {full} have?", f"The {full} is listed with {abs_value}."))
    if usable(front_susp) or usable(rear_susp):
        answer = " ".join(part for part in [
            f"Front: {front_susp}." if usable(front_susp) else "",
            f"Rear: {rear_susp}." if usable(rear_susp) else "",
        ] if part)
        faq.append((f"What suspension does the {full} use?", answer))
    if usable(front_brake) or usable(rear_brake):
        answer = " ".join(part for part in [
            f"Front: {front_brake}." if usable(front_brake) else "",
            f"Rear: {rear_brake}." if usable(rear_brake) else "",
        ] if part)
        faq.append((f"What brakes does the {full} use?", answer))
    if usable(interval):
        faq.append((f"What is the service interval for the {full}?", f"The listed service interval is {interval}. Confirm the schedule for your market and model year."))

    if battery:
        answer = f"The listed battery code is {battery}."
        if battery_options:
            answer += f" Alternative listed codes: {battery_options}."
        if battery_rating:
            answer += f" Battery rating: {battery_rating}."
        answer += " Confirm terminal layout and case dimensions against the battery fitted to your machine."
        faq.append((f"What battery does the {subject} use?", answer))
    elif battery_rating:
        faq.append((f"What is the battery rating of the {subject}?", f"The listed battery rating is {battery_rating}. The battery code is not yet verified for this entry."))

    if FAQ_OPTIONS.get("brakePads", True) and (usable(front_pads) or usable(rear_pads)):
        answer = " ".join(part for part in [
            f"Front: {front_pads}." if usable(front_pads) else "",
            f"Rear: {rear_pads}." if usable(rear_pads) else "",
        ] if part)
        answer += " These are pad-shape references; confirm the compound and exact model year before ordering."
        faq.append((f"What brake pads does the {subject} use?", answer))

    if FAQ_OPTIONS.get("sparkPlug", True) and usable(spark):
        faq.append((f"What spark plug does the {subject} use?", f"The listed spark plug is {spark}. Confirm the gap and heat range for your model year."))

    if FAQ_OPTIONS.get("chain", True) and usable(chain_value):
        faq.append((f"What chain does the {subject} use?", f"The listed chain or final drive is {chain_value}. Confirm the pitch, link count and adjustment procedure for your model year."))

    sprocket_text = " ".join(part for part in [chain_value, field(bike, "transmission"), final_drive] if usable(part))
    sprocket_match = re.search(r"\b\d{2}T\s*/\s*\d{2}T\b", sprocket_text, re.I)
    if FAQ_OPTIONS.get("sprocket", True) and sprocket_match:
        faq.append((f"What sprocket sizes does the {subject} use?", f"The listed final-drive sprocket sizes are {sprocket_match.group(0)}. Confirm the tooth count for your market and model year."))

    if oil:
        answer = f"Engine oil capacity is {oil}"
        if oil_grade:
            answer += f" and the recommended grade is {oil_grade}"
        answer += ". Confirm the exact fill procedure in the owner's or workshop manual."
        faq.append((f"What is the engine oil capacity of the {full}?", answer))
    elif oil_grade:
        faq.append((f"What engine oil grade does the {full} use?", f"The recommended grade is {oil_grade}. Confirm the exact fill procedure in the owner's or workshop manual."))

    legacy_fork_oil = service(bike, "fork_oil")
    fork_grade = service(bike, "fork_oil_grade")
    fork_volume = service(bike, "fork_oil_volume")
    fork_air = service(bike, "fork_air_gap")
    fork_seal = service(bike, "fork_seal")
    rear_shock = service(bike, "rear_shock")
    if usable(legacy_fork_oil):
        faq.append((f"What fork oil does the {full} use?", f"The listed fork oil specification is {legacy_fork_oil}. Confirm the fill procedure in the workshop manual."))
    elif usable(fork_grade) or usable(fork_volume) or usable(fork_air):
        parts = []
        if usable(fork_grade):
            parts.append(f"grade {fork_grade}")
        if usable(fork_volume):
            parts.append(f"quantity {fork_volume}")
        if usable(fork_air):
            parts.append(f"air gap {fork_air}")
        faq.append((f"What fork oil does the {full} use?", "Listed fork oil data: " + "; ".join(parts) + ". Confirm the fill procedure in the workshop manual."))
    if usable(fork_seal):
        faq.append((f"What fork seal size does the {full} use?", f"The listed fork oil seal is {fork_seal}."))
    if usable(rear_shock):
        faq.append((f"What rear shock does the {full} use?", f"The listed rear shock is {rear_shock}."))

    seen = set()
    unique = []
    for question, answer in faq:
        if question in seen:
            continue
        seen.add(question)
        unique.append((question, answer))
    return unique[:max_faq]


ALIAS_NICKNAMES = {
    "fireblade", "busa", "hayabusa", "gixxer", "goldwing", "vstrom", "tenere",
    "panigale", "monster", "multistrada", "scrambler", "bonneville", "trident",
    "tiger", "rocket", "sportster", "scout", "chief", "challenger", "himalayan",
    "classic", "hunter", "meteor", "interceptor", "continental", "cp2", "cp3", "gs", "adv"
}


def alias_label(value):
    words = []
    for word in str(value).split():
        if any(ch.isdigit() for ch in word):
            words.append(word.upper())
        elif len(word) <= 3:
            words.append(word.upper())
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


GENERIC_ALIASES = {
    "harley", "hd", "enfield", "royal enfield", "guzzi", "cf moto", "qj motor",
    "qj", "bmw motorrad", "kawi", "triumph motorcycles", "indian motorcycle"
}


def display_aliases(bike, aliases):
    model_key = re.sub(r"[^a-z0-9]", "", str(bike.get("model", "")).lower())
    scored = []
    for alias in aliases:
        if str(alias).lower() in GENERIC_ALIASES:
            continue
        key = re.sub(r"[^a-z0-9]", "", str(alias).lower())
        if key == model_key:
            continue
        score = 0
        if " " in str(alias):
            score += 3
        if str(alias).lower() in ALIAS_NICKNAMES:
            score += 2
        if len(str(alias)) > 5:
            score += 1
        if key == model_key:
            score -= 2
        scored.append((score, alias))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [alias_label(alias) for _, alias in scored[:7]]


def faq_alias(bike):
    """Pick a compact, model-specific alias for search-style FAQ questions."""
    model = str(bike.get("model", "")).strip()
    if not model:
        return str(bike.get("make") or "this motorcycle")
    model_key = re.sub(r"[^a-z0-9]", "", model.lower())
    compact_model = re.sub(r"[\s\-/]+", "", model.lower())
    aliases = bike.get("aliases") or aliases_for(bike.get("make", ""), model)
    candidates = []
    for alias in aliases:
        text = str(alias).strip()
        low = text.lower()
        if low in GENERIC_ALIASES:
            continue
        key = re.sub(r"[^a-z0-9]", "", low)
        if not key or key == model_key:
            continue
        # Avoid family prefixes (CBR1000 for CBR1000RR-R) and word+number
        # compact forms (HIMALAYAN450 for Himalayan 450).
        if model_key.startswith(key) and len(key) < len(model_key):
            continue
        if key == compact_model and " " in model and "-" not in model:
            continue
        if any(ch.isdigit() for ch in text) and " " not in text and 4 <= len(text) <= 14:
            candidates.append(text)
    if candidates:
        return alias_label(max(candidates, key=len))
    return model


def bike_image_entry(bike):
    return BIKE_IMAGES.get(bike["id"])


def bike_image_srcset(entry, fmt):
    variants = (entry.get("variants") or {}).get(fmt) or {}
    return ", ".join(
        f"../{path} {width}w"
        for width, path in sorted(variants.items(), key=lambda item: int(item[0]))
    )


def bike_image_url(bike, fmt="jpg", width="1200"):
    if not FEATURES.get("modelImages", True):
        return ""
    entry = bike_image_entry(bike)
    if not entry:
        return ""
    variants = (entry.get("variants") or {}).get(fmt) or {}
    path = variants.get(str(width)) or variants.get("1200") or variants.get("1600") or variants.get("800")
    return f"{SITE}/{path}" if path else ""


def bike_image_html(bike):
    if not FEATURES.get("modelImages", True):
        return ""
    entry = bike_image_entry(bike)
    if not entry:
        return ""
    jpg = (entry.get("variants") or {}).get("jpg") or {}
    fallback = jpg.get("1200") or jpg.get("800") or jpg.get("1600") or jpg.get("400")
    if not fallback:
        return ""
    sources = ""
    avif = bike_image_srcset(entry, "avif")
    webp = bike_image_srcset(entry, "webp")
    if avif:
        sources += f'<source type="image/avif" srcset="{avif}" sizes="(max-width: 720px) 100vw, (max-width: 1100px) 92vw, 960px">'
    if webp:
        sources += f'<source type="image/webp" srcset="{webp}" sizes="(max-width: 720px) 100vw, (max-width: 1100px) 92vw, 960px">'
    alt = esc(entry.get("alt") or f"{bike.get('make', '')} {bike.get('model', '')}")
    credit = ""
    if entry.get("creditRequired") and entry.get("credit"):
        credit_text = esc(entry["credit"])
        if entry.get("licenseUrl"):
            credit_text = (
                f'{credit_text} · <a href="{esc(entry["licenseUrl"])}" rel="license nofollow">'
                f'{esc(entry.get("license", ""))}</a>'
            )
        credit = f"<figcaption>{credit_text}</figcaption>"
    return (
        '<figure class="bike-photo"><picture>'
        f'{sources}<img src="../{fallback}" alt="{alt}" width="{entry.get("width", 1200)}" '
        f'height="{entry.get("height", 800)}" loading="eager" fetchpriority="high" decoding="async">'
        f'</picture>{credit}</figure>'
    )


def static_sections_html(bike):
    parts = []
    for key, section in (bike.get("sections") or {}).items():
        label = section.get("label") or key
        body = ""
        note = next((f.get("value", "") for f in section.get("fields") or [] if f.get("key") == "note"), "")
        if note and bike.get("fitment_only") and key == "service":
            note = (
                "Brake-pad fitment is recorded for this model. Other service capacities, "
                "fluid grades and torque values are not listed in this entry."
            )
        if note:
            body += f'<p class="spec-note">{esc(note)}</p>'
        field_rows = [
            (f.get("label", ""), f.get("value", ""))
            for f in section.get("fields") or []
            if f.get("key") not in {"note", "data_status"}
        ]
        if field_rows:
            body += property_table(field_rows)
        if section.get("table"):
            rows = section["table"]
            headers = list(rows[0].keys())
            labels = {
                "component": "Component", "torque": "Torque", "notes": "Notes",
                "name": "Name", "thread": "Thread", "length": "Length", "head": "Head"
            }
            body += table(
                [labels.get(h, h.replace("_", " ").title()) for h in headers],
                [[esc(row.get(h, "")) for h in headers] for row in rows]
            )
        if not body:
            continue
        is_open = key in ("general_specs", "service")
        parts.append(
            f'<details class="spec-section"{" open" if is_open else ""}>'
            f'<summary>{esc(label)}</summary><div class="spec-body">{body}</div></details>'
        )
    return f'<div class="spec-section-grid">{"".join(parts)}</div>'


def model_page(bike, related, pad_related, guide_links, brand_href):
    url = f"{SITE}/motorcycle/{quote(bike['id'])}.html"
    oil_capacity = service(bike, "oil_capacity")
    oil_grade = service(bike, "oil_grade")
    front_pads = service(bike, "front_brake_pads")
    rear_pads = service(bike, "rear_brake_pads")
    fitment_only = bool(bike.get("fitment_only"))
    model_label = str(bike.get("model") or "").strip()

    if oil_capacity:
        seo_title = f"{name(bike)} ({bike.get('year', '')}) Oil Capacity, Specs & Torque"
    elif oil_grade:
        seo_title = f"{name(bike)} ({bike.get('year', '')}) Oil Grade, Specs & Torque"
    elif fitment_only and (front_pads or rear_pads):
        if model_label:
            seo_title = f"{name(bike)} ({bike.get('year', '')}) Brake Pads & Fitment"
        else:
            seo_title = f"{name(bike)} ({bike.get('year', '')})"
    elif field(bike, "torque"):
        seo_title = f"{name(bike)} ({bike.get('year', '')}) Specs & Torque"
    else:
        seo_title = f"{name(bike)} ({bike.get('year', '')}) Specs & Service Data"

    def short(value):
        return re.sub(r"\([^)]*\)", "", str(value or "").split("@")[0]).strip()

    bits = []
    if field(bike, "power"):
        bits.append(f"{short(field(bike, 'power'))} power")
    if field(bike, "torque"):
        bits.append(f"{short(field(bike, 'torque'))} torque")
    if field(bike, "weight"):
        bits.append(field(bike, "weight"))
    if field(bike, "seat_height"):
        bits.append(f"{field(bike, 'seat_height')} seat")
    if oil_capacity:
        oil_parts = [part.strip() for part in str(oil_capacity).split(";") if part.strip()]
        oil_first = next((part for part in oil_parts if "with filter" in part.lower()), oil_parts[0] if oil_parts else str(oil_capacity))
        oil_desc = f"{name(bike)} ({bike.get('year', '')}) engine oil capacity: {oil_first}."
        if oil_grade:
            oil_desc += f" Recommended grade: {oil_grade}."
        description = f"{oil_desc} Full specs, service data, torque values and dimensions."
    elif fitment_only and (front_pads or rear_pads):
        fitment_bits = []
        if front_pads:
            fitment_bits.append(f"front {front_pads}")
        if rear_pads:
            fitment_bits.append(f"rear {rear_pads}")
        prefix = f"{name(bike)} ({bike.get('year', '')})"
        if model_label:
            prefix += " brake pad fitment"
        description = f"{prefix}: {', '.join(fitment_bits)}."
        extras = []
        displacement_value = str(bike.get("displacement") or "").strip()
        if displacement_value and displacement_value not in {"—", "-", "–"}:
            category_value = str(bike.get("category") or "").strip()
            extras.append(f"{category_value} {displacement_value}".strip())
        battery_code = service(bike, "battery")
        battery_rating = service(bike, "battery_rating")
        if battery_code:
            extras.append(f"battery {battery_code}")
        elif battery_rating:
            extras.append(f"battery rating {battery_rating}")
        tyre_value = field(bike, "tyres")
        if tyre_value:
            extras.append(f"tyres {tyre_value}")
        if extras:
            description += f" {' · '.join(extras)}."
        description += " Pad-shape references, service data and related specifications."
    elif bits:
        description = f"{name(bike)} specs: {', '.join(bits)}. Torque values, service data and dimensions."
    else:
        description = f"{name(bike)} ({bike.get('year', '')}) specifications, service data and reference tables."
    for tail in (
        " Pad-shape references, service data and related specifications.",
        " Full specs, service data, torque values and dimensions.",
        " Torque values, service data and dimensions.",
    ):
        if len(description) > 160 and description.endswith(tail):
            description = description[:-len(tail)]
            break
    oil_quick = ""
    if oil_capacity:
        oil_quick = f'<h2 class="section-heading">Engine oil capacity</h2><p class="data-note"><strong>Engine oil capacity:</strong> {esc(oil_capacity)}'
        if oil_grade:
            oil_quick += f' · <strong>Recommended grade:</strong> {esc(oil_grade)}'
        oil_quick += "</p>"
    fitment_quick = ""
    if fitment_only and (front_pads or rear_pads):
        fitment_crossref = brake_shape_crossref_html(front_pads, rear_pads)
        fitment_rows = []
        if front_pads:
            fitment_rows.append(f"<strong>Front:</strong> {esc(front_pads)}")
        if rear_pads:
            fitment_rows.append(f"<strong>Rear:</strong> {esc(rear_pads)}")
        fitment_subject = f"the {esc(title(bike))}" if model_label else "this fitment entry"
        fitment_quick = (
            '<section class="fitment-quick">'
            '<h2 class="section-heading">Brake pad fitment</h2>'
            f'<p class="data-note">{" · ".join(fitment_rows)}</p>'
            f'<p>These codes identify the backing-plate shape for {fitment_subject}. '
            'Confirm the friction compound, ABS variant and exact model year before ordering. '
            'See the <a href="../reference/brake-pad-fitment.html">brake pad fitment table</a> and '
            '<a href="../reference/pad-shape-cross-reference.html">pad shape cross-reference</a>.</p>'
            f'{fitment_crossref}'
            '</section>'
        )
    subtitle_displacement = str(bike.get("displacement") or "").strip()
    if subtitle_displacement in {"—", "-", "–"}:
        subtitle_displacement = ""
    summary_text = str(bike.get("summary") or "").strip()
    if fitment_only:
        summary_text = summary_text.replace(
            "Full engine, chassis and service specifications are being compiled.",
            "Engine, chassis and service specifications are not listed in this entry.",
        )
    faq = bike_faq(bike)
    bike_photo = bike_image_html(bike)
    bike_photo_block = f"\n      {bike_photo}" if bike_photo else ""
    og_image = bike_image_url(bike, "jpg", "1200")
    og_image_meta = f'\n  <meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    twitter_card = "summary_large_image" if og_image else "summary"
    twitter_image_meta = f'\n  <meta name="twitter:image" content="{esc(og_image)}">' if og_image else ""

    def qty(value, unit):
        number = numeric(value)
        return {"@type": "QuantitativeValue", "value": number, "unitCode": unit} if number else value

    fuel = field(bike, "fuel_capacity") or ""
    graph = [{
        "@type": "Motorcycle",
        "name": title(bike),
        "brand": {"@type": "Brand", "name": bike.get("make", "")},
        "model": bike.get("model", ""),
        "vehicleModelDate": bike.get("year", ""),
        "description": summary_text,
        "bodyType": bike.get("category", ""),
        "weight": qty(field(bike, "weight"), "KGM"),
        "fuelCapacity": qty(fuel, "KWH" if "kwh" in fuel.lower() else "LTR"),
        "vehicleEngine": {
            "@type": "EngineSpecification",
            "engineDisplacement": qty(bike.get("displacement", ""), "CMQ"),
            "enginePower": qty(field(bike, "power"), "BHP"),
            "engineTorque": qty(field(bike, "torque"), "NU")
        },
        "url": url
    }, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Browse", "item": SITE + "/#browse"},
            {"@type": "ListItem", "position": 3, "name": bike.get("make", ""), "item": f"{SITE}/reference/brand-{make_slug(bike.get('make', ''))}.html"},
            {"@type": "ListItem", "position": 4, "name": title(bike), "item": url}
        ]
    }]
    if og_image:
        graph[0]["image"] = [og_image]
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq
        ]})
    hero = "".join(f'<div class="hero-stat"><span class="hero-label">{esc(label)}</span><span class="hero-value">{esc(value)}</span></div>' for label, value in [
        ("Power", field(bike, "power")), ("Torque", field(bike, "torque")),
        ("Kerb Weight", field(bike, "weight")), ("Seat Height", field(bike, "seat_height"))
    ] if value)
    aliases = bike.get("aliases") or aliases_for(bike.get("make", ""), bike.get("model", ""))
    alias_labels = display_aliases(bike, aliases)
    alias_html = f'<p class="bike-alias"><strong>Also known as:</strong> {esc(", ".join(alias_labels))}</p>' if alias_labels else ""
    general_rows = []
    for item in ((bike.get("sections") or {}).get("general_specs") or {}).get("fields") or []:
        general_rows.append((item.get("label", ""), item.get("value", "")))
    service_rows = []
    for item in ((bike.get("sections") or {}).get("service") or {}).get("fields") or []:
        service_rows.append((item.get("label", ""), item.get("value", "")))
    torque_section = (bike.get("sections") or {}).get("torque_specs") or {}
    torque_note = next((f.get("value", "") for f in torque_section.get("fields") or [] if f.get("key") == "note"), "")
    torque_rows = torque_section.get("table") or []
    faq_html = "".join(f'<div class="faq-item"><h3 class="faq-question">{esc(q)}</h3><p class="faq-answer">{esc(a)}</p></div>' for q, a in faq)
    related_html = "".join(
        f'<a class="bike-card" href="{quote(other["id"])}.html"><span class="bike-make">{esc(other.get("make", ""))}</span><h3 class="bike-model">{esc(other.get("model", ""))}</h3><span class="bike-meta">{esc(other.get("year", ""))} · {esc(other.get("displacement", ""))}</span></a>'
        for other in related
    )
    pad_related_html = "".join(
        f'<a href="{quote(other["id"])}.html">{esc(title(other))}</a>'
        for other in pad_related
    )
    guides_html = "".join(
        f'<a href="{href if href.startswith("../") else f"../guides/{href}"}">{esc(label)}</a>'
        for href, label in guide_links
    )
    template = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{esc(seo_title)} | MotoX Wiki</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="MotoX Wiki">
  <meta property="og:title" content="{esc(seo_title)} | MotoX Wiki">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">{og_image_meta}
  <meta name="twitter:card" content="{twitter_card}">{twitter_image_meta}
  <meta name="theme-color" content="#c2410c">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/site.min.css?v=10" id="mx-main-css" data-mx-shield-css="../css/main.css?v=39" fetchpriority="high">
  <script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)}</script>
  {ADSENSE_HEAD}
</head>
<body>
  <header class="site-header static-header">
    <div class="container">
      <div class="header-row"><a class="brand" href="../index.html"><span class="brand-icon">⚙</span><span>MotoX Wiki</span></a></div>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="../guides/index.html">Guides</a>
        <a href="../pages.html">Reference</a>
      </nav>
    </div>
  </header>
  <main class="container">
    <div class="bike-header">
      <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="../index.html#browse">Browse</a> / <a href="{brand_href}">{esc(bike.get('make', ''))}</a> / {esc(name(bike))}</div>
      <h1>{esc(title(bike))}</h1>
      <p class="bike-subtitle">{esc(bike.get('category', ''))}{' · ' if bike.get('category') and subtitle_displacement else ''}{esc(subtitle_displacement)}</p>{bike_photo_block}
      <p>{esc(summary_text)}</p>
      {oil_quick}
      <p class="bike-alias"><strong>Brand:</strong> <a href="{brand_href}">All {esc(bike.get('make', ''))} models</a> · <a href="../reference/all-models.html">All models A–Z</a></p>
      {alias_html}
      <div class="hero-stats">{hero}</div>
    </div>
    <article class="model-content">
      {fitment_quick}
      <h2 class="section-heading">Specifications</h2>
      {static_sections_html(bike)}
      {f'<section class="faq-section"><h2 class="section-heading">Frequently Asked Questions</h2>{faq_html}</section>' if faq_html else ''}
      {f'<section class="related-section"><h2 class="related-title">Related Models</h2><div class="bike-grid related-grid">{related_html}</div></section>' if related_html else ''}
      {f'<section class="related-section"><h2 class="related-title">Models sharing this brake pad shape</h2><p class="home-guide-links">{pad_related_html}</p></section>' if pad_related_html else ''}
      <section class="related-section"><h2 class="related-title">Related Guides</h2><p class="home-guide-links">{guides_html}</p></section>
      <p class="data-note">Specifications are manufacturer-claimed and can vary by model year and market. Confirm service limits and torque values against the owner's or workshop manual. Data updated {LAST_MOD}.</p>
    </article>
  </main>
  <footer class="site-footer"><div class="container site-footer-inner"><span class="footer-text">© 2026 MotoX Wiki. Community-maintained motorcycle technical reference.</span></div></footer>
</body>
</html>
"""
    path = os.path.join(MODELS, f"{quote(bike['id'])}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(template)


COMPARISONS = [
    {
        "slug": "honda-crf450r-vs-yamaha-yz450f",
        "title": "Honda CRF450R vs Yamaha YZ450F",
        "description": "Honda CRF450R vs Yamaha YZ450F: 57 vs 59 hp, 111 vs 109 kg and 960 vs 965 mm seat height. Compare 450 motocross specs, suspension and service data.",
        "verdict": "The Yamaha YZ450F lists 2 hp more and 2 kg less than the Honda CRF450R, while the CRF450R has a 5 mm lower seat and 0.1 L more fuel capacity.",
        "a": "honda-crf450r-2021-present-global",
        "b": "yamaha-yz450f-2023-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "honda-crf450r-vs-kawasaki-kx450",
        "title": "Honda CRF450R vs Kawasaki KX450",
        "description": "Honda CRF450R vs Kawasaki KX450: 57 vs 58 hp, 111 vs 110 kg and the same 960 mm seat height. Compare 450 motocross specifications.",
        "verdict": "The Kawasaki KX450 lists 1 hp more, 2 Nm more torque and 1 kg less weight than the Honda CRF450R. Both list a 960 mm seat; the CRF450R has 0.1 L more fuel capacity.",
        "a": "honda-crf450r-2021-present-global",
        "b": "kawasaki-kx450-2024-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "honda-crf450r-vs-ktm-450-sx-f",
        "title": "Honda CRF450R vs KTM 450 SX-F",
        "description": "Honda CRF450R vs KTM 450 SX-F: 57 vs 63 hp, 111 vs 104 kg and 960 vs 958 mm seat height. Compare 450 motocross specs and service data.",
        "verdict": "The KTM 450 SX-F lists 6 hp more, 2 Nm more torque, 7 kg less weight, a 2 mm lower seat and 0.7 L more fuel capacity than the Honda CRF450R.",
        "a": "honda-crf450r-2021-present-global",
        "b": "ktm-450-sx-f-2022-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "yamaha-yz450f-vs-kawasaki-kx450",
        "title": "Yamaha YZ450F vs Kawasaki KX450",
        "description": "Yamaha YZ450F vs Kawasaki KX450: 59 vs 58 hp, 109 vs 110 kg and 965 vs 960 mm seat height. Compare 450 motocross specifications.",
        "verdict": "The Yamaha YZ450F lists 1 hp more and 1 kg less than the Kawasaki KX450, while the KX450 lists 1 Nm more torque and a 5 mm lower seat. Both list a 6.2 L tank.",
        "a": "yamaha-yz450f-2023-present-global",
        "b": "kawasaki-kx450-2024-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "yamaha-yz450f-vs-ktm-450-sx-f",
        "title": "Yamaha YZ450F vs KTM 450 SX-F",
        "description": "Yamaha YZ450F vs KTM 450 SX-F: 59 vs 63 hp, 109 vs 104 kg and 965 vs 958 mm seat height. Compare 450 motocross specs and service data.",
        "verdict": "The KTM 450 SX-F lists 4 hp more, 1 Nm more torque, 5 kg less weight, a 7 mm lower seat and 0.8 L more fuel capacity than the Yamaha YZ450F.",
        "a": "yamaha-yz450f-2023-present-global",
        "b": "ktm-450-sx-f-2022-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "kawasaki-kx450-vs-ktm-450-sx-f",
        "title": "Kawasaki KX450 vs KTM 450 SX-F",
        "description": "Kawasaki KX450 vs KTM 450 SX-F: 58 vs 63 hp, 110 vs 104 kg and 960 vs 958 mm seat height. Compare 450 motocross specifications.",
        "verdict": "The KTM 450 SX-F lists 5 hp more, 6 kg less weight, a 2 mm lower seat and 0.8 L more fuel capacity than the Kawasaki KX450. Both list 49 Nm of torque.",
        "a": "kawasaki-kx450-2024-present-global",
        "b": "ktm-450-sx-f-2022-present-global",
        "group": "450 Motocross",
    },
    {
        "slug": "cbr600rr-vs-cbr650r",
        "title": "CBR600RR vs CBR650R",
        "description": "Honda CBR600RR vs CBR650R: supersport vs sportbike specs, weight, seat height and power compared.",
        "verdict": "The CBR600RR is the sharper track-focused 600, while the CBR650R is the more usable road bike with a broader powerband and comfortable ergonomics.",
        "a": "honda-cbr600rr-2013",
        "b": "honda-cbr650r-2024-present-global",
        "group": "Sport",
    },
    {
        "slug": "ninja-400-vs-ninja-500",
        "title": "Ninja 400 vs Ninja 500",
        "description": "Kawasaki Ninja 400 vs Ninja 500: power, weight, seat height and specifications compared.",
        "verdict": "The Ninja 500 replaces the 400 with a larger, torquier engine while keeping the same lightweight formula.",
        "a": "kawasaki-ninja-400-2018-present",
        "b": "kawasaki-ninja-500-2024-present",
        "group": "Sport",
    },
    {
        "slug": "mt-07-vs-mt-09",
        "title": "MT-07 vs MT-09",
        "description": "Yamaha MT-07 vs MT-09: CP2 twin vs CP3 triple, with power, torque, weight and seat height compared.",
        "verdict": "The MT-07 is lighter and cheaper to run; the MT-09 adds a three-cylinder engine, more power and more equipment.",
        "a": "yamaha-mt-07-2018",
        "b": "yamaha-mt-09-2015-2018-global",
        "group": "Naked",
    },
    {
        "slug": "himalayan-450-vs-411",
        "title": "Himalayan 450 vs 411",
        "description": "Royal Enfield Himalayan 450 vs 411: power, weight, seat height and specifications compared.",
        "verdict": "The Himalayan 450 brings a new liquid-cooled engine, more power and a modern chassis; the 411 is simpler and lighter on electronics.",
        "a": "royal-enfield-himalayan-450",
        "b": "royal-enfield-himalayan-411-2015-2023-global",
        "group": "Adventure",
    },
    {
        "slug": "classic-350-vs-hunter-350",
        "title": "Classic 350 vs Hunter 350",
        "description": "Royal Enfield Classic 350 vs Hunter 350: weight, seat height, power and specifications compared.",
        "verdict": "The Classic 350 is the traditional, relaxed Royal Enfield; the Hunter 350 is lighter, shorter and more city-focused.",
        "a": "royal-enfield-classic-350-2021-present-global",
        "b": "royal-enfield-hunter-350-2022-present-global",
        "group": "Retro",
    },
    {
        "slug": "interceptor-650-vs-continental-gt-650",
        "title": "Interceptor 650 vs Continental GT 650",
        "description": "Royal Enfield Interceptor 650 vs Continental GT 650: power, weight, seat height and specifications compared.",
        "verdict": "Both use the same 648 cc twin; the Interceptor has upright bars and a more relaxed ride, while the Continental GT has clip-ons and a café-racer stance.",
        "a": "royal-enfield-interceptor-650-2018-present-global",
        "b": "royal-enfield-continental-gt-650-2019-present-global",
        "group": "Retro",
    },
]

SEGMENT_COMPARISONS = [
    {
        "slug": "under-500cc-adventure-motorcycles",
        "title": "Under 500cc Adventure Motorcycles Compared",
        "description": "Under-500cc adventure bikes compared: Xpulse 210, KTM 250 and 390 Adventure, V-Strom SX 250, Versys-X 300, G 310 GS, Himalayan 450, NX500, 450MT, F 450 GS and TRK 502.",
        "intro": "This group covers adventure and adventure-styled motorcycles up to 500cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres. Use it to narrow the class by size, seat height and tank range before a test ride.",
        "models": [
            "hero-xpulse-210-2025-present-global",
            "ktm-250-adventure-2020-present-global",
            "suzuki-v-strom-sx-250-2022-present-india",
            "kawasaki-versys-x-300-2017-present-global",
            "bmw-g-310-gs-2018-present-global",
            "ktm-adventure-390-2025-present-global",
            "royal-enfield-himalayan-450",
            "cfmoto-450mt-2024-present-global",
            "bmw-f450gs-2026-present-global",
            "honda-nx500-2023-present-global",
            "benelli-trk-502-2017-present-global",
        ],
    },
    {
        "slug": "under-500cc-tourers",
        "title": "Under 500cc Touring Motorcycles Compared",
        "description": "Under-500cc tourers compared: Honda NX500, Benelli TRK 502, Kawasaki Versys-X 300, Suzuki V-Strom SX 250, BMW G 310 GS, KTM 390 Adventure and Royal Enfield Himalayan 450.",
        "intro": "These are the road-biased touring options in the sub-500cc class. The comparison focuses on seat height, fuel capacity, weight and highway-friendly power rather than hard off-road hardware.",
        "models": [
            "suzuki-v-strom-sx-250-2022-present-india",
            "kawasaki-versys-x-300-2017-present-global",
            "bmw-g-310-gs-2018-present-global",
            "ktm-adventure-390-2025-present-global",
            "royal-enfield-himalayan-450",
            "honda-nx500-2023-present-global",
            "benelli-trk-502-2017-present-global",
        ],
    },
    {
        "slug": "budget-tourers",
        "title": "Budget Touring Motorcycles Compared",
        "description": "Budget-focused 200–500cc tourers compared: Xpulse 200 4V, Xpulse 210, KTM 250 Adventure, V-Strom SX 250, Versys-X 300, Himalayan 411 and BMW G 310 GS.",
        "intro": "This page groups the smaller-capacity touring and adventure-styled models. It compares specifications, not live prices: taxes, local pricing and equipment vary by market. Use the table to shortlist by seat height, weight, tank size and output.",
        "models": [
            "hero-xpulse-200-4v-2022-present-global",
            "hero-xpulse-210-2025-present-global",
            "ktm-250-adventure-2020-present-global",
            "suzuki-v-strom-sx-250-2022-present-india",
            "kawasaki-versys-x-300-2017-present-global",
            "royal-enfield-himalayan-411-2015-2023-global",
            "bmw-g-310-gs-2018-present-global",
        ],
    },
    {
        "slug": "under-500cc-twin-cylinder-sportbikes",
        "title": "Under 500cc Twin-Cylinder Sportbikes Compared",
        "description": "Twin-cylinder sportbikes under 500cc compared: Yamaha R3, Kawasaki Ninja 400 and 500, Honda CBR500R, CFMOTO 450SR and Aprilia RS 457.",
        "intro": "This group covers parallel-twin sportbikes below 500cc. The table compares claimed power and torque, weight, seat height, fuel capacity, suspension, brakes and tyres so the class can be compared on like-for-like listed data.",
        "models": [
            "yamaha-r3-2019-present-global",
            "kawasaki-ninja-400-2018-present",
            "kawasaki-ninja-500-2024-present",
            "honda-cbr500r-2022-present-global",
            "cfmoto-450sr-2022-present-global",
            "aprilia-rs-457-2023-present-global",
        ],
    },
    {
        "slug": "single-cylinder-sportbikes",
        "title": "Single-Cylinder Sportbikes Compared",
        "description": "Single-cylinder sportbikes compared: Yamaha R15 V4, KTM RC 200 and RC 390, TVS Apache RR 310, BMW G 310 RR, Honda CBR300R and Hero Karizma XMR 210.",
        "intro": "This group covers single-cylinder sport and sporty-commuter models. The comparison includes lightweight 150–200cc machines alongside 300–390cc sportbikes, so seat height and weight matter as much as peak power.",
        "models": [
            "yamaha-yzf-r15-v4-2021-present-global",
            "ktm-rc-200-2014-present-global",
            "ktm-rc-390",
            "tvs-apache-rr-310-2020-present-india",
            "bmw-g310rr-2015-2025",
            "honda-cbr-300-r-2014-2021-global",
            "hero-karizma-xmr-210-2023-present-india",
        ],
    },
    {
        "slug": "600cc-sportbikes",
        "title": "600cc Sportbikes Compared",
        "description": "600-class sportbikes compared: CBR600RR, GSX-R600, YZF-R6, Ninja ZX-6R, CBR650R, Aprilia RS 660 and Triumph Daytona 660.",
        "intro": "This page covers the 599–660cc sportbike class, including traditional inline-four supersports and newer twin- and triple-cylinder alternatives. Model years differ across the group; the table lists the catalogue entry for each machine.",
        "models": [
            "honda-cbr600rr-2013",
            "suzuki-gsx-r600-2011-present-global",
            "yamaha-yzf-r6-2017-2020-global",
            "kawasaki-ninja-zx-6r",
            "honda-cbr650r-2024-present-global",
            "aprilia-rs-660-2020-present-global",
            "triumph-daytona-660-2024-present-global",
        ],
    },
    {
        "slug": "160cc-sporty-commuters",
        "title": "160cc Sporty Commuters Compared",
        "description": "150–210cc sporty commuters compared: Yamaha R15 V4, Hero Karizma XMR 210, TVS Apache RTR 160 4V, Bajaj Pulsar N160 and Hero Xtreme 160R 4V.",
        "intro": "This group covers the 150–210cc sporty-commuter class. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres; model years differ across the group.",
        "models": [
            "yamaha-yzf-r15-v4-2021-present-global",
            "hero-karizma-xmr-210-2023-present-india",
            "tvs-apache-rtr-160-4v-2020-present-india",
            "bajaj-pulsar-n160-2022-present-india",
            "hero-xtreme-160r-4v-2023-present-india",
        ],
    },
    {
        "slug": "125cc-commuters",
        "title": "125cc Commuter Motorcycles Compared",
        "description": "100–125cc commuters compared: Hero Splendor Plus, Honda Shine 125, TVS Raider 125, Hero Glamour, Hero Passion Pro and Bajaj Platina 110.",
        "intro": "This group covers the 100–125cc commuter class. The comparison focuses on seat height, weight, fuel capacity and listed output; model years differ across the group.",
        "models": [
            "hero-splendor-plus-2010-present-india",
            "honda-shine-125-2018-present-india",
            "tvs-raider-125-2021-present-india",
            "hero-glamour-2020-present-india",
            "hero-passion-pro-2020-present-india",
            "bajaj-platina-110-2019-present-india",
        ],
    },
    {
        "slug": "250-400cc-naked-bikes",
        "title": "250–400cc Naked Bikes Compared",
        "description": "250–400cc naked bikes compared: KTM 390 Duke, Husqvarna Svartpilen 401, BMW G 310 R, Honda CB300R and KTM 250 Duke.",
        "intro": "This group covers naked and roadster models from roughly 250 to 400cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres.",
        "models": [
            "ktm-390-duke-2021",
            "husqvarna-svartpilen-401-2020-present-global",
            "bmw-g310r-2015-2025-global",
            "honda-cb300r-2018-present-global",
            "ktm-250-duke-2015-present-global",
        ],
    },
    {
        "slug": "350-500cc-retro-motorcycles",
        "title": "350–500cc Retro Motorcycles Compared",
        "description": "350–500cc retro motorcycles compared: Royal Enfield Classic 350, Hunter 350, Bullet 350, Honda CB350, Jawa 42 and Benelli Imperiale 400.",
        "intro": "This group covers retro roadsters and classic-styled models from roughly 350 to 500cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres.",
        "models": [
            "royal-enfield-classic-350-2021-present-global",
            "royal-enfield-hunter-350-2022-present-global",
            "royal-enfield-bullet-350-2023-present-global",
            "honda-cb350-2021-present-india",
            "jawa-42-2019-present-india",
            "benelli-imperiale-400-2019-present-global",
        ],
    },
    {
        "slug": "300-500cc-cruisers",
        "title": "300–500cc Cruisers Compared",
        "description": "300–500cc cruisers compared: Honda Rebel 300, Honda Rebel 500, Kawasaki Eliminator 500, Royal Enfield Meteor 350 and Benelli 502C.",
        "intro": "This group covers entry and mid-capacity cruisers from roughly 300 to 500cc. The comparison focuses on seat height, weight, tank size and listed output.",
        "models": [
            "honda-rebel-300-2017-present-global",
            "honda-rebel-500-2017-present-global",
            "kawasaki-eliminator-500-2023-present-global",
            "royal-enfield-meteor-350-2021-present-global",
            "benelli-502c-2021-present-global",
        ],
    },
    {
        "slug": "125cc-sportbikes",
        "title": "125cc Sportbikes Compared",
        "description": "125cc sportbikes compared: Yamaha YZF-R125, Aprilia RS 125, KTM RC 125, Kawasaki Ninja 125 and Suzuki GSX-R125.",
        "intro": "This group covers the 125cc sportbike class. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres.",
        "models": [
            "yamaha-yzf-r125-2008-present-global",
            "aprilia-rs-125-2021-present-global",
            "ktm-rc-125-2014-present-global",
            "kawasaki-ninja-125-2019-present-global",
            "suzuki-gsx-r125-2017-present-global",
        ],
    },
    {
        "slug": "250-450cc-dual-sport",
        "title": "250–450cc Dual-Sport Motorcycles Compared",
        "description": "250–450cc dual-sport bikes compared: Honda CRF300L, CRF300 Rally, Kawasaki KLX300, Kove 450 Rally and Voge 300 Rally.",
        "intro": "This group covers lightweight dual-sport models from roughly 250 to 450cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres. Tall seats and long suspension travel are central to this class.",
        "models": [
            "honda-crf300l-2021-present-global",
            "honda-crf300-rally-2021-present-global",
            "kawasaki-klx300-2021-present-global",
            "kove-450-rally-2023-present-global",
            "voge-300-rally-2022-present-global",
        ],
    },
    {
        "slug": "650-900cc-naked-bikes",
        "title": "650–900cc Naked Bikes Compared",
        "description": "650–900cc naked bikes compared: Yamaha MT-07 and MT-09, Triumph Street Triple 765, Ducati Monster 821, Suzuki SV650, Kawasaki Z650 and Honda CB650R.",
        "intro": "This group covers roadster and naked models from roughly 650 to 900cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres.",
        "models": [
            "yamaha-mt-07-2018",
            "yamaha-mt-09-2015-2018-global",
            "triumph-street-triple-765-2023-present-global",
            "ducati-monster-821-2014-2020-global",
            "suzuki-sv650-2016-present-global",
            "kawasaki-z650-2017-present-global",
            "honda-cb650r-2019-present-global",
        ],
    },
    {
        "slug": "650-900cc-adventure",
        "title": "650–900cc Adventure Motorcycles Compared",
        "description": "650–900cc adventure bikes compared: Kawasaki Versys 650, Suzuki V-Strom 650, Aprilia Tuareg 660, Honda NC750X and Yamaha Tracer 900.",
        "intro": "This group covers middleweight adventure and adventure-touring models from roughly 650 to 900cc. The table compares listed power, torque, weight, seat height, fuel capacity, suspension, brakes and tyres.",
        "models": [
            "kawasaki-versys-650-2022-present-global",
            "suzuki-v-strom-650-2017-present-global",
            "aprilia-tuareg-660-2022-present-global",
            "honda-nc750x-2021-present-global",
            "yamaha-mt-09-900-tracer-2015-2020-global",
        ],
    },
    {
        "slug": "sport-touring-650-900",
        "title": "650–900cc Sport-Touring Motorcycles Compared",
        "description": "650–900cc sport-tourers compared: Kawasaki Ninja 650, Honda CBR650R, Triumph Tiger Sport 660 and Yamaha Tracer 700.",
        "intro": "This group covers road-biased sport-touring models from roughly 650 to 900cc. The comparison focuses on seat height, weight, tank size, weather protection and listed output rather than off-road hardware.",
        "models": [
            "kawasaki-ninja-650-2021-present",
            "honda-cbr650r-2024-present-global",
            "triumph-tiger-sport-660-2022-present-global",
            "yamaha-mt-07-700-tracer-2016-2020-global",
        ],
    },
    {
        "slug": "650-900cc-cruisers",
        "title": "650–900cc Cruisers Compared",
        "description": "650–900cc cruisers compared: Kawasaki Vulcan S, Royal Enfield Super Meteor 650, Royal Enfield Shotgun 650 and Harley-Davidson Street 750.",
        "intro": "This group covers middleweight cruisers from roughly 650 to 900cc. The comparison focuses on seat height, weight, tank size and listed output. It complements the separate 300–500cc cruiser comparison.",
        "models": [
            "kawasaki-vulcan-s-2015-present-global",
            "royal-enfield-super-meteor-650-2023-present-global",
            "royal-enfield-shotgun-650-2024-present-global",
            "harley-davidson-street-2013-2021-global",
        ],
    },
    {
        "slug": "electric-motorcycles",
        "title": "Electric Motorcycles Compared",
        "description": "Electric motorcycles compared: Zero SR/F, LiveWire S2 Del Mar, Energica Eva Ribelle, Zero DSR/X, Energica Experia and Stark Varg.",
        "intro": "This group covers electric road, adventure and off-road motorcycles. The table compares listed power, torque, weight, seat height, suspension, brakes and tyres; battery capacity and range are not compared because the catalogue does not hold consistent battery data for every model.",
        "models": [
            "zero-sr-f-2020-present-global",
            "livewire-s2-del-mar-2023-present-global",
            "energica-eva-ribelle-2015-2021-global",
            "zero-dsr-x-2022-present-global",
            "energica-experia-2022-present-global",
            "stark-varg-2023-present-global",
        ],
    },
]

COMPARISON_LINKS = {}
for _comparison in COMPARISONS:
    _link = (f"{_comparison['slug']}.html", _comparison["title"])
    for _key in ("a", "b"):
        COMPARISON_LINKS.setdefault(_comparison[_key], []).append(_link)

SEGMENT_LINKS = {}
for _segment in SEGMENT_COMPARISONS:
    _segment_link = (f"{_segment['slug']}.html", _segment["title"])
    for _model_id in _segment["models"]:
        SEGMENT_LINKS.setdefault(_model_id, []).append(_segment_link)


def build_model_pages(bikes, brand_links):
    os.makedirs(MODELS, exist_ok=True)
    for entry in os.listdir(MODELS):
        if entry.endswith(".html"):
            os.remove(os.path.join(MODELS, entry))
    by_group = {}
    pad_index = {}
    for bike in bikes:
        group = bike.get("model_group") or ""
        if group:
            by_group.setdefault(group, []).append(bike)
        for key in ("front_brake_pads", "rear_brake_pads"):
            code = service(bike, key)
            if code:
                pad_index.setdefault(code, []).append(bike)
    for bike in bikes:
        related = [b for b in by_group.get(bike.get("model_group") or "", []) if b["id"] != bike["id"]][:6]
        if not related:
            related = [b for b in bikes if b["id"] != bike["id"] and b.get("make") == bike.get("make") and b.get("category") == bike.get("category")][:6]
        pad_codes = {
            code for code in (
                service(bike, "front_brake_pads"),
                service(bike, "rear_brake_pads"),
            ) if code
        }
        pad_related = []
        seen_pad_ids = set()
        for code in sorted(pad_codes):
            for candidate in pad_index.get(code, []):
                if candidate["id"] == bike["id"] or candidate["id"] in seen_pad_ids:
                    continue
                seen_pad_ids.add(candidate["id"])
                pad_related.append(candidate)
        pad_related.sort(key=lambda candidate: (
            candidate.get("make") != bike.get("make"),
            candidate.get("category") != bike.get("category"),
            name(candidate).lower(),
        ))
        pad_related = pad_related[:6]
        category = (bike.get("category") or "").lower()
        guides = [
            ("parts-fitment-codes.html", "Parts and fitment codes"),
            ("../reference/brake-pad-fitment.html", "Brake pad fitment table"),
            ("oil-capacity-chart.html", "Motorcycle oil capacity chart"),
            ("seat-height-chart.html", "Motorcycle seat height chart"),
            ("a2-motorcycles.html", "A2 motorcycles"),
            ("best-beginner-motorcycles.html", "Best beginner motorcycles"),
            ("torque-specs.html", "Motorcycle torque specs")
        ]
        comparisons = SEGMENT_LINKS.get(bike["id"], []) + COMPARISON_LINKS.get(bike["id"], [])
        if comparisons:
            guides = comparisons + guides
        if category == "scooter":
            guides.insert(0, ("best-scooters.html", "Best scooters"))
        elif category in ("adventure", "dual sport"):
            guides.insert(0, ("best-adventure-motorcycles.html", "Best adventure motorcycles"))
        elif category == "cruiser":
            guides.insert(0, ("best-cruiser-motorcycles.html", "Best cruiser motorcycles"))
        elif category == "commuter":
            guides.insert(0, ("best-commuter-motorcycles.html", "Best commuter motorcycles"))
        elif category in ("retro", "scrambler"):
            guides.insert(0, ("best-retro-motorcycles.html", "Best retro motorcycles"))
        model_page(bike, related, pad_related, guides[:7], brand_links.get(bike.get("make", ""), "../reference/brands.html"))
    return len(bikes)


def inject_third_party_codes():
    head_parts = [
        str(THIRD_PARTY.get("verification") or "").strip(),
        f"<style>{str(THIRD_PARTY.get('customCss') or '').strip()}</style>" if str(THIRD_PARTY.get("customCss") or "").strip() else "",
        str(THIRD_PARTY.get("head") or "").strip(),
    ]
    head_parts = [part for part in head_parts if part]
    body_start = str(THIRD_PARTY.get("bodyStart") or "").strip()
    body_end = str(THIRD_PARTY.get("bodyEnd") or "").strip()

    head_block = (
        "<!-- MX-HEAD-START -->\n" + "\n".join(head_parts) + "\n<!-- MX-HEAD-END -->"
        if head_parts else ""
    )
    body_start_block = (
        "<!-- MX-BODY-START -->\n" + body_start + "\n<!-- MX-BODY-END -->"
        if body_start else ""
    )
    body_end_block = (
        "<!-- MX-BODY-END-START -->\n" + body_end + "\n<!-- MX-BODY-END-END -->"
        if body_end else ""
    )

    paths = []
    for directory in (GUIDES, REFERENCE, MODELS):
        paths.extend(
            os.path.join(directory, name)
            for name in os.listdir(directory)
            if name.endswith(".html")
        )
    for name in ("index.html", "pages.html"):
        path = os.path.join(ROOT, name)
        if os.path.exists(path):
            paths.append(path)

    persistent_markers = {
        os.path.join(ROOT, "index.html"),
        os.path.join(ROOT, "pages.html"),
    }

    changed = 0
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        updated = re.sub(r"<!-- MX-HEAD-START -->.*?<!-- MX-HEAD-END -->\n?", "", text, flags=re.S)
        updated = re.sub(r"<!-- MX-BODY-START -->.*?<!-- MX-BODY-END -->\n?", "", updated, flags=re.S)
        updated = re.sub(r"<!-- MX-BODY-END-START -->.*?<!-- MX-BODY-END-END -->\n?", "", updated, flags=re.S)
        persistent = path in persistent_markers
        head_value = head_block or ("<!-- MX-HEAD-START --><!-- MX-HEAD-END -->" if persistent else "")
        body_start_value = body_start_block or ("<!-- MX-BODY-START --><!-- MX-BODY-END -->" if persistent else "")
        body_end_value = body_end_block or ("<!-- MX-BODY-END-START --><!-- MX-BODY-END-END -->" if persistent else "")
        if head_value and "</head>" in updated:
            updated = updated.replace("</head>", head_value + "\n</head>", 1)
        if body_start_value:
            match = re.search(r"<body[^>]*>", updated)
            if match:
                updated = updated[:match.end()] + "\n" + body_start_value + updated[match.end():]
        if body_end_value and "</body>" in updated:
            updated = updated.replace("</body>", body_end_value + "\n</body>", 1)
        if updated != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(updated)
            changed += 1
    return changed


def main():
    global bikes
    bikes, pages = load()
    os.makedirs(GUIDES, exist_ok=True)
    for entry in os.listdir(GUIDES):
        if entry.endswith(".html"):
            os.remove(os.path.join(GUIDES, entry))
    os.makedirs(REFERENCE, exist_ok=True)
    for entry in os.listdir(REFERENCE):
        if entry.endswith(".html"):
            os.remove(os.path.join(REFERENCE, entry))

    brand_urls, brand_links = build_brand_pages(bikes)
    model_count = build_model_pages(bikes, brand_links)
    urls = []
    urls.extend(brand_urls)
    urls.append(build_index(bikes))
    urls.append(build_oil_chart(bikes))
    urls.append(build_seat_chart(bikes))
    urls.append(build_weight_chart(bikes))
    urls.append(build_hp_chart(bikes))
    urls.append(build_torque_page(bikes))
    urls.append(build_parts_fitment(bikes))
    urls.append(build_brake_fitment(bikes))
    urls.append(build_pad_shape_crossref(bikes))
    urls.append(build_tyre_finder(bikes))
    urls.append(build_fork_seal_finder(bikes))
    urls.append(build_battery_finder(bikes))
    urls.append(build_beginner(bikes))
    urls.append(build_a2(bikes))
    urls.append(build_125(bikes))
    urls.append(category_page(
        "best-scooters", "Best Scooters",
        "Every scooter in the MotoX Wiki catalogue, from 110 cc commuters to 560 cc maxi-scooters.",
        "Best Scooters", "Scooters from 110 cc to 560 cc.",
        "Scooters are the practical end of motorcycling: CVT drive, storage, weather protection and low running costs. This page lists every scooter in the catalogue with power, weight and seat height.",
        "Scooter", "Best Scooters"
    ))
    urls.append(category_page(
        "best-adventure-motorcycles", "Best Adventure Motorcycles",
        "Adventure and dual-sport motorcycles in the catalogue, with power, weight and seat height.",
        "Best Adventure Motorcycles", "Adventure and dual-sport models.",
        "Adventure bikes trade some road focus for suspension travel, upright ergonomics and luggage capacity. Compare engine size, weight, seat height and power before choosing.",
        "Adventure", "Best Adventure Motorcycles"
    ))
    urls.append(category_page(
        "best-cruiser-motorcycles", "Best Cruiser Motorcycles",
        "Cruisers and baggers from Harley-Davidson, Indian, Royal Enfield, Honda, Kawasaki and more.",
        "Best Cruiser Motorcycles", "Cruisers and baggers in the catalogue.",
        "Cruisers prioritise low seats, torque and relaxed ergonomics. This list covers the class from 350 cc singles to 1,923 cc V-twins.",
        "Cruiser", "Best Cruiser Motorcycles"
    ))
    electric = [
        b for b in bikes
        if not b.get("fitment_only") and (
            str(b.get("displacement", "")).strip() in ("—", "-", "")
            or "electric" in (field(b, "engine") or "").lower()
        )
    ]
    urls.append(list_page(
        "best-electric-motorcycles", "Best Electric Motorcycles",
        "Electric motorcycles and scooters in the catalogue, with power, torque, weight and range data where available.",
        "Best Electric Motorcycles", "Electric motorcycles and scooters.",
        "Electric models deliver instant torque and low running costs, but battery capacity, charging and dealer support vary widely. Compare the models here before shortlisting.",
        electric, lambda b: (-hp(b), name(b)),
        [("Power", lambda b: esc(field(b, "power"))), ("Torque", lambda b: esc(field(b, "torque"))), ("Weight", lambda b: esc(field(b, "weight"))), ("Seat height", lambda b: esc(field(b, "seat_height")))],
        "Best Electric Motorcycles"
    ))
    urls.append(category_page(
        "best-commuter-motorcycles", "Best Commuter Motorcycles",
        "Commuter motorcycles and scooters with practical fuel economy, light weight and low seat heights.",
        "Best Commuter Motorcycles", "Practical bikes for daily transport.",
        "Commuting prioritises fuel economy, light weight, low seat height and easy maintenance. This list covers commuter-class models in the catalogue.",
        "Commuter", "Best Commuter Motorcycles"
    ))
    urls.append(category_page(
        "best-retro-motorcycles", "Best Retro Motorcycles",
        "Retro roadsters, scramblers and modern classics with specifications and links.",
        "Best Retro Motorcycles", "Modern classics and retro roadsters.",
        "Retro bikes combine classic styling with modern brakes, ABS and fuel injection. This list covers the category across engine sizes and price points.",
        "Retro", "Best Retro Motorcycles"
    ))
    urls.append(build_low_seat(bikes))

    id_map = {b["id"]: b for b in bikes}
    for item in COMPARISONS:
        a, b = id_map[item["a"]], id_map[item["b"]]
        urls.append(comparison(item, a, b))
    for item in SEGMENT_COMPARISONS:
        models = [id_map[model_id] for model_id in item["models"]]
        urls.append(segment_comparison(item, models))
    urls.append(build_comparisons_hub())

    build_brake_redirect()
    sync_reference_index(bikes, pages)

    # Sitemap
    model_urls = [f"{SITE}/motorcycle/{quote(b['id'])}.html" for b in bikes]
    page_urls = [f"{SITE}/pages.html?slug={quote(p.get('slug') or p['id'])}" for p in pages]
    urls = [f"{SITE}/", f"{SITE}/pages.html"] + page_urls + [f"{SITE}/guides/"] + urls + model_urls
    image_map = {}
    for bike in bikes:
        image_url = bike_image_url(bike, "jpg", "1200")
        if image_url:
            image_map[f"{SITE}/motorcycle/{quote(bike['id'])}.html"] = image_url
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n')
        for url in sorted(set(urls)):
            priority = "1.0" if url == f"{SITE}/" else "0.7" if "/motorcycle.html" in url else "0.6"
            image_xml = ""
            if url in image_map:
                image_xml = f"<image:image><image:loc>{image_map[url]}</image:loc></image:image>"
            fh.write(f"  <url><loc>{url}</loc><lastmod>{LAST_MOD}</lastmod><priority>{priority}</priority>{image_xml}</url>\n")
        fh.write("</urlset>\n")
    injected = inject_third_party_codes()
    with open(os.path.join(DATA, "reference-pages-index.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {"pages": sorted(REFERENCE_PAGE_META.values(), key=lambda item: (item["group"], item["title"].lower()))},
            fh,
            ensure_ascii=False,
            indent=2,
        )
        fh.write("\n")
    print(f"Generated {len(urls)} sitemap URLs, {len(os.listdir(GUIDES))} guide files, {len(os.listdir(REFERENCE))} reference pages and {model_count} model pages")
    if injected:
        print(f"Injected third-party code into {injected} pages")


if __name__ == "__main__":
    main()

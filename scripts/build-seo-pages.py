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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
GUIDES = os.path.join(ROOT, "guides")
SITE = "https://motoxref.com"
LAST_MOD = "2026-11-20"


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
    return f"{bike.get('make', '')} {bike.get('model', '')}".strip()


def title(bike):
    return f"{name(bike)} ({bike.get('year', '')})"


def bike_url(bike):
    return f"../motorcycle.html?id={quote(bike['id'])}"


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
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="spec-table-wrap"><table class="spec-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def related_guides(links):
    return '<h2>Related guides</h2><ul>' + "".join(
        f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in links
    ) + "</ul>"


def guide_page(slug, page_title, description, h1, subtitle, content, breadcrumb, extra_json=None):
    canonical = f"{SITE}/guides/{slug}.html" if slug != "index" else f"{SITE}/guides/"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": h1,
        "description": description,
        "url": canonical,
        "dateModified": LAST_MOD,
        "publisher": {"@type": "Organization", "name": "MotoX Wiki", "url": SITE}
    }
    graph = [jsonld, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
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
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="../css/main.css?v=21">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3716738858398465" crossorigin="anonymous"></script>
  <script type="application/ld+json">{json.dumps(graph, ensure_ascii=False)}</script>
</head>
<body>
  <header class="site-header static-header">
    <div class="container">
      <div class="header-row">
        <a class="brand" href="../index.html"><span class="brand-icon">⚙</span><span>MotoX Wiki</span></a>
      </div>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="../index.html">Browse</a>
        <a href="index.html" class="active">Guides</a>
        <a href="oil-capacity-chart.html">Oil Charts</a>
        <a href="../pages.html">Reference</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <div class="bike-header">
      <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="index.html">Guides</a> / {esc(breadcrumb)}</div>
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


def build_index(bikes):
    cards = [
        ("oil-capacity-chart", "Motorcycle Oil Capacity Chart", "Engine oil capacity and oil grade for every model with verified service data."),
        ("seat-height-chart", "Motorcycle Seat Height Chart", "Seat heights for 409 motorcycles, including a low-seat section for shorter riders."),
        ("weight-chart", "Motorcycle Weight Chart", "Kerb weights across every model, useful for A2, garage and touring decisions."),
        ("horsepower-chart", "Motorcycle Horsepower Chart", "Power and torque figures sorted from highest to lowest."),
        ("torque-specs", "Motorcycle Torque Specifications", "Fastener torque tables and links to model-specific torque data."),
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
        ("cbr600rr-vs-cbr650r", "CBR600RR vs CBR650R", "On-paper comparison of Honda's 600 cc supersport and 650 cc sportbike."),
        ("mt-07-vs-mt-09", "MT-07 vs MT-09", "Yamaha's CP2 and CP3 nakeds compared."),
        ("ninja-400-vs-ninja-500", "Ninja 400 vs Ninja 500", "Kawasaki's lightweight parallel-twin sportbikes compared."),
        ("classic-350-vs-hunter-350", "Classic 350 vs Hunter 350", "Royal Enfield's classic and city roadster compared."),
        ("himalayan-450-vs-411", "Himalayan 450 vs 411", "Old and new Royal Enfield adventure singles compared."),
        ("interceptor-650-vs-continental-gt-650", "Interceptor 650 vs Continental GT 650", "Royal Enfield's 650 twins compared."),
    ]
    items = "".join(f'<a class="page-item" href="{slug}.html"><h2>{esc(t)}</h2><p>{esc(d)}</p></a>' for slug, t, d in cards)
    content = f"""
      <p>These guides turn the MotoX Wiki catalogue into practical answers: oil capacities, seat heights, weights, horsepower, torque data, buying shortlists and direct model comparisons.</p>
      <div class="page-list">{items}</div>
    """
    return guide_page(
        "index", "Motorcycle Specs Guides, Charts & Comparisons",
        "Motorcycle oil capacity charts, seat height charts, weight and horsepower lists, A2 and beginner guides, and model comparisons.",
        "Motorcycle Guides, Charts & Comparisons",
        "Data-driven guides built from 409 motorcycle specifications.",
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
      <p>This chart lists published engine-oil capacities and recommended oil grades for {len(rows)} motorcycles. Oil capacity is shown with a filter change where the source specifies it; always confirm the exact fill procedure in the workshop manual.</p>
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
    candidates = [b for b in bikes if displacement(b) and displacement(b) <= 155]
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
    candidates = [b for b in bikes if (b.get("category") or "").lower() == category.lower()]
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


def comparison(slug, page_title, description, h1, subtitle, a, b, verdict):
    fields = [
        ("Engine", lambda x: field(x, "engine")),
        ("Displacement", lambda x: x.get("displacement", "")),
        ("Max power", lambda x: field(x, "power")),
        ("Max torque", lambda x: field(x, "torque")),
        ("Kerb weight", lambda x: field(x, "weight")),
        ("Seat height", lambda x: field(x, "seat_height")),
        ("Fuel capacity", lambda x: field(x, "fuel_capacity")),
        ("Transmission", lambda x: field(x, "transmission")),
        ("Front suspension", lambda x: field(x, "front_suspension")),
        ("Front brake", lambda x: field(x, "front_brake")),
        ("Tyres", lambda x: field(x, "tyres")),
        ("Oil capacity", lambda x: service(x, "oil_capacity")),
    ]
    rows = "".join(
        f"<tr><th>{esc(label)}</th><td>{esc(fn(a))}</td><td>{esc(fn(b))}</td></tr>"
        for label, fn in fields
    )
    content = f"""
      <p>{esc(verdict)}</p>
      <div class="spec-table-wrap"><table class="spec-table"><thead><tr><th>Specification</th><th>{bike_link(a)}</th><th>{bike_link(b)}</th></tr></thead><tbody>{rows}</tbody></table></div>
      <h2>On-paper differences</h2>
      <ul>
        <li><strong>Power:</strong> {esc(name(a))} {esc(field(a, "power"))} vs {esc(name(b))} {esc(field(b, "power"))}.</li>
        <li><strong>Weight:</strong> {esc(field(a, "weight"))} vs {esc(field(b, "weight"))}.</li>
        <li><strong>Seat height:</strong> {esc(field(a, "seat_height"))} vs {esc(field(b, "seat_height"))}.</li>
        <li><strong>Fuel capacity:</strong> {esc(field(a, "fuel_capacity"))} vs {esc(field(b, "fuel_capacity"))}.</li>
      </ul>
      <p>Use the linked model pages for the full specification, service data and torque tables. The better bike depends on your licence, riding mix, inseam, luggage and budget — this comparison is a starting point, not a verdict.</p>
      {related_guides([("best-beginner-motorcycles.html", "Best beginner motorcycles"), ("a2-motorcycles.html", "A2 motorcycles"), ("seat-height-chart.html", "Motorcycle seat height chart")])}
    """
    return guide_page(slug, page_title, description, h1, subtitle, content, h1)


def main():
    global bikes
    bikes, pages = load()
    os.makedirs(GUIDES, exist_ok=True)
    for entry in os.listdir(GUIDES):
        if entry.endswith(".html"):
            os.remove(os.path.join(GUIDES, entry))

    urls = []
    urls.append(build_index(bikes))
    urls.append(build_oil_chart(bikes))
    urls.append(build_seat_chart(bikes))
    urls.append(build_weight_chart(bikes))
    urls.append(build_hp_chart(bikes))
    urls.append(build_torque_page(bikes))
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
        if str(b.get("displacement", "")).strip() in ("—", "-", "")
        or "electric" in (field(b, "engine") or "").lower()
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

    comparisons = [
        ("cbr600rr-vs-cbr650r", "cbr600rr-vs-cbr650r", "CBR600RR vs CBR650R", "Honda CBR600RR vs CBR650R — specs, weight and seat height compared.",
         "The CBR600RR is the sharper track-focused 600, while the CBR650R is the more usable road bike with a broader powerband and comfortable ergonomics."),
        ("mt-07-vs-mt-09", "mt-07-vs-mt-09", "MT-07 vs MT-09", "Yamaha MT-07 vs MT-09 — CP2 twin vs CP3 triple compared.",
         "The MT-07 is lighter and cheaper to run; the MT-09 adds a three-cylinder engine, more power and more equipment."),
        ("ninja-400-vs-ninja-500", "ninja-400-vs-ninja-500", "Ninja 400 vs Ninja 500", "Kawasaki Ninja 400 vs Ninja 500 — specs and differences.",
         "The Ninja 500 replaces the 400 with a larger, torquier engine while keeping the same lightweight formula."),
        ("classic-350-vs-hunter-350", "classic-350-vs-hunter-350", "Classic 350 vs Hunter 350", "Royal Enfield Classic 350 vs Hunter 350 — weight, seat height and character.",
         "The Classic 350 is the traditional, relaxed Royal Enfield; the Hunter 350 is lighter, shorter and more city-focused."),
        ("himalayan-450-vs-411", "himalayan-450-vs-411", "Himalayan 450 vs 411", "Royal Enfield Himalayan 450 vs 411 — old vs new adventure single.",
         "The Himalayan 450 brings a new liquid-cooled engine, more power and a modern chassis; the 411 is simpler and lighter on electronics."),
        ("interceptor-650-vs-continental-gt-650", "interceptor-650-vs-continental-gt-650", "Interceptor 650 vs Continental GT 650", "Royal Enfield Interceptor 650 vs Continental GT 650 — roadster vs café racer.",
         "Both use the same 648 cc twin; the Interceptor has upright bars and a more relaxed ride, while the Continental GT has clip-ons and a café-racer stance."),
    ]
    id_map = {b["id"]: b for b in bikes}
    for slug, page_slug, h1, desc, verdict in comparisons:
        pairs = {
            "cbr600rr-vs-cbr650r": ("honda-cbr600rr-2013", "honda-cbr650r-2024-present-global"),
            "mt-07-vs-mt-09": ("yamaha-mt-07-2018", "yamaha-mt-09-2015-2018-global"),
            "ninja-400-vs-ninja-500": ("kawasaki-ninja-400-2018-present", "kawasaki-ninja-500-2024-present"),
            "classic-350-vs-hunter-350": ("royal-enfield-classic-350-2021-present-global", "royal-enfield-hunter-350-2022-present-global"),
            "himalayan-450-vs-411": ("royal-enfield-himalayan-450", "royal-enfield-himalayan-411-2015-2023-global"),
            "interceptor-650-vs-continental-gt-650": ("royal-enfield-interceptor-650-2018-present-global", "royal-enfield-continental-gt-650-2019-present-global"),
        }[slug]
        a, b = id_map[pairs[0]], id_map[pairs[1]]
        urls.append(comparison(slug, h1, desc, h1, f"{name(a)} vs {name(b)}", a, b, verdict))

    # Sitemap
    model_urls = [f"{SITE}/motorcycle.html?id={quote(b['id'])}" for b in bikes]
    page_urls = [f"{SITE}/pages.html?slug={quote(p.get('slug') or p['id'])}" for p in pages]
    urls = [f"{SITE}/", f"{SITE}/pages.html"] + page_urls + [f"{SITE}/guides/"] + urls + model_urls
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in sorted(set(urls)):
            priority = "1.0" if url == f"{SITE}/" else "0.7" if "/motorcycle.html" in url else "0.6"
            fh.write(f"  <url><loc>{url}</loc><lastmod>{LAST_MOD}</lastmod><priority>{priority}</priority></url>\n")
        fh.write("</urlset>\n")
    print(f"Generated {len(urls)} sitemap URLs and {len(os.listdir(GUIDES))} guide files")


if __name__ == "__main__":
    main()

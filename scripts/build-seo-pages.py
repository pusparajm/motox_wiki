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
MODELS = os.path.join(ROOT, "motorcycle")
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
  <link rel="stylesheet" href="../css/main.css?v=23">
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
        ("parts-fitment-codes", "Motorcycle Parts & Fitment Codes", "Spark plug, brake pad, wheel bearing, steering head bearing and fork seal codes by model."),
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


def build_parts_fitment(bikes):
    brake_rows = []
    bearing_rows = []
    for bike in sorted(bikes, key=name):
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
      <h2>Brake pad and spark plug codes</h2>
      <p>The table lists the codes shown on each model page. EBC codes come from EBC catalogue listings recorded on MotoSpecVault model-year pages; spark plug codes come from the same model-year records. Cross-brand pad references are added only where a second catalogue confirms the shape.</p>
      {table(["Model", "Spark plug", "Front brake pads", "Rear brake pads"], brake_rows)}
      <h2>Wheel bearing, steering head and fork seal codes</h2>
      <p>All Balls kit numbers are shown where the manufacturer's application list covers the model. A kit number is not a bearing dimension: it identifies a set of bearings and seals. Fork seal sizes are oil-seal dimensions in millimetres (inner diameter × outer diameter × thickness).</p>
      {table(["Model", "Front wheel bearings", "Rear wheel bearings", "Steering head bearings", "Fork seal"], bearing_rows)}
      <h2>What the codes mean</h2>
      {table(["Code", "What it identifies", "Notes"], [
        ["EBC FA252 / FA252HH", "EBC brake pad shape", "The number identifies the backing-plate shape; letters such as HH denote the compound."],
        ["SBS 634", "SBS brake pad shape", "SBS uses its own shape numbers. The compound is a separate suffix or product variant."],
        ["Brembo 07YA23", "Brembo brake pad code", "Brembo may add a compound suffix such as .SA or .LA. One blister normally does one caliper."],
        ["All Balls 25-1659", "Wheel bearing kit", "25-xxxx is a wheel bearing kit; confirm front or rear in the application list."],
        ["Pivot Works PWRWS-H68-000", "Wheel bearing kit", "Pivot Works is part of the All Balls Racing group; the PW prefix identifies a Pivot Works kit."],
        ["All Balls 22-1004", "Steering head bearing kit", "22-xxxx is a steering bearing kit, usually supplied with seals."],
        ["41 × 53 × 8/10.5 mm", "Fork oil seal", "Inner diameter × outer diameter × thickness. The dust wiper is a separate part."],
        ["41 × 54 × 11 mm", "Fork oil seal", "Inner diameter × outer diameter × thickness. Check the fork model, not just the bike model."],
      ])}
      <h2>Verified cross-reference example: Yamaha MT-07</h2>
      <p>The MT-07 is the model where we have the strongest multi-brand brake cross-reference. The front caliper uses the same pad shape as EBC FA252, SBS 634 and Brembo 07YA23; the rear uses EBC FA174 and SBS 657. These are shape equivalences, not identical friction compounds. Pick the compound for your riding and confirm the seller's application list for your exact year.</p>
      {table(["Position", "EBC", "SBS", "Brembo", "Verification"], [
        ["Front", "FA252", "634", "07YA23", "EBC catalogue via MotoSpecVault; EBC/SBS shape match via Delta Braking; Brembo fitment listings for MT-07."],
        ["Rear", "FA174", "657", "—", "EBC catalogue via MotoSpecVault; SBS 657 listings state FA174 equivalence."],
      ])}
      <p>Bearing and seal examples: the MT-07 uses All Balls 25-1659 front, 25-1703 rear and 22-1004 steering head kits, with a 41 × 53 × 8/10.5 mm fork oil seal. The CBR600RR uses All Balls 25-1562 front, Pivot Works PWRWS-H68-000 rear and All Balls 22-1020 steering head kits, with a 41 × 54 × 11 mm fork oil seal. The Ninja 400 uses All Balls 25-1104 front and 25-1780 rear kits.</p>
      <h2>Why some models have no bearing or seal code</h2>
      <p>Bearing and seal fitment is harder to verify than a spark plug code. The same bearing bore can use different widths, seals and spacers, and kit manufacturers revise application lists. We only publish a kit number or seal size when an application list or OEM parts fiche supports it. If your bike is not in the table, measure the old bearing or seal and use the OEM part number as the primary reference.</p>
      <h2>How to verify a part for your bike</h2>
      <ol>
        <li>Identify the exact model year, market and ABS/non-ABS variant. “MT-07” alone is not enough.</li>
        <li>Look up the OEM part number on a parts fiche for your VIN or model code.</li>
        <li>Cross-check the aftermarket application list, not only the product title.</li>
        <li>For bearings and seals, measure the old part or read the marking on the bearing race.</li>
        <li>For brake pads, compare the pad shape and backing plate; a different compound code can share the same shape.</li>
        <li>Use the workshop manual for torque values, fluid volumes and bed-in procedure.</li>
      </ol>
      <h2>Sources</h2>
      <ul>
        <li><a href="https://motospecvault.com/" rel="noopener">MotoSpecVault</a> — model-year specification pages used for spark plug and EBC brake pad codes.</li>
        <li><a href="https://www.motousher.com/" rel="noopener">MotoUsher</a> — parts importer catalogue with EBC and All Balls listings.</li>
        <li><a href="https://www.allballsracing.com/" rel="noopener">All Balls Racing</a> — wheel bearing and steering bearing kit application lists.</li>
        <li><a href="https://ebcbrakes.com/" rel="noopener">EBC Brakes</a> — motorcycle brake pad catalogue and compound information.</li>
        <li><a href="https://www.sbs.dk/" rel="noopener">SBS Friction</a> — motorcycle brake pad catalogue.</li>
        <li><a href="https://www.brembo.com/en/motorcycle" rel="noopener">Brembo</a> — motorcycle brake pad and fitment information.</li>
        <li><a href="https://galferusa.com/" rel="noopener">Galfer</a> — motorcycle brake pad catalogue.</li>
        <li><a href="https://www.vesrah.com/" rel="noopener">Vesrah</a> — motorcycle brake pad catalogue.</li>
        <li><a href="https://www.delta-braking.com/htm/crefEbc.php" rel="noopener">Delta Braking cross-reference</a> — EBC and SBS shape cross-reference used for the MT-07 example.</li>
      </ul>
      <p>Codes can change when a manufacturer revises a compound or kit. Treat this page as a starting point and confirm the part against your exact machine before ordering.</p>
      {related_guides([("oil-capacity-chart.html", "Motorcycle oil capacity chart"), ("torque-specs.html", "Motorcycle torque specifications"), ("seat-height-chart.html", "Motorcycle seat height chart"), ("best-beginner-motorcycles.html", "Best beginner motorcycles")])}
    """
    return guide_page(
        "parts-fitment-codes", "Motorcycle Parts & Fitment Codes",
        "Verified spark plug, brake pad, wheel bearing, steering head bearing and fork seal codes by model, with source notes and cross-reference guidance.",
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


def property_table(rows):
    body = "".join(
        f'<div class="spec-field"><span class="field-label">{esc(label)}</span><span class="field-value">{esc(value)}</span></div>'
        for label, value in rows if value
    )
    return f'<div class="spec-fields">{body}</div>'


def bike_faq(bike):
    full = name(bike)
    faq = []
    power = field(bike, "power")
    torque = field(bike, "torque")
    seat_height = field(bike, "seat_height")
    kerb = field(bike, "weight")
    oil = service(bike, "oil_capacity")
    oil_grade = service(bike, "oil_grade")
    top = field(bike, "top_speed")
    fuel = field(bike, "fuel_capacity")
    if power:
        faq.append((f"How much power does the {full} make?", f"The {full} is rated at {power}."))
    if torque:
        faq.append((f"What is the torque of the {full}?", f"Manufacturer-claimed peak torque is {torque}."))
    if seat_height:
        faq.append((f"What is the seat height of the {full}?", f"The seat height is listed as {seat_height}. Seat width and suspension sag also affect reach."))
    if kerb:
        faq.append((f"How much does the {full} weigh?", f"The kerb weight is listed as {kerb}."))
    if oil:
        faq.append((f"What engine oil does the {full} take?", f"Engine oil capacity is {oil}{f' and the recommended grade is {oil_grade}' if oil_grade else ''}. Confirm the exact fill procedure in the owner's or workshop manual."))
    elif oil_grade:
        faq.append((f"What engine oil grade does the {full} use?", f"The recommended grade is {oil_grade}. Confirm the exact fill procedure in the owner's or workshop manual."))
    if top:
        faq.append((f"What is the top speed of the {full}?", f"The listed top speed is {top}."))
    if fuel:
        faq.append((f"What is the fuel capacity of the {full}?", f"Fuel capacity is listed as {fuel}."))
    return faq[:6]


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
    return [alias_label(alias) for _, alias in scored[:5]]


def static_sections_html(bike):
    parts = []
    for key, section in (bike.get("sections") or {}).items():
        label = section.get("label") or key
        body = ""
        note = next((f.get("value", "") for f in section.get("fields") or [] if f.get("key") == "note"), "")
        if note:
            body += f'<p class="spec-note">{esc(note)}</p>'
        field_rows = [
            (f.get("label", ""), f.get("value", ""))
            for f in section.get("fields") or []
            if f.get("key") != "note"
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


def model_page(bike, related, guide_links):
    url = f"{SITE}/motorcycle/{quote(bike['id'])}.html"
    seo_title = f"{name(bike)} ({bike.get('year', '')}) Specs & Torque"

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
    description = f"{name(bike)} specs: {', '.join(bits)}. Torque values, service data and dimensions."
    faq = bike_faq(bike)

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
        "description": bike.get("summary", ""),
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
            {"@type": "ListItem", "position": 3, "name": title(bike), "item": url}
        ]
    }]
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
    guides_html = "".join(f'<a href="../guides/{href}">{esc(label)}</a>' for href, label in guide_links)
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
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary">
  <meta name="theme-color" content="#c2410c">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="../css/main.css?v=23">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3716738858398465" crossorigin="anonymous"></script>
  <script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)}</script>
</head>
<body>
  <header class="site-header static-header">
    <div class="container">
      <div class="header-row"><a class="brand" href="../index.html"><span class="brand-icon">⚙</span><span>MotoX Wiki</span></a></div>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="../index.html">Browse</a>
        <a href="../guides/index.html">Guides</a>
        <a href="../guides/oil-capacity-chart.html">Oil Charts</a>
        <a href="../pages.html">Reference</a>
      </nav>
    </div>
  </header>
  <main class="container">
    <div class="bike-header">
      <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="../index.html#browse">Browse</a> / {esc(name(bike))}</div>
      <h1>{esc(title(bike))}</h1>
      <p class="bike-subtitle">{esc(bike.get('category', ''))}{' · ' if bike.get('category') and bike.get('displacement') else ''}{esc(bike.get('displacement', ''))}</p>
      <p>{esc(bike.get('summary', ''))}</p>
      {alias_html}
      <div class="hero-stats">{hero}</div>
    </div>
    <article class="model-content">
      <h2 class="section-heading">Specifications</h2>
      {static_sections_html(bike)}
      {f'<section class="faq-section"><h2 class="section-heading">Frequently Asked Questions</h2>{faq_html}</section>' if faq_html else ''}
      {f'<section class="related-section"><h2 class="related-title">Related Models</h2><div class="bike-grid related-grid">{related_html}</div></section>' if related_html else ''}
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


COMPARISON_LINKS = {
    "honda-cbr600rr-2013": ("cbr600rr-vs-cbr650r.html", "CBR600RR vs CBR650R"),
    "honda-cbr650r-2024-present-global": ("cbr600rr-vs-cbr650r.html", "CBR600RR vs CBR650R"),
    "yamaha-mt-07-2018": ("mt-07-vs-mt-09.html", "MT-07 vs MT-09"),
    "yamaha-mt-09-2015-2018-global": ("mt-07-vs-mt-09.html", "MT-07 vs MT-09"),
    "kawasaki-ninja-400-2018-present": ("ninja-400-vs-ninja-500.html", "Ninja 400 vs Ninja 500"),
    "kawasaki-ninja-500-2024-present": ("ninja-400-vs-ninja-500.html", "Ninja 400 vs Ninja 500"),
    "royal-enfield-classic-350-2021-present-global": ("classic-350-vs-hunter-350.html", "Classic 350 vs Hunter 350"),
    "royal-enfield-hunter-350-2022-present-global": ("classic-350-vs-hunter-350.html", "Classic 350 vs Hunter 350"),
    "royal-enfield-himalayan-450": ("himalayan-450-vs-411.html", "Himalayan 450 vs 411"),
    "royal-enfield-himalayan-411-2015-2023-global": ("himalayan-450-vs-411.html", "Himalayan 450 vs 411"),
    "royal-enfield-interceptor-650-2018-present-global": ("interceptor-650-vs-continental-gt-650.html", "Interceptor 650 vs Continental GT 650"),
    "royal-enfield-continental-gt-650-2019-present-global": ("interceptor-650-vs-continental-gt-650.html", "Interceptor 650 vs Continental GT 650"),
}


def build_model_pages(bikes):
    os.makedirs(MODELS, exist_ok=True)
    for entry in os.listdir(MODELS):
        if entry.endswith(".html"):
            os.remove(os.path.join(MODELS, entry))
    by_group = {}
    for bike in bikes:
        group = bike.get("model_group") or ""
        if group:
            by_group.setdefault(group, []).append(bike)
    for bike in bikes:
        related = [b for b in by_group.get(bike.get("model_group") or "", []) if b["id"] != bike["id"]][:6]
        if not related:
            related = [b for b in bikes if b["id"] != bike["id"] and b.get("make") == bike.get("make") and b.get("category") == bike.get("category")][:6]
        category = (bike.get("category") or "").lower()
        guides = [
            ("parts-fitment-codes.html", "Parts and fitment codes"),
            ("oil-capacity-chart.html", "Motorcycle oil capacity chart"),
            ("seat-height-chart.html", "Motorcycle seat height chart"),
            ("a2-motorcycles.html", "A2 motorcycles"),
            ("best-beginner-motorcycles.html", "Best beginner motorcycles"),
            ("torque-specs.html", "Motorcycle torque specs")
        ]
        comparison = COMPARISON_LINKS.get(bike["id"])
        if comparison:
            guides.insert(0, comparison)
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
        model_page(bike, related, guides[:7])
    return len(bikes)


def main():
    global bikes
    bikes, pages = load()
    os.makedirs(GUIDES, exist_ok=True)
    for entry in os.listdir(GUIDES):
        if entry.endswith(".html"):
            os.remove(os.path.join(GUIDES, entry))

    model_count = build_model_pages(bikes)
    urls = []
    urls.append(build_index(bikes))
    urls.append(build_oil_chart(bikes))
    urls.append(build_seat_chart(bikes))
    urls.append(build_weight_chart(bikes))
    urls.append(build_hp_chart(bikes))
    urls.append(build_torque_page(bikes))
    urls.append(build_parts_fitment(bikes))
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
    model_urls = [f"{SITE}/motorcycle/{quote(b['id'])}.html" for b in bikes]
    page_urls = [f"{SITE}/pages.html?slug={quote(p.get('slug') or p['id'])}" for p in pages]
    urls = [f"{SITE}/", f"{SITE}/pages.html"] + page_urls + [f"{SITE}/guides/"] + urls + model_urls
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in sorted(set(urls)):
            priority = "1.0" if url == f"{SITE}/" else "0.7" if "/motorcycle.html" in url else "0.6"
            fh.write(f"  <url><loc>{url}</loc><lastmod>{LAST_MOD}</lastmod><priority>{priority}</priority></url>\n")
        fh.write("</urlset>\n")
    print(f"Generated {len(urls)} sitemap URLs, {len(os.listdir(GUIDES))} guide files and {model_count} model pages")


if __name__ == "__main__":
    main()

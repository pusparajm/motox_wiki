# Motorcycle comparison plan

## Purpose

Build comparison pages that answer real buying questions without inventing ride-test verdicts or copying review text. Every public page uses the catalogue's listed specifications and links back to the model pages.

## Research inputs

Segment names and buying criteria were checked against current coverage from:

- Global/US: Cycle World, Cycle News, Motorcyclist, Rider, MCN, ADVmoto, Motofomo, RideApart, Torquepedia.
- India: Autocar India, Bike India, HT Auto, CarToQ, BikeDekho, The Bike Junction.

Public pages do not name or cite these outlets. They are research inputs only.

## Selection rules

- At least four models per segment.
- Every model must have a catalogue entry with listed power, torque, weight, seat height and fuel capacity.
- Prefer models with suspension, brake and tyre data.
- No price, EMI, colour, mileage or unsupported comfort/reliability claims.
- Segment pages compare listed data. Head-to-head pages compare two specific models.
- Each page links to its model pages, the comparison hub and relevant reference tables.

## Full list

### Phase 1 — under-500cc and budget core

| # | Segment | Slug | Status |
|---|---|---|---|
| 1 | Under-500cc adventure | `under-500cc-adventure-motorcycles` | Implemented |
| 2 | Under-500cc tourers | `under-500cc-tourers` | Implemented |
| 3 | Budget tourers | `budget-tourers` | Implemented |
| 4 | Under-500cc twin-cylinder sportbikes | `under-500cc-twin-cylinder-sportbikes` | Implemented |
| 5 | Single-cylinder sportbikes | `single-cylinder-sportbikes` | Implemented |
| 6 | 600cc sportbikes | `600cc-sportbikes` | Implemented |

### Phase 2 — Indian and Asian volume segments

| # | Segment | Slug | Candidate models |
|---|---|---|---|
| 7 | 160cc sporty commuters | `160cc-sporty-commuters` | Apache RTR 160 4V, Pulsar N160, Xtreme 160R, R15 V4, Karizma XMR 210 |
| 8 | 125cc commuters | `125cc-commuters` | Splendor Plus, Shine 125, Raider 125, Glamour, Passion Pro, Platina 110 |
| 9 | 250–400cc naked bikes | `250-400cc-naked-bikes` | 390 Duke, Svartpilen 401, G 310 R, CB300R, Apache RTR 310 |
| 10 | 350–500cc retro motorcycles | `350-500cc-retro-motorcycles` | Classic 350, Hunter 350, Bullet 350, CB350, Jawa 42, Imperiale 400 |
| 11 | 300–500cc cruisers | `300-500cc-cruisers` | Rebel 300, Rebel 500, Eliminator 500, Meteor 350, Benelli 502C |
| 12 | 125cc sportbikes | `125cc-sportbikes` | YZF-R125, RS 125, RC 125, Ninja 125, GSX-R125 |

### Phase 3 — US/global and premium segments

| # | Segment | Slug | Candidate models |
|---|---|---|---|
| 13 | 250–450cc dual-sport | `250-450cc-dual-sport` | CRF300L, KLX300, WR250R, DR-Z400S, XT250 |
| 14 | Beginner cruisers | `beginner-cruisers` | Rebel 300, Rebel 500, Meteor 350, Eliminator 500, V-Star 250 |
| 15 | 650–900cc naked bikes | `650-900cc-naked-bikes` | MT-07, MT-09, Street Triple, Duke 790, Monster 821 |
| 16 | 650–900cc adventure | `650-900cc-adventure` | Tenere 700, Versys 650, V-Strom 650, Tiger Sport 660, Tuareg 660 |
| 17 | Sport-touring 650–900 | `sport-touring-650-900` | Ninja 650, CBR650R, Tiger Sport 660, Tracer 7, Versys 650 |
| 18 | Electric motorcycles | `electric-motorcycles` | Zero SR/F, LiveWire One, Energica Eva Ribelle, Stark Varg |

### Head-to-head set

Already implemented:

- CBR600RR vs CBR650R
- Ninja 400 vs Ninja 500
- MT-07 vs MT-09
- Himalayan 450 vs 411
- Classic 350 vs Hunter 350
- Interceptor 650 vs Continental GT 650
- CRF450R vs YZ450F
- CRF450R vs KX450
- CRF450R vs 450 SX-F
- YZ450F vs KX450
- YZ450F vs 450 SX-F
- KX450 vs 450 SX-F

## Execution order

1. Validate candidate model IDs and specification completeness.
2. Add segment metadata and model lists.
3. Generate the segment page, comparison table, leader summary and FAQs.
4. Add it to the comparison hub, guides index and sitemap.
5. Add segment links to every included model page.
6. Check breadcrumbs, canonical tags, internal links and duplicate titles.
7. Commit and verify live.

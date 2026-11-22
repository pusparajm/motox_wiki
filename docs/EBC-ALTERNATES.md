# EBC brake-pad alternates

## Phase 1 — Aprilia

The Aprilia RS 125 example was verified against SBS and EBC fitment listings:

| Position | SBS | EBC shape |
|---|---|---|
| Front | SBS 821HS | EBC FA399 |
| Rear | SBS 544HF | EBC FA83 |

The same mapping method was applied to the rest of Aprilia.

| Measure | Count |
|---|---:|
| Aprilia models with SBS-only brake data before | 102 |
| Models fixed with at least one EBC alternate | 63 |
| Brake positions fixed | 77 |
| Models still requiring manual research | 39 |

The 39 remaining Aprilia models use SBS numbers that do not map uniquely to an
EBC shape with an extracted diagram. They are left unchanged rather than
guessed.

## Catalogue after phase 1

| Measure | Before | After |
|---|---:|---:|
| Models with brake-pad data | 4,574 | 4,574 |
| Models with only SBS branding | 4,331 | 4,268 |
| Models with no EBC code | 4,409 | 4,346 |
| Models with an EBC shape and diagram | 157 | 211 |
| Models with EBC but no diagram | 17 | 17 |

“EBC shape and diagram” means at least one brake position has an EBC shape with
an extracted diagram.

## Remaining work

| Group | Models |
|---|---:|
| Aprilia — manual research | 39 |
| Other brands — unique SBS-to-EBC mapping available | 2,549 |
| EBC code present but diagram missing (X variants/FA715) | 17 |
| No EBC code and no unique mapping | remainder |

The 2,549 other-brand models can be processed in the next phases using the same
limited rule:

1. SBS base number maps to exactly one EBC shape.
2. That EBC shape has an extracted diagram.
3. The model does not already have an EBC code.
4. No existing compound or brand data is overwritten.

## Phase plan

1. **Aprilia** — done, 63 of 102 fixed.
2. **Honda and Yamaha** — next, largest SBS-only groups.
3. **Kawasaki, Suzuki, Harley-Davidson, Ducati, KTM, BMW** — follow.
4. **Remaining brands** — smaller groups.
5. **Manual research** — SBS codes with no unique EBC mapping.
6. **Newer EBC catalogue** — X variants and FA715.

## Script

`scripts/add-ebc-alternates.py` performs the phase update:

```bash
python3 scripts/add-ebc-alternates.py --make Aprilia
```

It writes `data/ebc-alternates-report.json` with the per-model changes.

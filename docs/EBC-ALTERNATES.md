# EBC brake-pad alternates

## Phase 1 — Aprilia

The Aprilia RS 125 example was verified against SBS and EBC fitment listings:

| Position | SBS | EBC shape |
|---|---|---|
| Front | SBS 821HS | EBC FA399 |
| Rear | SBS 544HF | EBC FA83 |

| Measure | Count |
|---|---:|
| Aprilia models with SBS-only brake data before | 102 |
| Models fixed with at least one EBC alternate | 63 |
| Brake positions fixed | 77 |
| Models still requiring manual research | 39 |

## Phase 2 — Honda and Yamaha

The same limited mapping rule was applied to Honda and Yamaha.

| Brand | Eligible | Fixed | Positions fixed | Remaining |
|---|---:|---:|---:|---:|
| Honda | 456 | 265 | 375 | 191 |
| Yamaha | 409 | 262 | 405 | 147 |
| **Total** | **865** | **527** | **780** | **338** |

## Catalogue after phase 2

| Measure | Before phase 1 | After phase 2 |
|---|---:|---:|
| Models with brake-pad data | 4,574 | 4,574 |
| Models with only SBS branding | 4,331 | 3,741 |
| Models with no EBC code | 4,409 | 3,819 |
| Models with an EBC shape and diagram | 157 | 738 |
| Models with EBC but no diagram | 17 | 17 |

“EBC shape and diagram” means at least one brake position has an EBC shape with
an extracted diagram.

## Remaining work

| Group | Models |
|---|---:|
| Aprilia — manual research | 39 |
| Honda — manual research | 191 |
| Yamaha — manual research | 147 |
| Other brands — unique SBS-to-EBC mapping available | 2,022 |
| EBC code present but diagram missing (X variants/FA715) | 17 |

The 2,022 other-brand models can be processed in the next phases using the same
limited rule:

1. SBS base number maps to exactly one EBC shape.
2. That EBC shape has an extracted diagram.
3. The model does not already have an EBC code.
4. No existing compound or brand data is overwritten.

The brake fitment reference now includes fitment-only models with brake data, so
the new EBC alternates are visible there as well as on the model pages.

## Phase plan

1. **Aprilia** — done, 63 of 102 fixed.
2. **Honda and Yamaha** — done, 527 of 865 fixed.
3. **Kawasaki, Suzuki, Harley-Davidson, Ducati, KTM, BMW** — next.
4. **Remaining brands** — smaller groups.
5. **Manual research** — SBS codes with no unique EBC mapping.
6. **Newer EBC catalogue** — X variants and FA715.

## Script

`scripts/add-ebc-alternates.py` performs each phase:

```bash
python3 scripts/add-ebc-alternates.py --make Honda --report data/ebc-alternates-honda.json
python3 scripts/add-ebc-alternates.py --make Yamaha --report data/ebc-alternates-yamaha.json
```

Phase reports:

- `data/ebc-alternates-aprilia.json`
- `data/ebc-alternates-honda.json`
- `data/ebc-alternates-yamaha.json`

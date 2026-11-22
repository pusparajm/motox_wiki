# EBC brake-pad shape coverage

Snapshot: 2026-11-22 (after Aprilia phase 1)

## Summary

| Status | Models |
|---|---:|
| EBC shape available | 211 |
| EBC code present, shape missing from the 2024 guide | 17 |
| Brake data present, but no EBC code | 4,346 |
| No brake-pad data | 145 |
| **Total catalogue** | **4,719** |

The 17 models below have an EBC pad code, but that exact code is not listed in
the EBC UK MC Pad Buyers Guide 203. They are left without an EBC shape badge
rather than mapped to a different shape.

## Models with an EBC code but no 2024 shape

| Make | Model | Years | Model ID | Missing position/code |
|---|---|---|---|---|
| Harley-Davidson | Street 750 | 2014–2021 | `harley-davidson-street-2013-2021-global` | rear `FA181X` |
| Harley-Davidson | Street Rod | 2017–2021 | `harley-davidson-street-rod-2017-2021-global` | rear `FA181X` |
| Honda | CRF300 Rally | 2021–Present | `honda-crf300-rally-2021-present-global` | front `FA465X`; rear `FA629X` |
| Honda | CRF300L | 2021–Present | `honda-crf300l-2021-present-global` | front `FA465X`; rear `FA629X` |
| Honda | CRF450R | 2021–Present | `honda-crf450r-2021-present-global` | front `FA185X`; rear `FA346X` |
| Husqvarna | FE 350 | 2017–Present | `husqvarna-fe-350-2017-present-global` | front `FA181X`; rear `FA368X` |
| Husqvarna | Svartpilen 401 | 2020–Present | `husqvarna-svartpilen-401-2020-present-global` | rear `FA208X` |
| Husqvarna | Vitpilen 401 | 2020–Present | `husqvarna-vitpilen-401-2020-present-global` | rear `FA208X` |
| KTM | 1290 Super Adventure S | 2021–Present | `ktm-1290-super-adventure-s-2021-present-global` | rear `FA181X` |
| KTM | 250 SX-F | 2013–Present | `ktm-250-sx-f-2013-present-global` | front `FA181X`; rear `FA368X` |
| KTM | 350 EXC-F | 2012–Present | `ktm-350-exc-f-2012-present-global` | front `FA181X`; rear `FA368X` |
| KTM | 690 Enduro R | 2008–Present | `ktm-690-enduro-r-2008-present-global` | rear `FA208X` |
| KTM | 890 Adventure R | 2021–Present | `ktm-890-adventure-r-2021-present-global` | rear `FA181X` |
| Kawasaki | KLX300 | 2021–Present | `kawasaki-klx300-2021-present-global` | front `FA135X`; rear `FA131X` |
| Suzuki | GSX-R125 | 2017–Present | `suzuki-gsx-r125-2017-present-global` | front `FA715` |
| Triumph | Bonneville Speedmaster | 2018–Present | `triumph-bonneville-speedmaster-2018-present-global` | front `FA181X` |
| Yamaha | Ténéré 700 | 2019–Present | `yamaha-tenere-700-2019-present-global` | front `FA181X`; rear `FA208X` |

## Missing EBC shape codes

| Code | Affected models |
|---|---|
| `FA131X` | Kawasaki KLX300 |
| `FA135X` | Kawasaki KLX300 |
| `FA181X` | Harley-Davidson Street 750, Street Rod; Husqvarna FE 350; KTM 1290 Super Adventure S, 250 SX-F, 350 EXC-F, 890 Adventure R; Triumph Bonneville Speedmaster; Yamaha Ténéré 700 |
| `FA185X` | Honda CRF450R |
| `FA208X` | Husqvarna Svartpilen 401, Vitpilen 401; KTM 690 Enduro R; Yamaha Ténéré 700 |
| `FA346X` | Honda CRF450R |
| `FA368X` | Husqvarna FE 350; KTM 250 SX-F, 350 EXC-F |
| `FA465X` | Honda CRF300 Rally, CRF300L |
| `FA629X` | Honda CRF300 Rally, CRF300L |
| `FA715` | Suzuki GSX-R125 |

Most are **X variants**. The 2024 guide lists the base shapes (`FA131`, `FA181`,
`FA208`, `FA346`, `FA368`, `FA465`, `FA629`) but not the X variants. `FA715` is
not listed at all.

## Why they were not guessed

The X suffix can indicate a different backing-plate outline, thickness or
locating-tab arrangement. Mapping `FA181X` to `FA181` automatically would risk
showing the wrong shape. The site therefore leaves these pages without an EBC
shape badge.

## Full list

`data/ebc-coverage.csv` lists every model with:

- Front and rear brake-pad strings
- Extracted EBC codes
- Coverage status

## How to close the gap

1. Check a newer EBC catalogue for the X variants and `FA715`.
2. If EBC publishes the shape, add it to `data/ebc-pad-shapes.json`.
3. Rebuild with `npm run build`.
4. Confirm the badge appears on the model page and the brake reference pages.

Do not infer an X shape from its base code.

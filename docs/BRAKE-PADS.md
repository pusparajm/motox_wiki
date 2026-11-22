# Brake pad shape data

## Source

Shape codes, dimensions and diagrams are extracted from the **EBC UK MC Pad Buyers Guide 203**:

<https://www.ebcbrakes.com/wp-content/uploads/2024/01/EBC_UK_MC_Pad_Buyers_Guide_203.pdf>

EBC diagrams are reproduced with **written permission from EBC**.
Permission reference: owner-confirmed written permission, 2026-11-22.

The extracted data lives in `data/ebc-pad-shapes.json`.
The diagrams live in `images/pad-shapes/`.

## What is stored

Each entry records:

- The normalised EBC shape code, for example `FA252`
- The printed EBC code, for example `FA252`
- The published dimensions, for example `69 x 51.5 x 8.5 mm`
- The PDF page number used for extraction
- The local diagram path, width and height

The site renders the actual diagram beside EBC pad codes on:

- Model pages, in the Service Data section
- `reference/brake-pad-fitment.html`
- `reference/pad-shape-cross-reference.html`
- `guides/parts-fitment-codes.html`
- Model service-data pages

## Copyright and permission

EBC's catalogue reserves copyright in its illustrations. The diagrams on this
site are reproduced under the written permission confirmed by the site owner.
Keep the permission record with the project. Do not add EBC diagrams from a
different edition or source without checking that the permission covers them.

## Updating the data

Download the current EBC PDF and run:

```bash
python3 scripts/extract-ebc-shapes.py /path/to/EBC_UK_MC_Pad_Buyers_Guide_203.pdf
python3 scripts/extract-ebc-diagrams.py /path/to/EBC_UK_MC_Pad_Buyers_Guide_203.pdf
```

Then rebuild:

```bash
npm run build
```

`extract-ebc-shapes.py` needs `pdftotext` and `pdfinfo` from Poppler.
`extract-ebc-diagrams.py` needs `pdfplumber` and Pillow.

## Matching rules

- Leading zeros are normalised: `FA027` becomes `FA27`.
- Variant suffixes such as `/2`, `/3` and `/4` are preserved.
- Compound or variant suffixes such as `HH`, `HS`, `LS`, `S`, `M` and `V` are
  stripped only when an exact shape match is not found.
- A missing shape is left blank rather than guessed.

## Adding a new EBC shape

1. Confirm the code, dimensions and diagram in the official EBC guide.
2. Re-run both extractors or add the entry to `data/ebc-pad-shapes.json`.
3. Run `npm run build`.
4. Check the model page, the fitment table and the cross-reference page.

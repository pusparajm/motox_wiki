# Brake pad shape data

## Source

Shape codes and dimensions are extracted from the **EBC UK MC Pad Buyers Guide 203**:

<https://www.ebcbrakes.com/wp-content/uploads/2024/01/EBC_UK_MC_Pad_Buyers_Guide_203.pdf>

The extracted data lives in `data/ebc-pad-shapes.json`.

## What is stored

Each entry records:

- The normalised EBC shape code, for example `FA252`
- The printed EBC code, for example `FA252`
- The published dimensions, for example `69 x 51.5 x 8.5 mm`
- The PDF page number for the official EBC drawing

The site renders a compact shape reference beside EBC pad codes on:

- Model pages, in the Service Data section
- `reference/brake-pad-fitment.html`
- `reference/pad-shape-cross-reference.html`
- `guides/parts-fitment-codes.html`
- Model service-data pages

The badge shows the shape code and dimensions only.

## Copyright

EBC's catalogue footer reserves the copyright in its photos, illustrations and
line drawings. The site therefore does **not** copy or redistribute the EBC
line drawings. It stores only the factual codes and dimensions. The PDF page
number is kept in the data for internal verification.

If written permission is obtained from EBC, the badges can be extended to show
the official drawings or original redrawn diagrams. Do not add them without
that permission.

## Updating the data

Download the current EBC PDF and run:

```bash
python3 scripts/extract-ebc-shapes.py /path/to/EBC_UK_MC_Pad_Buyers_Guide_203.pdf
```

Then rebuild:

```bash
npm run build
```

The extractor needs `pdftotext` and `pdfinfo` from Poppler.

## Matching rules

- Leading zeros are normalised: `FA027` becomes `FA27`.
- Variant suffixes such as `/2`, `/3` and `/4` are preserved.
- Compound or variant suffixes such as `HH`, `HS`, `LS`, `S`, `M` and `V` are
  stripped only when an exact shape match is not found.
- A missing shape is left blank rather than guessed.

## Adding a new EBC shape

1. Confirm the code and dimensions in the official EBC guide.
2. Re-run the extractor or add the entry to `data/ebc-pad-shapes.json`.
3. Run `npm run build`.
4. Check the model page, the fitment table and the cross-reference page.

# Battery fitment data

## Sources

- Yuasa 2021 and 2026 powersports application guides, motorcycle application pages.
- Manufacturer owner's manuals and technical specification sheets for selected models.
- Battery fitment listings used only where the model, year and code could be matched.

Public pages do not name or cite these sources. The battery code and rating are presented as service data.

## Method

1. Extract motorcycle application rows from the PDF application pages.
2. Match make, model and year range against the catalogue.
3. Prefer the maintenance-free AGM code; retain other listed codes as options.
4. Reject ambiguous or non-overlapping year matches.
5. Add manufacturer codes where a service manual or specification sheet gives one.
6. Leave the field blank when no code can be verified.

## Coverage

`data/battery-fitment.json` contains the verified entries. `scripts/apply-battery-fitment.py` merges them into each model's Service Data section.

Current coverage is deliberately partial. The application guides are US-market focused and do not cover every Indian, Chinese, electric or older model. Missing entries are not guessed. Add new entries only when the model, year and code are verified.

## Fields

- `battery`: primary verified code.
- `battery_options`: other compatible codes listed for the same application.
- `battery_rating`: voltage and capacity when the code is not published but the rating is verified.

# Model FAQ coverage

`bike_faq()` in `scripts/build-seo-pages.py` builds the on-page FAQ block and the
matching `FAQPage` JSON-LD. Search-style questions use a compact, model-specific
alias where one exists, such as `ZX10R`, `MT-07` or `390 Duke`.

## Current coverage

| Question type | Models |
|---|---|
| Brake pads | 4,589 |
| Battery | 591 |
| Tyres | 804 |
| Horsepower / BHP | 767 |
| Chain / final drive | 585 |
| Spark plug | 313 |
| Top speed | 15 |
| Sprocket sizes | 3 |

Model pages carry between 2 and 23 FAQs. The cap is 26.

## Rules

- Only verified service and specification fields are used.
- If a field is missing, the question is omitted rather than filled with a placeholder.
- Aliases are model-specific. Generic terms alone are not repeated across unrelated models.
- Questions are deduplicated per page.
- Brake-pad answers are pad-shape references, not a guarantee of compound or model-year fitment.
- Sprocket questions are emitted only when the final-drive text contains explicit tooth counts.

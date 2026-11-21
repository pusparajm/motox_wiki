# Motorcycle images

## Status

Phase 1 is complete: the image pipeline, manifest, responsive markup, social metadata
and image sitemap entries are in place. One hundred and two approved images are live:
61 from BikeDekho across current Aprilia, Bajaj, BMW, BSA, CFMOTO, Ducati,
Harley-Davidson, Hero, Honda, Indian, Kawasaki and Royal Enfield models, plus 41 from
MotorcycleSpecs covering older Honda CBR, CB and Africa Twin generations, current
Yamaha MT, XSR, TMAX, XMAX, Tracer and YZF-R models, current Suzuki GSX-R, GSX-S,
Katana, Hayabusa, V-Strom and Burgman models, and the 2016–2020 Kawasaki Ninja ZX-10R.
More batches are being added as model matches are verified.

Where the licence or written permission does not require public credit, no credit line
is rendered. Source, licence and permission details remain in the manifest for audit.

## Approved sources

- **BikeDekho** — written permission on file. Source images are unwatermarked and render
  at 800 px from the 930 × 620 originals.
- **CarBike360** — written permission on file. Watermarked files are not used; only
  unwatermarked originals or supplied files are accepted.
- **MotorcycleSpecs.co.za** — written permission on file. Used for models that are not
  available from the other approved sources. Its default Terms of Use still prohibit
  reuse without that written permission.

All other models have no image until a licensed source is supplied. The pipeline does
not scrape third-party pages and will not publish an image without an explicit licence
and rights approval.

## Pipeline

- `data/bike-image-sources.json` — approved source list. Every entry needs `modelId`,
  a direct HTTPS `imageUrl`, `sourcePage`, `license`, `credit` and `rightsApproved: true`.
- `scripts/fetch-bike-images.py` — downloads the approved file, generates 400/800/1200
  px AVIF, WebP and JPEG variants at a 3:2 hero ratio, strips metadata, hashes the filename
  and writes `data/bike-images.json`.
- `images/motorcycles/<make>/<model>/` — generated variants.
- `data/bike-images.json` — manifest used by the page builder. It records the source page,
  licence, licence URL, credit and alt text for each image.
- `scripts/build-seo-pages.py` — renders the hero `<picture>`, `og:image`, Twitter image,
  JSON-LD `Motorcycle.image` and the image sitemap entry.

## Page-speed rules

- Hero image: `loading="eager"`, `fetchpriority="high"`, `decoding="async"`.
- AVIF source first, WebP second, JPEG fallback.
- Explicit `width` and `height` on the fallback image.
- `srcset` at 400/800/1200 px with a 960 px desktop `sizes` cap.
- 1200 px AVIF target: under 160 KB.
- No image is repeated above the fold on the same page.

## Licensing rules

- `rightsApproved` must be true and a licence must be present, or the fetch script skips it.
- CC BY and CC BY-SA images require a visible credit and licence link.
- CC0 and public-domain images do not require a visible credit, but the source is still
  recorded in the manifest.
- Manufacturer press images are processed only when the manufacturer's terms or written
  permission allow this use. Public availability alone is not treated as a licence.
- **Written permission** entries must include a `permissionReference` (email date and
  subject, signed letter reference, or PDF filename). A verbal agreement is not enough.
- **Do not remove watermarks.** If a rights holder requires watermark removal, ask them
  to supply an unwatermarked original. The pipeline also rejects entries marked
  `watermark: true` or `watermarkRemovalRequired: true`.
- **Default source size is 1200 × 800 px.** If an approved original is smaller, set a
  per-source `maxWidth` (for example `800` for a 930 × 620 studio image). The pipeline then
  generates only 400 px and 800 px variants instead of upscaling to 1200 px. A 204 × 134
  thumbnail is still rejected.
- Per-source `maxWidth` must be one of the configured variant widths (400, 800 or 1200).

### Example written-permission entry

```json
{
  "modelId": "kawasaki-ninja-zx-10r-2021-2025",
  "imageUrl": "image-uploads/kawasaki-ninja-zx-10r.jpg",
  "sourcePage": "https://www.carbike360.com/bikes/kawasaki/ninja-zx-10r/abs",
  "credit": "Photo: CarBike360",
  "license": "Written permission — CarBike360",
  "licenseUrl": "",
  "permissionReference": "Email from CarBike360, 2026-11-22, subject: MotoX Wiki image use",
  "creditRequired": true,
  "rightsApproved": true,
  "alt": "Kawasaki Ninja ZX-10R side view"
}
```

## Phase plan

1. **Phase 1 — pipeline and pilot (done):** two models, responsive formats, social metadata,
   image sitemap and page-speed checks.
2. **Phase 2 — one manufacturer at a time (started):** add only approved assets, review 50–100 models,
   then run a page-speed and broken-image check.
3. **Phase 3 — remaining catalogue:** continue in batches until every model has either an
   approved image or an explicit "no licensed image" status.
4. **Phase 4 — audit:** verify image dimensions, licences, credits, sitemap entries and
   Core Web Vitals after the catalogue is populated.

## Adding a batch

1. Add approved entries to `data/bike-image-sources.json`.
2. Run `npm run fetch:images`.
3. Run `npm run build`.
4. Check the model page, `og:image`, sitemap image entry and generated file sizes.
5. Commit the source list, manifest and generated image files together.

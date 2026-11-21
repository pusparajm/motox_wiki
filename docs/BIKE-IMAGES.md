# Motorcycle images

## Status

Phase 1 is complete: the image pipeline, manifest, responsive markup, social metadata
and image sitemap entries are in place. Two free-licence images are live as the pilot.

All other models have no image until a licensed source is supplied. The pipeline does
not scrape third-party pages and will not publish an image without an explicit licence
and rights approval.

## Pipeline

- `data/bike-image-sources.json` — approved source list. Every entry needs `modelId`,
  a direct HTTPS `imageUrl`, `sourcePage`, `license`, `credit` and `rightsApproved: true`.
- `scripts/fetch-bike-images.py` — downloads the approved file, generates 400/800/1200/1600
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
- `srcset` at 400/800/1200/1600 px with a 960 px desktop `sizes` cap.
- 1600 px AVIF target: under 160 KB.
- No image is repeated above the fold on the same page.

## Licensing rules

- `rightsApproved` must be true and a licence must be present, or the fetch script skips it.
- CC BY and CC BY-SA images require a visible credit and licence link.
- CC0 and public-domain images do not require a visible credit, but the source is still
  recorded in the manifest.
- Manufacturer press images are processed only when the manufacturer's terms or written
  permission allow this use. Public availability alone is not treated as a licence.

## Phase plan

1. **Phase 1 — pipeline and pilot (done):** two models, responsive formats, social metadata,
   image sitemap and page-speed checks.
2. **Phase 2 — one manufacturer at a time:** add only approved assets, review 50–100 models,
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

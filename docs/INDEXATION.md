# Model indexation policy

## Why this exists

The catalogue has 4,719 model pages. Publishing all of them as indexable pages
would ask Google to crawl thousands of entries that contain only a model year,
displacement, a "full specifications pending" note and a brake-pad code.

A smaller, stronger indexable set gives crawlers a clearer quality signal and
concentrates internal links on pages that can rank.

Current state:

| Tier | Pages | Robots |
|---|---:|---|
| Indexable model pages | 1,248 | `index,follow,max-image-preview:large` |
| Fitment-only / thin pages | 3,471 | `noindex,follow` |
| Guides and comparisons | 69 files | `index,follow` |
| Reference pages | 101 | `index,follow` |

All model pages remain live, searchable and linked. `noindex,follow` only asks
search engines not to index the thin page; it does not remove the page or its
links.

## Completeness score

The score is intentionally simple and explainable. It counts:

- Published general-spec fields, including model years but excluding the
  "data pending" status note.
- Published service fields, excluding the editorial note.
- Up to five torque-table rows.
- A hero image.
- A model summary.

The default threshold is **8**. A model page with a hero image is indexed at a lower threshold of **6**, because the image is a material content asset.

The score and threshold are implemented in `scripts/build-seo-pages.py`:

```python
model_completeness(bike)
model_is_indexable(bike)
```

## Configuration

The policy is controlled from `data/settings.json`:

```json
{
  "options": {
    "indexing": {
      "minModelCompleteness": 8,
      "minImageModelCompleteness": 6,
      "noindexBelowThreshold": true
    }
  }
}
```

Set `noindexBelowThreshold` to `false` to make every model page indexable again.
Raise or lower `minModelCompleteness` and `minImageModelCompleteness` to tune the size of the indexable set.

## Sitemap split

`sitemap.xml` is now a sitemap index:

| File | Contents |
|---|---|
| `sitemap-core.xml` | Homepage, Reference index and static reference entries |
| `sitemap-models.xml` | Only indexable model pages, with image entries |
| `sitemap-guides.xml` | Guides, comparisons and model service-data pages |
| `sitemap-reference.xml` | Brand hubs and reference tools |

Thin model pages are deliberately excluded from `sitemap-models.xml`. Do not add
them back until they meet the threshold; the sitemap should describe pages that
are allowed to be indexed.

## Re-indexing a page

1. Add verified specification or service data to the model record.
2. Run `npm run build`.
3. Check the completeness score and confirm the page now emits
   `index,follow,max-image-preview:large`.
4. Confirm the page appears in `sitemap-models.xml`.
5. Request indexing in Google Search Console if it is a priority page.

## Review cadence

- **Weekly:** enrich 5–10 pages from the top of the missing-data queue.
- **Monthly:** re-run the build and review the indexable/noindex counts.
- **Quarterly:** raise the threshold if thin pages are still being indexed, or
  lower it if enriched pages are being excluded.

## What not to do

- Do not bulk-add thin pages back to the sitemap to increase the URL count.
- Do not remove the pages from the site; they are useful for parts fitment and
  internal navigation.
- Do not lower the threshold without checking that the pages have unique,
  verified data.

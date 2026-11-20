# Caching and PageSpeed

GitHub Pages currently serves CSS and JavaScript with `Cache-Control: max-age=1800` (30 minutes). That is the origin value Lighthouse reports as “Use efficient cache lifetimes”. The repository cannot change GitHub Pages response headers directly.

If the site is proxied by Cloudflare, add one Cache Rule to override the origin for versioned assets:

## Cloudflare Cache Rule

- **Rule name:** Static assets
- **Expression:**
  ```
  (http.request.uri.path matches "^/(css|js)/") or http.request.uri.path eq "/favicon.svg"
  ```
- **Cache eligibility:** Eligible for cache
- **Edge TTL:** Override origin, 1 year
- **Browser TTL:** Override origin, 1 year
- **Cache key:** include the query string (the default)

The site already uses versioned URLs (`?v=30`, `?v=14`, etc.). When an asset changes, bump its version query so browsers and Cloudflare request the new file. Do not apply the one-year rule to HTML.

## HTML and JSON

- Leave HTML on a short TTL (5–10 minutes is fine).
- `data/*.json` is fetched with `cache: 'no-store'` by the app, so it stays fresh even when the edge caches it briefly.

## Cloudflare Web Analytics

The PageSpeed report also flags `static.cloudflareinsights.com/beacon.min.js` as 10 KiB of legacy JavaScript. That script is injected by Cloudflare Web Analytics, not by this repository. If the analytics are not needed, turn off Web Analytics for the zone in the Cloudflare dashboard.

## Cloudflare Pages / Netlify

The repository includes a `_headers` file with the same policy for hosts that support it. GitHub Pages ignores `_headers`; the Cloudflare Cache Rule above is required for the live GitHub Pages origin.

#!/usr/bin/env python3
"""Scrape K-Tech Part Finder suspension data for motorcycle models already in
the MotoX Wiki database and write a staging file for review.

Data source: https://store.ktechsuspension.com/part-finder
The fitment list is available from the public `mmy` endpoint, and each
make/model/year page exposes the bike information and matching seal products.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path("/tmp/opencode/ktech-cache")
CACHE.mkdir(parents=True, exist_ok=True)
STAGING = Path("/tmp/opencode/ktech-parsed.json")
MMY_URL = "https://store.ktechsuspension.com/rest/V1/ktech/part-finder/mmy"
BIKE_URL = "https://store.ktechsuspension.com/bike-data/bike/index?find="
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0 Safari/537.36"
SAFE_VARIANT_TOKENS = {"abs", "lc", "annv", "anniversary"}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def tokens(value: str) -> list[str]:
    value = re.sub(r"\([^)]*\)", " ", str(value))
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return [t.lower() for t in value.split() if t]


def core_tokens(value: str) -> list[str]:
    toks = tokens(value)
    return [t for t in toks if t not in SAFE_VARIANT_TOKENS] or toks


def year_range(model: dict) -> tuple[int, int] | None:
    text = str(model.get("year", ""))
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", text)]
    if not years:
        return None
    end = max(years)
    if "present" in text.lower() or "current" in text.lower():
        end = 2026
    return min(years), end


def load_mmy(session: requests.Session) -> dict:
    cached = Path("/tmp/opencode/ktech-mmy-raw.json")
    if cached.exists():
        data = json.loads(cached.read_text())
        if isinstance(data, str):
            data = json.loads(data)
        return data
    res = session.get(MMY_URL, timeout=60)
    res.raise_for_status()
    data = json.loads(res.text)
    if isinstance(data, str):
        data = json.loads(data)
    cached.write_text(json.dumps(data))
    return data


def build_candidates(db: list[dict], mmy: dict) -> tuple[dict[str, list[tuple[str, list[int]]]], int]:
    by_make: dict[str, list[tuple[str, list[int]]]] = {}
    for make, models in mmy.items():
        for model, years in models.items():
            by_make.setdefault(norm(make), []).append((model, [int(y) for y in years]))

    matched = 0
    wanted: set[tuple[str, str, int]] = set()
    for model in db:
        if re.search(r"[,+/]| and ", str(model.get("model", "")), re.I):
            continue
        candidates = by_make.get(norm(model.get("make", "")), [])
        if not candidates:
            continue
        target_core = set(core_tokens(model.get("model", "")))
        exact = [c for c in candidates if norm(c[0]) == norm(model.get("model", ""))]
        base = [c for c in candidates if set(core_tokens(c[0])) == target_core]
        chosen = exact or base
        # Only accept an unambiguous model-name match.
        if len({name for name, _ in chosen}) != 1:
            continue
        span = year_range(model)
        if not span:
            continue
        name, years = chosen[0]
        fits = [y for y in years if span[0] <= y <= span[1]]
        if not fits:
            continue
        matched += 1
        for y in fits:
            wanted.add((model["make"], name, y))
    return {f"{m}|{n}|{y}": [m, n, y] for m, n, y in wanted}, matched


def size_from_name(name: str) -> str | None:
    match = re.search(r"(\d{2,3}\.\d{2})\s*x\s*([\d.]+(?:/[\d.]+)?)\s*x\s*([\d.]+(?:/[\d.]+)?)", name)
    if not match:
        return None
    inner, outer, width = match.groups()
    value = f"{inner} × {outer} × {width} mm"
    brands = []
    upper = name.upper()
    for brand in ("KYB", "SHOWA", "WP", "SACHS", "OHLINS", "MARZOCCHI", "NOK"):
        if re.search(rf"\b{brand}\b", upper):
            brands.append(brand)
    if brands:
        value += f" ({', '.join(brands)})"
    return value


def parse_page(html: str, make: str, kname: str, year: int) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out: dict = {
        "make": make,
        "ktech_model": kname,
        "year": year,
        "source": f"https://store.ktechsuspension.com/part-finder?find={urllib.parse.quote(f'{make}_{kname}_{year}')}",
    }
    title = soup.select_one(".bike-info-title")
    if title:
        text = " ".join(title.get_text(" ", strip=True).split())
        out["bike_title"] = text
        cc = re.search(r"/\s*(\d+)\s*CC\s*/\s*([^/]+)$", text, re.I)
        if cc:
            out["displacement"] = f"{cc.group(1)} cc"
            out["category"] = cc.group(2).strip()

    items = soup.select(".bike-details .item")
    for side, item in zip(("front", "rear"), items[:2]):
        fields = {}
        for li in item.select("li"):
            label_el = li.select_one(".title")
            if not label_el:
                continue
            label = label_el.get_text(" ", strip=True)
            value = li.get_text(" ", strip=True)
            if value.startswith(label):
                value = value[len(label):].strip()
            fields[label.rstrip(":").strip()] = value
        out[side] = fields

    for cat in soup.select(".pf-category"):
        heading = cat.select_one("h3")
        if not heading:
            continue
        heading_text = heading.get_text(" ", strip=True).lower()
        names = [" ".join(n.get_text(" ", strip=True).split()) for n in cat.select(".pf-product__name")]
        if heading_text.startswith("front fork seals oil"):
            out["oil_seal_products"] = names
        elif heading_text.startswith("front fork seals dust"):
            out["dust_seal_products"] = names
        elif heading_text == "front fork oil":
            out["fork_oil_products"] = names
        elif heading_text.startswith("front fork bushes slide"):
            out["slide_bush_products"] = names
        for product in names:
            if "oil seal circlip" in product.lower():
                out.setdefault("circlip_products", []).append(product)

    front = out.get("front") or {}
    rear = out.get("rear") or {}

    def clean(value: str | None) -> str:
        value = (value or "").strip()
        if value in {"", "-", "Unknown", "0.000", "0.0"}:
            return ""
        return " ".join(value.replace("_", " ").split())

    viscosity = clean(front.get("Oil Viscosity (wt)"))
    if re.fullmatch(r"\d+(?:\.\d+)?", viscosity) and float(viscosity) > 0:
        out["fork_oil_grade"] = f"{float(viscosity):g}W"

    gap = clean(front.get("Air Gap / Oil Volume"))
    if gap:
        volume = re.fullmatch(r"([\d.]+)\s*(cc|ml)", gap, re.I)
        air = re.fullmatch(r"([\d.]+)\s*(mm)?", gap, re.I)
        if volume:
            out["fork_oil_volume"] = f"{volume.group(1)} {volume.group(2).lower()}"
        elif air:
            out["fork_air_gap"] = f"{air.group(1)} mm"

    rear_oem = clean(rear.get("OEM"))
    if rear_oem and (re.search(r"\(\d{2,3}/\d{2,3}\)", rear_oem) or re.search(r"\b(?:Mono|Twin) Tube\b", rear_oem, re.I)):
        out["rear_shock"] = rear_oem

    oil_names = out.get("oil_seal_products") or []
    dust_names = out.get("dust_seal_products") or []
    for name in oil_names:
        size = size_from_name(name)
        if size:
            out["fork_seal"] = size
            out["fork_seal_product"] = name
            break
    for name in dust_names:
        size = size_from_name(name)
        if size:
            out["fork_dust_seal"] = size
            out["fork_dust_seal_product"] = name
            break

    for name in out.get("slide_bush_products") or []:
        match = re.search(r"(\d{2,3}\.\d{2})\s*x\s*(\d{2,3}\.\d{2})\s*x\s*([\d.]+)\s*mm", name, re.I)
        if match:
            out["fork_slide_bushes"] = f"{match.group(1)} × {match.group(2)} × {match.group(3)} mm"
            out["fork_slide_bush_product"] = name
            break

    for name in out.get("circlip_products") or []:
        match = re.search(r"(\d{2,3}\.\d{2})\s*/\s*(\d{2,3}\.\d{2})\s*mm", name, re.I)
        if match:
            out["fork_seal_circlip"] = f"{match.group(1)}/{match.group(2)} mm"
            out["fork_seal_circlip_product"] = name
            break

    return out


def fetch(key: str, meta: list) -> dict:
    make, kname, year = meta
    cache_file = CACHE / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    find = f"{make}_{kname}_{year}"
    url = BIKE_URL + urllib.parse.quote(find)
    last_error = None
    for attempt in range(3):
        try:
            res = subprocess.run(
                ["curl", "-sS", "-L", "--compressed", "--max-time", "75", "-A", UA, url],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if res.returncode == 0 and "bike-details" in res.stdout:
                parsed = parse_page(res.stdout, make, kname, year)
                cache_file.write_text(json.dumps(parsed, ensure_ascii=False))
                return parsed
            last_error = f"curl {res.returncode}: {res.stderr[:120]}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        time.sleep(1.0 * (attempt + 1))
    return {"make": make, "ktech_model": kname, "year": year, "error": last_error}


def main() -> None:
    db = json.loads((ROOT / "data/motorcycles.json").read_text())["motorcycles"]
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.9"})
    mmy = load_mmy(session)
    wanted, matched_models = build_candidates(db, mmy)
    print(f"Matched models: {matched_models}; fitments to fetch: {len(wanted)}")

    results: dict[str, dict] = {}
    errors = 0
    started = time.time()
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = {pool.submit(fetch, key, meta): key for key, meta in wanted.items()}
        for idx, future in enumerate(as_completed(futures), 1):
            key = futures[future]
            parsed = future.result()
            results[key] = parsed
            if parsed.get("error"):
                errors += 1
            if idx % 100 == 0 or idx == len(wanted):
                elapsed = time.time() - started
                print(f"{idx}/{len(wanted)} fetched in {elapsed:.0f}s ({errors} errors)")
    STAGING.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"Wrote {STAGING} ({len(results)} fitments, {errors} errors)")


if __name__ == "__main__":
    main()

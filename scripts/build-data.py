#!/usr/bin/env python3
"""Build the public site's lightweight JSON files from data/motorcycles.json.

Generates:
  data/motorcycles-index.json   compact list used by browse and cards
  data/motorcycles/<id>.json    one file per bike (lazy-loaded detail pages)
  data/pages-index.json         compact wiki page list
  data/pages/<slug>.json        one file per wiki page
  data/search-index.json        flattened client-side search index
  data/popular-summaries.json   small cache for the featured-model list
"""
from __future__ import annotations

import json
import os
import re
from html import unescape
from typing import Any

from search_aliases import aliases_for, SUGGESTIONS

SUMMARY_KEYS = (
    "id", "make", "model", "year", "region", "category", "displacement",
    "tags", "summary", "published", "model_group", "engine", "power",
    "torque", "weight", "seat_height", "fuel_capacity",
)
PAGE_INDEX_KEYS = ("id", "title", "slug", "summary", "order", "published")
GENERAL_FIELDS = {
    "engine": "engine", "power": "power", "torque": "torque",
    "weight": "weight", "seat_height": "seat_height",
    "fuel_capacity": "fuel_capacity",
}


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "item"


def strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def field_map(section: dict[str, Any] | None, key: str) -> dict[str, str]:
    if not section:
        return {}
    if key == "fields":
        return {f.get("key"): f.get("value") for f in section.get("fields") or [] if f.get("key")}
    return {}


def section_values(moto: dict[str, Any]) -> dict[str, str]:
    sections = moto.get("sections") or {}
    general = field_map(sections.get("general_specs"), "fields")
    service = field_map(sections.get("service"), "fields")
    legacy_oil = field_map(sections.get("engine_oil"), "fields")
    values = {}
    for key in SUMMARY_KEYS:
        if key in moto and moto.get(key) not in (None, ""):
            values[key] = moto[key]
    for key, source in GENERAL_FIELDS.items():
        if general.get(source):
            values[key] = general[source]
    values["oil_capacity"] = service.get("oil_capacity") or legacy_oil.get("capacity") or ""
    values["oil_type"] = service.get("oil_grade") or legacy_oil.get("type") or ""
    return values


def motorcycle_summary(moto: dict[str, Any]) -> dict[str, Any]:
    values = section_values(moto)
    summary = {key: values[key] for key in SUMMARY_KEYS if key in values}
    summary["oil_capacity"] = values.get("oil_capacity", "")
    summary["oil_type"] = values.get("oil_type", "")
    return summary


def flatten_bike_search(bike: dict[str, Any]) -> str:
    values = section_values(bike)
    parts = [
        values.get("make"), values.get("model"), values.get("year"),
        values.get("region"), values.get("category"), values.get("displacement"),
        values.get("summary"), values.get("engine"), values.get("power"),
        values.get("torque"), values.get("weight"), values.get("seat_height"),
        *(bike.get("tags") or []),
    ]
    for section in (bike.get("sections") or {}).values():
        if section.get("label"):
            parts.append(section["label"])
        for field in section.get("fields") or []:
            parts.extend([field.get("label"), field.get("value")])
        for row in section.get("table") or []:
            parts.extend(str(value) for value in row.values() if value)
    for custom in bike.get("custom_sections") or []:
        parts.extend([custom.get("title"), strip_html(custom.get("content") or "")])
    return " ".join(str(part) for part in parts if part).lower()


def page_index_entry(page: dict[str, Any]) -> dict[str, Any]:
    return {key: page.get(key) for key in PAGE_INDEX_KEYS if key in page}


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize_search_text(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"([a-z])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([a-z])", r"\1 \2", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = re.sub(r"\s+", " ", text).strip().split()
    seen = set()
    unique = []
    for word in words:
        if word not in seen:
            seen.add(word)
            unique.append(word)
    return " ".join(unique)


def build_from_data_dir(data_dir: str) -> None:
    data_dir = os.path.realpath(data_dir)
    with open(os.path.join(data_dir, "motorcycles.json"), encoding="utf-8") as handle:
        motorcycles = json.load(handle).get("motorcycles") or []
    with open(os.path.join(data_dir, "pages.json"), encoding="utf-8") as handle:
        pages = json.load(handle).get("pages") or []
    with open(os.path.join(data_dir, "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)

    published = [m for m in motorcycles if m.get("published") is not False]
    published_pages = [p for p in pages if p.get("published") is not False]

    moto_dir = os.path.join(data_dir, "motorcycles")
    page_dir = os.path.join(data_dir, "pages")
    for target in (moto_dir, page_dir):
        os.makedirs(target, exist_ok=True)
        for name in os.listdir(target):
            if name.endswith(".json"):
                os.remove(os.path.join(target, name))

    summaries = [motorcycle_summary(moto) for moto in published]
    write_json(os.path.join(data_dir, "motorcycles-index.json"), {"motorcycles": summaries})

    for moto in published:
        moto_id = moto.get("id")
        if not moto_id:
            continue
        write_json(os.path.join(moto_dir, f"{safe_filename(moto_id)}.json"), {"motorcycle": moto})

    page_summaries = [page_index_entry(page) for page in published_pages]
    write_json(os.path.join(data_dir, "pages-index.json"), {"pages": page_summaries})

    for page in published_pages:
        slug = page.get("slug") or page.get("id")
        if not slug:
            continue
        write_json(os.path.join(page_dir, f"{safe_filename(slug)}.json"), {"page": page})

    search_items: list[dict[str, Any]] = []
    for bike in published:
        values = section_values(bike)
        meta = " · ".join(part for part in [values.get("region"), values.get("category"), values.get("displacement")] if part) or "Motorcycle"
        title = f"{values.get('make', '')} {values.get('model', '')}".strip()
        variant = ", ".join(part for part in [values.get("year"), values.get("region")] if part)
        if variant:
            title = f"{title} ({variant})"
        aliases = aliases_for(bike.get("make", ""), bike.get("model", ""))
        search_text = flatten_bike_search(bike)
        if aliases:
            search_text = f"{search_text} {' '.join(aliases)}"
        search_items.append({
            "type": "motorcycle",
            "id": bike.get("id"),
            "title": title,
            "make": bike.get("make", ""),
            "model": bike.get("model", ""),
            "model_group": bike.get("model_group", ""),
            "aliases": aliases,
            "meta": meta,
            "power": values.get("power", ""),
            "weight": values.get("weight", ""),
            "url": f"motorcycle.html?id={bike.get('id')}",
            "searchText": normalize_search_text(search_text),
        })
    for page in published_pages:
        slug = page.get("slug") or page.get("id")
        search_items.append({
            "type": "page",
            "id": page.get("id"),
            "title": page.get("title"),
            "meta": page.get("summary") or "Wiki page",
            "url": f"pages.html?slug={slug}",
            "searchText": normalize_search_text(f"{page.get('title', '')} {page.get('summary', '')} {strip_html(page.get('content') or '')}"),
            "aliases": [],
        })
    write_json(os.path.join(data_dir, "search-index.json"), {"items": search_items})

    popular = settings.get("popular_models") or {}
    summary_map = {item["id"]: item for item in summaries}
    popular_summaries = [summary_map[i] for i in popular.get("ids") or [] if i in summary_map]
    write_json(os.path.join(data_dir, "popular-summaries.json"), {"motorcycles": popular_summaries})


def main() -> None:
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(script_dir), "data")
    if not os.path.isdir(data_dir):
        raise SystemExit(f"Data folder not found: {data_dir}")
    build_from_data_dir(data_dir)
    print(f"Built wiki data files in {os.path.realpath(data_dir)}")


if __name__ == "__main__":
    main()

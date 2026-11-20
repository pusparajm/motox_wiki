#!/usr/bin/env python3
"""Merge K-Tech Part Finder suspension data into data/motorcycles.json.

Input: /tmp/opencode/ktech-parsed.json produced by scrape-ktech-suspension.py
Only unambiguous make/model matches are used. Values that change within a
model's year range are written with year qualifiers; conflicting values that
cannot be expressed cleanly are skipped.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
STAGING = Path("/tmp/opencode/ktech-parsed.json")
DB_PATH = Path(os.environ.get("MOTOX_DB_PATH", ROOT / "data/motorcycles.json"))
BACKUP = Path("/tmp/opencode/motorcycles.before-ktech.json")

spec = importlib.util.spec_from_file_location("ktech", ROOT / "scripts/scrape-ktech-suspension.py")
ktech = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ktech)

FIELD_SPECS = [
    ("fork_oil_grade", "Fork Oil Grade"),
    ("fork_oil_volume", "Fork Oil Quantity"),
    ("fork_air_gap", "Fork Air Gap"),
    ("fork_seal", "Fork Seal Size"),
    ("fork_dust_seal", "Fork Dust Seal Size"),
    ("fork_slide_bushes", "Fork Slide Bushes"),
    ("fork_seal_circlip", "Fork Seal Circlip"),
    ("rear_shock", "Rear Shock Absorber"),
]


def unique_size(products: list[str] | None, parser) -> str | None:
    sizes = []
    for name in products or []:
        low = name.lower()
        if "min order" in low or "min qty" in low or "minimum" in low:
            continue
        size = parser(name)
        if size and size not in sizes:
            sizes.append(size)
    return sizes[0] if len(sizes) == 1 else None


def bush_size(name: str) -> str | None:
    match = re.search(r"(\d{2,3}\.\d{2})\s*x\s*(\d{2,3}\.\d{2})\s*x\s*([\d.]+)\s*mm", name, re.I)
    if not match:
        return None
    return f"{match.group(1)} × {match.group(2)} × {match.group(3)} mm"


def circlip_size(name: str) -> str | None:
    match = re.search(r"(\d{2,3}\.\d{2})\s*/\s*(\d{2,3}\.\d{2})\s*mm", name, re.I)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)} mm"


def enrich_record(record: dict) -> dict:
    """Derive sizes from the stored product names using the current parsers."""
    record = dict(record)
    oil = unique_size(record.get("oil_seal_products"), ktech.size_from_name)
    dust = unique_size(record.get("dust_seal_products"), ktech.size_from_name)
    bush = unique_size(record.get("slide_bush_products"), bush_size)
    circlip = unique_size(record.get("circlip_products"), circlip_size)
    if oil:
        record["fork_seal"] = oil
    else:
        record.pop("fork_seal", None)
    if dust:
        record["fork_dust_seal"] = dust
    else:
        record.pop("fork_dust_seal", None)
    if bush:
        record["fork_slide_bushes"] = bush
    else:
        record.pop("fork_slide_bushes", None)
    if circlip:
        record["fork_seal_circlip"] = circlip
    else:
        record.pop("fork_seal_circlip", None)
    rear = record.get("rear_shock")
    if rear and not (re.search(r"\(\d{2,3}/\d{2,3}\)", rear) or re.search(r"\b(?:Mono|Twin) Tube\b", rear, re.I)):
        record.pop("rear_shock", None)
    return record


def year_label(years: list[int]) -> str:
    years = sorted(set(years))
    if not years:
        return ""
    parts = []
    start = prev = years[0]
    for year in years[1:] + [None]:
        if year is not None and year == prev + 1:
            prev = year
            continue
        parts.append(str(start) if start == prev else f"{start}–{prev}")
        if year is not None:
            start = prev = year
    return ", ".join(parts)


def value_with_years(value: str, years: list[int], coverage: list[int], field: str) -> str:
    # Add a year qualifier when the K-Tech value does not span the full model range.
    if sorted(set(years)) == sorted(set(coverage)):
        return value
    label = year_label(years)
    return f"{value} — K-Tech {label}"


def group_field(years_values: list[tuple[int, str]], coverage: list[int], field: str) -> str | None:
    by_value: dict[str, list[int]] = defaultdict(list)
    for year, value in years_values:
        if value:
            by_value[value].append(year)
    if not by_value:
        return None

    groups = sorted(by_value.items(), key=lambda item: min(item[1]))
    if len(groups) == 1:
        value, years = groups[0]
        return value_with_years(value, years, coverage, field)

    # If values change, emit a year-qualified list only when every group is one
    # contiguous run and there are at most three generations. Otherwise publish
    # the latest verified value and let its year qualifier carry the warning.
    latest = max(years_values, key=lambda item: item[0])
    if len(groups) > 3:
        return f"{latest[1]} — K-Tech {latest[0]} (latest listed)"
    rendered = []
    for value, years in groups:
        years = sorted(set(years))
        contiguous = all(b == a + 1 for a, b in zip(years, years[1:]))
        if not contiguous:
            return f"{latest[1]} — K-Tech {latest[0]} (latest listed)"
        label = year_label(years)
        rendered.append(f"{value} — K-Tech {label}")
    return "; ".join(rendered)


def merge() -> None:
    db = json.loads(DB_PATH.read_text())["motorcycles"]
    parsed = json.loads(STAGING.read_text())
    BACKUP.write_bytes(DB_PATH.read_bytes())

    # Group parsed records by normalised make/model/year.
    by_key: dict[tuple[str, str, int], dict] = {}
    for record in parsed.values():
        if not record or record.get("error"):
            continue
        record = enrich_record(record)
        key = (ktech.norm(record.get("make", "")), ktech.norm(record.get("ktech_model", "")), int(record.get("year", 0)))
        by_key[key] = record

    # Build the same unambiguous candidates used for scraping.
    session = requests.Session()
    session.headers.update({"User-Agent": "MotoX Wiki suspension enrichment"})
    mmy = ktech.load_mmy(session)
    by_make: dict[str, list[tuple[str, list[int]]]] = defaultdict(list)
    for make, models in mmy.items():
        for model, years in models.items():
            by_make[ktech.norm(make)].append((model, [int(y) for y in years]))

    updated = 0
    field_counts = defaultdict(int)
    skipped_models = 0
    conflicts = []
    report = []

    for model in db:
        # Combined catalogue entries (e.g. "748, S" or "SV 650, S") cannot be
        # assigned one variant's suspension data safely.
        if re.search(r"[,+/]| and ", str(model.get("model", "")), re.I):
            continue
        candidates = by_make.get(ktech.norm(model.get("make", "")), [])
        if not candidates:
            continue
        target_core = set(ktech.core_tokens(model.get("model", "")))
        exact = [c for c in candidates if ktech.norm(c[0]) == ktech.norm(model.get("model", ""))]
        base = [c for c in candidates if set(ktech.core_tokens(c[0])) == target_core]
        chosen = exact or base
        if len({name for name, _ in chosen}) != 1:
            skipped_models += 1
            continue
        kname, kyars = chosen[0]
        span = ktech.year_range(model)
        if not span:
            skipped_models += 1
            continue
        coverage = [y for y in kyars if span[0] <= y <= span[1]]
        records = [by_key.get((ktech.norm(model.get("make", "")), ktech.norm(kname), y)) for y in coverage]
        records = [r for r in records if r]
        if not records:
            skipped_models += 1
            continue
        model_years = list(range(span[0], span[1] + 1))

        # Validate displacement when both sides have it.
        def cc_number(value: str) -> int | None:
            match = re.search(r"\d[\d,]*(?:\.\d+)?", str(value or ""))
            return round(float(match.group(0).replace(",", ""))) if match else None

        db_cc = cc_number(model.get("displacement"))
        kt_cc = cc_number(records[0].get("displacement"))
        if db_cc and kt_cc and abs(db_cc - kt_cc) > 40:
            conflicts.append((model["id"], f"displacement mismatch: {model.get('displacement')} vs {records[0].get('displacement')}"))
            continue

        section = model.setdefault("sections", {}).setdefault("service", {"label": "Service Data", "fields": []})
        fields = section.setdefault("fields", [])
        existing = {f.get("key"): f for f in fields}
        added = []
        coverage_years = sorted({int(r["year"]) for r in records})

        legacy_oil = existing.get("fork_oil", {}).get("value", "")
        legacy_has_quantity = bool(re.search(r"\d+(?:\.\d+)?\s*(?:ml|millilit|litre|liter|l)\b", legacy_oil, re.I))
        for key, label in FIELD_SPECS:
            if key in existing:
                continue
            # Do not duplicate the combined legacy fork_oil field. If it already
            # contains a fill quantity, skip K-Tech's quantity/air-gap values too.
            if key == "fork_oil_grade" and legacy_oil:
                continue
            if key in {"fork_oil_volume", "fork_air_gap"} and legacy_has_quantity:
                continue
            years_values = []
            for record in records:
                value = record.get(key)
                if value:
                    years_values.append((int(record["year"]), str(value)))
            value = group_field(years_values, model_years, key)
            if not value:
                continue
            added.append({"key": key, "label": label, "value": value})
            field_counts[key] += 1

        if not added:
            continue

        # Insert suspension fields after the fork-related entries (or before the
        # closing note), preserving the existing field order.
        insert_at = len(fields)
        for idx, field in enumerate(fields):
            if field.get("key") in {"fork_oil", "fork_seal", "parts_note", "note"}:
                insert_at = idx + 1
        for offset, field in enumerate(added):
            fields.insert(insert_at + offset, field)

        source_years = year_label(coverage_years)
        source_value = (
            f"K-Tech Part Finder ({source_years}). Confirm fork variant, per-leg oil fill "
            "and model-year before ordering."
        )
        if "suspension_source" not in existing:
            fields.append({"key": "suspension_source", "label": "Suspension Source", "value": source_value})
        updated += 1
        report.append({
            "id": model["id"],
            "make": model["make"],
            "model": model["model"],
            "year": model["year"],
            "ktech_model": kname,
            "ktech_years": coverage_years,
            "fields": [f["key"] for f in added],
        })

    DB_PATH.write_text(json.dumps({"motorcycles": db}, indent=2, ensure_ascii=False) + "\n")
    Path("/tmp/opencode/ktech-merge-report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"Updated models: {updated}")
    print("Field counts:", dict(field_counts))
    print(f"Skipped models: {skipped_models}")
    if conflicts:
        print("Conflicts:", len(conflicts))
        for item in conflicts[:20]:
            print(" ", item)


if __name__ == "__main__":
    merge()

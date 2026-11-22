#!/usr/bin/env python3
"""Add EBC shape alternates to models that only have SBS brake-pad codes.

Phase 1 is intended to be run per manufacturer:

    python3 scripts/add-ebc-alternates.py --make Aprilia

The script uses the existing EBC/SBS interchange table, but only adds a shape
when the SBS base maps to exactly one EBC shape and that shape has an extracted
diagram. It never overwrites an existing EBC code.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SBS_PATTERN = re.compile(r"SBS\s+([0-9]+(?:/[0-9]+)*)", re.I)
EBC_PATTERN = re.compile(
    r"\b(?:EBC\s+)?((?:RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)\s*\d+(?:/\d+)?[A-Z]*)\b",
    re.I,
)


def load(name):
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def save(name, document):
    with (DATA / name).open("w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize(code):
    code = str(code or "").upper().replace(" ", "").strip()
    match = re.match(r"^(RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)(\d+)(.*)$", code)
    if not match:
        return code
    return f"{match.group(1)}{int(match.group(2))}{match.group(3)}"


def reverse_sbs_map(interchange):
    reverse = collections.defaultdict(list)
    for ebc, item in interchange.items():
        for sbs in item.get("sbs", []):
            base = str(sbs).strip()
            if base:
                reverse[base].append(ebc)
    return {base: codes[0] for base, codes in reverse.items() if len(codes) == 1}


def map_text(text, reverse, shapes):
    if not text or EBC_PATTERN.search(text):
        return ""
    for group in SBS_PATTERN.findall(text):
        for base in group.split("/"):
            ebc = reverse.get(base)
            if not ebc:
                continue
            code = normalize(ebc)
            if code in shapes and shapes[code].get("diagram"):
                return code
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", required=True)
    parser.add_argument(
        "--report",
        type=Path,
        default=DATA / "ebc-alternates-report.json",
    )
    args = parser.parse_args()

    catalog = load("motorcycles.json")
    bikes = catalog["motorcycles"]
    interchange = load("brake-interchange.json")
    shapes = load("ebc-pad-shapes.json")["shapes"]
    crossref = load("brake-crossref.json")
    reverse = reverse_sbs_map(interchange)

    eligible = []
    fixed = []
    positions = 0
    only_sbs_before = 0

    for bike in bikes:
        if bike.get("make", "").lower() != args.make.lower():
            continue
        service = {
            item.get("key"): item.get("value", "")
            for item in (bike.get("sections", {}).get("service") or {}).get("fields", [])
        }
        front = str(service.get("front_brake_pads", "") or "")
        rear = str(service.get("rear_brake_pads", "") or "")
        if not front and not rear:
            continue
        text = f"{front} {rear}"
        if EBC_PATTERN.search(text):
            continue
        if "SBS" not in text.upper():
            continue
        eligible.append(bike["id"])
        brands = set(re.findall(r"\b(EBC|SBS|Brembo|Ferodo|Dunlopad|Emgo|Vesrah|Nissin|Tokico)\b", text, re.I))
        if brands == {"SBS"}:
            only_sbs_before += 1

        changes = {}
        for key in ("front_brake_pads", "rear_brake_pads"):
            value = str(service.get(key, "") or "")
            code = map_text(value, reverse, shapes)
            if not code:
                continue
            new_value = f"EBC {code} · {value}" if value else f"EBC {code}"
            for field in (bike.get("sections", {}).get("service") or {}).get("fields", []):
                if field.get("key") == key:
                    field["value"] = new_value
                    break
            service[key] = new_value
            changes[key] = {"ebc": code, "before": value, "after": new_value}
            positions += 1

        if not changes:
            continue

        crossref.setdefault(bike["id"], {})
        for key in ("front_brake_pads", "rear_brake_pads"):
            value = str(service.get(key, "") or "")
            if value:
                crossref[bike["id"]][key] = value
        fixed.append({
            "id": bike["id"],
            "make": bike.get("make", ""),
            "model": bike.get("model", ""),
            "changes": changes,
        })

    save("motorcycles.json", catalog)
    save("brake-crossref.json", crossref)
    report = {
        "make": args.make,
        "eligible_models": len(eligible),
        "only_sbs_before": only_sbs_before,
        "fixed_models": len(fixed),
        "fixed_positions": positions,
        "remaining_models": len(eligible) - len(fixed),
        "fixed": sorted(fixed, key=lambda item: item["id"]),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        f"{args.make}: eligible={len(eligible)} only_sbs={only_sbs_before} "
        f"fixed_models={len(fixed)} fixed_positions={positions} "
        f"remaining={len(eligible) - len(fixed)}"
    )


if __name__ == "__main__":
    main()

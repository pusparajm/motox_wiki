#!/usr/bin/env python3
"""Merge verified battery fitment data into the motorcycle service sections."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MOTORCYCLES = os.path.join(DATA, "motorcycles.json")
FITMENT = os.path.join(DATA, "battery-fitment.json")

LABELS = {
    "battery": "Battery",
    "battery_options": "Battery Options",
    "battery_rating": "Battery Rating",
}


def main():
    with open(MOTORCYCLES, encoding="utf-8") as fh:
        db = json.load(fh)
    with open(FITMENT, encoding="utf-8") as fh:
        fitment = json.load(fh)["models"]

    updated = 0
    for bike in db["motorcycles"]:
        entry = fitment.get(bike["id"])
        service = (bike.get("sections") or {}).get("service")
        if not service:
            continue
        fields = [f for f in service.get("fields", []) if f.get("key") not in LABELS]
        if entry:
            new_fields = []
            if entry.get("code"):
                new_fields.append({"key": "battery", "label": LABELS["battery"], "value": entry["code"]})
            if entry.get("options"):
                new_fields.append({"key": "battery_options", "label": LABELS["battery_options"], "value": ", ".join(entry["options"])})
            if entry.get("rating"):
                new_fields.append({"key": "battery_rating", "label": LABELS["battery_rating"], "value": entry["rating"]})
            if new_fields:
                insert_at = len(fields)
                for index, field in enumerate(fields):
                    if field.get("key") == "spark_plug":
                        insert_at = index + 1
                        break
                fields[insert_at:insert_at] = new_fields
                updated += 1
        service["fields"] = fields

    with open(MOTORCYCLES, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"Applied battery data to {updated} models")


if __name__ == "__main__":
    main()

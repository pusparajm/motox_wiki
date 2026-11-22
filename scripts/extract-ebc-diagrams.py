#!/usr/bin/env python3
"""Extract the EBC brake-pad diagrams from the EBC buyers guide.

The diagrams are reproduced with written permission from EBC. Run:

    python3 scripts/extract-ebc-diagrams.py /path/to/EBC_UK_MC_Pad_Buyers_Guide_203.pdf

The script writes PNGs to `images/pad-shapes/` and merges the diagram paths
into `data/ebc-pad-shapes.json`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber
from PIL import ImageOps

ROOT = Path(__file__).resolve().parent.parent
CODE_PATTERN = re.compile(
    r"^(?:FA|EPFA|SFA|GPFAX|MXS|SXR|RFA)\d{2,3}(?:/\d+)?[A-Z]*$"
)


def normalize(code: str) -> str:
    match = re.match(r"^(RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)(\d+)(.*)$", code)
    if not match:
        return code
    return f"{match.group(1)}{int(match.group(2))}{match.group(3)}"


def slug(code: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(code).lower()).strip("-")


def cluster(objects):
    objects = sorted(objects, key=lambda item: (item["top"], item["x0"]))
    groups = []
    for obj in objects:
        if groups and obj["top"] <= groups[-1]["bottom"] + 8:
            groups[-1]["objects"].append(obj)
            groups[-1]["bottom"] = max(groups[-1]["bottom"], obj["bottom"])
        else:
            groups.append({"objects": [obj], "top": obj["top"], "bottom": obj["bottom"]})
    return groups


def x_groups(objects, gap=100):
    groups = []
    for obj in sorted(objects, key=lambda item: item["x0"]):
        if groups and obj["x0"] <= groups[-1]["x1"] + gap:
            groups[-1]["objects"].append(obj)
            groups[-1]["x1"] = max(groups[-1]["x1"], obj["x1"])
        else:
            groups.append({"objects": [obj], "x0": obj["x0"], "x1": obj["x1"]})
    return groups


def bounds(objects):
    xs = []
    ys = []
    for obj in objects:
        xs.extend([obj["x0"], obj["x1"]])
        ys.extend([obj["top"], obj["bottom"]])
    return min(xs), min(ys), max(xs), max(ys)


def curve_bounds(objects):
    curves = [obj for obj in objects if obj["object_type"] == "curve"]
    return bounds(curves) if curves else bounds(objects)


def extract(pdf_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfplumber.open(str(pdf_path))
    candidates = {}

    for page_number, page in enumerate(pdf.pages, 1):
        words = [
            word
            for word in page.extract_words()
            if word["x0"] < 160 and CODE_PATTERN.match(word["text"])
        ]
        words.sort(key=lambda word: word["top"])
        groups = []
        for word in words:
            if groups and word["top"] - groups[-1][-1]["top"] < 40:
                groups[-1].append(word)
            else:
                groups.append([word])

        objects = [
            obj
            for obj in page.lines + page.curves + page.rects
            if obj.get("x0", 0) >= 50
            and obj.get("x1", 0) <= 760
            and not (obj["object_type"] == "line" and (obj.get("width", 0) > 200 or obj.get("height", 0) > 100))
        ]
        left_objects = [obj for obj in objects if obj.get("x1", 0) <= 300]
        right_objects = [obj for obj in objects if obj.get("x0", 0) > 300]

        for index, group in enumerate(groups):
            start = max(word["bottom"] for word in group) + 3
            end = (
                groups[index + 1][0]["top"] - 3
                if index + 1 < len(groups)
                else page.height - 20
            )
            def best_cluster(source):
                region = [
                    obj for obj in source
                    if obj["top"] >= start - 2 and obj["top"] <= end
                ]
                best = None
                for candidate in cluster(region):
                    for xcandidate in x_groups(candidate["objects"]):
                        items = xcandidate["objects"]
                        curves = sum(1 for obj in items if obj["object_type"] == "curve")
                        strokes = sum(1 for obj in items if obj.get("stroke"))
                        x0, y0, x1, y1 = bounds(items)
                        width, height = x1 - x0, y1 - y0
                        if width < 8 or height < 8 or not curves:
                            continue
                        score = curves * 10 + strokes + min(width, 120) / 10 + min(height, 120) / 10
                        if best is None or score > best[0]:
                            best = (score, {"objects": items})
                return best

            best = best_cluster(left_objects) or best_cluster(right_objects)
            if not best:
                continue

            x0, y0, x1, y1 = curve_bounds(best[1]["objects"])
            pad = 2.5
            crop = (
                max(0, x0 - pad),
                max(0, y0 - pad),
                min(page.width, x1 + pad),
                min(page.height, y1 + pad),
            )
            for word in group:
                code = normalize(word["text"])
                previous = candidates.get(code)
                if previous is None or best[0] > previous["score"]:
                    candidates[code] = {
                        "page": page_number,
                        "crop": crop,
                        "score": best[0],
                    }

    metadata = {}
    for code, item in sorted(candidates.items()):
        page = pdf.pages[item["page"] - 1]
        image = page.crop(item["crop"]).to_image(resolution=300).original.convert("L")
        box = ImageOps.invert(image).getbbox()
        if not box:
            continue
        image = image.crop(box)
        image = ImageOps.expand(image, border=4, fill=255)
        if image.width < 16 or image.height < 16:
            continue
        path = output_dir / f"{slug(code)}.png"
        image.save(path, optimize=True)
        metadata[code] = {
            "diagram": str(path.relative_to(ROOT)).replace("\\", "/"),
            "diagramWidth": image.width,
            "diagramHeight": image.height,
            "diagramPage": item["page"],
        }

    # FA231 and FA231/3 share the A/B drawing with FA231/2.
    for code in ("FA231", "FA231/3"):
        if code not in metadata and "FA231/2" in metadata:
            metadata[code] = dict(metadata["FA231/2"])

    data_path = ROOT / "data/ebc-pad-shapes.json"
    if data_path.exists():
        with data_path.open(encoding="utf-8") as handle:
            document = json.load(handle)
        for code, item in metadata.items():
            if code in document.get("shapes", {}):
                document["shapes"][code].update(item)
        with data_path.open("w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "images/pad-shapes",
    )
    args = parser.parse_args()
    metadata = extract(args.pdf, args.output_dir)
    print(f"Wrote {len(metadata)} diagrams to {args.output_dir}")


if __name__ == "__main__":
    main()

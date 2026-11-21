#!/usr/bin/env python3
"""Download approved motorcycle images and build responsive local variants.

Only entries with explicit rights approval and a licence are processed. The
script never scrapes a page: it fetches a direct image URL from the approved
source list and records the source page, licence and credit in the manifest.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMAGES = ROOT / "images" / "motorcycles"
SOURCES = DATA / "bike-image-sources.json"
MANIFEST = DATA / "bike-images.json"
MOTORCYCLES = DATA / "motorcycles.json"

DEFAULT_WIDTHS = (400, 800, 1200)
ASPECT = 2 / 3
USER_AGENT = "MotoXWikiImagePipeline/1.0 (+https://motoxref.com)"
MAX_BYTES = 20 * 1024 * 1024
MIN_SOURCE_WIDTH = 1200
MIN_SOURCE_HEIGHT = 800


def slug(value):
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "model"


def load_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def identify(path):
    out = subprocess.check_output(
        ["identify", "-format", "%w %h", str(path)], stderr=subprocess.STDOUT
    ).decode("utf-8", "replace").strip()
    width, height = out.split()[:2]
    return int(width), int(height)


def image_options():
    settings = load_json(DATA / "settings.json", {})
    options = (settings.get("options") or {}).get("images") or {}
    try:
        max_width = int(options.get("maxWidth", 1200))
    except (TypeError, ValueError):
        max_width = 1200
    max_width = 1200 if max_width >= 1200 else 800
    widths = tuple(width for width in DEFAULT_WIDTHS if width <= max_width)
    try:
        avif_quality = max(30, min(70, int(options.get("avifQuality", 55))))
    except (TypeError, ValueError):
        avif_quality = 55
    try:
        webp_quality = max(50, min(95, int(options.get("webpQuality", 82))))
    except (TypeError, ValueError):
        webp_quality = 82
    try:
        jpg_quality = max(50, min(95, int(options.get("jpegQuality", 82))))
    except (TypeError, ValueError):
        jpg_quality = 82
    return widths, max_width, avif_quality, webp_quality, jpg_quality


def prepare_source(image_url, destination):
    if image_url.startswith("https://"):
        download(image_url, destination)
        return
    if image_url.startswith("image-uploads/"):
        source = DATA / image_url
        if not source.exists():
            raise FileNotFoundError(f"uploaded image not found: {image_url}")
        shutil.copyfile(source, destination)
        return
    raise ValueError("image URL must be HTTPS or an admin upload path")


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type.startswith("image/"):
            raise ValueError(f"unexpected content type: {content_type or 'unknown'}")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("image exceeds the 20 MB download limit")
    destination.write_bytes(data)


def make_variants(source, directory, stem, fit, gravity, widths, qualities):
    variants = {}
    for width in widths:
        height = round(width * ASPECT)
        for fmt, quality in (("avif", qualities[0]), ("webp", qualities[1]), ("jpg", qualities[2])):
            target = directory / f"{stem}-{width}.{fmt}"
            cmd = [
                "convert",
                str(source),
                "-auto-orient",
                "-strip",
                "-background",
                "#f4f4f5",
                "-alpha",
                "remove",
                "-alpha",
                "off",
            ]
            if fit == "contain":
                cmd += ["-resize", f"{width}x{height}", "-gravity", gravity, "-extent", f"{width}x{height}"]
            else:
                cmd += ["-resize", f"{width}x{height}^", "-gravity", gravity, "-extent", f"{width}x{height}"]
            if fmt == "jpg":
                cmd += ["-quality", quality, "-interlace", "Plane", str(target)]
            else:
                cmd += ["-quality", quality, str(target)]
            run(cmd)
            relative = target.relative_to(ROOT).as_posix()
            variants.setdefault(fmt, {})[str(width)] = relative
    return variants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace existing variants")
    parser.add_argument("--dry-run", action="store_true", help="validate sources without downloading")
    args = parser.parse_args()

    widths, max_width, avif_quality, webp_quality, jpg_quality = image_options()
    qualities = (str(avif_quality), str(webp_quality), str(jpg_quality))
    motorcycles = {
        item["id"]: item
        for item in load_json(MOTORCYCLES, {"motorcycles": []}).get("motorcycles", [])
    }
    source_doc = load_json(SOURCES, {"sources": []})
    manifest = load_json(MANIFEST, {"version": 1, "images": {}})
    images = manifest.setdefault("images", {})

    downloaded = 0
    skipped = 0
    generated = 0

    for entry in source_doc.get("sources", []):
        model_id = entry.get("modelId", "")
        model = motorcycles.get(model_id)
        if not model:
            print(f"skip {model_id or '(no id)'}: model not in catalogue", file=sys.stderr)
            skipped += 1
            continue
        if not entry.get("rightsApproved") or not entry.get("license"):
            print(f"skip {model_id}: rights not approved or licence missing", file=sys.stderr)
            skipped += 1
            continue
        if entry.get("watermark") or entry.get("watermarkRemovalRequired"):
            print(f"skip {model_id}: watermarked source; supply an unwatermarked original", file=sys.stderr)
            skipped += 1
            continue
        if "permission" in str(entry.get("license") or "").lower() and not entry.get("permissionReference"):
            print(f"skip {model_id}: written permission reference missing", file=sys.stderr)
            skipped += 1
            continue
        image_url = entry.get("imageUrl", "")
        if not (image_url.startswith("https://") or image_url.startswith("image-uploads/")):
            print(f"skip {model_id}: image URL must be HTTPS or an admin upload", file=sys.stderr)
            skipped += 1
            continue
        source_page = entry.get("sourcePage", "")
        if not source_page:
            print(f"skip {model_id}: source page missing", file=sys.stderr)
            skipped += 1
            continue

        make_slug = slug(model.get("make"))
        model_slug = slug(model.get("model"))
        directory = IMAGES / make_slug / model_slug
        digest = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:8]
        stem = f"{model_slug}-{digest}"
        existing = images.get(model_id)
        if existing and not args.force:
            expected = [
                directory / f"{stem}-{width}.{fmt}"
                for width in widths
                for fmt in ("avif", "webp", "jpg")
            ]
            if all(path.exists() for path in expected):
                print(f"ok   {model_id}: variants already present")
                skipped += 1
                continue

        if args.dry_run:
            print(f"plan {model_id}: {image_url}")
            downloaded += 1
            continue

        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".img", delete=True) as tmp:
            try:
                prepare_source(image_url, Path(tmp.name))
                width, height = identify(tmp.name)
                if width < MIN_SOURCE_WIDTH or height < MIN_SOURCE_HEIGHT:
                    raise ValueError(
                        f"source image is {width}x{height}; minimum is "
                        f"{MIN_SOURCE_WIDTH}x{MIN_SOURCE_HEIGHT}"
                    )
                variants = make_variants(
                    tmp.name,
                    directory,
                    stem,
                    entry.get("fit", "cover"),
                    entry.get("gravity", "center"),
                    widths,
                    qualities,
                )
            except Exception as exc:
                print(f"fail {model_id}: {exc}", file=sys.stderr)
                skipped += 1
                continue

        images[model_id] = {
            "source": "approved",
            "sourcePage": source_page,
            "license": entry["license"],
            "licenseUrl": entry.get("licenseUrl", ""),
            "permissionReference": entry.get("permissionReference", ""),
            "credit": entry.get("credit", ""),
            "creditRequired": bool(entry.get("creditRequired")),
            "alt": entry.get("alt") or f"{model.get('make', '')} {model.get('model', '')}",
            "width": max_width,
            "height": round(max_width * ASPECT),
            "variants": variants,
        }
        downloaded += 1
        generated += sum(len(widths) for widths in variants.values())
        print(f"done {model_id}: {width}x{height} source -> {generated} variants")

    if not args.dry_run:
        save_json(MANIFEST, manifest)
    print(
        f"processed={downloaded} skipped={skipped} variants={generated} "
        f"manifest_entries={len(images)}"
    )


if __name__ == "__main__":
    main()

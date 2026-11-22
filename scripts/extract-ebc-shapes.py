#!/usr/bin/env python3
"""Extract EBC pad shape codes and dimensions from the EBC buyers guide.

The EBC PDF is not stored in this repository. Download it from the URL in
`data/ebc-pad-shapes.json`, then run:

    python3 scripts/extract-ebc-shapes.py /path/to/EBC_UK_MC_Pad_Buyers_Guide_203.pdf

The script keeps factual shape codes, dimensions and the PDF page number. It
does not extract or redistribute EBC's copyrighted line drawings.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

CODE_PATTERN = r"(?:RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)\s*\d{2,3}(?:/\d+)?(?:[A-Z]{1,3})?"
CODE_ONLY = re.compile(r"^(" + CODE_PATTERN + r")$")
CODE_WITH_DIMENSIONS = re.compile(r"^(" + CODE_PATTERN + r")\s+(.+)$")
NUMBER = r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?"

SOURCE = "https://www.ebcbrakes.com/wp-content/uploads/2024/01/EBC_UK_MC_Pad_Buyers_Guide_203.pdf"
SOURCE_LABEL = "EBC UK MC Pad Buyers Guide 203"
NOTE = (
    "Shape codes and dimensions extracted from the EBC Buyers Guide. "
    "EBC line drawings are not reproduced; only the factual shape codes and dimensions are stored."
)


def clean(value: str) -> str:
    value = value.replace("\x07", " ").replace("\u2002", " ").replace("\u00a0", " ")
    return " ".join(value.split())


def normalize(code: str) -> str:
    code = code.upper().replace(" ", "").strip()
    match = re.match(r"^(RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)(\d+)(.*)$", code)
    if not match:
        return code
    return f"{match.group(1)}{int(match.group(2))}{match.group(3)}"


def display(code: str) -> str:
    match = re.match(r"^(RFA|EPFA|GPFAX|SFA|MXS|SXR|FA)(\d+)(.*)$", code)
    if not match:
        return code
    return f"{match.group(1)}{match.group(2).zfill(3)}{match.group(3)}"


def dimensions(text: str) -> str:
    groups = re.findall(r"(" + NUMBER + r"(?:\s*[x×]\s*" + NUMBER + r")*)\s*mm", text)
    if not groups:
        return ""
    cleaned = []
    for group in groups:
        group = re.sub(r"\s*[x×]\s*", " x ", group.strip())
        cleaned.append(group + " mm")
    value = "; ".join(cleaned)
    parts = [part.strip() for part in value.split(";")]
    if len(parts) == 2 and " x " not in parts[1] and re.fullmatch(r"\d+(?:\.\d+)? mm", parts[1]):
        value = parts[0].replace(" mm", " x " + parts[1].replace(" mm", "") + " mm")
    return value


def page_text(pdf: Path, page: int) -> str:
    return subprocess.check_output(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
        text=True,
        errors="replace",
    )


def extract(pdf: Path) -> dict:
    shapes = {}
    page_count = int(
        subprocess.check_output(["pdfinfo", str(pdf)], text=True).split("Pages:")[1].split()[0]
    )
    for page in range(1, page_count + 1):
        lines = [clean(line) for line in page_text(pdf, page).splitlines()]
        for index, line in enumerate(lines):
            match = CODE_WITH_DIMENSIONS.match(line)
            if match and dimensions(match.group(2)):
                code = match.group(1)
                value = dimensions(match.group(2))
            else:
                match = CODE_ONLY.match(line)
                if not match:
                    continue
                code = match.group(1)
                value = ""
                for next_line in lines[index + 1:index + 5]:
                    value = dimensions(next_line)
                    if value:
                        break
                if not value:
                    continue
            key = normalize(code)
            item = {
                "code": key,
                "displayCode": display(code),
                "dimensions": value,
                "pdfPage": page,
            }
            if key not in shapes or len(value) > len(shapes[key]["dimensions"]):
                shapes[key] = item
    return {
        "source": SOURCE,
        "sourceLabel": SOURCE_LABEL,
        "note": NOTE,
        "shapes": dict(sorted(shapes.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data/ebc-pad-shapes.json",
    )
    args = parser.parse_args()
    result = extract(args.pdf)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Wrote {len(result['shapes'])} shapes to {args.output}")


if __name__ == "__main__":
    main()

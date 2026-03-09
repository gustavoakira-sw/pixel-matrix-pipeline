#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.palette_ops import swap_palette
from src.pipeline.renderer import matrix_to_png


def _parse_map_item(item: str) -> tuple[str, str]:
    if "=" not in item:
        raise ValueError(f"Invalid --map entry: {item}. Expected SOURCE=TARGET")
    source, target = item.split("=", 1)
    source = source.strip()
    target = target.strip()
    if not source or not target:
        raise ValueError(f"Invalid --map entry: {item}. Expected SOURCE=TARGET")
    return source, target


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply palette color swaps to SpriteMatrix JSON")
    parser.add_argument("input_json", type=Path, help="Path to input SpriteMatrix JSON")
    parser.add_argument(
        "--map",
        dest="maps",
        action="append",
        default=[],
        help="Color mapping in format #RRGGBBAA=#RRGGBBAA (repeatable)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path to output swapped JSON",
    )
    parser.add_argument(
        "--output-png",
        type=Path,
        default=None,
        help="Optional path to output swapped PNG preview",
    )
    args = parser.parse_args()

    color_map: dict[str, str] = {}
    for item in args.maps:
        source, target = _parse_map_item(item)
        color_map[source] = target

    data = json.loads(args.input_json.read_text(encoding="utf-8"))
    swapped = swap_palette(data, color_map)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(swapped, indent=2), encoding="utf-8")
    print(f"Wrote swapped matrix JSON to {args.output_json}")

    if args.output_png is not None:
        image = matrix_to_png(swapped["pixels"], swapped["palette"])
        args.output_png.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output_png)
        print(f"Wrote swapped PNG to {args.output_png}")


if __name__ == "__main__":
    main()

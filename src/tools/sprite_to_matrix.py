#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.extractor import sprite_to_matrix
from src.pipeline.importer import load_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a sprite PNG into SpriteMatrix JSON")
    parser.add_argument("input_png", type=Path, help="Path to input sprite PNG")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Path for JSON output (default: same name as input)",
    )
    args = parser.parse_args()

    image = load_png(args.input_png)
    matrix = sprite_to_matrix(image)

    output_json = args.output_json or args.input_png.with_suffix(".json")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(matrix, indent=2), encoding="utf-8")

    print(f"Wrote matrix JSON to {output_json}")


if __name__ == "__main__":
    main()

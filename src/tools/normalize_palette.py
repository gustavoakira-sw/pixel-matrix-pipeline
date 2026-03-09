#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.palette_ops import normalize_palette


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize palette in SpriteMatrix JSON")
    parser.add_argument("input_json", type=Path, help="Path to input SpriteMatrix JSON")
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path to output normalized JSON",
    )
    args = parser.parse_args()

    data = json.loads(args.input_json.read_text(encoding="utf-8"))
    normalized = normalize_palette(data)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    print(f"Wrote normalized matrix JSON to {args.output_json}")


if __name__ == "__main__":
    main()

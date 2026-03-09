#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.renderer import matrix_to_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert SpriteMatrix JSON back into a PNG")
    parser.add_argument("input_json", type=Path, help="Path to SpriteMatrix JSON")
    parser.add_argument(
        "--output-png",
        type=Path,
        default=None,
        help="Path for PNG output (default: same name as input)",
    )
    args = parser.parse_args()

    data = json.loads(args.input_json.read_text(encoding="utf-8"))
    image = matrix_to_png(data["pixels"], data["palette"])

    output_png = args.output_png or args.input_json.with_suffix(".png")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)

    print(f"Wrote sprite PNG to {output_png}")


if __name__ == "__main__":
    main()

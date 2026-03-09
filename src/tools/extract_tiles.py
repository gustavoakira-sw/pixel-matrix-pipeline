#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline.importer import load_png
from src.pipeline.slicer import slice_tiles


def main() -> None:
    parser = argparse.ArgumentParser(description="Slice a tilesheet into individual tile PNGs")
    parser.add_argument("input_png", type=Path, help="Path to source tilesheet PNG")
    parser.add_argument("tile_size", type=int, help="Square tile size in pixels")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "tiles",
        help="Directory where tile PNG files are written",
    )
    args = parser.parse_args()

    image = load_png(args.input_png)
    tiles = slice_tiles(image, args.tile_size)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for idx, tile in enumerate(tiles):
        tile.save(args.output_dir / f"tile_{idx:03d}.png")

    print(f"Wrote {len(tiles)} tiles to {args.output_dir}")


if __name__ == "__main__":
    main()

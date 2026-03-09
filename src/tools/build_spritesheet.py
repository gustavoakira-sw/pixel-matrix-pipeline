#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline.spritesheet import generate_atlas, pack_sprites


def main() -> None:
    parser = argparse.ArgumentParser(description="Build spritesheet PNG and atlas JSON from a tile folder")
    parser.add_argument("input_tiles_dir", type=Path, help="Directory containing input PNG tiles")
    parser.add_argument("--tile-size", type=int, required=True, help="Tile width and height in pixels")
    parser.add_argument(
        "--output-image",
        type=Path,
        default=Path("output") / "spritesheet.png",
        help="Output spritesheet PNG path",
    )
    parser.add_argument(
        "--output-atlas",
        type=Path,
        default=Path("output") / "atlas.json",
        help="Output atlas JSON path",
    )
    args = parser.parse_args()

    sprite_paths = sorted(str(path) for path in args.input_tiles_dir.glob("*.png"))
    if not sprite_paths:
        raise ValueError(f"No PNG files found in {args.input_tiles_dir}")

    sheet = pack_sprites(sprite_paths, args.tile_size)
    atlas = generate_atlas(sprite_paths, args.tile_size)

    args.output_image.parent.mkdir(parents=True, exist_ok=True)
    args.output_atlas.parent.mkdir(parents=True, exist_ok=True)

    sheet.save(args.output_image)
    args.output_atlas.write_text(json.dumps(atlas, indent=2), encoding="utf-8")

    print(f"Wrote spritesheet: {args.output_image}")
    print(f"Wrote atlas: {args.output_atlas}")


if __name__ == "__main__":
    main()

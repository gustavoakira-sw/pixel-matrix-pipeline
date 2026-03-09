#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image


def _require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Missing required file: {path}")


def _check_roundtrip_identity(original_tile: Path, rebuilt_tile: Path) -> None:
    _require_file(original_tile)
    _require_file(rebuilt_tile)

    if original_tile.read_bytes() != rebuilt_tile.read_bytes():
        raise ValueError(
            f"Roundtrip mismatch: {original_tile} and {rebuilt_tile} are not byte-identical"
        )


def _check_atlas_and_spritesheet(
    tiles_dir: Path,
    atlas_path: Path,
    sheet_path: Path,
    tile_size: int,
) -> None:
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")

    if not tiles_dir.exists() or not tiles_dir.is_dir():
        raise FileNotFoundError(f"Missing tiles directory: {tiles_dir}")

    tile_files = sorted(tiles_dir.glob("*.png"))
    if not tile_files:
        raise ValueError(f"No PNG tiles found in {tiles_dir}")

    _require_file(atlas_path)
    _require_file(sheet_path)

    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    frames = atlas.get("frames")
    if not isinstance(frames, dict):
        raise ValueError("atlas.json must contain an object key: 'frames'")
    meta = atlas.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("atlas.json must contain an object key: 'meta'")

    count = len(tile_files)
    if len(frames) != count:
        raise ValueError(f"Atlas frame count mismatch: expected {count}, got {len(frames)}")

    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    expected_sheet_size = (columns * tile_size, rows * tile_size)

    with Image.open(sheet_path) as sheet:
        actual_size = sheet.size
    if actual_size != expected_sheet_size:
        raise ValueError(
            f"Spritesheet size mismatch: expected {expected_sheet_size}, got {actual_size}"
        )
    if meta.get("size") != {"w": expected_sheet_size[0], "h": expected_sheet_size[1]}:
        raise ValueError(
            "Atlas meta.size mismatch with expected spritesheet dimensions "
            f"{expected_sheet_size}: got {meta.get('size')}"
        )

    for index in range(count):
        key = f"tile_{index:03d}"
        if key not in frames:
            raise ValueError(f"Missing atlas frame key: {key}")

        frame = frames[key]
        if not isinstance(frame, dict):
            raise ValueError(f"Invalid frame payload for {key}")
        frame_rect = frame.get("frame")
        if not isinstance(frame_rect, dict):
            raise ValueError(f"Missing frame.frame payload for {key}")

        expected = {
            "x": (index % columns) * tile_size,
            "y": (index // columns) * tile_size,
            "w": tile_size,
            "h": tile_size,
        }
        if frame_rect != expected:
            raise ValueError(f"Frame mismatch for {key}: expected {expected}, got {frame_rect}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated output artifacts")
    parser.add_argument("--tiles-dir", type=Path, default=Path("output/tiles"))
    parser.add_argument("--atlas", type=Path, default=Path("output/atlas.json"))
    parser.add_argument("--sheet", type=Path, default=Path("output/spritesheet.png"))
    parser.add_argument("--original-tile", type=Path, default=Path("output/tiles/tile_000.png"))
    parser.add_argument("--rebuilt-tile", type=Path, default=Path("output/tile_000_rebuilt.png"))
    parser.add_argument("--tile-size", type=int, default=16)
    args = parser.parse_args()

    try:
        _check_roundtrip_identity(args.original_tile, args.rebuilt_tile)
        _check_atlas_and_spritesheet(args.tiles_dir, args.atlas, args.sheet, args.tile_size)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1) from exc

    print("[OK] Roundtrip byte identity verified")
    print("[OK] Atlas/grid coordinates and spritesheet dimensions verified")


if __name__ == "__main__":
    main()

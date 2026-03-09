from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

from src.pipeline.importer import load_png


def _grid_dimensions(count: int) -> tuple[int, int]:
    if count <= 0:
        raise ValueError("At least one sprite is required")

    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    return columns, rows


def _ordered_paths(sprite_paths: list[str]) -> list[Path]:
    if not sprite_paths:
        raise ValueError("sprite_paths cannot be empty")
    return sorted(Path(path) for path in sprite_paths)


def _frame_entry(x: int, y: int, tile_size: int) -> dict:
    return {
        "frame": {"x": x, "y": y, "w": tile_size, "h": tile_size},
        "rotated": False,
        "trimmed": False,
        "spriteSourceSize": {"x": 0, "y": 0, "w": tile_size, "h": tile_size},
        "sourceSize": {"w": tile_size, "h": tile_size},
    }


def pack_sprites(sprite_paths: list[str], tile_size: int) -> Image.Image:
    """Pack equally sized PNG sprites into a deterministic grid spritesheet."""
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")

    paths = _ordered_paths(sprite_paths)
    columns, rows = _grid_dimensions(len(paths))
    sheet = Image.new("RGBA", (columns * tile_size, rows * tile_size))

    for index, path in enumerate(paths):
        sprite = load_png(path)
        if sprite.size != (tile_size, tile_size):
            raise ValueError(
                f"Sprite {path} has size {sprite.size}; expected {tile_size}x{tile_size}"
            )

        x = (index % columns) * tile_size
        y = (index // columns) * tile_size
        sheet.paste(sprite, (x, y))

    return sheet


def generate_atlas(sprite_paths: list[str], tile_size: int, *, image_name: str = "spritesheet.png") -> dict:
    """Generate deterministic Phaser-style hash atlas metadata for a spritesheet pack."""
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")

    paths = _ordered_paths(sprite_paths)
    columns, rows = _grid_dimensions(len(paths))

    frames: dict[str, dict] = {}
    for index, _path in enumerate(paths):
        x = (index % columns) * tile_size
        y = (index // columns) * tile_size
        frames[f"tile_{index:03d}"] = _frame_entry(x, y, tile_size)

    return {
        "frames": frames,
        "meta": {
            "app": "ai-game-pipeline",
            "version": "0.0.6-dev",
            "image": image_name,
            "format": "RGBA8888",
            "size": {"w": columns * tile_size, "h": rows * tile_size},
            "scale": "1",
        },
    }

from __future__ import annotations

from typing import Any

from PIL import Image


def _rgba_to_hex(color: tuple[int, int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}{:02X}".format(*color)


def extract_palette(image: Image.Image) -> list[str]:
    """Extract a deterministic palette in first-seen pixel order."""
    rgba = image.convert("RGBA")
    width, height = rgba.size

    seen: set[tuple[int, int, int, int]] = set()
    palette: list[str] = []

    for y in range(height):
        for x in range(width):
            color = rgba.getpixel((x, y))
            if color not in seen:
                seen.add(color)
                palette.append(_rgba_to_hex(color))

    return palette


def sprite_to_matrix(image: Image.Image) -> dict[str, Any]:
    """Convert an image into the SpriteMatrix JSON-compatible structure."""
    rgba = image.convert("RGBA")
    width, height = rgba.size
    palette = extract_palette(rgba)

    index_by_color = {
        tuple(int(palette_hex[i : i + 2], 16) for i in (1, 3, 5, 7)): idx
        for idx, palette_hex in enumerate(palette)
    }

    pixels: list[list[int]] = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            color = rgba.getpixel((x, y))
            row.append(index_by_color[color])
        pixels.append(row)

    return {
        "width": width,
        "height": height,
        "palette": palette,
        "pixels": pixels,
    }

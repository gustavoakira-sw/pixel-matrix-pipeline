from __future__ import annotations

import copy
import re

_HEX_RGBA_RE = re.compile(r"^#[0-9A-Fa-f]{8}$")


def _validate_hex_rgba(color: str) -> None:
    if not _HEX_RGBA_RE.fullmatch(color):
        raise ValueError(f"Invalid color format: {color}. Expected #RRGGBBAA")


def _validated_matrix_data(matrix_data: dict) -> tuple[int, int, list[str], list[list[int]]]:
    if not isinstance(matrix_data, dict):
        raise ValueError("matrix_data must be a dict")

    required = ("width", "height", "palette", "pixels")
    for key in required:
        if key not in matrix_data:
            raise ValueError(f"matrix_data is missing required key: {key}")

    width = matrix_data["width"]
    height = matrix_data["height"]
    palette = matrix_data["palette"]
    pixels = matrix_data["pixels"]

    if not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive int")
    if not isinstance(height, int) or height <= 0:
        raise ValueError("height must be a positive int")
    if not isinstance(palette, list) or not palette:
        raise ValueError("palette must be a non-empty list")
    if not isinstance(pixels, list) or not pixels:
        raise ValueError("pixels must be a non-empty 2D list")
    if len(pixels) != height:
        raise ValueError("pixels row count must match height")

    for color in palette:
        if not isinstance(color, str):
            raise ValueError("palette colors must be strings")
        _validate_hex_rgba(color)

    for row in pixels:
        if not isinstance(row, list):
            raise ValueError("pixels must be a 2D list")
        if len(row) != width:
            raise ValueError("all pixel rows must have length width")
        for idx in row:
            if not isinstance(idx, int):
                raise ValueError("pixel indices must be ints")
            if idx < 0 or idx >= len(palette):
                raise ValueError(f"pixel index out of palette range: {idx}")

    return width, height, list(palette), [list(row) for row in pixels]


def normalize_palette(matrix_data: dict) -> dict:
    """Remove unused palette entries and remap pixel indices deterministically."""
    width, height, palette, pixels = _validated_matrix_data(matrix_data)

    used_set = {idx for row in pixels for idx in row}
    used_indices = [idx for idx in range(len(palette)) if idx in used_set]

    old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(used_indices)}
    new_palette = [palette[idx] for idx in used_indices]
    new_pixels = [[old_to_new[idx] for idx in row] for row in pixels]

    return {
        "width": width,
        "height": height,
        "palette": new_palette,
        "pixels": new_pixels,
    }


def swap_palette(matrix_data: dict, color_map: dict[str, str]) -> dict:
    """Replace palette colors by exact hex key match and preserve pixel indices."""
    width, height, palette, pixels = _validated_matrix_data(matrix_data)

    if not isinstance(color_map, dict):
        raise ValueError("color_map must be a dict")

    for source, target in color_map.items():
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("color_map keys/values must be strings")
        _validate_hex_rgba(source)
        _validate_hex_rgba(target)

    new_palette = [color_map.get(color, color) for color in palette]

    return {
        "width": width,
        "height": height,
        "palette": new_palette,
        "pixels": copy.deepcopy(pixels),
    }


def matrix_palette_stats(matrix_data: dict) -> dict:
    """Return palette usage stats for matrix data."""
    _width, _height, palette, pixels = _validated_matrix_data(matrix_data)

    used = {idx for row in pixels for idx in row}
    transparent_present = any(color.lower().endswith("00") for color in palette)

    return {
        "total_palette_colors": len(palette),
        "used_colors": len(used),
        "unused_colors": len(palette) - len(used),
        "transparent_color_present": transparent_present,
    }

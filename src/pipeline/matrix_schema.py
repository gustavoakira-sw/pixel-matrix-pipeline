from __future__ import annotations

import json
import re
from typing import Any

HEX_RGBA_RE = re.compile(r"^#[0-9A-Fa-f]{8}$")


def parse_model_json(text: str) -> dict[str, Any]:
    """Parse model output text as JSON, accepting optional fenced blocks."""
    value = (text or "").strip()
    if not value:
        raise ValueError("Model output is empty")

    if value.startswith("```"):
        value = value.strip("`").strip()
        if value.startswith("json"):
            value = value[4:].strip()

    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        # Fallback: extract first JSON object if model added prose around it.
        start = value.find("{")
        end = value.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Model output is not valid JSON: {exc}") from exc
        candidate = value[start : end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc2:
            raise ValueError(f"Model output is not valid JSON: {exc2}") from exc2

    if not isinstance(data, dict):
        raise ValueError("Model output JSON must be an object")

    return data


def validate_sprite_matrix(
    matrix_data: dict[str, Any],
    *,
    expected_width: int | None = None,
    expected_height: int | None = None,
    expected_palette: list[str] | None = None,
) -> None:
    """Validate ai-game-pipeline sprite matrix schema and optional constraints."""
    required = ("width", "height", "palette", "pixels")
    for key in required:
        if key not in matrix_data:
            raise ValueError(f"Missing required key: {key}")

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
    if not isinstance(pixels, list) or len(pixels) != height:
        raise ValueError("pixels must be a list with length == height")

    if expected_width is not None and width != expected_width:
        raise ValueError(f"width mismatch: expected {expected_width}, got {width}")
    if expected_height is not None and height != expected_height:
        raise ValueError(f"height mismatch: expected {expected_height}, got {height}")
    if expected_palette is not None and palette != expected_palette:
        raise ValueError("palette mismatch: model must return identical palette")

    for color in palette:
        if not isinstance(color, str) or not HEX_RGBA_RE.fullmatch(color):
            raise ValueError(f"Invalid palette color: {color}. Expected #RRGGBBAA")

    for row in pixels:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("Each pixel row must be a list with length == width")
        for value in row:
            if not isinstance(value, int):
                raise ValueError("Pixel values must be integers")
            if value < 0 or value >= len(palette):
                raise ValueError(f"Pixel palette index out of range: {value}")

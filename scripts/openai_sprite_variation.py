#!/usr/bin/env python3
"""
Generate sprite variations from matrix JSON using OpenAI.

What this script does:
1) Loads an input matrix JSON in the ai-game-pipeline schema.
2) Prompts an OpenAI model to generate a similar (non-identical) variation.
3) Validates the returned JSON shape, indices, and dimensions.
4) Retries generation when validation fails (up to --max-attempts).
5) Renders the final JSON to PNG via `python -m src.tools.matrix_to_sprite`.

Requirements:
- `OPENAI_API_KEY` must be set in the environment.
- Input JSON must include: width, height, palette, pixels.
- Pixel indices must remain valid for the returned palette.

Basic usage:
        python scripts/openai_sprite_variation.py \
            --input-json output/tile_000.json \
            --output-json output/tile_000_variant.json \
            --output-png output/tile_000_variant.png

Targeted edit usage (allow palette changes):
        python scripts/openai_sprite_variation.py \
            --input-json output/extracted/tile_0020.json \
            --output-json output/extracted/tile_0020_blue_green_variant.json \
            --output-png output/extracted/tile_0020_blue_green_variant.png \
            --instruction "Recreate this tile with a blue box body and green corner accents. Keep shape and pixel-art shading style." \
            --allow-palette-change \
            --max-attempts 5

Tips:
- Use `--max-attempts` > 1 for better reliability.
- Keep `--allow-palette-change` off for minimal drift.
- Turn it on when requesting new hues not present in the original palette.
"""


from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI

HEX_RGBA_RE = re.compile(r"^#[0-9A-Fa-f]{8}$")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_matrix_data(
    matrix_data: dict[str, Any],
    *,
    expected_width: int | None = None,
    expected_height: int | None = None,
    expected_palette: list[str] | None = None,
) -> None:
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


def _build_prompt(reference: dict[str, Any]) -> str:
    return (
        "Generate one sprite variation in JSON only.\\n"
        "Rules:\\n"
        "1) Keep width identical.\\n"
        "2) Keep height identical.\\n"
        "3) Keep palette identical and in the same order.\\n"
        "4) Return only valid JSON with keys: width, height, palette, pixels.\\n"
        "5) pixels must be a 2D array of palette indices.\\n"
        "6) Make it similar but not identical to the input sprite.\\n\\n"
        f"Reference sprite JSON:\\n{json.dumps(reference, separators=(',', ':'))}"
    )


def _build_custom_prompt(
    reference: dict[str, Any],
    instruction: str,
    allow_palette_change: bool,
) -> str:
    width = reference["width"]
    height = reference["height"]
    palette_len = len(reference["palette"])
    palette_rule = (
        "3) Keep palette identical and in the same order."
        if not allow_palette_change
        else "3) Palette can change only if needed to satisfy the instruction."
    )
    return (
        "Generate one sprite variation in JSON only.\n"
        "Rules:\n"
        "1) Keep width identical.\n"
        "2) Keep height identical.\n"
        f"{palette_rule}\n"
        "4) Return only valid JSON with keys: width, height, palette, pixels.\n"
        f"5) width must be exactly {width} and height must be exactly {height}.\n"
        f"6) pixels must contain exactly {height} rows, and each row must contain exactly {width} integers.\n"
        f"7) Every pixel index must be in range [0, len(palette)-1], with len(palette) currently {palette_len}.\n"
        "6) Keep pixel-art style and preserve crisp pixel layout.\n\n"
        f"Requested variation: {instruction}\n\n"
        f"Reference sprite JSON:\n{json.dumps(reference, separators=(',', ':'))}"
    )


def _generate_variation(
    reference: dict[str, Any],
    model: str,
    instruction: str | None,
    allow_palette_change: bool,
    max_attempts: int,
) -> dict[str, Any]:
    client = OpenAI()
    base_prompt = (
        _build_custom_prompt(reference, instruction, allow_palette_change)
        if instruction
        else _build_prompt(reference)
    )

    last_error: ValueError | None = None
    for attempt in range(1, max_attempts + 1):
        previous_error_note = (
            f"\nPrevious attempt failed validation with: {last_error}. Fix that exactly."
            if last_error is not None
            else ""
        )
        prompt = (
            base_prompt
            + "\n\nHard requirement: output pixels must not be identical to the reference pixels."
            + f"\nThis is attempt {attempt} of {max_attempts}."
            + previous_error_note
        )
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        )

        text = response.output_text.strip()
        if not text:
            last_error = ValueError("OpenAI response did not include text output")
            continue

        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            last_error = ValueError(f"Model output is not valid JSON: {exc}")
            continue

        if not isinstance(data, dict):
            last_error = ValueError("Model output JSON must be an object")
            continue

        try:
            _validate_matrix_data(
                data,
                expected_width=reference["width"],
                expected_height=reference["height"],
                expected_palette=None if allow_palette_change else reference["palette"],
            )
        except ValueError as exc:
            last_error = exc
            continue

        if data["pixels"] == reference["pixels"]:
            last_error = ValueError("Model returned identical pixels; expected a variation")
            continue

        return data

    raise last_error or ValueError("Failed to generate a valid variation")


def _render_png(json_path: Path, png_path: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "src.tools.matrix_to_sprite",
        str(json_path),
        "--output-png",
        str(png_path),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a similar sprite JSON via OpenAI and render PNG")
    parser.add_argument("--input-json", type=Path, required=True, help="Input sprite matrix JSON")
    parser.add_argument("--output-json", type=Path, required=True, help="Output variation JSON")
    parser.add_argument("--output-png", type=Path, required=True, help="Output variation PNG")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model name")
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum generation attempts before failing",
    )
    parser.add_argument(
        "--instruction",
        default=None,
        help="Optional targeted edit instruction for the model",
    )
    parser.add_argument(
        "--allow-palette-change",
        action="store_true",
        help="Allow palette changes when needed by --instruction",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    reference = _load_json(args.input_json)
    if not isinstance(reference, dict):
        raise SystemExit("Input JSON must be an object")

    try:
        _validate_matrix_data(reference)
        variation = _generate_variation(
            reference,
            args.model,
            args.instruction,
            args.allow_palette_change,
            args.max_attempts,
        )
    except ValueError as exc:
        raise SystemExit(f"Validation failed: {exc}") from exc

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(variation, indent=2), encoding="utf-8")

    _render_png(args.output_json, args.output_png)

    print(f"Wrote variation JSON: {args.output_json}")
    print(f"Wrote variation PNG: {args.output_png}")


if __name__ == "__main__":
    main()

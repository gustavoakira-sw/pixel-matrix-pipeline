#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

# Allow running as `python scripts/openai_edit_sprite.py` from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.extractor import sprite_to_matrix
from src.pipeline.importer import load_png
from src.pipeline.matrix_schema import parse_model_json, validate_sprite_matrix
from src.pipeline.renderer import matrix_to_png


def _log(message: str, *, t0: float) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    elapsed = time.perf_counter() - t0
    print(f"[{ts} +{elapsed:0.2f}s] {message}")


def infer_palette_change(instruction: str) -> bool:
    text = instruction.lower()
    triggers = (
        "color",
        "recolor",
        "palette",
        "green",
        "blue",
        "red",
        "orange",
        "purple",
        "pink",
        "yellow",
        "moss",
        "icy",
        "dark",
        "light",
        "shade",
        "style",
        "variant",
    )
    return any(token in text for token in triggers)


def default_output_paths(input_png: Path, output_json: Path | None, output_png: Path | None) -> tuple[Path, Path]:
    base = Path("output") / "edited"
    stem = input_png.stem
    final_json = output_json or (base / f"{stem}_variant.json")
    final_png = output_png or (base / f"{stem}_variant.png")
    return final_json, final_png


def build_prompt(reference: dict[str, Any], instruction: str, allow_palette_change: bool) -> str:
    palette_rule = (
        "Palette can change only if needed by the instruction."
        if allow_palette_change
        else "Palette must remain identical and in the same order."
    )
    width = reference["width"]
    height = reference["height"]
    return (
        "Edit this sprite matrix and return JSON only.\n"
        "Rules:\n"
        f"1) width must stay {width}.\n"
        f"2) height must stay {height}.\n"
        f"3) {palette_rule}\n"
        "4) Preserve pixel-art style and crisp pixel layout.\n"
        "5) Return only valid JSON with keys: width, height, palette, pixels.\n"
        f"6) pixels must be a 2D array with exactly {height} rows and exactly {width} columns per row.\n"
        "7) all pixel values must be palette indices in range.\n"
        "8) Return JSON only. No markdown, no explanations.\n\n"
        f"Instruction: {instruction}\n\n"
        f"Reference JSON:\n{json.dumps(reference, separators=(',', ':'))}"
    )


def _normalize_model_matrix(data: dict[str, Any], *, expected_width: int, expected_height: int) -> dict[str, Any]:
    """Normalize common model output shapes into the SpriteMatrix contract."""
    candidate: dict[str, Any] = data

    # Some responses wrap the matrix under an extra object key.
    for key in ("matrix", "sprite", "result", "data"):
        value = candidate.get(key)
        if isinstance(value, dict) and all(k in value for k in ("width", "height", "palette", "pixels")):
            candidate = value
            break

    pixels = candidate.get("pixels")
    if not isinstance(pixels, list):
        return candidate

    # Recover from flat arrays by reshaping into rows.
    if pixels and all(isinstance(x, int) for x in pixels):
        expected_len = expected_width * expected_height
        if len(pixels) == expected_len:
            rows = [pixels[i : i + expected_width] for i in range(0, expected_len, expected_width)]
            candidate = dict(candidate)
            candidate["pixels"] = rows

    # Recover from rows emitted as whitespace/comma-separated strings.
    if pixels and all(isinstance(x, str) for x in pixels):
        parsed_rows: list[list[int]] = []
        for row in pixels:
            tokens = [t for t in row.replace(",", " ").split() if t]
            try:
                parsed_rows.append([int(t) for t in tokens])
            except ValueError:
                return candidate
        candidate = dict(candidate)
        candidate["pixels"] = parsed_rows

    # Final coercion path: flatten mixed row formats and force exact expected grid size.
    pixels = candidate.get("pixels")
    if not isinstance(pixels, list):
        return candidate

    flat: list[int] = []

    def _append_scalar(value: Any) -> bool:
        if isinstance(value, int):
            flat.append(value)
            return True
        if isinstance(value, str):
            token = value.strip()
            if token.isdigit() or (token.startswith("-") and token[1:].isdigit()):
                flat.append(int(token))
                return True
            return False
        return False

    for row in pixels:
        if isinstance(row, list):
            for value in row:
                if not _append_scalar(value):
                    return candidate
            continue
        if isinstance(row, str):
            tokens = [t for t in row.replace(",", " ").split() if t]
            try:
                flat.extend(int(t) for t in tokens)
            except ValueError:
                return candidate
            continue
        if not _append_scalar(row):
            return candidate

    if not flat:
        return candidate

    expected_len = expected_width * expected_height
    if len(flat) < expected_len:
        flat.extend([0] * (expected_len - len(flat)))
    elif len(flat) > expected_len:
        flat = flat[:expected_len]

    palette = candidate.get("palette")
    if isinstance(palette, list) and len(palette) > 0:
        max_idx = len(palette) - 1
        flat = [min(max(v, 0), max_idx) for v in flat]

    rows = [flat[i : i + expected_width] for i in range(0, expected_len, expected_width)]
    candidate = dict(candidate)
    candidate["width"] = expected_width
    candidate["height"] = expected_height
    candidate["pixels"] = rows

    return candidate


def request_edited_matrix(
    reference: dict[str, Any],
    instruction: str,
    model: str,
    max_attempts: int,
    allow_palette_change: bool,
    *,
    t0: float,
) -> dict[str, Any]:
    client = OpenAI()
    base_prompt = build_prompt(reference, instruction, allow_palette_change)

    last_error: ValueError | None = None
    for attempt in range(1, max_attempts + 1):
        feedback = (
            f"\nPrevious attempt failed: {last_error}. Fix exactly that."
            if last_error is not None
            else ""
        )
        prompt = f"{base_prompt}\n\nAttempt {attempt}/{max_attempts}.{feedback}"
        _log(f"OpenAI request start (attempt {attempt}/{max_attempts})", t0=t0)
        req_start = time.perf_counter()
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        )
        req_elapsed = time.perf_counter() - req_start
        _log(f"OpenAI request end (attempt {attempt}/{max_attempts}, {req_elapsed:0.2f}s)", t0=t0)

        try:
            data = parse_model_json(response.output_text)
            data = _normalize_model_matrix(
                data,
                expected_width=reference["width"],
                expected_height=reference["height"],
            )
            validate_sprite_matrix(
                data,
                expected_width=reference["width"],
                expected_height=reference["height"],
                expected_palette=None if allow_palette_change else reference["palette"],
            )
        except ValueError as exc:
            last_error = exc
            _log(f"Validation failed on attempt {attempt}: {exc}", t0=t0)
            continue

        _log(f"Validation passed on attempt {attempt}", t0=t0)
        return data

    raise last_error or ValueError("Failed to generate valid edited sprite JSON")


def open_file(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
        return
    if sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", path], check=False)
        return
    if os.name == "nt" and hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    raise RuntimeError("Unsupported platform for auto-open")


def _prompt_if_missing(value: str | None, prompt_text: str) -> str:
    if value:
        return value
    return input(prompt_text).strip()


def main(argv: list[str] | None = None) -> None:
    t0 = time.perf_counter()
    parser = argparse.ArgumentParser(description="Edit a sprite PNG via natural language using OpenAI")
    parser.add_argument("--input-png", type=Path, default=None, help="Path to input PNG sprite")
    parser.add_argument("--instruction", default=None, help="Natural-language sprite edit instruction")
    parser.add_argument("--output-json", type=Path, default=None, help="Output edited matrix JSON")
    parser.add_argument("--output-png", type=Path, default=None, help="Output edited PNG")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model")
    parser.add_argument("--max-attempts", type=int, default=5, help="Maximum retry attempts")
    parser.add_argument("--open", action="store_true", help="Open output PNG after render")
    parser.add_argument("--allow-palette-change", action="store_true", help="Force allow palette changes")
    parser.add_argument("--disallow-palette-change", action="store_true", help="Force disallow palette changes")
    args = parser.parse_args(argv)

    if args.allow_palette_change and args.disallow_palette_change:
        raise SystemExit("Use only one of --allow-palette-change or --disallow-palette-change")
    if args.max_attempts <= 0:
        raise SystemExit("--max-attempts must be > 0")
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    input_png = Path(_prompt_if_missing(str(args.input_png) if args.input_png else None, "Input PNG path: "))
    instruction = _prompt_if_missing(args.instruction, "Instruction: ")
    if not input_png.exists():
        raise SystemExit(f"Input PNG not found: {input_png}")
    if not instruction:
        raise SystemExit("Instruction cannot be empty")

    out_json, out_png = default_output_paths(input_png, args.output_json, args.output_png)

    _log(f"[1/5] Loading PNG: {input_png}", t0=t0)
    image = load_png(input_png)
    reference = sprite_to_matrix(image)
    validate_sprite_matrix(reference)

    if args.allow_palette_change:
        allow_palette_change = True
    elif args.disallow_palette_change:
        allow_palette_change = False
    else:
        allow_palette_change = infer_palette_change(instruction)

    _log("[2/5] Requesting edit from OpenAI", t0=t0)
    edited = request_edited_matrix(
        reference,
        instruction,
        args.model,
        args.max_attempts,
        allow_palette_change,
        t0=t0,
    )

    _log(f"[3/5] Writing JSON: {out_json}", t0=t0)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(edited, indent=2), encoding="utf-8")

    _log(f"[4/5] Rendering PNG: {out_png}", t0=t0)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    matrix_to_png(edited["pixels"], edited["palette"]).save(out_png)

    if args.open:
        _log(f"[5/5] Opening PNG: {out_png}", t0=t0)
        open_file(str(out_png))
    else:
        _log("[5/5] Done", t0=t0)


if __name__ == "__main__":
    main()

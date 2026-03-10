#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Allow running as `python scripts/openai_edit_sprite_gui.py` from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import openai_edit_sprite


class DialogCanceled(RuntimeError):
    pass


def _run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip().lower()
        if "user canceled" in stderr:
            raise DialogCanceled("User canceled the dialog")
        raise RuntimeError(f"osascript failed: {(proc.stderr or '').strip()}")
    return proc.stdout.strip()


def choose_input_png() -> Path:
    script = (
        'POSIX path of (choose file with prompt "Select input PNG sprite" '
        'of type {"public.png"})'
    )
    chosen = _run_osascript(script)
    path = Path(chosen)
    if not path.exists():
        raise SystemExit(f"Selected file does not exist: {path}")
    return path


def ask_instruction() -> str:
    script = (
        'text returned of (display dialog "Describe your sprite edit" '
        'default answer "Make it icy blue with subtle highlights")'
    )
    instruction = _run_osascript(script).strip()
    if not instruction:
        raise SystemExit("Instruction cannot be empty")
    return instruction


def ask_palette_mode() -> str:
    script = (
        'button returned of (display dialog "Palette behavior" '
        'buttons {"Disallow", "Auto", "Allow"} default button "Auto")'
    )
    button = _run_osascript(script)
    if button == "Allow":
        return "allow"
    if button == "Disallow":
        return "disallow"
    return "auto"


def ask_max_attempts(default: int = 5) -> int:
    script = (
        'text returned of (display dialog "Max attempts" '
        f'default answer "{default}")'
    )
    raw = _run_osascript(script).strip()
    try:
        attempts = int(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid max attempts: {raw}") from exc
    if attempts <= 0:
        raise SystemExit("Max attempts must be > 0")
    return attempts


def notify(message: str, title: str = "OpenAI Sprite GUI") -> None:
    safe_message = message.replace('"', "'")
    safe_title = title.replace('"', "'")
    _run_osascript(f'display notification "{safe_message}" with title "{safe_title}"')


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("This GUI wrapper requires macOS (osascript)")

    try:
        input_png = choose_input_png()
        instruction = ask_instruction()
        palette_mode = ask_palette_mode()
        max_attempts = ask_max_attempts(default=5)
    except DialogCanceled:
        print("Canceled by user.")
        return

    out_json, out_png = openai_edit_sprite.default_output_paths(input_png, None, None)

    argv = [
        "--input-png",
        str(input_png),
        "--instruction",
        instruction,
        "--output-json",
        str(out_json),
        "--output-png",
        str(out_png),
        "--max-attempts",
        str(max_attempts),
    ]
    if palette_mode == "allow":
        argv.append("--allow-palette-change")
    elif palette_mode == "disallow":
        argv.append("--disallow-palette-change")

    try:
        openai_edit_sprite.main(argv)
        # Open both images for side-by-side comparison.
        openai_edit_sprite.open_file(str(input_png))
        openai_edit_sprite.open_file(str(out_png))
        notify(f"Done: {out_png}")
    except Exception as exc:
        notify(f"Failed: {exc}")
        raise


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from PIL import Image


def load_png(path: str | Path) -> Image.Image:
    """Load a PNG image as RGBA without any resampling or filtering."""
    image = Image.open(path)
    return image.convert("RGBA")

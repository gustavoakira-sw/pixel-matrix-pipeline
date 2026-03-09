from __future__ import annotations

from PIL import Image


def _hex_to_rgba(color: str) -> tuple[int, int, int, int]:
    value = color.strip()
    if value.startswith("#"):
        value = value[1:]

    if len(value) == 6:
        value = f"{value}FF"
    if len(value) != 8:
        raise ValueError(f"Invalid color format: {color}")

    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4, 6))  # type: ignore[return-value]


def matrix_to_png(matrix: list[list[int]], palette: list[str]) -> Image.Image:
    """Render a palette-indexed matrix back into an RGBA Pillow image."""
    if not matrix or not matrix[0]:
        raise ValueError("Matrix cannot be empty")

    height = len(matrix)
    width = len(matrix[0])

    for row in matrix:
        if len(row) != width:
            raise ValueError("All matrix rows must have the same width")

    rgba_palette = [_hex_to_rgba(color) for color in palette]
    image = Image.new("RGBA", (width, height))

    for y, row in enumerate(matrix):
        for x, palette_index in enumerate(row):
            if palette_index < 0 or palette_index >= len(rgba_palette):
                raise ValueError(f"Palette index out of range at ({x}, {y}): {palette_index}")
            image.putpixel((x, y), rgba_palette[palette_index])

    return image

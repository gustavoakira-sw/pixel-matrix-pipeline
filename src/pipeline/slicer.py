from __future__ import annotations

from PIL import Image


def slice_tiles(image: Image.Image, tile_size: int | tuple[int, int]) -> list[Image.Image]:
    """Slice an image into fixed-size tiles in row-major order."""
    if isinstance(tile_size, int):
        tile_w = tile_h = tile_size
    else:
        tile_w, tile_h = tile_size

    if tile_w <= 0 or tile_h <= 0:
        raise ValueError("tile_size must be positive")

    rgba = image.convert("RGBA")
    width, height = rgba.size

    if width % tile_w != 0 or height % tile_h != 0:
        raise ValueError(
            f"Image size {width}x{height} is not divisible by tile size {tile_w}x{tile_h}"
        )

    tiles: list[Image.Image] = []
    for y in range(0, height, tile_h):
        for x in range(0, width, tile_w):
            tile = rgba.crop((x, y, x + tile_w, y + tile_h))
            tiles.append(tile)

    return tiles

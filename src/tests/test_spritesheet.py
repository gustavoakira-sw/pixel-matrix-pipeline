from __future__ import annotations

import math
import unittest
from pathlib import Path

from src.pipeline.importer import load_png
from src.pipeline.slicer import slice_tiles
from src.pipeline.spritesheet import generate_atlas, pack_sprites


class SpritesheetTest(unittest.TestCase):
    def test_build_spritesheet_and_atlas_grid(self) -> None:
        tile_size = 16
        tiles_dir = Path("output/tiles")
        tiles_dir.mkdir(parents=True, exist_ok=True)

        sprite_paths = sorted(str(path) for path in tiles_dir.glob("*.png"))
        if not sprite_paths:
            source = Path("Assets/Tilesheets/Small tiles/Thin outline/tilemap_packed.png")
            self.assertTrue(source.exists(), f"Missing source asset: {source}")

            tiles = slice_tiles(load_png(source), tile_size)
            for index, tile in enumerate(tiles):
                tile.save(tiles_dir / f"tile_{index:03d}.png")
            sprite_paths = sorted(str(path) for path in tiles_dir.glob("*.png"))

        sheet = pack_sprites(sprite_paths, tile_size)
        atlas = generate_atlas(sprite_paths, tile_size)

        count = len(sprite_paths)
        columns = math.ceil(math.sqrt(count))
        rows = math.ceil(count / columns)

        self.assertEqual(sheet.size, (columns * tile_size, rows * tile_size))
        self.assertIn("frames", atlas)
        self.assertEqual(len(atlas["frames"]), count)

        for index in range(count):
            key = f"tile_{index:03d}"
            self.assertIn(key, atlas["frames"])
            expected = {
                "x": (index % columns) * tile_size,
                "y": (index // columns) * tile_size,
                "w": tile_size,
                "h": tile_size,
            }
            self.assertEqual(atlas["frames"][key], expected)


if __name__ == "__main__":
    unittest.main()

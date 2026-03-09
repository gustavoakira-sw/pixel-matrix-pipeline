from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.pipeline.extractor import sprite_to_matrix
from src.pipeline.importer import load_png
from src.pipeline.renderer import matrix_to_png
from src.pipeline.slicer import slice_tiles


class PipelineV001Test(unittest.TestCase):
    def test_tilesheet_roundtrip_is_pixel_perfect(self) -> None:
        tilesheet = Path("Assets/Tilesheets/Small tiles/Thin outline/tilemap_packed.png")
        self.assertTrue(tilesheet.exists(), f"Missing test asset: {tilesheet}")

        image = load_png(tilesheet)
        tiles = slice_tiles(image, 16)
        self.assertGreater(len(tiles), 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            # Validate several tiles to keep test fast while still checking behavior.
            for index, tile in enumerate(tiles[:20]):
                matrix_data = sprite_to_matrix(tile)
                rebuilt = matrix_to_png(matrix_data["pixels"], matrix_data["palette"])

                src_path = out_dir / f"src_{index:03d}.png"
                dst_path = out_dir / f"dst_{index:03d}.png"
                tile.save(src_path)
                rebuilt.save(dst_path)

                original_bytes = src_path.read_bytes()
                rebuilt_bytes = dst_path.read_bytes()
                self.assertEqual(original_bytes, rebuilt_bytes, f"Mismatch on tile {index}")


if __name__ == "__main__":
    unittest.main()

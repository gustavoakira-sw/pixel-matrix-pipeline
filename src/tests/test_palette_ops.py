from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline.palette_ops import matrix_palette_stats, normalize_palette, swap_palette
from src.pipeline.renderer import matrix_to_png


class PaletteOpsTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture = Path("src/tests/fixtures/palette_fixture.json")
        self.assertTrue(fixture.exists(), f"Missing fixture: {fixture}")
        self.matrix_data = json.loads(fixture.read_text(encoding="utf-8"))

    def test_normalize_palette_removes_unused_and_preserves_render(self) -> None:
        normalized = normalize_palette(self.matrix_data)

        self.assertEqual(normalized["palette"], ["#00000000", "#FF0000FF", "#0000FFFF"])
        self.assertEqual(normalized["pixels"], [[1, 2, 1], [0, 2, 0]])

        original_img = matrix_to_png(self.matrix_data["pixels"], self.matrix_data["palette"])
        normalized_img = matrix_to_png(normalized["pixels"], normalized["palette"])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            src_path = tmp / "src.png"
            norm_path = tmp / "norm.png"
            original_img.save(src_path)
            normalized_img.save(norm_path)
            self.assertEqual(src_path.read_bytes(), norm_path.read_bytes())

    def test_swap_palette_changes_only_targeted_colors(self) -> None:
        color_map = {
            "#FF0000FF": "#00FF00FF",
            "#0000FFFF": "#FFFFFFFF",
        }
        swapped = swap_palette(self.matrix_data, color_map)

        self.assertEqual(swapped["pixels"], self.matrix_data["pixels"])
        self.assertEqual(swapped["palette"][0], "#00000000")
        self.assertEqual(swapped["palette"][1], "#00FF00FF")
        self.assertEqual(swapped["palette"][2], "#00FF00FF")
        self.assertEqual(swapped["palette"][3], "#FFFFFFFF")
        self.assertEqual(swapped["palette"][4], "#FFFFFFFF")

        original_img = matrix_to_png(self.matrix_data["pixels"], self.matrix_data["palette"])
        swapped_img = matrix_to_png(swapped["pixels"], swapped["palette"])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            src_path = tmp / "src.png"
            swp_path = tmp / "swp.png"
            original_img.save(src_path)
            swapped_img.save(swp_path)
            self.assertNotEqual(src_path.read_bytes(), swp_path.read_bytes())

    def test_matrix_palette_stats(self) -> None:
        stats = matrix_palette_stats(self.matrix_data)
        self.assertEqual(stats["total_palette_colors"], 5)
        self.assertEqual(stats["used_colors"], 3)
        self.assertEqual(stats["unused_colors"], 2)
        self.assertTrue(stats["transparent_color_present"])


if __name__ == "__main__":
    unittest.main()

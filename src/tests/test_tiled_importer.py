from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.pipeline.importer import decode_tiled_gid, load_tmx, load_tsx, map_tile_ids_to_regions


class TiledImporterTest(unittest.TestCase):
    def test_load_tsx_sample(self) -> None:
        tsx = load_tsx(Path("Assets/Tiled/sample-sheet.tsx"))

        self.assertEqual(tsx["name"], "tilemap_packed")
        self.assertEqual(tsx["tilewidth"], 8)
        self.assertEqual(tsx["tileheight"], 8)
        self.assertEqual(tsx["tilecount"], 150)
        self.assertEqual(tsx["columns"], 15)
        self.assertTrue(tsx["image"]["source"].endswith("Assets/Default/Tilemap/tilemap_packed.png"))

    def test_load_tmx_sample(self) -> None:
        tmx = load_tmx(Path("Assets/Tiled/sample-map.tmx"))

        self.assertEqual(tmx["width"], 40)
        self.assertEqual(tmx["height"], 24)
        self.assertEqual(tmx["tilewidth"], 8)
        self.assertEqual(tmx["tileheight"], 8)
        self.assertEqual(len(tmx["tilesets"]), 1)
        self.assertEqual(tmx["tilesets"][0]["firstgid"], 1)
        self.assertEqual(len(tmx["layers"]), 1)
        self.assertEqual(len(tmx["layers"][0]["gids"]), 40 * 24)

    def test_decode_tiled_gid_flags(self) -> None:
        decoded = decode_tiled_gid(0xE0000000 | 9)
        self.assertEqual(decoded["gid"], 9)
        self.assertTrue(decoded["flip_h"])
        self.assertTrue(decoded["flip_v"])
        self.assertTrue(decoded["flip_d"])

    def test_map_tile_ids_to_regions(self) -> None:
        tsx = load_tsx(Path("Assets/Tiled/sample-sheet.tsx"))
        regions = map_tile_ids_to_regions([1, 15, 16, 0x80000000 | 5, 0], tsx, firstgid=1)

        self.assertEqual(regions[0]["x"], 0)
        self.assertEqual(regions[0]["y"], 0)
        self.assertEqual(regions[1]["x"], 112)
        self.assertEqual(regions[1]["y"], 0)
        self.assertEqual(regions[2]["x"], 0)
        self.assertEqual(regions[2]["y"], 8)
        self.assertTrue(regions[3]["flip_h"])
        self.assertEqual(regions[3]["gid"], 5)
        self.assertTrue(regions[4]["empty"])

    def test_load_tmx_rejects_non_csv_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmx_path = Path(tmpdir) / "bad.tmx"
            tmx_path.write_text(
                """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<map width=\"1\" height=\"1\" tilewidth=\"8\" tileheight=\"8\">
  <layer id=\"1\" name=\"tiles\" width=\"1\" height=\"1\">
    <data encoding=\"base64\">AAAA</data>
  </layer>
</map>
""",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_tmx(tmx_path)

    def test_map_tile_ids_to_regions_rejects_out_of_range_gid(self) -> None:
        tsx = load_tsx(Path("Assets/Tiled/sample-sheet.tsx"))
        with self.assertRaises(ValueError):
            map_tile_ids_to_regions([9999], tsx, firstgid=1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.tools.validate_outputs import _check_atlas_and_spritesheet


class ValidateOutputsContractTest(unittest.TestCase):
    def test_rejects_old_atlas_contract_without_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            tiles_dir = base / "tiles"
            tiles_dir.mkdir(parents=True, exist_ok=True)

            # Fake one tile artifact; validator only checks count and filenames.
            (tiles_dir / "tile_000.png").write_bytes(b"x")

            Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(base / "sheet.png")

            # Old contract: no meta and flat frame payload.
            atlas = {
                "frames": {
                    "tile_000": {"x": 0, "y": 0, "w": 16, "h": 16}
                }
            }
            atlas_path = base / "atlas.json"
            atlas_path.write_text(json.dumps(atlas), encoding="utf-8")

            with self.assertRaises(ValueError):
                _check_atlas_and_spritesheet(tiles_dir, atlas_path, base / "sheet.png", 16)


if __name__ == "__main__":
    unittest.main()

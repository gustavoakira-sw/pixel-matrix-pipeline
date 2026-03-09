from __future__ import annotations

import unittest

from src.pipeline.matrix_schema import parse_model_json, validate_sprite_matrix


class MatrixSchemaTest(unittest.TestCase):
    def test_parse_model_json_accepts_fenced_json(self) -> None:
        data = parse_model_json("```json\n{\"width\":1,\"height\":1,\"palette\":[\"#00000000\"],\"pixels\":[[0]]}\n```")
        self.assertEqual(data["width"], 1)

    def test_validate_sprite_matrix_happy_path(self) -> None:
        data = {
            "width": 2,
            "height": 2,
            "palette": ["#00000000", "#FFFFFFFF"],
            "pixels": [[0, 1], [1, 0]],
        }
        validate_sprite_matrix(data, expected_width=2, expected_height=2)

    def test_validate_sprite_matrix_rejects_bad_palette_color(self) -> None:
        data = {
            "width": 1,
            "height": 1,
            "palette": ["#ZZZZZZZZ"],
            "pixels": [[0]],
        }
        with self.assertRaises(ValueError):
            validate_sprite_matrix(data)

    def test_parse_model_json_extracts_object_from_wrapped_text(self) -> None:
        wrapped = "Here is your JSON: {\"width\":1,\"height\":1,\"palette\":[\"#00000000\"],\"pixels\":[[0]]}"
        data = parse_model_json(wrapped)
        self.assertEqual(data["height"], 1)


if __name__ == "__main__":
    unittest.main()

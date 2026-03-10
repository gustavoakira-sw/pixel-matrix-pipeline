from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from scripts import openai_edit_sprite


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.output_text = text


class _FakeResponsesClient:
    def __init__(self, texts: list[str]) -> None:
        self._texts = texts
        self.calls = 0

    def create(self, **_kwargs):  # type: ignore[no-untyped-def]
        text = self._texts[min(self.calls, len(self._texts) - 1)]
        self.calls += 1
        return _FakeResponse(text)


class _FakeOpenAI:
    def __init__(self, texts: list[str]) -> None:
        self.responses = _FakeResponsesClient(texts)


class OpenAIEditSpriteTest(unittest.TestCase):
    def test_infer_palette_change(self) -> None:
        self.assertTrue(openai_edit_sprite.infer_palette_change("make it icy blue"))
        self.assertFalse(openai_edit_sprite.infer_palette_change("same sprite geometry"))

    def test_request_retries_until_valid(self) -> None:
        reference = {
            "width": 1,
            "height": 1,
            "palette": ["#00000000"],
            "pixels": [[0]],
        }
        bad = "{\"width\":1,\"height\":2,\"palette\":[\"#00000000\"],\"pixels\":[[0],[0]]}"
        good = "{\"width\":1,\"height\":1,\"palette\":[\"#00000000\"],\"pixels\":[[0]]}"

        with patch.object(openai_edit_sprite, "OpenAI", lambda: _FakeOpenAI([bad, good])):
            result = openai_edit_sprite.request_edited_matrix(
                reference,
                "keep it",
                "gpt-4.1-mini",
                2,
                False,
                t0=0.0,
            )
        self.assertEqual(result["width"], 1)

    def test_request_accepts_flat_pixel_array(self) -> None:
        reference = {
            "width": 2,
            "height": 2,
            "palette": ["#00000000", "#FFFFFFFF"],
            "pixels": [[0, 0], [0, 0]],
        }
        flattened = "{\"width\":2,\"height\":2,\"palette\":[\"#00000000\",\"#FFFFFFFF\"],\"pixels\":[0,1,1,0]}"

        with patch.object(openai_edit_sprite, "OpenAI", lambda: _FakeOpenAI([flattened])):
            result = openai_edit_sprite.request_edited_matrix(
                reference,
                "make a cross",
                "gpt-4.1-mini",
                1,
                False,
                t0=0.0,
            )
        self.assertEqual(result["pixels"], [[0, 1], [1, 0]])

    def test_request_accepts_wrapped_matrix_object(self) -> None:
        reference = {
            "width": 1,
            "height": 1,
            "palette": ["#00000000", "#FFFFFFFF"],
            "pixels": [[0]],
        }
        wrapped = "{\"result\":{\"width\":1,\"height\":1,\"palette\":[\"#00000000\",\"#FFFFFFFF\"],\"pixels\":[[1]]}}"

        with patch.object(openai_edit_sprite, "OpenAI", lambda: _FakeOpenAI([wrapped])):
            result = openai_edit_sprite.request_edited_matrix(
                reference,
                "brighten",
                "gpt-4.1-mini",
                1,
                False,
                t0=0.0,
            )
        self.assertEqual(result["pixels"], [[1]])

    def test_request_repairs_wrong_height_and_pixel_shape(self) -> None:
        reference = {
            "width": 2,
            "height": 2,
            "palette": ["#00000000", "#FFFFFFFF"],
            "pixels": [[0, 0], [0, 0]],
        }
        malformed = (
            "{\"width\":2,\"height\":4,\"palette\":[\"#00000000\",\"#FFFFFFFF\"],"
            "\"pixels\":[\"0, 1\",\"1, 0\"]}"
        )

        with patch.object(openai_edit_sprite, "OpenAI", lambda: _FakeOpenAI([malformed])):
            result = openai_edit_sprite.request_edited_matrix(
                reference,
                "adjust it",
                "gpt-4.1-mini",
                1,
                False,
                t0=0.0,
            )

        self.assertEqual(result["width"], 2)
        self.assertEqual(result["height"], 2)
        self.assertEqual(result["pixels"], [[0, 1], [1, 0]])

    def test_main_happy_path_with_explicit_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            inp = base / "in.png"
            out_json = base / "out.json"
            out_png = base / "out.png"
            Image.new("RGBA", (2, 2), (0, 0, 0, 0)).save(inp)

            edited = {
                "width": 2,
                "height": 2,
                "palette": ["#00000000", "#FFFFFFFF"],
                "pixels": [[0, 1], [1, 0]],
            }

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
                openai_edit_sprite,
                "OpenAI",
                lambda: _FakeOpenAI([json.dumps(edited)]),
            ):
                openai_edit_sprite.main(
                    [
                        "--input-png",
                        str(inp),
                        "--instruction",
                        "make it icy blue",
                        "--output-json",
                        str(out_json),
                        "--output-png",
                        str(out_png),
                        "--max-attempts",
                        "1",
                    ]
                )

            self.assertTrue(out_json.exists())
            self.assertTrue(out_png.exists())

    def test_main_interactive_fallback_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            inp = base / "interactive.png"
            out_json = base / "interactive_out.json"
            out_png = base / "interactive_out.png"
            Image.new("RGBA", (2, 2), (0, 0, 0, 0)).save(inp)

            edited = {
                "width": 2,
                "height": 2,
                "palette": ["#00000000", "#FFFFFFFF"],
                "pixels": [[0, 1], [1, 0]],
            }

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
                openai_edit_sprite,
                "OpenAI",
                lambda: _FakeOpenAI([json.dumps(edited)]),
            ), patch("builtins.input", side_effect=[str(inp), "make it green"]):
                openai_edit_sprite.main(
                    [
                        "--output-json",
                        str(out_json),
                        "--output-png",
                        str(out_png),
                        "--max-attempts",
                        "1",
                    ]
                )

            self.assertTrue(out_json.exists())
            self.assertTrue(out_png.exists())


if __name__ == "__main__":
    unittest.main()

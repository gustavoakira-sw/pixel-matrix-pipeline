# ai-game-pipeline

Deterministic pixel-art pipeline for browser game assets.

## v0.0.1

Implemented:
- PNG loading (`load_png`)
- palette extraction (`extract_palette`)
- sprite to matrix (`sprite_to_matrix`)
- matrix to PNG (`matrix_to_png`)
- fixed-size tile slicing (`slice_tiles`)

Data format:

```json
{
  "width": 16,
  "height": 16,
  "palette": ["#RRGGBBAA"],
  "pixels": [[0, 1, 2]]
}
```

## Project Layout

- `Assets/`: all base art and source assets
- `src/pipeline/`: core modules
- `src/tools/`: CLI entry points
- `src/tests/`: test suite

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI Usage

Run from project root:

```bash
python -m src.tools.extract_tiles "Assets/Tilesheets/Small tiles/Thin outline/tilemap_packed.png" 16 --output-dir output/tiles
python -m src.tools.sprite_to_matrix output/tiles/tile_000.png --output-json output/tile_000.json
python -m src.tools.matrix_to_sprite output/tile_000.json --output-png output/tile_000_rebuilt.png
```

## Test

```bash
python -m unittest discover -s src/tests -v
```

# AI Game Pipeline PRD

## 1. Project

**Name:** `ai-game-pipeline`

Python toolchain for AI-generated 2D pixel game assets for browser engines.

**Target runtimes**
- Phaser.js
- PixiJS
- HTML5 Canvas

**Primary outputs**
- PNG sprites and spritesheets
- JSON metadata (matrix format now, atlas later)
- JS-compatible assets

## 2. Core Objective

Provide deterministic, pixel-perfect operations for:
- importing pixel-art assets
- extracting exact palette and pixel-index matrices
- slicing tiles from spritesheets
- converting sprite PNG <-> SpriteMatrix JSON

No interpolation and no unwanted palette modifications are allowed.

## 3. Current Repository Structure (Updated)

```text
ai-game-pipeline/
├── Assets/
│   ├── Default/
│   ├── Tiled/
│   ├── Tilemap/
│   ├── Tiles/
│   ├── Tilesheets/
│   ├── Transparent/
│   ├── zips/
│   ├── Preview.png
│   ├── Sample.png
│   ├── Tilesheet.txt
│   └── License.txt
├── src/
│   ├── PRD.md
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── importer.py
│   │   ├── extractor.py
│   │   ├── renderer.py
│   │   └── slicer.py
│   ├── tools/
│   │   ├── extract_tiles.py
│   │   ├── sprite_to_matrix.py
│   │   └── matrix_to_sprite.py
│   └── tests/
│       └── test_v001_pipeline.py
└── requirements.txt
```

## 4. Core Data Format

### SpriteMatrix (internal, JSON-serializable)

```json
{
  "width": 16,
  "height": 16,
  "palette": ["#00000000", "#2D2D2D", "#FFCC66", "#FFFFFFFF"],
  "pixels": [
    [0, 0, 1, 1, 0],
    [0, 1, 2, 2, 1],
    [1, 2, 3, 3, 2]
  ]
}
```

**Properties**
- palette-indexed
- lossless for RGBA source
- deterministic
- LLM-friendly

Palette colors use `#RRGGBBAA`.

## 5. v0.0.1 Implemented Modules

### `src/pipeline/importer.py`
- `load_png(path)`
  - loads image with Pillow
  - converts to `RGBA`

### `src/pipeline/extractor.py`
- `extract_palette(image)`
  - deterministic first-seen color order
  - returns list of `#RRGGBBAA`
- `sprite_to_matrix(image)`
  - returns `{width, height, palette, pixels}`

### `src/pipeline/renderer.py`
- `matrix_to_png(matrix, palette)`
  - renders palette-indexed matrix to RGBA image
  - validates matrix shape and palette index bounds

### `src/pipeline/slicer.py`
- `slice_tiles(image, tile_size)`
  - slices row-major tiles
  - validates divisibility and positive tile size

## 6. CLI Tools (v0.0.1)

Use module execution from project root:

```bash
python -m src.tools.extract_tiles <tilesheet.png> 16 --output-dir output/tiles
python -m src.tools.sprite_to_matrix <tile.png> --output-json output/tile.json
python -m src.tools.matrix_to_sprite <tile.json> --output-png output/tile.png
```

## 7. Determinism Rules

The pipeline must never:
- interpolate pixels
- apply smoothing
- alter palette unless explicitly requested

The pipeline always uses exact RGBA values and nearest-neighbor-safe behavior.

## 8. Test Status and Findings

### Implemented first test
- File: `src/tests/test_v001_pipeline.py`
- Flow:
  1. Load tilesheet PNG
  2. Slice into `16x16` tiles
  3. Convert each tile to SpriteMatrix
  4. Render each matrix back to PNG
  5. Compare original and rebuilt PNG bytes

### Verified passing dataset
- `Assets/Tilesheets/Small tiles/Thin outline/tilemap_packed.png`
  - dimensions: `368x112`
  - divisible by `16x16`

### Important finding
- `Assets/Default/Tilemap/tilemap.png` is not divisible by `16x16` (`134x89`) and is unsuitable for strict fixed-grid slicing tests.

## 9. v0.0.1 Scope Summary

Implemented in v0.0.1:
1. PNG loading
2. Tile slicing
3. Sprite -> matrix conversion
4. Matrix -> sprite conversion
5. Palette extraction

Deferred for later versions:
- tileset/tmx/tsx loaders
- atlas packing and export
- spritesheet builder
- matrix preview rendering utilities

## 10. Success Criteria (Current)

The v0.0.1 pipeline is considered correct when it can:
- import a real tilesheet from `Assets/`
- slice tiles deterministically
- convert tiles to SpriteMatrix
- rebuild tiles pixel-perfect

Current status: **achieved with automated test pass**.
Output:

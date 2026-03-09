# AI Game Pipeline PRD

## 1. Project

**Name:** `pixel-matrix-pipeline`

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

## 3. Current Repository Structure (Actual)

```text
pixel-matrix-pipeline/
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
│   │   ├── slicer.py
│   │   ├── spritesheet.py
│   │   └── palette_ops.py
│   ├── tools/
│   │   ├── extract_tiles.py
│   │   ├── sprite_to_matrix.py
│   │   ├── matrix_to_sprite.py
│   │   ├── build_spritesheet.py
│   │   ├── normalize_palette.py
│   │   ├── swap_palette.py
│   │   └── validate_outputs.py
│   └── tests/
│       ├── test_v001_pipeline.py
│       ├── test_spritesheet.py
│       └── test_palette_ops.py
├── scripts/
│   └── openai_sprite_variation.py
├── samples/
│   └── blue_green_variation_demo/
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

## 5. Implemented Capabilities By Version

### v0.0.1

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

### v0.0.2

### `src/pipeline/spritesheet.py`
- `pack_sprites(sprite_paths, tile_size)`
  - deterministic grid packing
  - stable path ordering
- `generate_atlas(sprite_paths, tile_size)`
  - deterministic frame coordinates for atlas JSON

### `src/tools/build_spritesheet.py`
- builds spritesheet PNG + atlas JSON from an input tile folder

### v0.0.3 / v0.0.4

### `src/pipeline/palette_ops.py`
- `normalize_palette(matrix_data)`
- `swap_palette(matrix_data, color_map)`
- `matrix_palette_stats(matrix_data)`

### `src/tools/normalize_palette.py`
- normalizes palette and writes JSON

### `src/tools/swap_palette.py`
- palette remap with optional PNG render

### `src/tools/validate_outputs.py`
- checks roundtrip byte identity
- checks atlas/grid and spritesheet dimensions

### v0.0.5 (experimental)

### `scripts/openai_sprite_variation.py`
- OpenAI-based matrix variation generation
- strict schema validation + retries
- PNG rendering through existing pipeline

## 6. CLI Tools (Current)

Use module execution from project root:

```bash
python -m src.tools.extract_tiles <tilesheet.png> 16 --output-dir output/tiles
python -m src.tools.sprite_to_matrix <tile.png> --output-json output/tile.json
python -m src.tools.matrix_to_sprite <tile.json> --output-png output/tile.png
python -m src.tools.build_spritesheet <input_tiles_dir> --tile-size 16 --output-image output/spritesheet.png --output-atlas output/atlas.json
python -m src.tools.normalize_palette <input.json> --output-json <normalized.json>
python -m src.tools.swap_palette <input.json> --map '#AABBCCDD=#11223344' --output-json <swapped.json> --output-png <swapped.png>
python -m src.tools.validate_outputs
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

### Additional tests in place
- `src/tests/test_spritesheet.py`: validates deterministic grid packing + atlas coordinates
- `src/tests/test_palette_ops.py`: validates normalize/swap/stats and rendering invariants

## 9. Scope Summary (Current)

Implemented:
1. PNG loading
2. Tile slicing
3. Sprite -> matrix conversion
4. Matrix -> sprite conversion
5. Palette extraction
6. Deterministic spritesheet packing + atlas generation
7. Palette normalization/swap/statistics
8. Output validation script
9. Experimental OpenAI variation workflow

Deferred for later versions:
- tileset/tmx/tsx loaders
- richer atlas compatibility metadata for target engines
- matrix preview rendering utilities
- CI automation and expanded fixture coverage

## 10. Success Criteria (Current)

The v0.0.1 pipeline is considered correct when it can:
- import a real tilesheet from `Assets/`
- slice tiles deterministically
- convert tiles to SpriteMatrix
- rebuild tiles pixel-perfect

Current status: **achieved with automated test pass**.

## 11. Next Milestone Objectives (v0.0.6+)

1. Implement TMX/TSX importers (`load_tmx`, `load_tsx`) and extraction helpers.
2. Formalize atlas JSON compatibility contract for Phaser/Pixi usage.
3. Expand validation checks for palette invariants and strict artifact contracts.
4. Add CI-level test execution for regression prevention.
5. Keep AI variation path explicitly experimental and optional.

## 12. Implementation To-Do (Actionable)

### Phase 1: Contracts and import expansion
- [ ] Define final atlas schema and naming rules for engine compatibility.
- [ ] Implement TMX loader path in importer module.
- [ ] Implement TSX loader path in importer module.
- [ ] Add tile-region extraction from TMX/TSX metadata.

### Phase 2: Validation hardening
- [ ] Add strict mode to `validate_outputs` for required artifacts.
- [ ] Add palette invariant checks after normalize/swap.
- [ ] Add atlas naming and ordering checks.

### Phase 3: Tests and reliability
- [ ] Add malformed JSON and index-bound fixture tests.
- [ ] Add TMX/TSX parsing tests (happy path and failure cases).
- [ ] Add deterministic regression fixtures for atlas generation.

### Phase 4: Experimental AI hardening
- [ ] Add non-network unit tests for OpenAI script validation helpers.
- [ ] Add optional changed-pixel threshold guard for targeted edits.
- [ ] Add optional mask-based allowed-change constraints.

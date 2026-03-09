# Blue/Green Variation Demo

This sample demonstrates the matrix workflow using a visible style change.

Files:
- `original_tile_0020.png`: original sprite copied from `Assets/`.
- `original_tile_0020.json`: matrix extracted from the original PNG.
- `blue_green_variant.json`: OpenAI-generated variant matrix (blue body + green corners).
- `blue_green_variant_rerendered.png`: PNG re-rendered from `blue_green_variant.json` using pipeline tools.

Quick validation:
```bash
python -m src.tools.matrix_to_sprite samples/blue_green_variation_demo/blue_green_variant.json --output-png samples/blue_green_variation_demo/check.png
cmp -s samples/blue_green_variation_demo/check.png samples/blue_green_variation_demo/blue_green_variant_rerendered.png && echo "identical"
```

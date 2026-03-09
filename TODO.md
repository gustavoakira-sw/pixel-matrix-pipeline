# Implementation TODO

This checklist starts the next implementation cycle toward engine-ready asset export.

## Phase 1: Contracts and import expansion
- [ ] Define final atlas JSON contract for Phaser/Pixi compatibility.
- [ ] Implement `load_tmx()` in importer path.
- [ ] Implement `load_tsx()` in importer path.
- [ ] Add extraction helper mapping tile IDs to source regions.

## Phase 2: Validation hardening
- [ ] Add strict mode to `python -m src.tools.validate_outputs`.
- [ ] Validate palette invariants after normalize/swap.
- [ ] Validate atlas naming, ordering, and frame completeness.

## Phase 3: Tests and reliability
- [ ] Add fixtures for malformed SpriteMatrix JSON.
- [ ] Add TMX/TSX tests for happy/failure paths.
- [ ] Add deterministic atlas regression tests.
- [ ] Add CI command: `python -m unittest discover -s src/tests -v`.

## Phase 4: AI variation guardrails (experimental)
- [ ] Add non-network tests for OpenAI script validation paths.
- [ ] Add optional changed-pixel threshold checks.
- [ ] Add optional edit-mask enforcement for targeted transformations.

## Phase 5: Documentation sync
- [ ] Keep `src/PRD.md` and `README.md` in lockstep per release.
- [ ] Add a spritesheet-plus-atlas sample alongside blue/green variation demo.
- [ ] Keep external asset attribution updated.

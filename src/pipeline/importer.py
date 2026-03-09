from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

from PIL import Image


_FLIP_H = 0x80000000
_FLIP_V = 0x40000000
_FLIP_D = 0x20000000
_GID_MASK = ~(_FLIP_H | _FLIP_V | _FLIP_D)


def load_png(path: str | Path) -> Image.Image:
    """Load a PNG image as RGBA without any resampling or filtering."""
    image = Image.open(path)
    return image.convert("RGBA")


def _resolve_relative(path: Path, relative: str) -> Path:
    return (path.parent / relative).resolve()


def _parse_csv_gid_data(csv_text: str, width: int, height: int) -> list[int]:
    values = [chunk.strip() for chunk in csv_text.replace("\n", "").split(",") if chunk.strip()]
    gids = [int(value) for value in values]
    expected = width * height
    if len(gids) != expected:
        raise ValueError(f"Layer gid count mismatch: expected {expected}, got {len(gids)}")
    return gids


def load_tsx(path: str | Path) -> dict[str, Any]:
    """Load and parse a TSX tileset file into a deterministic dictionary."""
    tsx_path = Path(path)
    if not tsx_path.exists():
        raise FileNotFoundError(f"TSX not found: {tsx_path}")

    root = ET.parse(tsx_path).getroot()
    if root.tag != "tileset":
        raise ValueError(f"Invalid TSX root tag: {root.tag}")

    image = root.find("image")
    if image is None:
        raise ValueError("TSX is missing <image> element")

    image_source = image.attrib.get("source")
    if not image_source:
        raise ValueError("TSX image source is missing")

    return {
        "path": str(tsx_path.resolve()),
        "name": root.attrib.get("name", ""),
        "tilewidth": int(root.attrib["tilewidth"]),
        "tileheight": int(root.attrib["tileheight"]),
        "tilecount": int(root.attrib.get("tilecount", "0")),
        "columns": int(root.attrib.get("columns", "0")),
        "image": {
            "source": str(_resolve_relative(tsx_path, image_source)),
            "width": int(image.attrib["width"]),
            "height": int(image.attrib["height"]),
        },
    }


def load_tmx(path: str | Path) -> dict[str, Any]:
    """Load and parse a TMX tilemap file into deterministic map data."""
    tmx_path = Path(path)
    if not tmx_path.exists():
        raise FileNotFoundError(f"TMX not found: {tmx_path}")

    root = ET.parse(tmx_path).getroot()
    if root.tag != "map":
        raise ValueError(f"Invalid TMX root tag: {root.tag}")

    map_width = int(root.attrib["width"])
    map_height = int(root.attrib["height"])

    tilesets: list[dict[str, Any]] = []
    for elem in root.findall("tileset"):
        firstgid = int(elem.attrib["firstgid"])
        source = elem.attrib.get("source")
        if source:
            source_path = _resolve_relative(tmx_path, source)
            tileset = load_tsx(source_path)
            tileset["firstgid"] = firstgid
            tileset["source"] = str(source_path)
            tilesets.append(tileset)
        else:
            # Inline tilesets are rare in this repo; store minimum metadata when encountered.
            tilesets.append(
                {
                    "firstgid": firstgid,
                    "name": elem.attrib.get("name", ""),
                    "tilewidth": int(elem.attrib["tilewidth"]),
                    "tileheight": int(elem.attrib["tileheight"]),
                    "tilecount": int(elem.attrib.get("tilecount", "0")),
                    "columns": int(elem.attrib.get("columns", "0")),
                }
            )

    layers: list[dict[str, Any]] = []
    for layer in root.findall("layer"):
        width = int(layer.attrib["width"])
        height = int(layer.attrib["height"])
        data = layer.find("data")
        if data is None:
            raise ValueError(f"Layer {layer.attrib.get('name', '<unnamed>')} is missing <data>")
        if data.attrib.get("encoding") != "csv":
            raise ValueError("Only CSV-encoded TMX layer data is supported")
        gids = _parse_csv_gid_data(data.text or "", width, height)
        layers.append(
            {
                "id": int(layer.attrib["id"]),
                "name": layer.attrib.get("name", ""),
                "width": width,
                "height": height,
                "gids": gids,
            }
        )

    return {
        "path": str(tmx_path.resolve()),
        "orientation": root.attrib.get("orientation", ""),
        "width": map_width,
        "height": map_height,
        "tilewidth": int(root.attrib["tilewidth"]),
        "tileheight": int(root.attrib["tileheight"]),
        "tilesets": tilesets,
        "layers": layers,
    }


def decode_tiled_gid(gid: int) -> dict[str, Any]:
    """Decode Tiled flip flags and return the base gid."""
    if gid < 0:
        raise ValueError("gid must be >= 0")
    return {
        "gid": gid & _GID_MASK,
        "flip_h": bool(gid & _FLIP_H),
        "flip_v": bool(gid & _FLIP_V),
        "flip_d": bool(gid & _FLIP_D),
    }


def map_tile_ids_to_regions(
    tile_ids: list[int],
    tileset: dict[str, Any],
    *,
    firstgid: int = 1,
) -> list[dict[str, Any]]:
    """Map tile gids to source image regions using tileset geometry."""
    tilewidth = int(tileset["tilewidth"])
    tileheight = int(tileset["tileheight"])
    columns = int(tileset["columns"])
    tilecount = int(tileset["tilecount"])

    mapped: list[dict[str, Any]] = []
    for raw_gid in tile_ids:
        decoded = decode_tiled_gid(raw_gid)
        gid = decoded["gid"]
        if gid == 0:
            mapped.append({"gid": 0, "empty": True})
            continue

        local_id = gid - firstgid
        if local_id < 0 or local_id >= tilecount:
            raise ValueError(f"gid {gid} out of range for firstgid {firstgid} and tilecount {tilecount}")

        mapped.append(
            {
                "gid": gid,
                "local_id": local_id,
                "x": (local_id % columns) * tilewidth,
                "y": (local_id // columns) * tileheight,
                "w": tilewidth,
                "h": tileheight,
                "flip_h": decoded["flip_h"],
                "flip_v": decoded["flip_v"],
                "flip_d": decoded["flip_d"],
            }
        )

    return mapped

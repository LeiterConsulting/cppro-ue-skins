"""Validate, preview, and lock CPPRO designer manifests without dependencies."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
from pathlib import Path
from typing import Any


HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")
ALLOWED_STATES = {"boot", "attract", "ready", "live", "paused", "result"}


class ManifestError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{path}: root must be a JSON object")
    return value


def resolve(base: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{field} must be a non-empty relative path")
    path = (base / value).resolve()
    if not path.is_file():
        raise ManifestError(f"{field} does not exist: {path}")
    return path


def require(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ManifestError(f"{label} missing fields: {', '.join(missing)}")


def validate_layout(layout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require(layout, {"schema", "version", "canvas", "keys", "blank_regions"}, "layout")
    if layout["schema"] != "cppro-key-layout" or layout["version"] != 1:
        raise ManifestError("layout must use cppro-key-layout version 1")
    canvas = layout["canvas"]
    if canvas.get("width_px") != 1920 or canvas.get("height_px") != 550:
        raise ManifestError("layout canvas must be the confirmed 1920x550 viewport")
    keys = layout["keys"]
    if not isinstance(keys, list) or len(keys) != 68:
        raise ManifestError("layout must contain exactly 68 keys")
    indices = [key.get("layout_index") for key in keys]
    if indices != list(range(68)):
        raise ManifestError("layout indices must be ordered exactly 0..67")
    ids = [key.get("id") for key in keys]
    if len(ids) != len(set(ids)) or any(not isinstance(item, str) for item in ids):
        raise ManifestError("layout key IDs must be 68 unique strings")
    if not layout.get("reactive_mapping_contract", {}).get("physically_validated"):
        raise ManifestError("layout reactive mapping must be physically validated")
    return {key["id"]: key for key in keys}


def validate_theme(theme: dict[str, Any]) -> None:
    require(
        theme,
        {"schema", "version", "name", "background", "text", "row_colors", "palettes"},
        "theme",
    )
    if theme["schema"] != "cppro-theme" or theme["version"] != 1:
        raise ManifestError("theme must use cppro-theme version 1")
    colors = [theme["background"], theme["text"], *theme["row_colors"]]
    colors.extend(palette.get("accent") for palette in theme["palettes"])
    if any(not isinstance(color, str) or not HEX_COLOR.fullmatch(color) for color in colors):
        raise ManifestError("theme colors must be #RRGGBB or #RRGGBBAA")
    if len(theme["row_colors"]) != 5:
        raise ManifestError("theme must provide exactly five row colors")
    palette_ids = [palette.get("id") for palette in theme["palettes"]]
    if not 1 <= len(palette_ids) <= 8 or len(palette_ids) != len(set(palette_ids)):
        raise ManifestError("theme must provide 1..8 palettes with unique IDs")


def validate_profile(profile: dict[str, Any], key_by_id: dict[str, dict[str, Any]]) -> None:
    require(profile, {"schema", "version", "name", "bindings"}, "profile")
    if profile["schema"] != "cppro-profile" or profile["version"] != 1:
        raise ManifestError("profile must use cppro-profile version 1")
    bindings = profile["bindings"]
    if not isinstance(bindings, dict) or not bindings:
        raise ManifestError("profile bindings must be a non-empty object")
    unknown = sorted(set(bindings) - set(key_by_id))
    if unknown:
        raise ManifestError(f"profile references unknown physical keys: {', '.join(unknown)}")
    actions = list(bindings.values())
    if any(not isinstance(action, str) or not action for action in actions):
        raise ManifestError("profile actions must be non-empty strings")
    if len(actions) != len(set(actions)):
        raise ManifestError("reference profiles must bind each semantic action once")


def validate_effects(effects: dict[str, Any]) -> None:
    require(effects, {"key_lights", "release_pad", "wave"}, "effects")
    if effects["key_lights"].get("pool_size") != 68:
        raise ManifestError("key_lights.pool_size must remain exactly 68")
    if effects["release_pad"].get("pool_size") != 68:
        raise ManifestError("release_pad.pool_size must remain exactly 68")
    wave = effects["wave"]
    radii = wave.get("radii_px")
    stage_ms = wave.get("stage_ms")
    opacity = wave.get("opacity")
    if not all(isinstance(items, list) for items in (radii, stage_ms, opacity)):
        raise ManifestError("wave radii_px, stage_ms, and opacity must be arrays")
    if not radii or len(radii) != len(stage_ms) or len(radii) != len(opacity):
        raise ManifestError("wave arrays must be non-empty and have equal lengths")
    expected_pool = 68 * len(radii)
    if wave.get("pool_size") != expected_pool:
        raise ManifestError(f"wave.pool_size must be 68 x stages ({expected_pool})")
    if any(not isinstance(value, (int, float)) or value <= 0 for value in radii):
        raise ManifestError("wave radii must be positive numbers")
    if any(not isinstance(value, int) or not 1 <= value <= 2000 for value in stage_ms):
        raise ManifestError("wave stage times must be integers in 1..2000 ms")
    if any(not isinstance(value, (int, float)) or not 0 <= value <= 1 for value in opacity):
        raise ManifestError("wave opacity values must be in 0..1")
    if any(opacity[index] < opacity[index + 1] for index in range(len(opacity) - 1)):
        raise ManifestError("wave opacity must not increase across outward stages")


def load_bundle(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    manifest = read_json(manifest_path)
    require(
        manifest,
        {
            "schema",
            "version",
            "id",
            "name",
            "canvas",
            "layout",
            "theme",
            "profile",
            "states",
            "effects",
        },
        "skin",
    )
    if manifest["schema"] != "cppro-skin" or manifest["version"] != 1:
        raise ManifestError("skin must use cppro-skin version 1")
    if manifest["canvas"] != {"width": 1920, "height": 550}:
        raise ManifestError("skin canvas must be exactly 1920x550")
    states = manifest["states"]
    allowed = states.get("allowed")
    if not isinstance(allowed, list) or not allowed or len(allowed) != len(set(allowed)):
        raise ManifestError("states.allowed must be a non-empty unique array")
    if not set(allowed) <= ALLOWED_STATES:
        raise ManifestError("states.allowed contains an unknown state")
    if states.get("initial") not in allowed:
        raise ManifestError("states.initial must appear in states.allowed")
    validate_effects(manifest["effects"])

    base = manifest_path.parent
    paths = {
        "manifest": manifest_path,
        "layout": resolve(base, manifest["layout"], "layout"),
        "theme": resolve(base, manifest["theme"], "theme"),
        "profile": resolve(base, manifest["profile"], "profile"),
    }
    layout = read_json(paths["layout"])
    theme = read_json(paths["theme"])
    profile = read_json(paths["profile"])
    key_by_id = validate_layout(layout)
    validate_theme(theme)
    validate_profile(profile, key_by_id)
    return {
        "manifest": manifest,
        "layout": layout,
        "theme": theme,
        "profile": profile,
        "paths": paths,
    }


def rgba(color: str) -> tuple[str, float]:
    rgb = color[:7]
    alpha = int(color[7:9], 16) / 255 if len(color) == 9 else 1.0
    return rgb, alpha


def svg_preview(bundle: dict[str, Any]) -> str:
    manifest = bundle["manifest"]
    layout = bundle["layout"]
    theme = bundle["theme"]
    unit_x = layout["device_fit_calibration"]["unit_x_px"]
    unit_y = layout["canvas"]["unit_px"]["y_visible"]
    background, background_alpha = rgba(theme["background"])
    rows = []
    for color in theme["row_colors"]:
        rows.append(rgba(color))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="550" viewBox="0 0 1920 550">',
        f'<rect width="1920" height="550" fill="{background}" fill-opacity="{background_alpha:.3f}"/>',
    ]
    for region in layout["blank_regions"]:
        rect = region["pixels"]
        parts.append(
            f'<rect x="{rect["x"]:.3f}" y="{rect["y"]:.3f}" '
            f'width="{rect["width"]:.3f}" height="{rect["height"]:.3f}" '
            'fill="#49217a" fill-opacity=".34" stroke="#c985ff" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{rect["x"] + 8:.3f}" y="{rect["y"] + 20:.3f}" '
            'fill="#ffffff" font-family="monospace" font-size="14">'
            f'{html.escape(region["id"])}</text>'
        )
    for key in layout["keys"]:
        x = key["x_u"] * unit_x
        y = key["row"] * unit_y
        width = key["width_u"] * unit_x
        color, alpha = rows[key["row"]]
        parts.append(
            f'<rect x="{x + 4:.3f}" y="{y + 4:.3f}" width="{width - 8:.3f}" '
            f'height="{unit_y - 8:.3f}" rx="7" fill="{color}" '
            f'fill-opacity="{alpha * .28:.3f}" stroke="{color}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{x + 10:.3f}" y="{y + 24:.3f}" fill="#ffffff" '
            'font-family="monospace" font-size="16">'
            f'L{key["layout_index"]:02d} {html.escape(key["label"])}</text>'
        )
    palette_labels = " / ".join(item["label"] for item in theme["palettes"])
    parts.append(
        '<text x="1612" y="252" fill="#ffffff" font-family="monospace" '
        f'font-size="19">{html.escape(manifest["name"])}</text>'
    )
    parts.append(
        '<text x="1612" y="278" fill="#ffffff" font-family="monospace" '
        f'font-size="16">READY · {html.escape(palette_labels)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def lock_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    paths = bundle["paths"]
    manifest_root = paths["manifest"].parent
    return {
        "schema": "cppro-skin-lock",
        "version": 1,
        "skin_id": bundle["manifest"]["id"],
        "inputs": {
            name: {
                "path": os.path.relpath(path, manifest_root).replace("\\", "/"),
                "sha256": sha256(path),
            }
            for name, path in paths.items()
        },
        "resolved": {
            "canvas": bundle["manifest"]["canvas"],
            "key_count": len(bundle["layout"]["keys"]),
            "native_indices": [key["layout_index"] for key in bundle["layout"]["keys"]],
            "bindings": bundle["profile"]["bindings"],
            "states": bundle["manifest"]["states"],
            "palettes": [item["id"] for item in bundle["theme"]["palettes"]],
            "effect_pool_total": sum(
                effect["pool_size"] for effect in bundle["manifest"]["effects"].values()
            ),
        },
    }


def write_text(path: Path, value: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "preview", "lock"):
        child = subparsers.add_parser(command)
        child.add_argument("manifest", type=Path)
        if command != "validate":
            child.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        bundle = load_bundle(args.manifest)
        if args.command == "preview":
            write_text(args.out, svg_preview(bundle))
            print(f"Preview written: {args.out.resolve()}")
        elif args.command == "lock":
            write_text(args.out, json.dumps(lock_bundle(bundle), indent=2) + "\n")
            print(f"Lock written: {args.out.resolve()}")
        else:
            print(
                f"VALID {bundle['manifest']['id']}: "
                f"{len(bundle['layout']['keys'])} keys, "
                f"{len(bundle['theme']['palettes'])} palettes, "
                f"{len(bundle['manifest']['states']['allowed'])} states"
            )
    except ManifestError as exc:
        parser.exit(2, f"INVALID: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

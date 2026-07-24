"""Build the CPPRO loader catalog from per-example library manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
CATALOG = ROOT / "catalog" / "skins.json"
REPOSITORY = "LeiterConsulting/cppro-ue-skins"
PAK_MAGIC = 0x5A6F12E1
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
ASSET = re.compile(r"^[A-Za-z0-9._-]+\.pak$")


class CatalogError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path}: root must be an object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def pak_version(path: Path) -> int:
    size = path.stat().st_size
    tail_size = min(size, 4096)
    with path.open("rb") as stream:
        stream.seek(size - tail_size)
        tail = stream.read()
    magic = struct.pack("<I", PAK_MAGIC)
    positions = [
        index
        for index in range(len(tail) - 7)
        if tail[index : index + 4] == magic
    ]
    for index in reversed(positions):
        version = struct.unpack_from("<I", tail, index + 4)[0]
        if 1 <= version <= 20:
            return version
    raise CatalogError(f"{path}: Unreal PAK footer was not found")


def require_text(value: dict[str, Any], field: str, limit: int) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip() or len(result) > limit:
        raise CatalogError(f"{field} must be a non-empty string up to {limit} characters")
    return result.strip()


def validate_timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise CatalogError("published_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CatalogError("published_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise CatalogError("published_at must include a timezone")
    return value


def checksum_entry(example: Path, pak: Path) -> None:
    checksum_file = example / "release" / "SHA256SUMS.txt"
    if not checksum_file.is_file():
        raise CatalogError(f"{example.name}: release/SHA256SUMS.txt is required")
    expected = sha256(pak)
    lines = [
        line.strip().split()
        for line in checksum_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [
        parts
        for parts in lines
        if len(parts) >= 2 and parts[-1].lstrip("*") == pak.name
    ]
    if not matches or matches[0][0].upper() != expected:
        raise CatalogError(f"{example.name}: SHA256SUMS.txt does not match {pak.name}")


def build_entry(manifest_path: Path) -> dict[str, Any]:
    example = manifest_path.parent
    value = read_json(manifest_path)
    if value.get("schema") != "cppro-skin-library-entry" or value.get("version") != 1:
        raise CatalogError(f"{manifest_path}: unsupported schema or version")

    skin_id = require_text(value, "id", 64)
    if not ID.fullmatch(skin_id) or skin_id != example.name:
        raise CatalogError(f"{example.name}: id must equal the example folder name")
    name = require_text(value, "name", 48)
    subtitle = require_text(value, "subtitle", 64)
    description = require_text(value, "description", 240)

    tags = value.get("tags")
    if (
        not isinstance(tags, list)
        or not 1 <= len(tags) <= 6
        or len(tags) != len(set(tags))
        or any(not isinstance(tag, str) or not tag or len(tag) > 24 for tag in tags)
    ):
        raise CatalogError(f"{skin_id}: tags must contain 1..6 unique short strings")

    accent = value.get("accent")
    if not isinstance(accent, str) or not COLOR.fullmatch(accent):
        raise CatalogError(f"{skin_id}: accent must be #RRGGBB")
    published_at = validate_timestamp(value.get("published_at"))

    pak_value = value.get("pak")
    if (
        not isinstance(pak_value, str)
        or not pak_value.startswith("release/")
        or Path(pak_value).suffix.lower() != ".pak"
    ):
        raise CatalogError(f"{skin_id}: pak must be a release/*.pak path")
    pak = (example / pak_value).resolve()
    if not pak.is_file() or example.resolve() not in pak.parents:
        raise CatalogError(f"{skin_id}: PAK does not exist inside the example")
    if pak_version(pak) != 11:
        raise CatalogError(f"{skin_id}: release PAK must be version 11")
    checksum_entry(example, pak)

    readme = example / "README.md"
    if not readme.is_file():
        raise CatalogError(f"{skin_id}: README.md is required")

    release = value.get("release")
    if not isinstance(release, dict) or set(release) != {"tag", "asset"}:
        raise CatalogError(f"{skin_id}: release must contain only tag and asset")
    tag = require_text(release, "tag", 64)
    asset = require_text(release, "asset", 128)
    if not ASSET.fullmatch(asset) or asset != pak.name:
        raise CatalogError(f"{skin_id}: release.asset must equal the PAK filename")

    source_path = pak.relative_to(ROOT).as_posix()
    return {
        "id": skin_id,
        "name": name,
        "subtitle": subtitle,
        "description": description,
        "tags": tags,
        "filename": pak.name,
        "bytes": pak.stat().st_size,
        "sha256": sha256(pak),
        "source_path": source_path,
        "download_url": (
            f"https://github.com/{REPOSITORY}/releases/download/{tag}/{asset}"
        ),
        "docs_url": f"https://github.com/{REPOSITORY}/tree/main/examples/{skin_id}",
        "accent": accent.upper(),
        "published_at": published_at,
        "release_tag": tag,
        "release_asset": asset,
        "downloads": 0,
    }


def build_catalog() -> dict[str, Any]:
    manifests = sorted(EXAMPLES.glob("*/library.json"))
    if not manifests:
        raise CatalogError("No examples/*/library.json files were found")
    entries = [build_entry(path) for path in manifests]
    for field in ("id", "source_path", "release_asset"):
        values = [entry[field] for entry in entries]
        if len(values) != len(set(values)):
            raise CatalogError(f"Duplicate {field} in skin library")
    entries.sort(key=lambda item: (item["published_at"], item["name"]), reverse=True)
    return {
        "schema": "cppro-skin-catalog",
        "version": 1,
        "repository": f"https://github.com/{REPOSITORY}",
        "releases_api": f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100",
        "skins": entries,
    }


def rendered_catalog() -> str:
    return json.dumps(build_catalog(), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if catalog/skins.json is not the generated result.",
    )
    args = parser.parse_args()
    try:
        rendered = rendered_catalog()
        if args.check:
            current = CATALOG.read_text(encoding="utf-8") if CATALOG.is_file() else ""
            if current != rendered:
                raise CatalogError(
                    "catalog/skins.json is stale; run tools/build-skin-catalog.py"
                )
            print(f"Catalog current: {len(build_catalog()['skins'])} skins")
        else:
            CATALOG.parent.mkdir(parents=True, exist_ok=True)
            CATALOG.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"Catalog written: {CATALOG}")
    except CatalogError as exc:
        parser.exit(2, f"CATALOG ERROR: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

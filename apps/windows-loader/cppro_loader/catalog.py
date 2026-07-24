from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Callable

from .pak import inspect_pak
from .resources import local_app_data, resource_path


REMOTE_CATALOG = (
    "https://raw.githubusercontent.com/LeiterConsulting/"
    "cppro-ue-skins/main/catalog/skins.json"
)
RELEASES_API = (
    "https://api.github.com/repos/LeiterConsulting/"
    "cppro-ue-skins/releases?per_page=100"
)

SORT_NEWEST = "Newest"
SORT_A_Z = "A–Z"
SORT_DOWNLOADS = "Most downloaded"
SORT_OPTIONS = (SORT_NEWEST, SORT_A_Z, SORT_DOWNLOADS)


@dataclass(frozen=True)
class Skin:
    id: str
    name: str
    subtitle: str
    description: str
    tags: tuple[str, ...]
    filename: str
    bytes: int
    sha256: str
    source_path: str
    download_url: str
    docs_url: str
    accent: str
    published_at: str
    release_tag: str
    release_asset: str
    downloads: int

    @classmethod
    def from_dict(cls, value: dict) -> "Skin":
        required = {
            "id",
            "name",
            "subtitle",
            "description",
            "tags",
            "filename",
            "bytes",
            "sha256",
            "source_path",
            "download_url",
            "docs_url",
            "accent",
            "published_at",
            "release_tag",
            "release_asset",
            "downloads",
        }
        missing = required - value.keys()
        if missing:
            raise ValueError(f"Catalog entry is missing: {', '.join(sorted(missing))}")
        if not str(value["filename"]).lower().endswith(".pak"):
            raise ValueError("Catalog filenames must end in .pak.")
        sha = str(value["sha256"]).upper()
        if len(sha) != 64 or any(c not in "0123456789ABCDEF" for c in sha):
            raise ValueError("Catalog SHA-256 values must be 64 hexadecimal digits.")
        try:
            published_at = datetime.fromisoformat(
                str(value["published_at"]).replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError("Catalog published_at values must be ISO-8601.") from exc
        if published_at.tzinfo is None:
            raise ValueError("Catalog published_at values must include a timezone.")
        downloads = int(value["downloads"])
        if downloads < 0:
            raise ValueError("Catalog download counts cannot be negative.")
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            subtitle=str(value["subtitle"]),
            description=str(value["description"]),
            tags=tuple(str(tag) for tag in value["tags"]),
            filename=str(value["filename"]),
            bytes=int(value["bytes"]),
            sha256=sha,
            source_path=str(value["source_path"]),
            download_url=str(value["download_url"]),
            docs_url=str(value["docs_url"]),
            accent=str(value["accent"]),
            published_at=str(value["published_at"]),
            release_tag=str(value["release_tag"]),
            release_asset=str(value["release_asset"]),
            downloads=downloads,
        )


def _parse_catalog(payload: bytes) -> list[Skin]:
    document = json.loads(payload.decode("utf-8"))
    if document.get("schema") != "cppro-skin-catalog":
        raise ValueError("Unsupported catalog schema.")
    if document.get("version") != 1:
        raise ValueError("Unsupported catalog version.")
    skins = [Skin.from_dict(item) for item in document.get("skins", [])]
    if not skins:
        raise ValueError("The skin catalog is empty.")
    if len({skin.id for skin in skins}) != len(skins):
        raise ValueError("The skin catalog contains duplicate IDs.")
    return skins


def _enrich_downloads(skins: list[Skin], payload: bytes) -> list[Skin]:
    releases = json.loads(payload.decode("utf-8"))
    if not isinstance(releases, list):
        raise ValueError("GitHub Releases response must be an array.")

    counts: dict[str, int] = {}
    urls: dict[str, str] = {}
    for release in releases:
        if not isinstance(release, dict):
            continue
        for asset in release.get("assets", []):
            if not isinstance(asset, dict):
                continue
            name = asset.get("name")
            if not isinstance(name, str):
                continue
            count = int(asset.get("download_count") or 0)
            counts[name] = counts.get(name, 0) + max(0, count)
            url = asset.get("browser_download_url")
            if name not in urls and isinstance(url, str) and url:
                urls[name] = url

    return [
        replace(
            skin,
            downloads=counts.get(skin.release_asset, skin.downloads),
            download_url=urls.get(skin.release_asset, skin.download_url),
        )
        for skin in skins
    ]


def _with_live_downloads(
    skins: list[Skin],
    timeout: float,
) -> tuple[list[Skin], bool]:
    request = urllib.request.Request(
        RELEASES_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CPPRO-Skin-Loader/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _enrich_downloads(skins, response.read()), True
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return skins, False


def sort_skins(skins: list[Skin], order: str) -> list[Skin]:
    if order == SORT_A_Z:
        return sorted(skins, key=lambda skin: (skin.name.casefold(), skin.id))
    if order == SORT_DOWNLOADS:
        return sorted(
            skins,
            key=lambda skin: (-skin.downloads, skin.name.casefold(), skin.id),
        )
    return sorted(
        skins,
        key=lambda skin: (
            datetime.fromisoformat(skin.published_at.replace("Z", "+00:00")),
            skin.name.casefold(),
        ),
        reverse=True,
    )


def load_catalog(timeout: float = 4.0) -> tuple[list[Skin], str]:
    request = urllib.request.Request(
        REMOTE_CATALOG,
        headers={"User-Agent": "CPPRO-Skin-Loader/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            skins = _parse_catalog(response.read())
            source = "Online library"
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        bundled = resource_path("catalog/skins.json")
        skins = _parse_catalog(bundled.read_bytes())
        source = "Built-in library (offline)"
    skins, live_counts = _with_live_downloads(skins, timeout)
    if live_counts:
        source += " • live download counts"
    return skins, source


def download_skin(
    skin: Skin,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    destination_dir = local_app_data() / "downloads"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / skin.filename

    if destination.exists():
        try:
            inspect_pak(destination, skin.sha256)
            if progress:
                progress(skin.bytes, skin.bytes)
            return destination
        except ValueError:
            destination.unlink(missing_ok=True)

    partial = destination.with_name(f"{destination.stem}.download.pak")
    partial.unlink(missing_ok=True)
    request = urllib.request.Request(
        skin.download_url,
        headers={"User-Agent": "CPPRO-Skin-Loader/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            total = int(response.headers.get("Content-Length") or skin.bytes)
            consumed = 0
            with partial.open("wb") as stream:
                while chunk := response.read(256 * 1024):
                    stream.write(chunk)
                    consumed += len(chunk)
                    if progress:
                        progress(consumed, total)
        info = inspect_pak(partial, skin.sha256)
        if info.bytes != skin.bytes:
            raise ValueError(
                f"Expected {skin.bytes:,} bytes but downloaded {info.bytes:,}."
            )
        partial.replace(destination)
        return destination
    except Exception:
        partial.unlink(missing_ok=True)
        raise

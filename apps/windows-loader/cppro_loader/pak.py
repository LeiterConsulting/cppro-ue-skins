from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PAK_MAGIC = 0x5A6F12E1
PAK_MAGIC_BYTES = struct.pack("<I", PAK_MAGIC)


@dataclass(frozen=True)
class PakInfo:
    path: Path
    bytes: int
    sha256: str
    version: int
    index_offset: int
    index_size: int


def sha256_file(
    path: Path,
    progress: Callable[[int, int], None] | None = None,
) -> str:
    total = path.stat().st_size
    consumed = 0
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            consumed += len(chunk)
            if progress:
                progress(consumed, total)
    return digest.hexdigest().upper()


def inspect_pak(
    path: Path,
    expected_sha256: str | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> PakInfo:
    path = path.resolve()
    if path.suffix.lower() != ".pak":
        raise ValueError("Choose a file ending in .pak.")
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError("The selected PAK is missing or empty.")

    size = path.stat().st_size
    tail_length = min(size, 1024)
    with path.open("rb") as stream:
        stream.seek(size - tail_length)
        tail = stream.read(tail_length)
    relative_magic = tail.rfind(PAK_MAGIC_BYTES)
    if relative_magic < 0:
        raise ValueError("This file does not contain a valid Unreal PAK footer.")

    magic_offset = size - tail_length + relative_magic
    with path.open("rb") as stream:
        stream.seek(magic_offset)
        footer = stream.read(28)
    if len(footer) < 28:
        raise ValueError("The Unreal PAK footer is incomplete.")

    magic, version = struct.unpack_from("<II", footer, 0)
    index_offset, index_size = struct.unpack_from("<QQ", footer, 8)
    if magic != PAK_MAGIC:
        raise ValueError("The Unreal PAK footer magic is invalid.")
    if version != 11:
        raise ValueError(
            f"PAK version {version} is not the CPPRO-tested version 11."
        )
    if index_offset <= 0 or index_size <= 0 or index_offset + index_size > size:
        raise ValueError("The Unreal PAK index points outside the file.")

    actual_hash = sha256_file(path, progress)
    if expected_sha256 and actual_hash != expected_sha256.upper():
        raise ValueError(
            "The downloaded PAK failed SHA-256 verification. "
            "Delete it and try again."
        )
    return PakInfo(path, size, actual_hash, version, index_offset, index_size)

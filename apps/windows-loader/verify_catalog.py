from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cppro_loader.catalog import _parse_catalog  # noqa: E402
from cppro_loader.pak import inspect_pak  # noqa: E402


def main() -> int:
    catalog_path = ROOT / "catalog" / "skins.json"
    skins = _parse_catalog(catalog_path.read_bytes())
    for skin in skins:
        local_path = ROOT / skin.source_path
        if ROOT.resolve() not in local_path.resolve().parents:
            raise ValueError(f"{skin.id}: source path is outside the repository")
        info = inspect_pak(local_path, skin.sha256)
        if info.bytes != skin.bytes:
            raise ValueError(
                f"{skin.id}: catalog bytes {skin.bytes} != file bytes {info.bytes}"
            )
        print(
            f"PASS {skin.id}: {info.bytes:,} bytes, "
            f"PAK {info.version}, {info.sha256[:12]}…"
        )
    print(f"Catalog verified: {len(skins)} skins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

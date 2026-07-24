from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """Return a bundled resource in source and PyInstaller builds."""
    if hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)
    else:
        root = Path(__file__).resolve().parents[3]
    return root / relative


def local_app_data() -> Path:
    if sys.platform == "win32":
        base = Path(
            os.environ.get("LOCALAPPDATA")
            or Path.home() / "AppData" / "Local"
        )
        path = base / "CPPRO Skin Loader"
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Caches" / "CPPRO Skin Loader"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        path = base / "cppro-skin-loader"
    path.mkdir(parents=True, exist_ok=True)
    return path

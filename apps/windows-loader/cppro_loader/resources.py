from __future__ import annotations

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
    import os

    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    path = Path(base) / "CPPRO Skin Loader"
    path.mkdir(parents=True, exist_ok=True)
    return path

from __future__ import annotations

import ctypes
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

from .catalog import Skin


COLORS = {
    "nav": "#17233A",
    "nav_hover": "#223250",
    "canvas": "#F3F5F8",
    "surface": "#FFFFFF",
    "surface_alt": "#E9EDF3",
    "text": "#172033",
    "muted": "#657086",
    "line": "#D8DEE8",
    "accent": "#087EA4",
    "accent_hover": "#096B8A",
    "success": "#18875A",
    "warning": "#B76700",
    "danger": "#B23B3B",
}


def enable_windows_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def configure_ttk(root: tk.Misc) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass
    style.configure(
        "CPPRO.Horizontal.TProgressbar",
        troughcolor="#E3E8EF",
        background=COLORS["accent"],
        bordercolor="#E3E8EF",
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        thickness=10,
    )
    style.configure("CPPRO.TCombobox", padding=6)


def format_bytes(value: int) -> str:
    return f"{value / 1024 / 1024:.1f} MB"


def shorten_hash(value: str) -> str:
    if not value:
        return "Calculated before install"
    return f"{value[:12]}…{value[-8:]}"


@dataclass
class Selection:
    name: str
    subtitle: str
    filename: str
    bytes: int
    sha256: str
    local_path: Path | None = None
    skin: Skin | None = None

    @classmethod
    def from_skin(cls, skin: Skin) -> "Selection":
        return cls(
            skin.name,
            skin.subtitle,
            skin.filename,
            skin.bytes,
            skin.sha256,
            skin=skin,
        )

    @classmethod
    def from_local(cls, path: Path) -> "Selection":
        return cls(
            path.stem.replace("_", " ").strip().title(),
            "Local PAK file",
            path.name,
            path.stat().st_size,
            "",
            local_path=path,
        )


class BackgroundJobs:
    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.events: queue.Queue[tuple[Callable, tuple]] = queue.Queue()
        self.root.after(40, self._drain)

    def call_ui(self, callback: Callable, *args) -> None:
        self.events.put((callback, args))

    def run(
        self,
        task: Callable,
        success: Callable,
        failure: Callable | None = None,
    ) -> None:
        def worker() -> None:
            try:
                result = task()
            except Exception as exc:
                self.call_ui(failure or self._default_failure, exc)
            else:
                self.call_ui(success, result)

        threading.Thread(target=worker, daemon=True).start()

    def _drain(self) -> None:
        try:
            while True:
                callback, args = self.events.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        try:
            self.root.after(40, self._drain)
        except tk.TclError:
            pass

    @staticmethod
    def _default_failure(exc: Exception) -> None:
        messagebox.showerror("CPPRO Skin Loader", str(exc))


def primary_button(
    parent: tk.Misc,
    text: str,
    command: Callable,
    width: int = 18,
) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=width,
        bg=COLORS["accent"],
        activebackground=COLORS["accent_hover"],
        fg="white",
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=16,
        pady=10,
        cursor="hand2",
        font=("Segoe UI Semibold", 10),
    )


def secondary_button(
    parent: tk.Misc,
    text: str,
    command: Callable,
    width: int = 14,
) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=width,
        bg=COLORS["surface_alt"],
        activebackground=COLORS["line"],
        fg=COLORS["text"],
        activeforeground=COLORS["text"],
        relief="flat",
        bd=0,
        padx=12,
        pady=9,
        cursor="hand2",
        font=("Segoe UI", 10),
    )


def section_title(parent: tk.Misc, title: str, subtitle: str) -> tk.Frame:
    frame = tk.Frame(parent, bg=COLORS["canvas"])
    tk.Label(
        frame,
        text=title,
        bg=COLORS["canvas"],
        fg=COLORS["text"],
        font=("Segoe UI Semibold", 22),
        anchor="w",
    ).pack(fill="x")
    tk.Label(
        frame,
        text=subtitle,
        bg=COLORS["canvas"],
        fg=COLORS["muted"],
        font=("Segoe UI", 10),
        anchor="w",
        justify="left",
    ).pack(fill="x", pady=(4, 0))
    return frame

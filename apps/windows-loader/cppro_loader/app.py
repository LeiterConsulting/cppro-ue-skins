from __future__ import annotations

import argparse
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import APP_NAME, APP_VERSION
from .catalog import (
    SORT_NEWEST,
    SORT_OPTIONS,
    Skin,
    download_skin,
    load_catalog,
    sort_skins,
)
from .device import DeviceStatus, detect_device, upload_pak
from .pak import inspect_pak
from .ui_common import (
    COLORS,
    BackgroundJobs,
    Selection,
    configure_ttk,
    enable_windows_dpi_awareness,
    format_bytes,
    primary_button,
    secondary_button,
    shorten_hash,
)


class SkinLibrary(tk.Tk):
    def __init__(self, demo: bool = False) -> None:
        super().__init__()
        self.demo = demo
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(1040, 680)
        self.configure(bg=COLORS["canvas"])
        configure_ttk(self)
        self.jobs = BackgroundJobs(self)

        self.skins: list[Skin] = []
        self.catalog_source = "Loading library…"
        self.selection: Selection | None = None
        self.sort_order = tk.StringVar(value=SORT_NEWEST)
        self.slot = tk.StringVar(value="5")
        self.activate = tk.BooleanVar(value=True)
        self.device_status = DeviceStatus(False, 0, "Checking…")
        self.installing = False

        self._build_shell()
        self._render_cards()
        self._render_install_panel()
        self._refresh_catalog()
        self._refresh_device()

    def _build_shell(self) -> None:
        sidebar = tk.Frame(self, width=210, bg=COLORS["nav"])
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(
            sidebar,
            text="CPPRO",
            bg=COLORS["nav"],
            fg="white",
            font=("Segoe UI Semibold", 21),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(26, 0))
        tk.Label(
            sidebar,
            text="SKIN LIBRARY",
            bg=COLORS["nav"],
            fg="#8DD9EB",
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(fill="x", padx=25, pady=(0, 30))

        self._nav_button(sidebar, "▦   Skin library", lambda: None, active=True)
        self._nav_button(sidebar, "＋   Open local PAK", self._browse_local)
        self._nav_button(
            sidebar,
            "↗   Project on GitHub",
            lambda: webbrowser.open(
                "https://github.com/LeiterConsulting/cppro-ue-skins"
            ),
        )
        tk.Label(
            sidebar,
            text=(
                f"Version {APP_VERSION}\n\n"
                "Independent community tool\n"
                "Not an official Finalmouse app"
            ),
            justify="left",
            bg=COLORS["nav"],
            fg="#8591A6",
            font=("Segoe UI", 8),
        ).pack(side="bottom", anchor="w", padx=24, pady=20)

        central = tk.Frame(self, bg=COLORS["canvas"])
        central.pack(side="left", fill="both", expand=True)
        header = tk.Frame(central, height=74, bg=COLORS["surface"])
        header.pack(fill="x")
        header.pack_propagate(False)
        title = tk.Frame(header, bg=COLORS["surface"])
        title.pack(side="left", padx=26)
        tk.Label(
            title,
            text="Skin library",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 16),
            anchor="w",
        ).pack(anchor="w", pady=(11, 0))
        self.catalog_label = tk.Label(
            title,
            text=self.catalog_source,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.catalog_label.pack(anchor="w")
        self.device_label = tk.Label(
            header,
            text="●  Checking for CPPRO…",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        self.device_label.pack(side="right", padx=(8, 26))
        tk.Button(
            header,
            text="↻",
            command=self._refresh_device,
            bg=COLORS["surface"],
            activebackground=COLORS["surface_alt"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 14),
            cursor="hand2",
        ).pack(side="right")

        content = tk.Frame(central, bg=COLORS["canvas"])
        content.pack(fill="both", expand=True)
        gallery_area = tk.Frame(content, bg=COLORS["canvas"])
        gallery_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(24, 16),
            pady=22,
        )
        gallery_toolbar = tk.Frame(gallery_area, bg=COLORS["canvas"])
        gallery_toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(
            gallery_toolbar,
            text="TESTED SKINS FROM THE DEVELOPER",
            bg=COLORS["canvas"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
            anchor="w",
        ).pack(side="left")
        sort_box = ttk.Combobox(
            gallery_toolbar,
            textvariable=self.sort_order,
            values=SORT_OPTIONS,
            state="readonly",
            style="CPPRO.TCombobox",
            width=18,
            font=("Segoe UI", 9),
        )
        sort_box.pack(side="right")
        sort_box.bind("<<ComboboxSelected>>", self._sort_changed)
        tk.Label(
            gallery_toolbar,
            text="Sort",
            bg=COLORS["canvas"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(side="right", padx=(0, 8))

        gallery_viewport = tk.Frame(gallery_area, bg=COLORS["canvas"])
        gallery_viewport.pack(fill="both", expand=True)
        self.gallery_canvas = tk.Canvas(
            gallery_viewport,
            bg=COLORS["canvas"],
            highlightthickness=0,
            bd=0,
        )
        gallery_scrollbar = ttk.Scrollbar(
            gallery_viewport,
            orient="vertical",
            command=self.gallery_canvas.yview,
        )
        self.gallery_canvas.configure(yscrollcommand=gallery_scrollbar.set)
        gallery_scrollbar.pack(side="right", fill="y")
        self.gallery_canvas.pack(side="left", fill="both", expand=True)
        self.gallery = tk.Frame(self.gallery_canvas, bg=COLORS["canvas"])
        self.gallery_window = self.gallery_canvas.create_window(
            (0, 0),
            window=self.gallery,
            anchor="nw",
        )
        self.gallery.bind("<Configure>", self._gallery_content_changed)
        self.gallery_canvas.bind("<Configure>", self._gallery_canvas_changed)
        self.bind_all("<MouseWheel>", self._gallery_mousewheel, add="+")
        self.install_panel = tk.Frame(
            content,
            width=310,
            bg=COLORS["surface"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )
        self.install_panel.pack(side="right", fill="y", padx=(0, 22), pady=22)
        self.install_panel.pack_propagate(False)

    def _nav_button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        active: bool = False,
    ) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            bg=COLORS["nav_hover"] if active else COLORS["nav"],
            activebackground=COLORS["nav_hover"],
            fg="white" if active else "#CDD5E3",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=22,
            pady=12,
            font=("Segoe UI Semibold" if active else "Segoe UI", 10),
            cursor="hand2",
        ).pack(fill="x", padx=10, pady=2)

    def _render_cards(self) -> None:
        for child in self.gallery.winfo_children():
            child.destroy()
        self.gallery.grid_columnconfigure(0, weight=1)
        self.gallery.grid_columnconfigure(1, weight=1)
        if not self.skins:
            tk.Label(
                self.gallery,
                text="Loading the library…",
                bg=COLORS["canvas"],
                fg=COLORS["muted"],
                font=("Segoe UI", 11),
            ).grid(row=0, column=0, columnspan=2, pady=80)
            return
        for index, skin in enumerate(sort_skins(self.skins, self.sort_order.get())):
            row = index // 2
            column = index % 2
            self._skin_card(skin).grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 6, 6 if column == 0 else 0),
                pady=6,
            )

    def _sort_changed(self, _event=None) -> None:
        self._render_cards()
        self.gallery_canvas.yview_moveto(0)

    def _gallery_content_changed(self, _event=None) -> None:
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def _gallery_canvas_changed(self, event) -> None:
        self.gallery_canvas.itemconfigure(self.gallery_window, width=event.width)

    def _gallery_mousewheel(self, event):
        left = self.gallery_canvas.winfo_rootx()
        top = self.gallery_canvas.winfo_rooty()
        right = left + self.gallery_canvas.winfo_width()
        bottom = top + self.gallery_canvas.winfo_height()
        pointer_x, pointer_y = self.winfo_pointerxy()
        if left <= pointer_x <= right and top <= pointer_y <= bottom:
            self.gallery_canvas.yview_scroll(int(-event.delta / 120), "units")
            return "break"
        return None

    def _skin_card(self, skin: Skin) -> tk.Frame:
        selected = bool(self.selection and self.selection.skin and self.selection.skin.id == skin.id)
        frame = tk.Frame(
            self.gallery,
            bg=COLORS["surface"],
            highlightthickness=2 if selected else 1,
            highlightbackground=skin.accent if selected else COLORS["line"],
        )
        tk.Frame(frame, bg=skin.accent, height=6).pack(fill="x")
        tk.Label(
            frame,
            text=skin.name,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 13),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(13, 2))
        tk.Label(
            frame,
            text=skin.subtitle,
            bg=COLORS["surface"],
            fg=skin.accent,
            font=("Segoe UI Semibold", 8),
            anchor="w",
        ).pack(fill="x", padx=16)
        published = datetime.fromisoformat(
            skin.published_at.replace("Z", "+00:00")
        ).strftime("%b %d, %Y")
        tk.Label(
            frame,
            text=f"Published {published}",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 7),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(3, 0))
        tk.Label(
            frame,
            text=skin.description,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            justify="left",
            anchor="nw",
            wraplength=255,
            height=3,
        ).pack(fill="x", padx=16, pady=(10, 7))
        tk.Label(
            frame,
            text=(
                f"{format_bytes(skin.bytes)}  •  Verified  •  "
                f"{skin.downloads:,} download"
                f"{'' if skin.downloads == 1 else 's'}"
            ),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=16)
        actions = tk.Frame(frame, bg=COLORS["surface"])
        actions.pack(fill="x", padx=12, pady=11)
        tk.Button(
            actions,
            text="Details",
            command=lambda: webbrowser.open(skin.docs_url),
            bg=COLORS["surface"],
            activebackground=COLORS["surface_alt"],
            fg=COLORS["muted"],
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            font=("Segoe UI", 8),
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            actions,
            text="Selected" if selected else "Use this skin",
            command=lambda: self._select_skin(skin),
            bg=skin.accent if selected else COLORS["surface_alt"],
            activebackground=skin.accent,
            fg="white" if selected else COLORS["text"],
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            font=("Segoe UI Semibold", 8),
            cursor="hand2",
        ).pack(side="right")
        return frame

    def _select_skin(self, skin: Skin) -> None:
        self.selection = Selection.from_skin(skin)
        self._render_cards()
        self._render_install_panel()

    def _browse_local(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Choose a CPPRO skin",
            filetypes=[("Unreal PAK skin", "*.pak"), ("All files", "*.*")],
        )
        if not selected:
            return
        path = Path(selected)
        try:
            inspect_pak(path)
        except ValueError as exc:
            messagebox.showerror("Unsupported PAK", str(exc), parent=self)
            return
        self.selection = Selection.from_local(path)
        self._render_cards()
        self._render_install_panel()

    def _render_install_panel(self) -> None:
        for child in self.install_panel.winfo_children():
            child.destroy()
        tk.Label(
            self.install_panel,
            text="INSTALL",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(22, 15))
        if not self.selection:
            tk.Label(
                self.install_panel,
                text="Choose a skin",
                bg=COLORS["surface"],
                fg=COLORS["text"],
                font=("Segoe UI Semibold", 16),
                anchor="w",
            ).pack(fill="x", padx=22)
            tk.Label(
                self.install_panel,
                text=(
                    "Select a developer skin from the library, or open a local "
                    ".pak file from the navigation."
                ),
                wraplength=250,
                justify="left",
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9),
                anchor="nw",
            ).pack(fill="x", padx=22, pady=(8, 20))
            return
        tk.Label(
            self.install_panel,
            text=self.selection.name,
            wraplength=260,
            justify="left",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 16),
            anchor="w",
        ).pack(fill="x", padx=22)
        tk.Label(
            self.install_panel,
            text=self.selection.subtitle,
            wraplength=260,
            justify="left",
            bg=COLORS["surface"],
            fg=COLORS["accent"],
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(4, 14))
        self._fact("File", self.selection.filename)
        self._fact("Size", format_bytes(self.selection.bytes))
        self._fact("SHA-256", shorten_hash(self.selection.sha256))
        tk.Frame(self.install_panel, height=1, bg=COLORS["line"]).pack(
            fill="x", padx=22, pady=16
        )
        tk.Label(
            self.install_panel,
            text="Destination slot",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).pack(fill="x", padx=22)
        slot_box = ttk.Combobox(
            self.install_panel,
            textvariable=self.slot,
            values=("1", "2", "3", "4", "5"),
            state="readonly",
            style="CPPRO.TCombobox",
            font=("Segoe UI", 10),
        )
        slot_box.pack(fill="x", padx=22, pady=(6, 8))
        tk.Checkbutton(
            self.install_panel,
            text="Activate after installation",
            variable=self.activate,
            bg=COLORS["surface"],
            activebackground=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=18)
        self.progress = ttk.Progressbar(
            self.install_panel,
            maximum=100,
            mode="determinate",
            style="CPPRO.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", padx=22, pady=(20, 7))
        self.progress_label = tk.Label(
            self.install_panel,
            text=(
                "Demo mode — no device writes"
                if self.demo
                else "Ready to send"
            ),
            wraplength=260,
            justify="left",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.progress_label.pack(fill="x", padx=22)
        self.install_button = primary_button(
            self.install_panel,
            "Simulate install" if self.demo else "Send to CPPRO",
            self._install,
            width=25,
        )
        self.install_button.pack(side="bottom", padx=22, pady=22)

    def _fact(self, label: str, value: str) -> None:
        tk.Label(
            self.install_panel,
            text=label.upper(),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 7),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(8, 0))
        tk.Label(
            self.install_panel,
            text=value,
            wraplength=255,
            justify="left",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=22)

    def _install(self) -> None:
        assert self.selection is not None
        if not self.demo and not self.device_status.connected:
            messagebox.showerror(
                "CPPRO not found",
                "Connect the Centerpiece Pro directly by USB, then refresh.",
                parent=self,
            )
            return
        slot = int(self.slot.get())
        if not messagebox.askyesno(
            "Confirm installation",
            (
                f"{'Simulate installing' if self.demo else 'Replace'} slot "
                f"{slot} with {self.selection.name}?\n\n"
                "Do not disconnect the keyboard until completion."
            ),
            parent=self,
        ):
            return
        self.installing = True
        self.install_button.configure(state="disabled")
        selection = self.selection
        activate = self.activate.get()

        def progress(value: float, text: str) -> None:
            self.jobs.call_ui(self._set_progress, value, text)

        def task():
            path = selection.local_path
            if selection.skin:
                progress(0.01, f"Downloading {selection.skin.name}…")

                def download_progress(done: int, total: int) -> None:
                    ratio = done / total if total else 0
                    progress(0.01 + ratio * 0.24, f"Downloading — {ratio:.0%}")

                path = download_skin(selection.skin, download_progress)
            assert path is not None

            def upload_progress(value: float, text: str) -> None:
                progress(0.25 + value * 0.75, text)

            return upload_pak(
                path,
                slot,
                activate,
                upload_progress,
                expected_sha256=selection.sha256 or None,
                demo=self.demo,
            )

        self.jobs.run(task, self._install_complete, self._install_failed)

    def _set_progress(self, value: float, text: str) -> None:
        self.progress["value"] = value * 100
        self.progress_label.configure(text=text)

    def _install_complete(self, result) -> None:
        _info, upload = result
        self.installing = False
        self.install_button.configure(state="normal")
        title = "Demo complete" if upload.demo else "Skin installed"
        detail = (
            f"No device data was sent. The full workflow for slot {upload.slot} "
            "completed successfully."
            if upload.demo
            else (
                f"Slot {upload.slot} was written successfully in "
                f"{upload.seconds:.1f} seconds."
            )
        )
        messagebox.showinfo(title, detail, parent=self)

    def _install_failed(self, exc: Exception) -> None:
        self.installing = False
        self.install_button.configure(state="normal")
        self.progress_label.configure(text="Installation stopped")
        messagebox.showerror("Installation failed", str(exc), parent=self)

    def _refresh_catalog(self) -> None:
        self.jobs.run(load_catalog, self._catalog_loaded)

    def _catalog_loaded(self, result) -> None:
        self.skins, self.catalog_source = result
        self.catalog_label.configure(text=self.catalog_source)
        if not self.selection:
            self.selection = Selection.from_skin(
                sort_skins(self.skins, self.sort_order.get())[0]
            )
        self._render_cards()
        self._render_install_panel()

    def _refresh_device(self) -> None:
        if self.demo:
            self.device_status = DeviceStatus(False, 0, "Demo mode")
            self.device_label.configure(
                text="●  Demo mode — no device writes",
                fg=COLORS["warning"],
            )
            return
        self.device_label.configure(text="●  Checking for CPPRO…", fg=COLORS["muted"])
        self.jobs.run(detect_device, self._device_loaded)

    def _device_loaded(self, status: DeviceStatus) -> None:
        self.device_status = status
        self.device_label.configure(
            text=("●  CPPRO connected" if status.connected else "●  CPPRO not found"),
            fg=COLORS["success"] if status.connected else COLORS["danger"],
        )


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--demo", action="store_true")
    args, _ = parser.parse_known_args()
    enable_windows_dpi_awareness()
    app = SkinLibrary(demo=args.demo)
    app.mainloop()
    return 0

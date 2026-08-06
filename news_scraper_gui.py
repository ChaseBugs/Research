"""Windows GUI: a four-tab research workbench.

Tabs:
- **Scrapping** -- collect public news articles (the original tool).
- **Generate** -- turn a keyword into technology topics and AI-written illustrated
  documents.
- **Source Books** -- download full-text patent/paper PDFs for a keyword.
- **History** -- history and counts of everything downloaded.

All tabs share one workspace folder and one SQLite activity ledger
(``research_ledger.db`` in that folder). The ledger gives cross-tab, cross-day
de-duplication and feeds the History tab. Each tab runs its slow work on a daemon
thread via ``WorkerTab``; widgets are only ever touched from the Tk thread.
"""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, ttk
import tkinter as tk
from tkinter import font as tkfont

from activity_log import ActivityLog
from tab_download import DownloadTab
from tab_generate import GenerateTab
from tab_history import HistoryTab
from tab_scrape import ScrapeTab


class ResearchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self._configure_fonts()
        self.title("Research Collection & Generation")
        self.geometry("1020x780")
        self.minsize(900, 680)

        self.base_dir_var = tk.StringVar(value=str(Path.cwd()))
        self.activity = ActivityLog.load(self.base_dir())

        self._build()

    def _configure_fonts(self) -> None:
        """Use a comfortably readable font size throughout the application."""
        size = 12
        font_names = (
            "TkDefaultFont",
            "TkTextFont",
            "TkFixedFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
        )
        for name in font_names:
            try:
                tkfont.nametofont(name).configure(size=size)
            except tk.TclError:
                pass

        style = ttk.Style(self)
        style.configure(".", font=("Segoe UI", size))
        style.configure("TNotebook.Tab", font=("Segoe UI", size))
        style.configure("Treeview", font=("Segoe UI", size), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", size, "bold"))

    # ------------------------------------------------------------ shared state
    def base_dir(self) -> Path:
        return Path(self.base_dir_var.get())

    def subdir(self, name: str) -> Path:
        """A per-purpose folder under the workspace (e.g. Scraped_News)."""
        return self.base_dir() / name

    def refresh_history(self) -> None:
        """Redraw the History tab after any tab produces new artifacts."""
        if getattr(self, "history_tab", None) is not None:
            self.history_tab.refresh()

    def _reload_workspace(self) -> None:
        self.activity = ActivityLog.load(self.base_dir())
        self.refresh_history()

    # ------------------------------------------------------------------ layout
    def _build(self) -> None:
        top = ttk.Frame(self, padding=(12, 10, 12, 4))
        top.pack(fill="x")
        ttk.Label(top, text="Workspace folder").pack(side="left")
        ttk.Entry(top, textvariable=self.base_dir_var).pack(side="left", fill="x",
                                                            expand=True, padx=(8, 8))
        ttk.Button(top, text="Change", command=self._choose_base).pack(side="left")
        ttk.Button(top, text="Open", command=self._open_base).pack(side="left", padx=(6, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.scrape_tab = ScrapeTab(notebook, self)
        self.generate_tab = GenerateTab(notebook, self)
        self.download_tab = DownloadTab(notebook, self)
        self.history_tab = HistoryTab(notebook, self)

        notebook.add(self.scrape_tab, text="Scrapping")
        notebook.add(self.generate_tab, text="Generate")
        notebook.add(self.download_tab, text="Source Books")
        notebook.add(self.history_tab, text="History")
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self._notebook = notebook

    def _on_tab_change(self, _event) -> None:
        if self._notebook.nametowidget(self._notebook.select()) is self.history_tab:
            self.history_tab.refresh()

    def _choose_base(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.base_dir_var.get())
        if selected:
            self.base_dir_var.set(selected)
            self._reload_workspace()

    def _open_base(self) -> None:
        path = self.base_dir()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]


if __name__ == "__main__":
    ResearchApp().mainloop()

"""History tab -- everything this program has downloaded, counted over time.

Reads the shared activity ledger and shows two views for a chosen date range:

- a **summary** table of counts per period (day / week / month) split by kind
  (collected articles / generated documents / source books) with a total column, and
- a **detail** list of the individual artifacts in range.

It does no network work; ``refresh()`` just re-reads the in-memory ledger, so the
app calls it after every scrape / generate / download to keep counts current.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from tkinter import ttk
import tkinter as tk

from activity_log import KINDS

_KIND_ORDER = ("scrape", "generate", "book")


class HistoryTab(ttk.Frame):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=14)
        self.app = app
        self.start_var = tk.StringVar(value=(date.today() - timedelta(days=30)).isoformat())
        self.end_var = tk.StringVar(value=date.today().isoformat())
        self.gran_var = tk.StringVar(value="day")
        self.total_var = tk.StringVar(value="")
        self.columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self) -> None:
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Label(controls, text="Start").pack(side="left")
        ttk.Entry(controls, textvariable=self.start_var, width=12).pack(side="left", padx=(4, 10))
        ttk.Label(controls, text="End").pack(side="left")
        ttk.Entry(controls, textvariable=self.end_var, width=12).pack(side="left", padx=(4, 12))
        for label, value in (("Daily", "day"), ("Weekly", "week"), ("Monthly", "month")):
            ttk.Radiobutton(controls, text=label, value=value, variable=self.gran_var,
                            command=self.refresh).pack(side="left")
        ttk.Button(controls, text="Refresh", command=self.refresh).pack(side="left", padx=(12, 0))
        ttk.Label(controls, textvariable=self.total_var, foreground="#2468a2").pack(side="right")

        # summary: counts per period
        ttk.Label(self, text="Counts by period").grid(row=1, column=0, sticky="w", pady=(10, 2))
        sum_frame = ttk.Frame(self)
        sum_frame.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        cols = ("period", "scrape", "generate", "book", "total")
        headings = ("Period", KINDS["scrape"], KINDS["generate"], KINDS["book"], "Total")
        self.summary = ttk.Treeview(sum_frame, columns=cols, show="headings", height=7)
        for c, h in zip(cols, headings):
            self.summary.heading(c, text=h)
            self.summary.column(c, width=90 if c != "period" else 130,
                                anchor="center" if c != "period" else "w")
        ssb = ttk.Scrollbar(sum_frame, command=self.summary.yview)
        self.summary.configure(yscrollcommand=ssb.set)
        self.summary.pack(side="left", fill="both", expand=True)
        ssb.pack(side="right", fill="y")

        # detail: individual items
        ttk.Label(self, text="Items (double-click to open folder)").grid(row=3, column=0, sticky="w", pady=(10, 2))
        det_frame = ttk.Frame(self)
        det_frame.grid(row=4, column=0, sticky="nsew")
        self.rowconfigure(4, weight=2)
        dcols = ("date", "kind", "title", "source")
        self.detail = ttk.Treeview(det_frame, columns=dcols, show="headings", height=10)
        for c, h, w in (("date", "Date", 90), ("kind", "Type", 120),
                        ("title", "Title", 460), ("source", "Source", 130)):
            self.detail.heading(c, text=h)
            self.detail.column(c, width=w, anchor="w")
        dsb = ttk.Scrollbar(det_frame, command=self.detail.yview)
        self.detail.configure(yscrollcommand=dsb.set)
        self.detail.pack(side="left", fill="both", expand=True)
        dsb.pack(side="right", fill="y")
        self.detail.bind("<Double-1>", self._open_selected)
        self._paths: dict[str, str] = {}

    # ------------------------------------------------------------------ helpers
    def _range(self) -> tuple[date | None, date | None]:
        def parse(v):
            try:
                return date.fromisoformat(v.strip())
            except ValueError:
                return None
        return parse(self.start_var.get()), parse(self.end_var.get())

    def refresh(self) -> None:
        start, end = self._range()
        log = self.app.activity
        # summary
        self.summary.delete(*self.summary.get_children())
        for period, counter in log.counts_by_period(self.gran_var.get(), start, end):
            total = sum(counter.values())
            self.summary.insert("", "end", values=(
                period, counter.get("scrape", 0), counter.get("generate", 0),
                counter.get("book", 0), total))
        # detail (newest first)
        self.detail.delete(*self.detail.get_children())
        self._paths.clear()
        rows = sorted(log.filtered(start, end), key=lambda e: e.ts, reverse=True)
        for e in rows:
            iid = self.detail.insert("", "end", values=(
                e.day.isoformat(), KINDS.get(e.kind, e.kind), e.title[:90], e.source[:30]))
            self._paths[iid] = e.path
        totals = log.totals(start, end)
        self.total_var.set(
            f"Total {sum(totals.values())}  ·  " +
            "  ".join(f"{KINDS[k]} {totals.get(k, 0)}" for k in _KIND_ORDER))

    def _open_selected(self, _event) -> None:
        sel = self.detail.selection()
        if not sel:
            return
        path = self._paths.get(sel[0], "")
        if not path:
            return
        folder = Path(path).parent
        if folder.exists():
            os.startfile(folder)  # type: ignore[attr-defined]

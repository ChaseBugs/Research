"""Scrapping tab -- the original news-scraper UI, hosted inside the notebook.

Behaviour is unchanged from the standalone window: pick a field, pick a site (or
'★ All sites in this field' for the whole field), a date range and options, then collect. The
only addition is that each saved article is also recorded in the shared activity
ledger so the History tab can count it.
"""

from __future__ import annotations

import os
import queue
import threading
from datetime import date, timedelta
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

from article_filter import DEFAULT_KEYWORD_FILE, KeywordFilter
from gui_common import WorkerTab
from news_scraper import DEFAULT_LIMIT, scrape, scrape_field
from sites import FIELDS, SITES, register_site, sites_in_field

ALL_SITES_PREFIX = "★ All sites in this field"


class ScrapeTab(WorkerTab):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, app)
        self.field_labels = {label: key for key, label in FIELDS.items()}
        self.field_var = tk.StringVar(value=next(iter(self.field_labels)))
        self.site_var = tk.StringVar()
        self.start_var = tk.StringVar(value=(date.today() - timedelta(days=7)).isoformat())
        self.end_var = tk.StringVar(value=date.today().isoformat())
        self.limit_var = tk.StringVar(value=str(DEFAULT_LIMIT))
        self.skip_seen_var = tk.BooleanVar(value=True)
        self.classify_var = tk.BooleanVar(value=False)
        self._build()
        self._refresh_sites()

    def _build(self) -> None:
        f = self.top
        ttk.Label(f, text="Field").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        fb = ttk.Combobox(f, textvariable=self.field_var, values=list(self.field_labels),
                          state="readonly")
        fb.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        fb.bind("<<ComboboxSelected>>", self._refresh_sites)

        ttk.Label(f, text="News site").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        site_row = ttk.Frame(f)
        site_row.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        site_row.columnconfigure(0, weight=1)
        self.site_box = ttk.Combobox(site_row, textvariable=self.site_var, state="readonly")
        self.site_box.grid(row=0, column=0, sticky="ew")
        self.site_box.bind("<<ComboboxSelected>>", self._show_homepage)
        ttk.Button(site_row, text="＋ Add site",
                   command=self._open_add_site).grid(row=0, column=1, padx=(6, 0))

        self.homepage = ttk.Label(f, text="", foreground="#2468a2")
        self.homepage.grid(row=2, column=1, columnspan=2, sticky="w")
        self.warning = ttk.Label(f, text="", foreground="#b06a00")
        self.warning.grid(row=3, column=1, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(f, text="Start date").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(f, textvariable=self.start_var).grid(row=4, column=1, sticky="ew", pady=5)
        ttk.Label(f, text="YYYY-MM-DD").grid(row=4, column=2, sticky="w", padx=(8, 0))
        ttk.Label(f, text="End date").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Entry(f, textvariable=self.end_var).grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Label(f, text="YYYY-MM-DD").grid(row=5, column=2, sticky="w", padx=(8, 0))

        opts = ttk.Frame(f)
        opts.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Label(opts, text="Maximum articles per site").pack(side="left")
        ttk.Spinbox(opts, from_=0, to=1000, increment=10, width=7,
                    textvariable=self.limit_var).pack(side="left", padx=(8, 4))
        ttk.Label(opts, text="(0 = unlimited)").pack(side="left")
        ttk.Checkbutton(opts, text="Skip previously collected articles",
                        variable=self.skip_seen_var).pack(side="left", padx=(16, 0))

        opts2 = ttk.Frame(f)
        opts2.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        ttk.Checkbutton(opts2, text="Separate technology articles only (news articles go to _news_only; classified by Groq/g4f)",
                        variable=self.classify_var).pack(side="left")

        ctrl = ttk.Frame(f)
        ctrl.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(10, 4))
        self.start_button = ttk.Button(ctrl, text="Start collection", command=self._start)
        self.start_button.pack(side="left")
        ttk.Button(ctrl, text="Open output folder", command=self._open_output).pack(side="left", padx=8)
        ttk.Button(ctrl, text="Edit keyword file", command=self._edit_keywords).pack(side="left")

    # -------------------------------------------------------------- site picker
    def _field_key(self) -> str:
        return self.field_labels[self.field_var.get()]

    def _refresh_sites(self, _e=None) -> None:
        members = sites_in_field(self._field_key())
        values = [f"{ALL_SITES_PREFIX} ({len(members)} sites)"] + [s.name for s in members]
        self.site_box.configure(values=values)
        self.site_var.set(values[0])
        self._show_homepage()

    def _open_add_site(self) -> None:
        AddSiteDialog(self, self._field_key(), on_added=self._site_added)

    def _site_added(self, site) -> None:
        """Refresh the picker to the field of the newly added site and select it."""
        for label, key in self.field_labels.items():
            if key == site.field:
                self.field_var.set(label)
                break
        self._refresh_sites()
        self.site_var.set(site.name)
        self._show_homepage()

    def _is_whole_field(self) -> bool:
        return self.site_var.get().startswith(ALL_SITES_PREFIX)

    def _show_homepage(self, _e=None) -> None:
        if self._is_whole_field():
            members = sites_in_field(self._field_key())
            self.homepage.configure(text=f"Collecting {len(members)} sites at once")
            thin = [s.name for s in members if s.low_volume]
            self.warning.configure(text=(f"Low volume: {', '.join(thin)}" if thin else ""))
            return
        site = SITES[self.site_var.get()]
        self.homepage.configure(text=site.homepage)
        self.warning.configure(text="This site updates infrequently" if site.low_volume else "")

    def _output_dir(self) -> Path:
        return self.app.subdir("Scraped_News")

    def _open_output(self) -> None:
        path = self._output_dir()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]

    def _edit_keywords(self) -> None:
        if not DEFAULT_KEYWORD_FILE.exists():
            DEFAULT_KEYWORD_FILE.write_text("# Excluded keywords\n", encoding="utf-8")
        os.startfile(DEFAULT_KEYWORD_FILE)  # type: ignore[attr-defined]

    # --------------------------------------------------------------------- run
    def _start(self) -> None:
        try:
            start = date.fromisoformat(self.start_var.get().strip())
            end = date.fromisoformat(self.end_var.get().strip())
            if start > end:
                raise ValueError("Start date cannot be after end date.")
        except ValueError as exc:
            messagebox.showerror("Date Error", f"Enter dates as YYYY-MM-DD.\n{exc}")
            return
        try:
            limit = int(self.limit_var.get().strip() or 0)
            if limit < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Maximum articles must be a non-negative integer.")
            return

        output = self._output_dir()
        whole = self._is_whole_field()
        target = self._field_key() if whole else self.site_var.get()
        if whole:
            n = len(sites_in_field(target))
            if not messagebox.askyesno("Collect Entire Field",
                                       f"This will collect all {n} sites in {self.field_var.get()}.\nContinue?"):
                return

        classifier, backend = self._build_classifier()
        if classifier is False:   # user wanted classification but no key
            return

        self.clear_log()
        self.log(f"{self.field_var.get()} / {'Entire field' if whole else target} / {start} ~ {end}")
        keyword_filter = KeywordFilter.from_file()
        ledger = self.app.activity          # global SQLite ledger, shared across tabs
        skip_dup = self.skip_seen_var.get()  # dedup spans every past run (any day)

        def work(emit):
            if keyword_filter:
                emit(f"Applied {len(keyword_filter)} excluded keywords")
            if skip_dup:
                emit(f"Collection history: {len(ledger.entries())} entries (global duplicate skipping)")
            if classifier is not None:
                emit(f"Technology/news classification enabled ({backend}); news articles go to _news_only")
            if whole:
                return scrape_field(target, start, end, output, emit, limit=limit or None,
                                    keyword_filter=keyword_filter, ledger=ledger,
                                    skip_duplicates=skip_dup, classifier=classifier)
            return scrape(target, start, end, output, emit, limit=limit or None,
                          keyword_filter=keyword_filter, ledger=ledger,
                          skip_duplicates=skip_dup, classifier=classifier)

        self.run_worker(work, on_done=self._done, manage=(self.start_button,), status="Collecting...")

    def _build_classifier(self):
        """Return (classifier_or_None, backend_name).

        Returns (False, "") when the user asked for classification but no usable
        backend/key is available, so the caller aborts and shows the warning.
        """
        if not self.classify_var.get():
            return None, ""
        from ai_client import AIClient, load_ai_config
        from relevance import is_technical
        cfg = load_ai_config()
        if cfg["backend"] == "groq" and not cfg["groq_api_key"]:
            messagebox.showwarning(
                "Classification Engine Key Required",
                "A Groq API key is required for technology/news classification.\n"
                "Enter it on the Generate tab or set GROQ_API_KEY in .env.\n"
                "(To run without a key, change the Generate tab engine to g4f.)")
            return False, ""
        ai = AIClient(backend=cfg["backend"], groq_api_key=cfg["groq_api_key"])
        return (lambda title, body: is_technical(ai, title, body)), cfg["backend"]

    def _done(self, result) -> None:
        errors = getattr(result, "site_errors", {})
        tech = result.saved - getattr(result, "news", 0)
        msg = f"Saved {result.saved}, skipped {result.skipped}, failed {result.failed}"
        if self.classify_var.get():
            msg += f"  (technology {tech}, news {getattr(result, 'news', 0)})"
        if errors:
            msg += f", site errors {len(errors)}"
        self.log(f"== {msg} ==")
        self.app.refresh_history()
        messagebox.showinfo("Collection Complete", f"{msg}\n{result.folder}")


class AddSiteDialog(tk.Toplevel):
    """Modal form to verify and add a new site.

    The user supplies only a name and an RSS feed URL; verification probes the
    feed and auto-discovers a body selector (see ``site_probe``). It runs on a
    daemon thread and reports back through a queue polled on the Tk thread, so the
    window stays responsive. Only a site that passes verification is added.
    """

    def __init__(self, master, field_key: str, on_added) -> None:
        super().__init__(master)
        self.on_added = on_added
        self.title("Add News Site")
        self.transient(master)
        self.resizable(False, False)
        self.field_labels = {label: key for key, label in FIELDS.items()}
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()

        init_label = next((l for l, k in self.field_labels.items() if k == field_key),
                          next(iter(self.field_labels)))
        self.field_var = tk.StringVar(value=init_label)
        self.name_var = tk.StringVar()
        self.feed_var = tk.StringVar()
        self.homepage_var = tk.StringVar()

        frame = ttk.Frame(self, padding=16)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Field").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Combobox(frame, textvariable=self.field_var, values=list(self.field_labels),
                     state="readonly", width=32).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Site name").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(frame, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="RSS feed URL").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(frame, textvariable=self.feed_var, width=44).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Homepage (optional)").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(frame, textvariable=self.homepage_var).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="The article-body selector is detected automatically during verification.",
                  foreground="#777").grid(row=4, column=1, sticky="w")

        self.status_var = tk.StringVar(value="Enter a site name and RSS feed URL, then verify it.")
        ttk.Label(frame, textvariable=self.status_var, foreground="#2468a2",
                  wraplength=380).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 4))
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e")
        self.verify_button = ttk.Button(buttons, text="Verify and add", command=self._verify)
        self.verify_button.pack(side="left")
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="left", padx=(8, 0))

        self.grab_set()
        self.after(100, self._poll)

    def _verify(self) -> None:
        from site_probe import probe_new_site  # local import keeps startup light
        field_key = self.field_labels[self.field_var.get()]
        name = self.name_var.get().strip()
        feed = self.feed_var.get().strip()
        homepage = self.homepage_var.get().strip()
        if not name or not feed:
            messagebox.showerror("Input Required", "Enter a site name and RSS feed URL.", parent=self)
            return
        self.verify_button.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Verifying... checking the feed and article body.")

        def work() -> None:
            try:
                outcome = probe_new_site(name, feed, field_key, homepage,
                                         log=lambda m: self._events.put(("log", m)))
                self._events.put(("result", outcome))
            except Exception as exc:
                self._events.put(("error", f"{type(exc).__name__}: {exc}"))

        threading.Thread(target=work, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self._events.get_nowait()
                if kind == "log":
                    self.status_var.set(str(value))
                elif kind == "error":
                    self._reset()
                    messagebox.showerror("Verification Error", str(value), parent=self)
                elif kind == "result":
                    self._reset()
                    self._handle(value)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _handle(self, outcome) -> None:
        if outcome.site is None:
            messagebox.showerror("Cannot Add Site",
                                 f"This site cannot be collected.\n\n{outcome.reason}", parent=self)
            self.status_var.set("Verification failed. Check the URL and try again.")
            return
        register_site(outcome.site)
        messagebox.showinfo(
            "Site Added",
            f"Added '{outcome.site.name}'.\n\n"
            f"Article-body selector: {outcome.selector}\n"
            f"Verified article body: {outcome.chars} characters, {outcome.images} images",
            parent=self)
        self.on_added(outcome.site)
        self.destroy()

    def _reset(self) -> None:
        self.progress.stop()
        self.verify_button.configure(state="normal")

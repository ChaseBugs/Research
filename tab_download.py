"""Source Books tab -- download full-text PDFs for a keyword from legal open sources.

Search Google Patents and/or arXiv for the keyword, then download the resulting
PDFs into ``Source_Books/<keyword>_<date>/``. Korean-titled or Korean-published
results are filtered out, and anything already downloaded (tracked in the activity
ledger) is skipped so repeated runs don't duplicate.

Only legal, openly downloadable sources are used -- patents are public documents
and arXiv is open access. Piracy mirrors (LibGen/Z-Library/Anna's/Sci-Hub) are
deliberately not integrated.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

from ai_client import make_session
from book_downloader import download, safe_filename, search
from gui_common import WorkerTab


class DownloadTab(WorkerTab):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, app)
        self.keyword_var = tk.StringVar()
        self.patents_var = tk.BooleanVar(value=True)
        self.arxiv_var = tk.BooleanVar(value=True)
        self.limit_var = tk.StringVar(value="25")
        self.results: list = []
        self._build()

    def _build(self) -> None:
        f = self.top
        ttk.Label(f, text="Keyword (technology)").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        entry = ttk.Entry(f, textvariable=self.keyword_var)
        entry.grid(row=0, column=1, sticky="ew", pady=5)
        entry.bind("<Return>", lambda _e: self._search())

        opts = ttk.Frame(f)
        opts.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        ttk.Checkbutton(opts, text="Patents (patents.google.com)",
                        variable=self.patents_var).pack(side="left")
        ttk.Checkbutton(opts, text="arXiv papers", variable=self.arxiv_var).pack(side="left", padx=(12, 0))
        ttk.Label(opts, text="Result count").pack(side="left", padx=(16, 4))
        ttk.Spinbox(opts, from_=5, to=100, increment=5, width=6,
                    textvariable=self.limit_var).pack(side="left")
        self.search_button = ttk.Button(opts, text="Search", command=self._search)
        self.search_button.pack(side="left", padx=(12, 0))

        ttk.Label(f, text="Search results").grid(row=2, column=0, sticky="nw", pady=(6, 0))
        list_frame = ttk.Frame(f)
        list_frame.grid(row=2, column=1, sticky="nsew", pady=(6, 0))
        f.rowconfigure(2, weight=1)
        self.result_list = tk.Listbox(list_frame, height=9, selectmode="extended")
        scroll = ttk.Scrollbar(list_frame, command=self.result_list.yview)
        self.result_list.configure(yscrollcommand=scroll.set)
        self.result_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        row = ttk.Frame(f)
        row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        self.download_button = ttk.Button(row, text="Download selected PDFs", command=lambda: self._download(False))
        self.download_button.pack(side="left")
        self.download_all_button = ttk.Button(row, text="Download all", command=lambda: self._download(True))
        self.download_all_button.pack(side="left", padx=8)
        ttk.Button(row, text="Open output folder", command=self._open_output).pack(side="left")
        ttk.Label(f, text="If nothing is selected, Download all retrieves every search result.",
                  foreground="#777").grid(row=4, column=1, sticky="w")

    # -------------------------------------------------------------------- utils
    def _keyword(self) -> str:
        return self.keyword_var.get().strip()

    def _providers(self) -> set[str]:
        p = set()
        if self.patents_var.get():
            p.add("patent")
        if self.arxiv_var.get():
            p.add("arxiv")
        return p

    def _output_dir(self) -> Path:
        import re
        stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", self._keyword()).strip() or "keyword"
        return self.app.subdir("Source_Books") / f"{stem[:60]}_{date.today().isoformat()}"

    def _open_output(self) -> None:
        path = self._output_dir()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ search
    def _search(self) -> None:
        keyword = self._keyword()
        if not keyword:
            messagebox.showwarning("Input Required", "Enter a keyword.")
            return
        providers = self._providers()
        if not providers:
            messagebox.showwarning("Select Sources", "Select patents, arXiv, or both.")
            return
        limit = int(self.limit_var.get() or 25)
        self.clear_log()
        self.result_list.delete(0, "end")
        self.results = []
        self.log(f"Searching for '{keyword}'...")
        session = make_session()

        def work(emit):
            return search(session, keyword, providers, limit=limit, log=emit)

        self.run_worker(work, on_done=self._search_done,
                        manage=(self.search_button, self.download_button, self.download_all_button),
                        status="Searching...")

    def _search_done(self, results: list) -> None:
        self.results = results
        self.result_list.delete(0, "end")
        for r in results:
            tag = "Patent" if r.provider == "patent" else "arXiv"
            self.result_list.insert("end", f"[{tag}] {r.ident}  {r.title[:70]}")
        self.log(f"== {len(results)} search results ==")
        if not results:
            messagebox.showinfo("No Results", "No search results. Try another keyword or source.")

    # ---------------------------------------------------------------- download
    def _download(self, everything: bool) -> None:
        if not self.results:
            messagebox.showwarning("No Results", "Search first.")
            return
        if everything:
            picks = list(self.results)
        else:
            idx = self.result_list.curselection()
            if not idx:
                messagebox.showwarning("No Selection", "Select items or click Download all.")
                return
            picks = [self.results[i] for i in idx]

        keyword = self._keyword()
        output = self._output_dir()
        output.mkdir(parents=True, exist_ok=True)
        ledger = self.app.activity
        session = make_session()
        self.log(f"\nDownloading {len(picks)} items -> {output}")

        def work(emit):
            used: set[str] = set()
            got = skipped = failed = 0
            for book in picks:
                if ledger.seen_key("book", book.ident):
                    emit(f"Skipped (already downloaded): {book.ident}")
                    skipped += 1
                    continue
                target = output / safe_filename(book.ident, book.title, used, output)
                try:
                    size = download(session, book, target)
                    emit(f"Downloaded: {target.name[:60]} ({size // 1024} KB)")
                    ledger.record("book", f"{book.ident} {book.title}", key=book.ident,
                                  path=str(target), source=book.provider, keyword=keyword)
                    got += 1
                except Exception as exc:
                    emit(f"Failed: {book.ident} - {type(exc).__name__}: {exc}")
                    failed += 1
            return got, skipped, failed, output

        self.run_worker(work, on_done=self._download_done,
                        manage=(self.search_button, self.download_button, self.download_all_button),
                        status="Downloading...")

    def _download_done(self, result) -> None:
        got, skipped, failed, output = result
        self.log(f"== Download complete: downloaded {got}, skipped {skipped}, failed {failed} ==")
        self.app.refresh_history()
        messagebox.showinfo("Download Complete",
                            f"Downloaded {got}, skipped {skipped}, failed {failed}\n{output}")

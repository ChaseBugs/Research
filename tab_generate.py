"""Generate tab -- keyword to a list of technologies, then to illustrated documents.

Flow matches the two buttons:

1. Enter a keyword (e.g. "mining town modernization") and press **Generate topics**: the model returns up
   to N concrete technology titles, shown in the list.
2. Press **Generate documents**: for each listed topic not already generated before (checked
   against the activity ledger), a detailed beginner guide DOCX with AI images is
   written to ``Generated_Docs/<keyword>_<date>/``.

Text comes from g4f, images from Pollinations; both are free. Documents are English.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

from gui_common import WorkerTab
from tech_generator import generate_document, generate_topics, safe_filename


class GenerateTab(WorkerTab):
    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, app)
        from ai_client import load_ai_config
        cfg = load_ai_config()
        self.keyword_var = tk.StringVar()
        self.topic_count_var = tk.StringVar(value="100")
        self.doc_count_var = tk.StringVar(value="5")
        self.images_var = tk.BooleanVar(value=True)
        self.backend_var = tk.StringVar(value=cfg["backend"])
        self.groq_key_var = tk.StringVar(value=cfg["groq_api_key"])
        self.topics: list[str] = []
        self._build()
        self._sync_key_state()

    def _build(self) -> None:
        f = self.top
        ttk.Label(f, text="Keyword (technology)").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        entry = ttk.Entry(f, textvariable=self.keyword_var)
        entry.grid(row=0, column=1, sticky="ew", pady=5)
        entry.bind("<Return>", lambda _e: self._make_topics())
        ttk.Label(f, text="e.g. mining town modernization, diatomite utilization", foreground="#777").grid(
            row=1, column=1, sticky="w")

        # text backend picker: g4f (keyless) or Groq (free, needs API key)
        backend = ttk.Frame(f)
        backend.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(backend, text="Engine").pack(side="left")
        ttk.Radiobutton(backend, text="g4f (free)", value="g4f", variable=self.backend_var,
                        command=self._sync_key_state).pack(side="left", padx=(6, 0))
        ttk.Radiobutton(backend, text="Groq (free API key)", value="groq", variable=self.backend_var,
                        command=self._sync_key_state).pack(side="left", padx=(6, 12))
        ttk.Label(backend, text="Groq key").pack(side="left")
        self.groq_entry = ttk.Entry(backend, textvariable=self.groq_key_var, width=28, show="•")
        self.groq_entry.pack(side="left", padx=(4, 0))

        row = ttk.Frame(f)
        row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        ttk.Label(row, text="Topic count").pack(side="left")
        ttk.Spinbox(row, from_=5, to=100, increment=5, width=6,
                    textvariable=self.topic_count_var).pack(side="left", padx=(6, 12))
        self.topics_button = ttk.Button(row, text="Generate topics", command=self._make_topics)
        self.topics_button.pack(side="left")

        ttk.Label(f, text="Generated technology topics").grid(row=4, column=0, sticky="nw", pady=(6, 0))
        list_frame = ttk.Frame(f)
        list_frame.grid(row=4, column=1, sticky="nsew", pady=(6, 0))
        f.rowconfigure(4, weight=1)
        self.topic_list = tk.Listbox(list_frame, height=8)
        scroll = ttk.Scrollbar(list_frame, command=self.topic_list.yview)
        self.topic_list.configure(yscrollcommand=scroll.set)
        self.topic_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        row2 = ttk.Frame(f)
        row2.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        ttk.Label(row2, text="Documents to generate").pack(side="left")
        ttk.Spinbox(row2, from_=1, to=100, increment=1, width=6,
                    textvariable=self.doc_count_var).pack(side="left", padx=(6, 12))
        ttk.Checkbutton(row2, text="Include images", variable=self.images_var).pack(side="left")
        self.docs_button = ttk.Button(row2, text="Generate documents", command=self._make_docs)
        self.docs_button.pack(side="left", padx=(12, 0))
        ttk.Button(row2, text="Open output folder", command=self._open_output).pack(side="left", padx=8)

    # -------------------------------------------------------------------- utils
    def _sync_key_state(self) -> None:
        """Enable the Groq key field only when Groq is the chosen backend."""
        self.groq_entry.configure(state="normal" if self.backend_var.get() == "groq" else "disabled")

    def _build_client(self):
        """Construct an AIClient from the current backend choice, or None if invalid.

        Also persists the choice + key so the next launch remembers them.
        """
        from ai_client import AIClient, save_ai_config
        backend = self.backend_var.get()
        key = self.groq_key_var.get().strip()
        if backend == "groq" and not key:
            messagebox.showwarning("Groq API Key Required",
                                   "Groq is free, but requires an API key.\n"
                                   "Create one at console.groq.com and enter it here.")
            return None
        save_ai_config(backend, key)
        return AIClient(backend=backend, groq_api_key=key)

    def _keyword(self) -> str:
        return self.keyword_var.get().strip()

    def _output_dir(self) -> Path:
        return self.app.subdir("Generated_Docs") / self._safe_folder()

    def _safe_folder(self) -> str:
        import re
        stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", self._keyword()).strip() or "keyword"
        return f"{stem[:60]}_{date.today().isoformat()}"

    def _open_output(self) -> None:
        path = self._output_dir()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # type: ignore[attr-defined]

    # ------------------------------------------------------------- topic stage
    def _make_topics(self) -> None:
        keyword = self._keyword()
        if not keyword:
            messagebox.showwarning("Input Required", "Enter a keyword.")
            return
        ai = self._build_client()
        if ai is None:
            return
        count = int(self.topic_count_var.get() or 100)
        self.clear_log()
        self.topic_list.delete(0, "end")
        self.topics = []
        self.log(f"[{self.backend_var.get()}] Generating {count} topics related to '{keyword}'...")

        def work(emit):
            return generate_topics(ai, keyword, count=count, log=emit)

        self.run_worker(work, on_done=self._topics_done,
                        manage=(self.topics_button, self.docs_button), status="Generating topics...")

    def _topics_done(self, topics: list[str]) -> None:
        self.topics = topics
        self.topic_list.delete(0, "end")
        for i, topic in enumerate(topics, 1):
            self.topic_list.insert("end", f"{i:3}. {topic}")
        self.log(f"== Generated {len(topics)} topics ==")
        if not topics:
            messagebox.showwarning("No Results", "No topics were generated. Please try again shortly.")

    # ------------------------------------------------------------ document stage
    def _make_docs(self) -> None:
        if not self.topics:
            messagebox.showwarning("No Topics", "Generate a topic list first.")
            return
        ai = self._build_client()
        if ai is None:
            return
        keyword = self._keyword()
        max_docs = int(self.doc_count_var.get() or 1)
        with_images = self.images_var.get()
        output = self._output_dir()
        output.mkdir(parents=True, exist_ok=True)
        ledger = self.app.activity
        topics = list(self.topics)

        self.log(f"\n[{self.backend_var.get()}] Document generation started: up to {max_docs} -> {output}")

        def work(emit):
            used: set[str] = set()
            made = skipped = failed = 0
            for topic in topics:
                if made >= max_docs:
                    break
                if ledger.seen_title("generate", topic):
                    emit(f"Skipped (already generated): {topic}")
                    skipped += 1
                    continue
                target = output / safe_filename(topic, used, output)
                try:
                    images, title = generate_document(ai, topic, keyword, target,
                                                      with_images=with_images, log=emit)
                    ledger.record("generate", title, path=str(target),
                                  source="pollinations+g4f", keyword=keyword)
                    made += 1
                except Exception as exc:
                    emit(f"Failed: {topic} - {type(exc).__name__}: {exc}")
                    failed += 1
            return made, skipped, failed, output

        self.run_worker(work, on_done=self._docs_done,
                        manage=(self.topics_button, self.docs_button), status="Generating documents...")

    def _docs_done(self, result) -> None:
        made, skipped, failed, output = result
        self.log(f"== Document generation complete: generated {made}, skipped {skipped}, failed {failed} ==")
        self.app.refresh_history()
        messagebox.showinfo("Document Generation Complete",
                            f"Generated {made}, skipped {skipped}, failed {failed}\n{output}")

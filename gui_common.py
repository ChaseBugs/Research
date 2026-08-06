"""Shared plumbing for the notebook tabs.

Every tab does the same dance: run slow network/AI work on a daemon thread, and
push results back to the Tk thread through a ``queue.Queue`` drained by a periodic
``after()`` poll -- because Tk widgets must only be touched from the main thread.
``WorkerTab`` captures that pattern once so each tab only writes its own controls
and its ``on_done`` handler.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable


class WorkerTab(ttk.Frame):
    """A notebook tab with a background-worker helper and a shared log console.

    Subclasses build their controls into ``self.top`` and call ``run_worker`` to
    launch background jobs; the worker function receives an ``emit`` callback for
    log lines and returns a value delivered to ``on_done`` on the Tk thread.
    """

    def __init__(self, master: tk.Misc, app: "object") -> None:
        super().__init__(master, padding=14)
        self.app = app
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._busy = False
        self._managed: tuple[ttk.Widget, ...] = ()

        self.columnconfigure(0, weight=1)
        self.top = ttk.Frame(self)
        self.top.grid(row=0, column=0, sticky="nsew")
        self.top.columnconfigure(1, weight=1)

        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        bar.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(bar, mode="indeterminate")
        self.progress.grid(row=0, column=0, sticky="ew")
        self.status = tk.StringVar(value="Idle")
        ttk.Label(bar, textvariable=self.status).grid(row=0, column=1, padx=(10, 0))

        self.console = tk.Text(self, height=12, wrap="word", state="disabled")
        self.console.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)

        self.after(100, self._poll_events)

    # ------------------------------------------------------------------ logging
    def log(self, message: str) -> None:
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def clear_log(self) -> None:
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    # ------------------------------------------------------------------- worker
    def run_worker(self, target: Callable[[Callable[[str], None]], object],
                   on_done: Callable[[object], None] | None = None,
                   manage: tuple[ttk.Widget, ...] = (),
                   status: str = "Working...") -> bool:
        """Run ``target(emit)`` on a daemon thread. Returns False if already busy.

        ``manage`` widgets are disabled for the duration. Results flow back as
        ("log"|"done"|"error", value) tuples drained by ``_poll_events``.
        """
        if self._busy:
            self.log("A task is already running.")
            return False
        self._busy = True
        self._managed = manage
        self._on_done = on_done
        for widget in manage:
            widget.configure(state="disabled")
        self.progress.start(12)
        self.status.set(status)

        def runner() -> None:
            try:
                result = target(lambda msg: self.events.put(("log", msg)))
                self.events.put(("done", result))
            except Exception as exc:  # surfaced to the user, never crashes the thread
                self.events.put(("error", f"{type(exc).__name__}: {exc}"))

        threading.Thread(target=runner, daemon=True).start()
        return True

    def _poll_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self.log(str(value))
                elif kind == "done":
                    self._finish()
                    if self._on_done:
                        self._on_done(value)
                elif kind == "error":
                    self._finish()
                    self.log(f"Error: {value}")
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _finish(self) -> None:
        self.progress.stop()
        self.status.set("Done")
        for widget in self._managed:
            widget.configure(state="normal")
        self._managed = ()
        self._busy = False

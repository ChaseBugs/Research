"""Global activity ledger (SQLite) shared by the Scrape, Generate and Download tabs.

Every artifact this program produces -- a scraped article DOCX, an AI-generated
document, a downloaded patent/paper PDF -- is one row in ``research_ledger.db`` at
the workspace root. Two things depend on it:

- **Deduplication that spans every run and every day.** Before doing work a tab
  asks ``seen_key`` / ``seen_title``; because the store is a single database at the
  workspace root (not a per-collection file), something collected yesterday is
  still recognised as a duplicate today.
- **The History tab**, which aggregates counts by day / week / month.

SQLite gives durable, concurrent-safe storage: writes from the GUI's worker
threads and reads from the Tk thread each open their own short-lived connection,
and WAL mode lets them proceed without blocking. Legacy JSON stores from earlier
versions (``activity_log.jsonl`` and ``Scraped_News/_history.json``) are imported
once, the first time the database is created, so existing dedup history carries
over.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from article_filter import normalize_title

DB_FILENAME = "research_ledger.db"

# The three artifact kinds and their labels for the History tab.
KINDS = {
    "scrape": "Collected articles",
    "generate": "Generated documents",
    "book": "Source books",
}


@dataclass(frozen=True)
class Activity:
    kind: str            # one of KINDS
    title: str
    key: str             # dedup key: url / publication number / normalized title
    path: str            # saved file path (may be "")
    source: str          # origin url / site / provider
    keyword: str         # the keyword/field that produced it
    ts: str              # ISO timestamp

    @property
    def day(self) -> date:
        return datetime.fromisoformat(self.ts).date()


class ActivityLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._write_lock = threading.Lock()
        self._init_db()

    # ------------------------------------------------------------------ set-up
    @classmethod
    def load(cls, base_dir: Path) -> "ActivityLog":
        return cls(Path(base_dir) / DB_FILENAME)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind       TEXT NOT NULL,
                    title      TEXT NOT NULL,
                    norm_title TEXT NOT NULL,
                    key        TEXT NOT NULL DEFAULT '',
                    path       TEXT NOT NULL DEFAULT '',
                    source     TEXT NOT NULL DEFAULT '',
                    keyword    TEXT NOT NULL DEFAULT '',
                    ts         TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kind_key ON activity(kind, key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kind_title ON activity(kind, norm_title)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON activity(ts)")
            fresh = conn.execute("SELECT COUNT(*) FROM activity").fetchone()[0] == 0
        if fresh:
            self._migrate_legacy()

    # -------------------------------------------------------------------- reads
    def seen_key(self, kind: str, key: str) -> bool:
        if not key:
            return False
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM activity WHERE kind=? AND key=? LIMIT 1",
                (kind, key)).fetchone()
        return row is not None

    def seen_title(self, kind: str, title: str) -> bool:
        norm = normalize_title(title)
        if not norm:
            return False
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM activity WHERE kind=? AND norm_title=? LIMIT 1",
                (kind, norm)).fetchone()
        return row is not None

    def entries(self) -> list[Activity]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT kind,title,key,path,source,keyword,ts FROM activity ORDER BY ts").fetchall()
        return [self._row(r) for r in rows]

    # ------------------------------------------------------------------- writes
    def record(self, kind: str, title: str, key: str = "", path: str | os.PathLike = "",
               source: str = "", keyword: str = "") -> Activity:
        """Insert one artifact and return it."""
        entry = Activity(
            kind=kind, title=title, key=key or normalize_title(title),
            path=str(path), source=source, keyword=keyword,
            ts=datetime.now().isoformat(timespec="seconds"),
        )
        with self._write_lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO activity(kind,title,norm_title,key,path,source,keyword,ts)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (entry.kind, entry.title, normalize_title(entry.title), entry.key,
                 entry.path, entry.source, entry.keyword, entry.ts))
        return entry

    # -------------------------------------------------------------- aggregation
    def filtered(self, start: date | None = None, end: date | None = None,
                 kinds: set[str] | None = None) -> list[Activity]:
        clauses, params = [], []
        if start:
            clauses.append("ts >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("ts < ?")   # < next day => the whole end day is included
            params.append(_next_day(end))
        if kinds:
            clauses.append(f"kind IN ({','.join('?' * len(kinds))})")
            params.extend(sorted(kinds))
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT kind,title,key,path,source,keyword,ts FROM activity"
                + where + " ORDER BY ts", params).fetchall()
        return [self._row(r) for r in rows]

    def counts_by_period(self, granularity: str, start: date | None = None,
                         end: date | None = None) -> list[tuple[str, Counter]]:
        """Return [(period_label, Counter(kind -> n)), ...] sorted by period."""
        buckets: dict[str, Counter] = {}
        for e in self.filtered(start, end):
            buckets.setdefault(self._period_label(e.day, granularity), Counter())[e.kind] += 1
        return sorted(buckets.items())

    def totals(self, start: date | None = None, end: date | None = None) -> Counter:
        c: Counter = Counter()
        for e in self.filtered(start, end):
            c[e.kind] += 1
        return c

    # ---------------------------------------------------------------- internals
    @staticmethod
    def _row(r: sqlite3.Row) -> Activity:
        return Activity(kind=r["kind"], title=r["title"], key=r["key"], path=r["path"],
                        source=r["source"], keyword=r["keyword"], ts=r["ts"])

    @staticmethod
    def _period_label(day: date, granularity: str) -> str:
        if granularity == "day":
            return day.isoformat()
        if granularity == "week":
            iso = day.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        if granularity == "month":
            return f"{day.year}-{day.month:02d}"
        raise ValueError(f"unknown granularity: {granularity}")

    # ------------------------------------------------------------------ migrate
    def _migrate_legacy(self) -> None:
        """One-time import of the old JSON stores into the fresh database."""
        rows: list[tuple] = []
        base = self.path.parent

        jsonl = base / "activity_log.jsonl"
        if jsonl.exists():
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rows.append(self._legacy_row(
                    d.get("kind", ""), d.get("title", ""), d.get("key", ""),
                    d.get("path", ""), d.get("source", ""), d.get("keyword", ""),
                    d.get("ts", "")))

        # scrape history lived per-collection as _history.json under the workspace.
        for hist in base.rglob("_history.json"):
            try:
                data = json.loads(hist.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for a in data.get("articles", []):
                rows.append(self._legacy_row(
                    "scrape", a.get("title", ""), a.get("url", ""), a.get("file", ""),
                    a.get("site", ""), "", a.get("scraped", "") or a.get("published", "")))

        # The same article can appear in both legacy stores; de-duplicate by
        # (kind, key) and (kind, norm_title) so migration doesn't double-count.
        deduped: list[tuple] = []
        seen_keys: set[tuple] = set()
        seen_titles: set[tuple] = set()
        for r in rows:
            kind, title, norm, key = r[0], r[1], r[2], r[3]
            if not kind or not (key or title):
                continue
            if key and (kind, key) in seen_keys:
                continue
            if norm and (kind, norm) in seen_titles:
                continue
            seen_keys.add((kind, key))
            seen_titles.add((kind, norm))
            deduped.append(r)
        if not deduped:
            return
        with self._write_lock, self._conn() as conn:
            conn.executemany(
                "INSERT INTO activity(kind,title,norm_title,key,path,source,keyword,ts)"
                " VALUES (?,?,?,?,?,?,?,?)", deduped)
        print(f"[activity_log] Migrated {len(deduped)} existing records to SQLite.")

    @staticmethod
    def _legacy_row(kind, title, key, path, source, keyword, ts) -> tuple:
        ts = ts or datetime.now().isoformat(timespec="seconds")
        return (kind, title, normalize_title(title), key or normalize_title(title),
                path, source, keyword, ts)


def _next_day(day: date) -> str:
    return date.fromordinal(day.toordinal() + 1).isoformat()

"""Keyword exclusion and title normalization for scraped/generated artifacts.

`KeywordFilter` screens articles by unwanted keyword. `normalize_title` produces
the comparison key the SQLite ledger (`activity_log.py`) uses for duplicate
detection. Duplicate *storage* now lives in that ledger, not here.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


DEFAULT_KEYWORD_FILE = Path(__file__).with_name("exclude_keywords.txt")
_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Collapse a title to a comparison key.

    Lowercases, strips punctuation and collapses whitespace so that the same story
    republished with different punctuation or spacing still compares equal.
    """
    folded = unicodedata.normalize("NFKC", title).casefold()
    return _WHITESPACE.sub(" ", _PUNCTUATION.sub(" ", folded)).strip()


class KeywordFilter:
    """Case-insensitive exclusion by keyword.

    ASCII-only keywords match on word boundaries, so a short entry such as "ai"
    does not fire inside "said". Keywords containing non-ASCII characters (Korean)
    match as substrings, because word boundaries are not meaningful there.
    """

    def __init__(self, keywords: list[str]) -> None:
        self.keywords = [word for word in (k.strip() for k in keywords) if word]
        self._patterns: list[tuple[str, re.Pattern[str]]] = []
        for word in self.keywords:
            escaped = re.escape(word)
            if word.isascii():
                pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
            else:
                pattern = re.compile(escaped, re.IGNORECASE)
            self._patterns.append((word, pattern))

    def __bool__(self) -> bool:
        return bool(self._patterns)

    def __len__(self) -> int:
        return len(self._patterns)

    @classmethod
    def from_file(cls, path: Path | None = None) -> "KeywordFilter":
        """Load keywords, one per line. Blank lines and '#' comments are ignored."""
        path = path or DEFAULT_KEYWORD_FILE
        if not path.exists():
            return cls([])
        lines = path.read_text(encoding="utf-8").splitlines()
        return cls([line for line in lines if not line.lstrip().startswith("#")])

    def match(self, *texts: str) -> str | None:
        """Return the first keyword found in any of the given texts, else None."""
        for text in texts:
            if not text:
                continue
            for word, pattern in self._patterns:
                if pattern.search(text):
                    return word
        return None

"""Download full-text technical PDFs for a keyword from legal, open sources.

Two providers, both freely and legally downloadable:

- **Google Patents** (``patents.google.com``) -- the primary source. Patents are
  public documents; their PDFs are served from ``patentimages.storage.googleapis.com``.
- **arXiv** (``export.arxiv.org``) -- open-access scientific papers.

Deliberately excluded: Library Genesis, Z-Library, Anna's Archive, Sci-Hub and the
like. Those distribute copyrighted books without permission; this tool does not
touch them.

Korean material is filtered out per project rule: any result whose title contains
Hangul or the words korea/korean, or (for patents) a ``KR`` publication number, is
skipped.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ai_client import make_session  # retrying session with research UA

PATENTS_QUERY = "https://patents.google.com/xhr/query"
PATENT_PDF_HOST = "https://patentimages.storage.googleapis.com/"
ARXIV_QUERY = "http://export.arxiv.org/api/query"

_HANGUL = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]")
_KOREAN_WORD = re.compile(r"\bkorean?\b", re.IGNORECASE)
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def is_korean(*texts: str) -> bool:
    """True if any text contains Hangul or the word korea/korean."""
    for text in texts:
        if text and (_HANGUL.search(text) or _KOREAN_WORD.search(text)):
            return True
    return False


@dataclass(frozen=True)
class BookResult:
    provider: str        # "patent" | "arxiv"
    ident: str           # publication number / arXiv id -- the dedup key
    title: str
    pdf_url: str
    meta: str            # short human line (authors, date, assignee...)


def safe_filename(ident: str, title: str, used: set[str], folder: Path) -> str:
    base = f"{ident} {title}".strip()
    stem = INVALID_FILENAME.sub("", base).rstrip(" .") or ident or "document"
    budget = 250 - len(str(folder)) - len(".pdf") - 6
    budget = max(24, min(180, budget))
    stem = stem[:budget].rstrip(" .")
    candidate, n = stem, 2
    while candidate.casefold() in used:
        suffix = f" ({n})"
        candidate, n = stem[:budget - len(suffix)].rstrip(" .") + suffix, n + 1
    used.add(candidate.casefold())
    return candidate + ".pdf"


# ------------------------------------------------------------------- searching

def search_patents(session: requests.Session, keyword: str, limit: int = 25,
                   log=lambda _m: None) -> list[BookResult]:
    results: list[BookResult] = []
    try:
        response = session.get(
            PATENTS_QUERY,
            params={"url": f"q={keyword}&num={min(limit * 2, 100)}", "exp": ""},
            headers={"Referer": "https://patents.google.com/",
                     "Accept": "application/json, text/plain, */*",
                     "X-Requested-With": "XMLHttpRequest"},
            timeout=45,
        )
        response.raise_for_status()
        data = json.loads(response.text)
    except (requests.RequestException, json.JSONDecodeError) as exc:
        log(f"Patent search failed: {exc}")
        return results
    clusters = data.get("results", {}).get("cluster", []) or []
    for cluster in clusters:
        for item in cluster.get("result", []):
            patent = item.get("patent", {})
            number = patent.get("publication_number", "")
            title = _strip_html(patent.get("title", ""))
            pdf = patent.get("pdf", "")
            if not number or not pdf:
                continue
            if number.upper().startswith("KR") or is_korean(title):
                continue  # skip Korean-published or Korean-titled patents
            meta = " · ".join(filter(None, [
                patent.get("assignee", ""),
                patent.get("publication_date", ""),
            ]))
            results.append(BookResult("patent", number, title,
                                      PATENT_PDF_HOST + pdf, meta))
            if len(results) >= limit:
                return results
    return results


def search_arxiv(session: requests.Session, keyword: str, limit: int = 25,
                 log=lambda _m: None) -> list[BookResult]:
    results: list[BookResult] = []
    try:
        response = session.get(
            ARXIV_QUERY,
            # relevance sort (arXiv default) matches the keyword far better than
            # date sort, which just returns the newest papers touching any term.
            params={"search_query": f"all:{keyword}", "max_results": limit * 2},
            timeout=45,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        log(f"arXiv search failed: {exc}")
        return results
    soup = BeautifulSoup(response.content, "xml")
    for entry in soup.find_all("entry"):
        title = " ".join(entry.find("title").get_text(" ", strip=True).split()) if entry.find("title") else ""
        ident = entry.find("id").get_text(strip=True) if entry.find("id") else ""
        ident = ident.rsplit("/", 1)[-1]  # arXiv id
        pdf = None
        for link in entry.find_all("link"):
            if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                pdf = link.get("href")
        if not pdf and ident:
            pdf = f"https://arxiv.org/pdf/{ident}"
        if not ident or not pdf:
            continue
        authors = [a.get_text(strip=True) for a in entry.find_all("name")][:3]
        if is_korean(title):
            continue
        meta = " · ".join(filter(None, [", ".join(authors),
                                        (entry.find("published").get_text(strip=True)[:10]
                                         if entry.find("published") else "")]))
        results.append(BookResult("arxiv", ident, title, pdf, meta))
        if len(results) >= limit:
            break
    return results


def search(session: requests.Session, keyword: str, providers: set[str],
           limit: int = 25, log=lambda _m: None) -> list[BookResult]:
    """Combined search across the chosen providers."""
    out: list[BookResult] = []
    if "patent" in providers:
        found = search_patents(session, keyword, limit, log)
        log(f"Patents: {len(found)}")
        out += found
    if "arxiv" in providers:
        found = search_arxiv(session, keyword, limit, log)
        log(f"arXiv: {len(found)}")
        out += found
    return out


# ---------------------------------------------------------------- downloading

def download(session: requests.Session, book: BookResult, target: Path,
             timeout: int = 90) -> int:
    """Download one PDF to `target`. Returns the byte count. Raises on failure."""
    response = session.get(book.pdf_url, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    body = response.content
    if "pdf" not in content_type and not body[:5] == b"%PDF-":
        raise RuntimeError(f"Response is not a PDF ({content_type or 'unknown'})")
    target.write_bytes(body)
    return len(body)


def _strip_html(text: str) -> str:
    return " ".join(BeautifulSoup(text, "html.parser").get_text(" ", strip=True).split())

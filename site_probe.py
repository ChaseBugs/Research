"""Verify a candidate news site and auto-discover its body selector.

Adding a site by hand means knowing its CSS body selector; this module removes
that step. Given a name, an RSS feed URL and a field, ``probe_new_site`` runs the
same checks a site must pass to enter the registry -- feed reachable and dated,
the full public article body extractable, images present -- and *discovers* a
working content selector from a candidate list. On success it returns a ready
``Site``; on failure it returns a human-readable reason for the error dialog.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import scitechdaily_scraper
from sites import SITES, Site

# Body-container selectors seen across the registry, broad first-match-wins order.
CANDIDATE_SELECTORS: tuple[str, ...] = (
    "article .article-body", "article .entry-content", ".post-content.entry-content",
    "#story_text", "article .rich-text", "div[itemprop='articleBody']",
    "[itemprop='articleBody']", ".article__body", ".article-body", ".article-content",
    ".article__content", ".entry-content", ".post-content", ".c-entry-content",
    ".story-body", ".single__content", ".content-body", ".post-body", ".body-copy",
    ".td-post-content", ".elementor-widget-theme-post-content", ".post_cnt",
    ".et_pb_post_content", ".ArticleBase-Body", ".ArticleBase-BodyContent",
    ".body-description", "article .content", "main.article .body",
    "main article", "article",
)

MIN_CHARS = 400
MIN_PARAGRAPHS = 3


@dataclass
class ProbeOutcome:
    site: Site | None
    reason: str            # "" on success, else the failure message
    chars: int = 0
    images: int = 0
    selector: str = ""
    sampled: str = ""      # the article URL the selector was confirmed on


def _text(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _homepage_from_feed(feed_url: str) -> str:
    parts = urlparse(feed_url)
    if parts.scheme and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}/"
    return feed_url


def probe_new_site(name: str, feed_url: str, field: str, homepage: str = "",
                   log=lambda _m: None) -> ProbeOutcome:
    """Verify a site and return a ready Site, or a reason it cannot be added."""
    name = name.strip()
    feed_url = feed_url.strip()
    if not name:
        return ProbeOutcome(None, "Enter a site name.")
    if name in SITES:
        return ProbeOutcome(None, f"A site with this name already exists: {name}")
    if not feed_url.lower().startswith(("http://", "https://")):
        return ProbeOutcome(None, "RSS feed URL must use http or https.")

    session = scitechdaily_scraper.make_session()
    homepage = homepage.strip() or _homepage_from_feed(feed_url)

    # 1) feed reachable and has dated entries -- reuse the scraper's own parser.
    from news_scraper import feed_articles
    probe_site = Site(name, homepage, feed_url, ("article",), field=field)
    try:
        entries = feed_articles(session, probe_site, date(2000, 1, 1), date.today(), log)
    except requests.RequestException as exc:
        return ProbeOutcome(None, f"Could not reach the feed: {exc}")
    except Exception as exc:  # malformed feed, etc.
        return ProbeOutcome(None, f"Could not parse the feed: {type(exc).__name__}: {exc}")
    if not entries:
        return ProbeOutcome(None, "No dated articles found in the feed.")
    log(f"Feed OK: found {len(entries)} articles")

    # 2) try the newest few articles; pass if any yields a full body via some selector.
    last_reason = "Could not find an article-body selector."
    for _published, _title, url in entries[:3]:
        try:
            response = session.get(url, timeout=45)
        except requests.RequestException as exc:
            last_reason = f"Could not reach the article: {exc}"
            continue
        if response.status_code != 200:
            last_reason = f"Article response error (HTTP {response.status_code})"
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        for selector in CANDIDATE_SELECTORS:
            try:
                node = soup.select_one(selector)
            except Exception:
                continue
            if node is None:
                continue
            chars = len(_text(node))
            paras = len(node.find_all("p"))
            if chars < MIN_CHARS or paras < MIN_PARAGRAPHS:
                continue
            images = len(node.find_all("img"))
            log(f"Article body: '{selector}' ({chars} characters, {paras} paragraphs, {images} images)")
            site = Site(name, homepage, feed_url, (selector,), field=field)
            return ProbeOutcome(site, "", chars=chars, images=images,
                                selector=selector, sampled=url)
        last_reason = "Could not find a selector containing the full article body (the feed may only provide a preview or use an unusual structure)."
    return ProbeOutcome(None, last_reason)

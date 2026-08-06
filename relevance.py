"""Classify a scraped article as substantive technology vs. announcement-only.

Some feeds mix genuine technical writing (how a technology works, engineering
detail, specifications, a method or mechanism) with pure "news" -- deals, funding,
personnel, market moves, events -- that merely mention technology. This module
asks the text model to make that call so the scraper can keep the two apart.

The classifier is deliberately conservative: on any failure or ambiguity it
returns *technical* (True), so a service hiccup never causes real content to be
filed away as news.
"""

from __future__ import annotations

from ai_client import AIClient, AIError

_SYSTEM = "You are a strict classifier. Reply with exactly one word and nothing else."

_PROMPT = (
    "Classify the article below. Reply with exactly one word: TECHNICAL or NEWS.\n\n"
    "TECHNICAL = it explains how a technology, method, system, material or scientific "
    "mechanism actually works -- design, principle, process, specifications, or "
    "engineering/technical detail a practitioner could learn from.\n"
    "NEWS = it only reports an announcement, contract, funding round, acquisition, "
    "personnel change, market/finance move, policy or event, WITHOUT substantive "
    "technical explanation, even if it names a technology.\n\n"
    "Title: {title}\n\n"
    "Article (excerpt):\n{body}\n\n"
    "Answer (TECHNICAL or NEWS):"
)

BODY_LIMIT = 1600  # enough to judge; keeps the call fast and cheap


def is_technical(ai: AIClient, title: str, body: str) -> bool:
    """Return True if the article is substantive-technical, False if news-only.

    Failure-safe: returns True on any error so nothing is lost to a bad call.
    """
    prompt = _PROMPT.format(title=title.strip(), body=body.strip()[:BODY_LIMIT])
    try:
        reply = ai.chat(prompt, system=_SYSTEM)
    except AIError:
        return True
    verdict = reply.strip().upper()
    # Only classify as news when the model clearly says NEWS and not TECHNICAL.
    if "NEWS" in verdict and "TECHNICAL" not in verdict:
        return False
    return True


def label(ai: AIClient, title: str, body: str) -> str:
    """Convenience: 'technical' or 'news'."""
    return "technical" if is_technical(ai, title, body) else "news"

"""Health check for every registered site.

Feeds move and page markup changes, so entries in sites.py rot over time. This
re-runs the checks each site had to pass to be added: feed reachable, dated items
present, content selector matches the newest article, images extractable.

    python -B verify_sites.py                 # all sites
    python -B verify_sites.py --field energy  # one field
    python -B verify_sites.py --site "NASA"

Exit code is non-zero if any site fails, so it can gate a maintenance script.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

import scitechdaily_scraper
from news_scraper import _text, feed_articles
from sites import FIELDS, SITES, Site, sites_in_field


def check(site: Site, days: int) -> dict:
    """Probe one site. Returns a row describing what worked and what did not."""
    row = {"site": site, "ok": False, "note": "", "items": 0, "newest": "-",
           "chars": 0, "images": 0, "selector": "-"}
    session = scitechdaily_scraper.make_session()
    end = date.today()
    start = end - timedelta(days=days)
    try:
        if site.feed is None:
            entries = scitechdaily_scraper.archive_articles(session, start, end)
        else:
            entries = feed_articles(session, site, start, end, lambda _msg: None)
        row["items"] = len(entries)
        if not entries:
            row["note"] = f"No articles in the last {days} days"
            return row
        row["newest"] = str(entries[0][0])
        selectors = site.content_selectors or ("article .entry-content",)

        # A single paywalled or off-template entry at the top of the feed should
        # not fail the whole site, so try the few newest and pass if any yields a
        # full body. The last article's note is kept when none succeed.
        for _published, _title, url in entries[:3]:
            response = session.get(url, timeout=45)
            if response.status_code != 200:
                row["note"] = f"Article HTTP {response.status_code}"
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            content = next((soup.select_one(s) for s in selectors if soup.select_one(s)), None)
            if content is None:
                row["note"] = f"Selector mismatch: {', '.join(selectors)}"
                continue
            chars = len(_text(content))
            if chars < 400:
                row["note"] = f"Article body too short ({chars} characters)"
                continue
            row["selector"] = next(s for s in selectors if soup.select_one(s))
            row["chars"] = chars
            row["images"] = len(content.find_all("img"))
            row["ok"] = True
            row["note"] = "OK"
            break
    except requests.RequestException as exc:
        row["note"] = f"{type(exc).__name__}: {exc}"[:80]
    except Exception as exc:
        row["note"] = f"{type(exc).__name__}: {exc}"[:80]
    return row


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Korean output on a cp1252 console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--field", choices=FIELDS)
    group.add_argument("--site", choices=SITES)
    parser.add_argument("--days", type=int, default=14,
                        help="How many recent days to check (default: 14)")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    if args.site:
        targets = [SITES[args.site]]
    elif args.field:
        targets = sites_in_field(args.field)
    else:
        targets = list(SITES.values())

    print(f"Checking {len(targets)} sites (last {args.days} days)...\n")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda site: check(site, args.days), targets))

    rows.sort(key=lambda r: (r["ok"], r["site"].field, r["site"].name))
    print(f"{'':4} {'Site':34} {'Field':20} {'Articles':>8} {'Latest':12} {'Body':>7} {'Images':>6}  Note")
    print("-" * 118)
    for row in rows:
        site: Site = row["site"]
        flag = "OK " if row["ok"] else "FAILED"
        thin = "*" if site.low_volume else " "
        print(f"{flag}{thin} {site.name:34} {site.field:13} {row['items']:>4} "
              f"{row['newest']:12} {row['chars']:>7} {row['images']:>4}  {row['note']}")

    failed = [r for r in rows if not r["ok"]]
    print(f"\nOK {len(rows) - len(failed)} / {len(rows)}   (* = low-volume site)")
    if failed:
        print("\nSites needing attention:")
        for row in failed:
            print(f"  {row['site'].name}: {row['note']}")
        print("\nFix: update the feed URL or content_selectors in sites.py; if recovery is not possible, "
              "remove the entry and add it to the exclusions list in README_NewsScraper.md.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

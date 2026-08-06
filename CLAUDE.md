# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Windows research workspace holding Python tools plus a large corpus of `.docx` research documents. Not a git repository, no test suite, no linter config.

- **Research workbench GUI** (`news_scraper_gui.py`) — a four-tab tkinter app (`ttk.Notebook`) sharing one workspace folder and one activity ledger:
  - **Scrapping** — the news scraper (`news_scraper.py`, `sites.py`, `article_filter.py`, `scitechdaily_scraper.py`, `verify_sites.py`), 144 sites in 24 fields.
  - **Generate** (`tech_generator.py`, `ai_client.py`) — a keyword → up to 100 technology topics → one illustrated beginner-guide DOCX per topic.
  - **원문도서** (`book_downloader.py`) — downloads full-text patent/paper PDFs for a keyword from Google Patents + arXiv.
  - **리력** (`tab_history.py`) — counts and lists everything downloaded, by day/week/month.
- **DOCX math/text cleanup** (`fix_docx_math_text.py`) — repairs LaTeX-style artifacts left behind when AI-generated text is pasted into Word documents.

The GUI tabs live in `tab_scrape.py`, `tab_generate.py`, `tab_download.py`, `tab_history.py`; `gui_common.py` holds the `WorkerTab` base. The scraper CLI (`news_scraper.py`) is unchanged and still usable standalone.

## Commands

```powershell
python -m pip install -r requirements.txt

# GUI (or double-click Run_NewsScraper.bat)
python -B news_scraper_gui.py

# List registered fields and sites
python -B news_scraper.py --list

# CLI, one site
python -B news_scraper.py --site "ScienceDaily" --start 2026-07-20 --end 2026-07-22 --output D:\Research\Scraped_News

# CLI, an entire field
python -B news_scraper.py --field military --start 2026-07-20 --end 2026-07-22 --limit 30 --output D:\Research\Scraped_News

# Health-check feeds and selectors (first thing to run when collection breaks)
python -B verify_sites.py --field energy

# SciTechDaily standalone (also usable directly)
python -B scitechdaily_scraper.py --start 2026-07-20 --end 2026-07-22 --output D:\Research\Scraped_News

# DOCX cleanup — ALWAYS dry-run first
python -B fix_docx_math_text.py "D:\Research\6" --dry-run
python -B fix_docx_math_text.py "D:\Research\6"
```

`-B` is used consistently to keep `__pycache__` out of the tree. Scraper entry points exit non-zero when any article failed.

Console output is Korean, so `main()` in `news_scraper.py` and `verify_sites.py` calls `reconfigure(encoding="utf-8")` on stdout/stderr — without it these crash on a cp1252 console. `fix_docx_math_text.py` does the same.

## Scraper architecture

`sites.py` owns the registry: the frozen `Site` dataclass, `FIELDS` (category key → Korean label), and `SITES` (144 entries). It is split from the scraping logic purely so the definitions don't swamp it. `Site` carries the homepage, optional RSS feed, CSS selector tuples tried in order (first match wins), a `field` key, and `low_volume` for feeds that are legitimately quiet. Several publisher families share a body selector — Informa/Endeavor titles (Feedstuffs, Beef Magazine, Packaging Digest, Plastics Today, Farm Progress) use `.ArticleBase-Body`; when adding a site from a known platform, reuse the platform's selector before probing.

`news_scraper.py` is the engine. `scrape()` handles one site; `scrape_field()` loops `scrape()` over every site in a field. Both take the `Log = Callable[[str], None]` callback the GUI depends on. `scrape()` branches on whether the site has a feed:

- **`feed is None`** (only SciTechDaily) delegates to `scitechdaily_scraper.archive_articles()` (walks homepage pagination, stopping once a page's oldest entry predates `start`) and `scitechdaily_scraper.write_article()`.
- **Everything else** goes through `feed_articles()` (RSS/Atom, filtered to the date window) and `write_generic_article()`.

So `scitechdaily_scraper.py` is both a standalone CLI *and* a library — `make_session()` (retrying `requests.Session` with a research User-Agent) is shared by all sites. The two `write_*_article` functions are deliberate near-duplicates with site-specific junk filtering; changing DOCX layout usually means editing both. Both return `(image_count, resolved_title)` and both screen the article before building the document.

`news_scraper_gui.py` is a thin tkinter shell: a category combobox filters the site combobox, whose first entry (`★ 이 분야 전체`) triggers `scrape_field`. It runs the work on a daemon thread, pushes `("log"|"done"|"error", value)` tuples onto a `queue.Queue`, and drains it from the Tk thread via a 100 ms `after()` poll. Never touch widgets from the worker thread.

User-facing log and dialog strings are Korean; docstrings and code are English. Keep that split.

### Filtering and duplicate history

`article_filter.py` holds `KeywordFilter` (loaded from `exclude_keywords.txt`; ASCII-only keywords compile to word-boundary patterns so `ai` doesn't fire inside `said`, non-ASCII keywords match as substrings) and `normalize_title` (the comparison key). Duplicate *storage* lives in the SQLite ledger, not here.

`scrape()`/`scrape_field()` take the global `ledger: ActivityLog` and `skip_duplicates: bool`. **Dedup spans every past run and day**, because the ledger is one database at the workspace root, not a per-collection file. When `skip_duplicates` is true: URL is checked pre-fetch via `ledger.seen_key("scrape", url)` (saving a request) and title post-parse via `ledger.seen_title("scrape", title)` (catching the same story at a new URL). Every saved article is recorded via `ledger.record("scrape", …)` **regardless** of `skip_duplicates`, so the History tab always sees it; `skip_duplicates=False` re-collects (and may add duplicate rows — the user's explicit choice).

Screening runs in `_screen_article()` on parsed text *before* the document is built, so an excluded article costs no image downloads. It raises `ArticleSkipped`, which `scrape()` distinguishes from a genuine failure.

### Relevance classification (technical vs news-only)

`relevance.is_technical(ai, title, body)` asks the text model (Groq/g4f) to label an article TECHNICAL (explains how something works / specs / method) vs NEWS (announcement, deal, funding, personnel, market — no technical substance). It is **failure-safe: any error or ambiguity returns True (technical)** so a bad call never hides real content. The scraper takes an optional `classifier: Callable[[str, str], bool]`; when given, the writers route news-only articles to a `보도기사/` subfolder instead of discarding them (`NEWS_ONLY_DIR`), the writers return `(images, title, category)`, and `ScrapeResult.news` counts them. The Scrapping tab's "기술 기사만 분리" checkbox builds the classifier from `ai_config` via `_build_classifier()`. It costs one model call per saved article, so it's off by default.

### Output layout

Articles are filed by day into DPRK-Korean per-source folders: `<output>/MM-DD/<category>_<sub-category>(문서-영문)/<Article Title>.docx`. `scrape_output_folder(output_root, site)` builds the path from `sites.folder_label(site)`, which joins `FIELD_CATEGORY[site.field]` (군사, 콤퓨터, …) with `SITE_SUBCATEGORY[site.name]` (함선, 인공지능, …); a site missing from `SITE_SUBCATEGORY` (e.g. user-added) falls back to `DEFAULT_SUBCATEGORY` = `새기술`. Both maps and `folder_label` live in `sites.py`. Category and sub-category are chosen to never be equal, so no `군사_군사` folders.

A **field run** gives each site its *own* `<category>_<sub-category>(문서-영문)` folder under the same `MM-DD/` day folder — there is no shared field folder; `FieldResult.folder` is the day folder. Two sites that map to the same label simply share a folder (intentional, e.g. Defense One + DefenseScoop → `군사_군사기술`, Aquaculture Magazine + Global Seafood Alliance → `수산업_양식`).

Folders are created **lazily** — `scrape()` no longer `mkdir`s upfront; the writers call `target.parent.mkdir` right before `document.save`, so a run that saves nothing (all duplicates / no new news) leaves no empty folder. Report files are likewise only written when `output.exists()`.

With the relevance classifier on, news-only articles go to a `보도기사/` subfolder (`NEWS_ONLY_DIR`) beside the technical ones. `failures.txt` (`url\terror`) and `_skipped.txt` (keyword/duplicate skips) appear only when there is something to report; there is **no** `_summary.txt` (removed — the same counts are in the completion dialog and live log). A failed article never aborts its site; a failed site never aborts its field.

`_safe_filename()` budgets the stem against the length of the destination folder because Windows `MAX_PATH` is 260 — a long headline in a nested field folder otherwise fails at save time with a misleading `No such file or directory`. `scitechdaily_scraper.safe_filename()` carries its own copy of this logic since that module stays standalone.

### Adding a site

Add a `Site` entry to `sites.py` only after live-verifying all four of: feed reachable, per-item dates parseable, selector yields the **full public body** (not a paywall teaser), and images extract. `verify_sites.py` re-runs exactly these checks over the registry — use it to confirm a new entry and to diagnose rot later.

**User-added sites** go through the GUI, not this file. `site_probe.probe_new_site(name, feed, field)` runs the same four checks *and auto-discovers* the body selector from `CANDIDATE_SELECTORS` (trying the 3 newest articles), returning a ready `Site` or a failure reason. `sites.register_site()` merges it into `SITES` and persists it to `custom_sites.json` (loaded and merged at `sites.py` import via `load_custom_sites()`), so hand-curated entries stay in source while user entries stay out of it. The Scrapping tab's "＋ 새 사이트 추가" dialog drives this on a worker thread and shows an error dialog when a site can't be scraped. `custom_sites.json` is generated, not checked in.

`verify_sites.py`'s `check()` tries the **3 newest** feed entries and passes if any yields a full body, so a single paywalled or off-template entry at the top of a feed (e.g. ENR's `/blogs/` posts, which are paywalled while `/articles/` are not) does not fail the whole site.

`README_NewsScraper.md` records ~140 sites evaluated and rejected, grouped by reason (bot-block, dead feed, no extractable body, teaser-only). Do not re-add those without re-verifying; the list carries a last-checked date.

## GUI workbench architecture

`ResearchApp(tk.Tk)` in `news_scraper_gui.py` owns a `ttk.Notebook`, one shared `base_dir` (the workspace folder), and one `ActivityLog`. Each tab derives its own output under the workspace: `Scraped_News/`, `Generated_Docs/<keyword>_<date>/`, `Source_Books/<keyword>_<date>/`.

`gui_common.WorkerTab` is the base for the three working tabs. It captures the thread→queue→`after()`-poll pattern once: `run_worker(target, on_done, manage)` runs `target(emit)` on a daemon thread, disables the `manage` widgets, and delivers `("log"|"done"|"error", value)` back to the Tk thread. **Widgets are only touched from the Tk thread** — the worker communicates solely via the queue. The History tab is a plain `Frame` (no worker; it only reads the ledger).

### Activity ledger (`activity_log.py`)

`research_ledger.db` — **SQLite** at the workspace root, one row per artifact (`kind` ∈ `scrape|generate|book`). It does double duty: **cross-run/cross-day/cross-tab dedup** (`seen_key`, `seen_title`, both scoped by `kind` so a scrape URL and a book id never collide) and the **History tab's** day/week/month aggregation (`counts_by_period`, `filtered`, `totals`). Because it is a single database at the workspace root — not a per-collection file — an article collected yesterday is still recognised today.

Concurrency: each read/write opens its own short-lived `sqlite3` connection (WAL mode, writes under a lock), so the GUI's worker threads write while the Tk thread reads. All three tabs share the one `app.activity` instance and call `ledger.record(...)` / `ledger.seen_*(...)` directly; there is no `on_saved` callback anymore. On first creation the DB imports the legacy JSON stores once — `activity_log.jsonl` and every `Scraped_News/**/_history.json` — de-duplicating across them, so upgrade preserves history (kept D:\Research\research_ledger.db already holds the migrated 325 rows). `research_ledger.db` is generated, not checked in.

### Free AI backends (`ai_client.py`)

Text has two selectable backends via `AIClient(backend=...)`, chosen in the Generate tab:
- **g4f** (GPT4Free) — keyless; `_chat_g4f` retries across `G4F_MODELS`. Convenient, flaky.
- **groq** — the Groq API, free on a personal key; `_chat_groq` POSTs to their OpenAI-compatible endpoint and retries across `GROQ_MODELS`. 401 → invalid key (surfaced immediately), 429 → rate limit (retried), 404 → try next model.

Backend + key persist via `save_ai_config`/`load_ai_config` (`ai_config.json`, generated not checked in; env `GROQ_API_KEY` is the default key). Images always come from **Pollinations** (`GET image.pollinations.ai/prompt/<prompt>` → JPEG, keyless) regardless of text backend — Pollinations' keyless **text** endpoint is paywalled (402 on any uncached prompt), which is why text uses g4f/groq.

`try_image()` returns `None` instead of raising, so a document is still produced when only the illustration service is down. All generated prose is English by instruction (the workspace corpus is English; Korean is deliberately avoided).

Scraped article DOCX and generated DOCX carry **no metadata paragraph** (no Published/Source/Keyword/Generated line) — just the title heading then body. Source URL still lives in `core_properties.comments` (invisible), not the body.

### Book downloads (`book_downloader.py`)

**Legal, open sources only** — Google Patents (`patents.google.com/xhr/query`, PDFs from `patentimages.storage.googleapis.com`) and arXiv (`export.arxiv.org`, relevance-sorted). The Google Patents xhr endpoint is unofficial and rate-limits with 503 under load; requests carry `Referer`/`X-Requested-With` headers. **Do not add LibGen, Z-Library, Anna's Archive, or Sci-Hub** — they distribute pirated books; this boundary is intentional. `is_korean()` filters Hangul-titled results and `KR` publication numbers per the workspace's no-Korean rule.

## DOCX cleanup architecture

`fix_docx_math_text.py` deliberately does **not** use `python-docx`. It opens the `.docx` zip, rewrites only `word/*.xml`, and regex-substitutes the inner text of `<w:t>` nodes, then rewrites the zip entry-by-entry preserving all other parts. This keeps every run, style, and relationship intact — a python-docx round-trip would not.

Consequence: a math expression split across multiple runs (`<w:t>` nodes) will not match. Fixes are per-text-node.

The pipeline is `INLINE_MATH_RE` (`$...$`) → `latex_body_to_text()` → strip `\text{}`/`\mathrm{}`/`\operatorname{}` wrappers, map `\ge`/`\le`/etc. to ASCII, drop remaining braces/backslashes → `normalize_spaces()`. `EXACT_REPLACEMENTS` handles one-off literals that the regex path gets wrong. Prefer extending the regex family over adding exact strings.

Writes `.docx.bak` alongside each modified file unless `--no-backup`. Skips `~$` lock files and `.docx.bak`.

Per `AGENTS.md`: when given a folder path for cleanup, run `--dry-run` first, touch `.docx` only (never PDFs, images, or archives), and never hand-rewrite whole documents — only content matching the math artifact pattern.

## Document corpus

`3/`, `6/`, `6-1000/`, `7/`, `7-1000/`, `8-1000/` are data, not code: batches of Korean-named topic folders (`분야_주제(문서-영문)`) each containing English `.docx` research documents. `Game/` and `Scraped_News/` are likewise generated/collected output. Do not restructure or bulk-edit these unless asked; they are the input to `fix_docx_math_text.py`.

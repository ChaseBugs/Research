#!/usr/bin/env python3
r"""
Fix common AI-copy math/text artifacts in .docx files under a folder.

Usage:
    python fix_docx_math_text.py "D:\\Research\\6" --dry-run
    python fix_docx_math_text.py "D:\\Research\\6"

The script edits .docx files in place and creates .bak backups by default.
It focuses on LaTeX-style inline math artifacts such as $2\text{ kV}$,
$\ge 850\text{ kVA/t}$, and $35\text{ to }50\text{ minutes}$.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


EXACT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"($2\text{ to }5\text{ seconds}$)", "Slow (2 to 5seconds)"),
)

WORD_TEXT_RE = re.compile(rb"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.DOTALL)
INLINE_MATH_RE = re.compile(r"\$([^$\r\n]+)\$")
TEXT_COMMAND_RE = re.compile(r"\\(?:text|mathrm|operatorname)\{([^{}]*)\}")
LATEX_SYMBOLS: tuple[tuple[str, str], ...] = (
    (r"\geq", ">="),
    (r"\ge", ">="),
    (r"\leq", "<="),
    (r"\le", "<="),
    (r"\gt", ">"),
    (r"\lt", "<"),
    (r"\times", "x"),
    (r"\cdot", "."),
    (r"\degree", " "),
    (r"\circ", " "),
)


def normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;:)])", r"\1", text)
    text = re.sub(r"([(<>=])\s+", r"\1", text)
    text = re.sub(r"(?<![<>=])([<>])(?=\d)", r"\1 ", text)
    text = re.sub(r"([<>]=?)(?=\d)", r"\1 ", text)
    text = re.sub(r"\s*/\s*", "/", text)
    return text.strip()


def latex_body_to_text(body: str) -> str:
    updated = body
    previous = None
    while previous != updated:
        previous = updated
        updated = TEXT_COMMAND_RE.sub(lambda match: match.group(1), updated)

    for bad, good in LATEX_SYMBOLS:
        updated = updated.replace(bad, good)

    updated = re.sub(r"\^\s*\{?\s*o\s*\}?", " ", updated)
    updated = updated.replace("^", "")
    updated = updated.replace("{", "").replace("}", "")
    updated = updated.replace("\\", "")
    return normalize_spaces(updated)


def replace_inline_math(match: re.Match[str]) -> str:
    return latex_body_to_text(match.group(1))


def apply_replacements(text: str) -> tuple[str, int]:
    count = 0
    updated = text
    for bad, good in EXACT_REPLACEMENTS:
        occurrences = updated.count(bad)
        if occurrences:
            updated = updated.replace(bad, good)
            count += occurrences

    updated, regex_count = INLINE_MATH_RE.subn(replace_inline_math, updated)
    count += regex_count
    return updated, count


def update_text_node(match: re.Match[bytes]) -> bytes:
    prefix, raw_text, suffix = match.groups()
    original = html.unescape(raw_text.decode("utf-8"))
    updated, count = apply_replacements(original)
    if count == 0:
        return match.group(0)

    update_text_node.count += count
    return prefix + escape(updated).encode("utf-8") + suffix


update_text_node.count = 0  # type: ignore[attr-defined]


def update_xml(xml_bytes: bytes) -> tuple[bytes, int]:
    update_text_node.count = 0  # type: ignore[attr-defined]
    updated = WORD_TEXT_RE.sub(update_text_node, xml_bytes)
    return updated, update_text_node.count  # type: ignore[attr-defined]


def should_process_zip_entry(name: str) -> bool:
    return name.startswith("word/") and name.endswith(".xml")


def fix_docx(path: Path, dry_run: bool, backup: bool) -> int:
    total_replacements = 0
    changed_entries: dict[str, bytes] = {}

    try:
        with zipfile.ZipFile(path, "r") as source:
            for info in source.infolist():
                if not should_process_zip_entry(info.filename):
                    continue
                updated_bytes, count = update_xml(source.read(info.filename))
                if count:
                    changed_entries[info.filename] = updated_bytes
                    total_replacements += count
    except zipfile.BadZipFile:
        print(f"SKIP invalid docx: {path}")
        return 0

    if total_replacements == 0 or dry_run:
        return total_replacements

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        if not backup_path.exists():
            shutil.copy2(path, backup_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp_path, "w") as target:
            for info in source.infolist():
                data = changed_entries.get(info.filename)
                if data is None:
                    data = source.read(info.filename)
                target.writestr(info, data)
        shutil.move(str(temp_path), path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return total_replacements


def iter_docx_files(folder: Path):
    for path in folder.rglob("*.docx"):
        if path.name.startswith("~$"):
            continue
        if path.name.endswith(".docx.bak"):
            continue
        yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replace known broken math/text artifacts in .docx files under a folder."
    )
    parser.add_argument("folder", help="Folder path containing .docx files to process.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files.")
    parser.add_argument("--no-backup", action="store_true", help="Do not create .docx.bak backups.")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    folder = Path(args.folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"ERROR folder does not exist: {folder}", file=sys.stderr)
        return 2

    files_changed = 0
    replacements = 0
    for docx_path in iter_docx_files(folder):
        count = fix_docx(docx_path, dry_run=args.dry_run, backup=not args.no_backup)
        if count:
            files_changed += 1
            replacements += count
            action = "WOULD CHANGE" if args.dry_run else "CHANGED"
            print(f"{action} {docx_path} ({count} replacements)")

    mode = "dry run" if args.dry_run else "written"
    print(f"Done: {files_changed} files, {replacements} replacements, {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

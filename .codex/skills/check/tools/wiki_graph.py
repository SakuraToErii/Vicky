#!/usr/bin/env python3
"""Repo-local wiki graph diagnostics for Vicky."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.markdown import WIKILINK_RE, find_wikilinks
from vicky.schema import INDEXED_DIRS


def _all_markdown_pages(wiki_root: str) -> dict[str, Path]:
    root = Path(wiki_root)
    pages: dict[str, Path] = {}
    duplicates: dict[str, list[Path]] = defaultdict(list)
    for subdir in INDEXED_DIRS:
        directory = root / subdir
        if not directory.exists():
            continue
        for file_path in sorted(directory.glob("*.md")):
            if file_path.stem in pages:
                if not duplicates[file_path.stem]:
                    duplicates[file_path.stem].append(pages[file_path.stem])
                duplicates[file_path.stem].append(file_path)
                continue
            pages[file_path.stem] = file_path
    if duplicates:
        duplicate_paths = {
            slug: [str(path.relative_to(root)) for path in paths]
            for slug, paths in sorted(duplicates.items())
        }
        raise ValueError(f"duplicate slug names in wiki: {json.dumps(duplicate_paths, ensure_ascii=False)}")
    return pages


def _normalize_link_target(value: str) -> str:
    text = str(value).strip().strip('"').strip("'")
    match = WIKILINK_RE.fullmatch(text)
    if match:
        text = match.group(1)
    return text.split("#", 1)[0]


def _graph_links(wiki_root: str) -> tuple[dict[str, Path], dict[str, set[str]], dict[str, set[str]]]:
    pages = _all_markdown_pages(wiki_root)
    inbound: dict[str, set[str]] = {slug: set() for slug in pages}
    outbound: dict[str, set[str]] = {slug: set() for slug in pages}
    for slug, file_path in pages.items():
        content = file_path.read_text(encoding="utf-8")
        for target in find_wikilinks(content):
            link_target = _normalize_link_target(target)
            if link_target not in pages:
                continue
            inbound[link_target].add(slug)
            outbound[slug].add(link_target)
    return pages, inbound, outbound


def query_orphans(wiki_root: str) -> None:
    pages, inbound, _ = _graph_links(wiki_root)
    orphans = []
    for slug, file_path in pages.items():
        if file_path.parent.name == "outputs":
            continue
        if not inbound.get(slug):
            orphans.append({"slug": slug, "path": str(file_path.relative_to(Path(wiki_root)))})
    print(json.dumps(orphans, ensure_ascii=False, indent=2))


def query_deadends(wiki_root: str) -> None:
    pages, _, outbound = _graph_links(wiki_root)
    deadends = []
    for slug, file_path in pages.items():
        if file_path.parent.name == "outputs":
            continue
        if outbound.get(slug):
            continue
        deadends.append({"slug": slug, "path": str(file_path.relative_to(Path(wiki_root)))})
    print(json.dumps(deadends, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_root")
    parser.add_argument("subquery", choices=["orphans", "deadends"])
    args = parser.parse_args()

    try:
        if args.subquery == "orphans":
            query_orphans(args.wiki_root)
        else:
            query_deadends(args.wiki_root)
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Find wiki pages by frontmatter fields."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.frontmatter import parse_frontmatter_file
from vicky.markdown import WIKILINK_RE
from vicky.schema import INDEXED_DIRS

COMPARE_RE = re.compile(r"^([<>]=?|!=)(.+)$")


def _normalize_link_target(value) -> str:
    text = str(value).strip().strip('"').strip("'")
    match = WIKILINK_RE.fullmatch(text)
    if match:
        text = match.group(1)
    return text.split("#", 1)[0]


def _match_filter(actual, pattern: str) -> bool:
    compare = COMPARE_RE.match(pattern)
    if compare:
        operator, threshold_raw = compare.group(1), compare.group(2)
        try:
            actual_number = float(actual)
            threshold = float(threshold_raw)
        except (TypeError, ValueError):
            return False
        if operator == "<":
            return actual_number < threshold
        if operator == ">":
            return actual_number > threshold
        if operator == "<=":
            return actual_number <= threshold
        if operator == ">=":
            return actual_number >= threshold
        if operator == "!=":
            return actual_number != threshold
    return str(actual) == pattern or _normalize_link_target(actual) == _normalize_link_target(pattern)


def _value_matches(value, pattern: str) -> bool:
    if isinstance(value, list):
        return any(_match_filter(item, pattern) for item in value)
    return _match_filter(value, pattern)


def _parse_filters(raw_filters: list[str]) -> list[tuple[str, str]]:
    filters: list[tuple[str, str]] = []
    iterator = iter(raw_filters)
    for item in iterator:
        if not item.startswith("--"):
            continue
        field = item[2:]
        try:
            pattern = next(iterator)
        except StopIteration:
            break
        filters.append((field, pattern))
    return filters


def find_entities(wiki_root: Path, entity_type: str, filters: list[tuple[str, str]]) -> list[dict]:
    entity_dir = wiki_root / entity_type
    if not entity_dir.exists():
        return []
    results: list[dict] = []
    for file_path in sorted(entity_dir.glob("*.md")):
        frontmatter = parse_frontmatter_file(file_path)
        if not frontmatter:
            continue
        matched = True
        for field, pattern in filters:
            if field not in frontmatter or not _value_matches(frontmatter[field], pattern):
                matched = False
                break
        if matched:
            results.append(
                {
                    "slug": file_path.stem,
                    "path": str(file_path.relative_to(wiki_root)),
                    **frontmatter,
                }
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_root")
    parser.add_argument("entity_type", choices=INDEXED_DIRS)
    args, raw_filters = parser.parse_known_args()

    results = find_entities(Path(args.wiki_root), args.entity_type, _parse_filters(raw_filters))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

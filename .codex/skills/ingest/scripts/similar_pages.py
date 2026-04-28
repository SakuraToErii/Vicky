#!/usr/bin/env python3
"""Find similar concept, foundation, or theorem pages before creating new pages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.frontmatter import parse_frontmatter_file
from vicky.slug import phrase_match_score


def _scan_similar(entity_dir: Path, entity_type: str, candidate_names: list[str], key_field: str) -> list[dict]:
    matches: list[dict] = []
    if not entity_dir.exists():
        return matches
    for file_path in sorted(entity_dir.glob("*.md")):
        frontmatter = parse_frontmatter_file(file_path)
        title = str(frontmatter.get("title", "") or frontmatter.get("name", ""))
        aliases = frontmatter.get("aliases", []) or []
        if not isinstance(aliases, list):
            aliases = []
        existing_names = [title] + [str(alias) for alias in aliases]
        best_score = 0.0
        best_pair: tuple[str, str] | None = None
        for candidate in candidate_names:
            for existing in existing_names:
                score = phrase_match_score(candidate, existing)
                if score > best_score:
                    best_score = score
                    best_pair = (candidate, existing)
        if best_score < 0.4:
            continue
        reason = ""
        if best_pair:
            candidate, existing = best_pair
            if best_score >= 1.0:
                reason = f"exact normalized match: '{candidate}' == '{existing}'"
            elif best_score >= 0.85:
                reason = f"phrase containment: '{candidate}' <-> '{existing}'"
            else:
                reason = f"token overlap: '{candidate}' <-> '{existing}'"
        matches.append(
            {
                "entity_type": entity_type,
                "slug": file_path.stem,
                "path": str(file_path.relative_to(entity_dir.parent)),
                "title": title,
                "aliases": aliases,
                key_field: frontmatter.get(key_field, []) or [],
                "score": round(best_score, 3),
                "match_reason": reason,
            }
        )
    matches.sort(key=lambda item: (-item["score"], item["slug"]))
    return matches


def find_similar_concept(wiki_root: Path, candidate_title: str, candidate_aliases: list[str] | None = None) -> list[dict]:
    candidate_names = [candidate_title] + [alias for alias in (candidate_aliases or []) if alias]
    matches = _scan_similar(wiki_root / "foundations", "foundation", candidate_names, "key_sources")
    matches.extend(_scan_similar(wiki_root / "concepts", "concept", candidate_names, "key_sources"))
    matches.sort(key=lambda item: (0 if item["entity_type"] == "foundation" else 1, -item["score"], item["slug"]))
    return matches


def find_similar_theorem(wiki_root: Path, candidate_title: str, candidate_aliases: list[str] | None = None) -> list[dict]:
    candidate_names = [candidate_title] + [alias for alias in (candidate_aliases or []) if alias]
    return _scan_similar(wiki_root / "theorems", "theorem", candidate_names, "key_sources")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_root")
    parser.add_argument("kind", choices=["concept", "theorem"])
    parser.add_argument("title")
    parser.add_argument("--aliases", default="", help="Comma-separated aliases")
    args = parser.parse_args()

    aliases = [item.strip() for item in args.aliases.split(",") if item.strip()]
    wiki_root = Path(args.wiki_root)
    if args.kind == "concept":
        results = find_similar_concept(wiki_root, args.title, aliases)
    else:
        results = find_similar_theorem(wiki_root, args.title, aliases)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

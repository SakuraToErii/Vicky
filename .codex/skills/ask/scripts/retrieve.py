#!/usr/bin/env python3
"""Retrieve seed pages and one-hop relation evidence for ask."""

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

from frontmatter import parse_frontmatter_file
from markdown import WIKILINK_RE
from schema import INDEXED_DIRS, RELATION_FIELDS

RELATION_WEIGHTS = {
    "relation_derived_from": 5,
    "relation_uses": 4,
    "relation_extends": 3,
    "relation_compares_with": 2,
    "relation_contradicts": 1,
}
RELATIONS_HEADING = "## Relations"
HEADING_RE = re.compile(r"^#{1,6}\s+")


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _normalize_link_target(value) -> str:
    text = str(value).strip().strip('"').strip("'")
    match = WIKILINK_RE.fullmatch(text)
    if match:
        text = match.group(1)
    return text.split("#", 1)[0]


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _page_path(path: Path, wiki_root: Path) -> str:
    try:
        return str(path.relative_to(wiki_root.parent))
    except ValueError:
        return str(path)


def _load_page_records(wiki_root: Path) -> list[dict]:
    pages: list[dict] = []
    for entity_type in INDEXED_DIRS:
        entity_dir = wiki_root / entity_type
        if not entity_dir.exists():
            continue
        for file_path in sorted(entity_dir.glob("*.md")):
            frontmatter = parse_frontmatter_file(file_path)
            if not frontmatter:
                continue
            slug = str(frontmatter.get("slug") or file_path.stem).strip()
            aliases = _as_list(frontmatter.get("aliases", []))
            relation_map = {
                field: [_normalize_link_target(item) for item in _as_list(frontmatter.get(field, []))]
                for field in RELATION_FIELDS
            }
            pages.append(
                {
                    "slug": slug,
                    "page_type": entity_type,
                    "path": _page_path(file_path, wiki_root),
                    "file_path": file_path,
                    "aliases": aliases,
                    "frontmatter": frontmatter,
                    "relation_map": relation_map,
                }
            )
    return pages


def _score_page(page: dict, candidate_terms: list[str]) -> tuple[int, list[str]]:
    slug_norm = _normalize_text(page["slug"])
    alias_norms = [_normalize_text(alias) for alias in page["aliases"]]
    score = 0
    matched_terms: list[str] = []
    for term in candidate_terms:
        normalized = _normalize_text(term)
        if not normalized:
            continue
        term_score = 0
        if normalized == slug_norm:
            term_score = 100
        elif len(normalized) >= 4 and normalized in slug_norm:
            term_score = 80
        else:
            for alias_norm in alias_norms:
                if not alias_norm:
                    continue
                if normalized == alias_norm:
                    term_score = max(term_score, 70)
                elif len(normalized) >= 4 and normalized in alias_norm:
                    term_score = max(term_score, 50)
        if term_score:
            score += term_score
            matched_terms.append(term)
    return score, matched_terms


def _relations_section_lines(content: str) -> list[str]:
    lines = content.splitlines()
    in_relations = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == RELATIONS_HEADING:
            in_relations = True
            continue
        if in_relations and stripped.startswith("#") and HEADING_RE.match(stripped):
            break
        if in_relations and stripped:
            collected.append(stripped)
    return collected


def _relation_evidence(file_path: Path, target_slug: str) -> list[str]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return []
    evidence: list[str] = []
    raw_target = target_slug.casefold()
    wikilink_target = f"[[{target_slug}]]".casefold()
    for line in _relations_section_lines(content):
        folded = line.casefold()
        if wikilink_target in folded or raw_target in folded:
            evidence.append(line)
    return evidence


def _make_neighbor_item(
    page: dict,
    relation_field: str,
    direction: str,
    evidence_owner_path: Path,
    target_slug: str,
) -> dict:
    return {
        "slug": page["slug"],
        "page_type": page["page_type"],
        "path": page["path"],
        "direction": direction,
        "relation_field": relation_field,
        "relation_weight": RELATION_WEIGHTS[relation_field],
        "relations_sentences": _relation_evidence(evidence_owner_path, target_slug),
    }


def _neighbors_for_seed(seed: dict, pages_by_slug: dict[str, dict], pages: list[dict]) -> tuple[list[dict], list[dict]]:
    outgoing: list[dict] = []
    incoming: list[dict] = []
    seed_slug = seed["slug"]

    for relation_field in RELATION_FIELDS:
        for target_slug in seed["relation_map"].get(relation_field, []):
            target = pages_by_slug.get(target_slug)
            if not target:
                continue
            outgoing.append(
                _make_neighbor_item(
                    target,
                    relation_field,
                    "outgoing",
                    seed["file_path"],
                    target_slug,
                )
            )

    for page in pages:
        if page["slug"] == seed_slug:
            continue
        for relation_field in RELATION_FIELDS:
            if seed_slug in page["relation_map"].get(relation_field, []):
                incoming.append(
                    _make_neighbor_item(
                        page,
                        relation_field,
                        "incoming",
                        page["file_path"],
                        seed_slug,
                    )
                )

    outgoing.sort(key=lambda item: (-item["relation_weight"], item["slug"]))
    incoming.sort(key=lambda item: (-item["relation_weight"], item["slug"]))
    return outgoing, incoming


def build_candidate_package(wiki_root: Path, candidate_terms: list[str], max_seeds: int = 5) -> dict:
    normalized_terms = [term.strip() for term in candidate_terms if term.strip()]
    pages = _load_page_records(wiki_root)
    pages_by_slug = {page["slug"]: page for page in pages}

    scored_pages: list[tuple[int, list[str], dict]] = []
    for page in pages:
        score, matched_terms = _score_page(page, normalized_terms)
        if score <= 0:
            continue
        scored_pages.append((score, matched_terms, page))

    scored_pages.sort(key=lambda item: (-item[0], item[2]["slug"]))
    seeds = []
    for score, matched_terms, page in scored_pages[:max_seeds]:
        outgoing, incoming = _neighbors_for_seed(page, pages_by_slug, pages)
        seeds.append(
            {
                "slug": page["slug"],
                "page_type": page["page_type"],
                "path": page["path"],
                "seed_score": score,
                "matched_terms": matched_terms,
                "aliases": page["aliases"],
                "incoming_neighbors": incoming,
                "outgoing_neighbors": outgoing,
            }
        )

    return {
        "candidate_terms": normalized_terms,
        "seed_count": len(seeds),
        "seeds": seeds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki_root")
    parser.add_argument("candidate_terms", nargs="+")
    parser.add_argument("--max-seeds", type=int, default=5)
    args = parser.parse_args()

    payload = build_candidate_package(Path(args.wiki_root), args.candidate_terms, max_seeds=args.max_seeds)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

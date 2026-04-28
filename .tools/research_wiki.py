#!/usr/bin/env python3
"""Core utilities for the Vicky LLM wiki.

The wiki is an Obsidian-first Markdown vault maintained by a human and an LLM
together. Raw sources live under ``raw/``. Structured notes live under
``wiki/``.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from _schemas import FIELD_DEFAULTS, INDEXED_DIRS
from _support_files import LOG_TEMPLATE, ensure_support_files
from _frontmatter import (
    FRONTMATTER_RE,
    parse_frontmatter_file as _parse_frontmatter,
    parse_scalar as _parse_scalar,
    parse_yaml_block as _parse_yaml_block,
    serialize_frontmatter as _serialize_frontmatter,
    update_frontmatter_field as _update_frontmatter_field,
)

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "this",
        "to",
        "with",
    }
)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
COMPARE_RE = re.compile(r"^([<>]=?|!=)(.+)$")


def slugify(title: str) -> str:
    """Generate a short kebab-case slug."""
    text = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    words = [w for w in text.split() if w and w not in STOP_WORDS]
    if not words:
        words = [w for w in text.split() if w]
    if not words:
        return "untitled"
    return "-".join(words[:6])


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def init_wiki(wiki_root: str) -> None:
    """Create the wiki directory scaffold."""
    root = Path(wiki_root)
    for name in INDEXED_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    ensure_support_files(root, missing_only=True)
    append_log(wiki_root, "init | wiki initialized")
    print(json.dumps({"status": "ok", "wiki_root": str(root)}))


def append_log(wiki_root: str, message: str) -> None:
    log_path = Path(wiki_root) / "log.md"
    entry = f"## [{_today()}] {message}\n"
    if log_path.exists():
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(entry)
    else:
        log_path.write_text(LOG_TEMPLATE + entry, encoding="utf-8")


def read_meta(path: str, field: str | None = None) -> None:
    file_path = Path(path)
    if not file_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(1)
    frontmatter = _parse_frontmatter(file_path)
    if not frontmatter:
        print(json.dumps({"status": "error", "message": "No frontmatter found"}))
        sys.exit(1)
    if field is None:
        print(json.dumps(frontmatter, ensure_ascii=False, indent=2))
        return
    if field not in frontmatter:
        print(json.dumps({"status": "error", "message": f"Field '{field}' not in frontmatter"}))
        sys.exit(1)
    print(json.dumps(frontmatter[field], ensure_ascii=False))


def set_meta(path: str, field: str, value: str, append: bool = False) -> None:
    file_path = Path(path)
    if not file_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(1)
    content = file_path.read_text(encoding="utf-8")
    parsed_value = value if append else _parse_scalar(value)
    try:
        new_content, old_value, new_value = _update_frontmatter_field(
            content, field, parsed_value, append=append
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        sys.exit(1)
    file_path.write_text(new_content, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "field": field,
                "old": old_value,
                "new": new_value,
                "action": "append" if append else "set",
            },
            ensure_ascii=False,
        )
    )


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
        for target in WIKILINK_RE.findall(content):
            link_target = _normalize_link_target(target)
            if link_target not in pages:
                continue
            inbound[link_target].add(slug)
            outbound[slug].add(link_target)
    return pages, inbound, outbound


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
    return str(actual) == pattern


def find_entities(wiki_root: str, entity_type: str, filters: list[tuple[str, str]]) -> None:
    root = Path(wiki_root)
    entity_dir = root / entity_type
    if not entity_dir.exists():
        print(json.dumps([]))
        return
    results: list[dict] = []
    for file_path in sorted(entity_dir.glob("*.md")):
        frontmatter = _parse_frontmatter(file_path)
        if not frontmatter:
            continue
        matched = True
        for field, pattern in filters:
            value = frontmatter.get(field)
            if value is None:
                matched = False
                break
            if isinstance(value, list):
                if pattern not in [str(item) for item in value]:
                    matched = False
                    break
            elif not _match_filter(value, pattern):
                matched = False
                break
        if matched:
            results.append({"slug": file_path.stem, **frontmatter})
    print(json.dumps(results, ensure_ascii=False, indent=2))


def _normalize_text(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return " ".join(text.split())


def _content_tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {token for token in normalized.split() if len(token) >= 3 and token not in STOP_WORDS}


def _phrase_match_score(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    normalized_left = _normalize_text(left)
    normalized_right = _normalize_text(right)
    if not normalized_left or not normalized_right:
        return 0.0
    if normalized_left == normalized_right:
        return 1.0
    if normalized_left in normalized_right or normalized_right in normalized_left:
        shorter = normalized_left if len(normalized_left) < len(normalized_right) else normalized_right
        if len(shorter.split()) >= 2:
            return 0.85
    left_tokens = _content_tokens(left)
    right_tokens = _content_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if union == 0:
        return 0.0
    score = overlap / union
    return score if score >= 0.4 else 0.0


def _scan_similar(entity_dir: Path, entity_type: str, candidate_names: list[str], key_field: str) -> list[dict]:
    matches: list[dict] = []
    if not entity_dir.exists():
        return matches
    for file_path in sorted(entity_dir.glob("*.md")):
        frontmatter = _parse_frontmatter(file_path)
        title = str(frontmatter.get("title", "") or frontmatter.get("name", ""))
        aliases = frontmatter.get("aliases", []) or []
        if not isinstance(aliases, list):
            aliases = []
        names = [title] + [str(alias) for alias in aliases]
        best_score = 0.0
        best_pair: tuple[str, str] | None = None
        for candidate in candidate_names:
            for existing in names:
                score = _phrase_match_score(candidate, existing)
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
                reason = f"phrase containment: '{candidate}' ↔ '{existing}'"
            else:
                reason = f"token overlap: '{candidate}' ↔ '{existing}'"
        matches.append(
            {
                "entity_type": entity_type,
                "slug": file_path.stem,
                "title": title,
                "aliases": aliases,
                key_field: frontmatter.get(key_field, []) or [],
                "score": round(best_score, 3),
                "match_reason": reason,
            }
        )
    matches.sort(key=lambda item: (-item["score"], item["slug"]))
    return matches


def find_similar_concept(wiki_root: str, candidate_title: str, candidate_aliases: list[str] | None = None) -> None:
    root = Path(wiki_root)
    candidate_names = [candidate_title] + [alias for alias in (candidate_aliases or []) if alias]
    matches = _scan_similar(root / "foundations", "foundation", candidate_names, "key_sources")
    matches.extend(_scan_similar(root / "concepts", "concept", candidate_names, "key_sources"))
    matches.sort(key=lambda item: (0 if item["entity_type"] == "foundation" else 1, -item["score"], item["slug"]))
    print(json.dumps(matches, ensure_ascii=False, indent=2))


def find_similar_theorem(wiki_root: str, candidate_title: str, candidate_aliases: list[str] | None = None) -> None:
    root = Path(wiki_root)
    candidate_names = [candidate_title] + [alias for alias in (candidate_aliases or []) if alias]
    matches = _scan_similar(root / "theorems", "theorem", candidate_names, "key_sources")
    print(json.dumps(matches, ensure_ascii=False, indent=2))


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


def get_stats(wiki_root: str, as_json: bool = False) -> dict:
    root = Path(wiki_root)
    stats = {name: len(list((root / name).glob("*.md"))) if (root / name).exists() else 0 for name in INDEXED_DIRS}
    if as_json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print("Vicky Wiki Stats")
        for key in INDEXED_DIRS:
            print(f"  {key}: {stats[key]}")
    return stats


MATURITY_WARM = {"sources": 5, "concepts": 10}
MATURITY_HOT = {"sources": 20, "concepts": 30}


def get_maturity(wiki_root: str, as_json: bool = False) -> dict:
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    try:
        stats = get_stats(wiki_root, as_json=True)
    finally:
        sys.stdout = old_stdout
    sources = stats["sources"]
    concepts = stats["concepts"]
    theorems = stats["theorems"]
    ideas = stats["ideas"]
    if sources >= MATURITY_HOT["sources"] and concepts >= MATURITY_HOT["concepts"]:
        level = "hot"
    elif sources >= MATURITY_WARM["sources"] and concepts >= MATURITY_WARM["concepts"]:
        level = "warm"
    else:
        level = "cold"
    result = {
        "level": level,
        "sources": sources,
        "concepts": concepts,
        "theorems": theorems,
        "ideas": ideas,
    }
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Wiki Maturity: {level}")
        print(f"  Sources: {sources}")
        print(f"  Concepts: {concepts}")
        print(f"  Theorems: {theorems}")
        print(f"  Ideas: {ideas}")
    return result


TRANSITIONS: dict[str, dict[str, list[str]]] = {
    "ideas": {
        "fleeting": ["working", "archived"],
        "working": ["stable", "archived"],
        "stable": ["archived"],
    },
    "theorems": {
        "draft": ["stable", "historical"],
        "stable": ["historical"],
    },
}

AUTO_FIELDS: dict[tuple[str, str], dict[str, str]] = {
    ("ideas", "stable"): {"date_stabilized": "_today_"},
    ("ideas", "archived"): {"date_archived": "_today_"},
    ("theorems", "stable"): {"date_stabilized": "_today_"},
}


def transition(path: str, new_status: str, reason: str = "") -> None:
    file_path = Path(path)
    if not file_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(1)
    entity_type = file_path.parent.name
    if entity_type not in TRANSITIONS:
        print(json.dumps({"status": "error", "message": f"No lifecycle rules for '{entity_type}'"}))
        sys.exit(1)
    frontmatter = _parse_frontmatter(file_path)
    current_status = str(frontmatter.get("status", ""))
    allowed = TRANSITIONS[entity_type].get(current_status)
    if not allowed:
        print(json.dumps({"status": "error", "message": f"Current status '{current_status}' is terminal or unknown"}))
        sys.exit(1)
    if new_status not in allowed:
        print(json.dumps({"status": "error", "message": f"Invalid transition {current_status} -> {new_status}. Allowed: {allowed}"}))
        sys.exit(1)
    content = file_path.read_text(encoding="utf-8")
    content, _, _ = _update_frontmatter_field(content, "status", new_status)
    for field, value in AUTO_FIELDS.get((entity_type, new_status), {}).items():
        actual_value = _today() if value == "_today_" else value
        try:
            content, _, _ = _update_frontmatter_field(content, field, actual_value)
        except ValueError:
            frontmatter = _parse_yaml_block(FRONTMATTER_RE.match(content).group(1))
            frontmatter[field] = actual_value
            match = FRONTMATTER_RE.match(content)
            content = f"---\n{_serialize_frontmatter(frontmatter)}---{content[match.end():]}"
    if reason:
        try:
            content, _, _ = _update_frontmatter_field(content, "transition_note", reason)
        except ValueError:
            frontmatter = _parse_yaml_block(FRONTMATTER_RE.match(content).group(1))
            frontmatter["transition_note"] = reason
            match = FRONTMATTER_RE.match(content)
            content = f"---\n{_serialize_frontmatter(frontmatter)}---{content[match.end():]}"
    file_path.write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "entity": f"{entity_type}/{file_path.stem}",
                "old_status": current_status,
                "new_status": new_status,
            },
            ensure_ascii=False,
        )
    )


def _checkpoint_path(wiki_root: str, task_id: str) -> Path:
    return Path(wiki_root) / ".checkpoints" / f"{task_id}.json"


def _checkpoint_read(wiki_root: str, task_id: str, strict: bool = False) -> dict:
    checkpoint_file = _checkpoint_path(wiki_root, task_id)
    data = {"task_id": task_id, "completed": [], "failed": [], "metadata": {}}
    parse_failed = object()
    if checkpoint_file.exists():
        try:
            loaded = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if strict:
                raise
            loaded = parse_failed
        if isinstance(loaded, dict):
            data.update(loaded)
        elif loaded is not parse_failed and strict:
            raise ValueError("checkpoint top-level JSON is not an object")
    data.setdefault("completed", [])
    data.setdefault("failed", [])
    data.setdefault("metadata", {})
    if not isinstance(data["metadata"], dict):
        data["metadata"] = {}
    return data


def _checkpoint_write(wiki_root: str, task_id: str, data: dict) -> None:
    checkpoint_dir = Path(wiki_root) / ".checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    _checkpoint_path(wiki_root, task_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def checkpoint_save(wiki_root: str, task_id: str, item: str, status: str = "completed") -> None:
    data = _checkpoint_read(wiki_root, task_id)
    target_list = "completed" if status == "completed" else "failed"
    if item not in data[target_list]:
        data[target_list].append(item)
    _checkpoint_write(wiki_root, task_id, data)
    print(json.dumps({"status": "ok", "task_id": task_id, "item": item, "item_status": status}))


def checkpoint_set_meta(wiki_root: str, task_id: str, key: str, value: str) -> None:
    data = _checkpoint_read(wiki_root, task_id)
    data["metadata"][key] = value
    _checkpoint_write(wiki_root, task_id, data)
    print(json.dumps({"status": "ok", "task_id": task_id, "key": key, "value": value}))


def checkpoint_get_meta(wiki_root: str, task_id: str, key: str = "") -> None:
    data = _checkpoint_read(wiki_root, task_id)
    metadata = data.get("metadata", {})
    if key:
        print(metadata.get(key, ""))
        return
    print(json.dumps(metadata, ensure_ascii=False))


def checkpoint_load(wiki_root: str, task_id: str) -> None:
    checkpoint_file = _checkpoint_path(wiki_root, task_id)
    if not checkpoint_file.exists():
        print(json.dumps({"task_id": task_id, "completed": [], "failed": [], "metadata": {}, "exists": False}))
        return
    try:
        data = _checkpoint_read(wiki_root, task_id, strict=True)
    except (json.JSONDecodeError, ValueError):
        print(
            json.dumps(
                {
                    "task_id": task_id,
                    "completed": [],
                    "failed": [],
                    "metadata": {},
                    "exists": False,
                    "error": "corrupt checkpoint",
                }
            )
        )
        return
    data["exists"] = True
    print(json.dumps(data, ensure_ascii=False))


def checkpoint_clear(wiki_root: str, task_id: str) -> None:
    checkpoint_file = _checkpoint_path(wiki_root, task_id)
    if checkpoint_file.exists():
        checkpoint_file.unlink()
    print(json.dumps({"status": "ok", "task_id": task_id, "cleared": True}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Core utilities for the Vicky LLM wiki")
    sub = parser.add_subparsers(dest="command")

    command = sub.add_parser("init", help="Initialize wiki directory structure")
    command.add_argument("wiki_root")

    command = sub.add_parser("slug", help="Generate kebab-case slug from title")
    command.add_argument("title")

    command = sub.add_parser("log", help="Append an audit log entry")
    command.add_argument("wiki_root")
    command.add_argument("message")

    command = sub.add_parser("read-meta", help="Read frontmatter field(s) as JSON")
    command.add_argument("path")
    command.add_argument("field", nargs="?", default=None)

    command = sub.add_parser("set-meta", help="Set a frontmatter field")
    command.add_argument("path")
    command.add_argument("field")
    command.add_argument("value")
    command.add_argument("--append", action="store_true")

    command = sub.add_parser("stats", help="Print wiki statistics")
    command.add_argument("wiki_root")
    command.add_argument("--json", action="store_true")

    command = sub.add_parser("maturity", help="Assess wiki maturity")
    command.add_argument("wiki_root")
    command.add_argument("--json", action="store_true")

    command = sub.add_parser("find", help="Search entities by frontmatter fields")
    command.add_argument("wiki_root")
    command.add_argument("entity_type", choices=INDEXED_DIRS)

    command = sub.add_parser("find-similar-concept", help="Find similar concepts or foundations")
    command.add_argument("wiki_root")
    command.add_argument("title")
    command.add_argument("--aliases", default="")

    command = sub.add_parser("find-similar-theorem", help="Find similar theorem pages")
    command.add_argument("wiki_root")
    command.add_argument("title")
    command.add_argument("--aliases", default="")

    command = sub.add_parser("query", help="Run a wiki query")
    command.add_argument("wiki_root")
    command.add_argument("subquery", choices=["orphans", "deadends"])

    command = sub.add_parser("transition", help="Transition entity lifecycle status")
    command.add_argument("path")
    command.add_argument("--to", dest="new_status", required=True)
    command.add_argument("--reason", default="")

    command = sub.add_parser("checkpoint-save", help="Save item to batch checkpoint")
    command.add_argument("wiki_root")
    command.add_argument("task_id")
    command.add_argument("item")
    command.add_argument("--failed", action="store_true")

    command = sub.add_parser("checkpoint-load", help="Load batch checkpoint state")
    command.add_argument("wiki_root")
    command.add_argument("task_id")

    command = sub.add_parser("checkpoint-clear", help="Clear a checkpoint file")
    command.add_argument("wiki_root")
    command.add_argument("task_id")

    command = sub.add_parser("checkpoint-set-meta", help="Persist a metadata value in a checkpoint")
    command.add_argument("wiki_root")
    command.add_argument("task_id")
    command.add_argument("key")
    command.add_argument("value")

    command = sub.add_parser("checkpoint-get-meta", help="Read checkpoint metadata")
    command.add_argument("wiki_root")
    command.add_argument("task_id")
    command.add_argument("key", nargs="?", default="")

    args = parser.parse_args()

    if args.command == "init":
        init_wiki(args.wiki_root)
        return
    if args.command == "slug":
        print(slugify(args.title))
        return
    if args.command == "log":
        append_log(args.wiki_root, args.message)
        return
    if args.command == "read-meta":
        read_meta(args.path, args.field)
        return
    if args.command == "set-meta":
        set_meta(args.path, args.field, args.value, args.append)
        return
    if args.command == "stats":
        get_stats(args.wiki_root, as_json=args.json)
        return
    if args.command == "maturity":
        get_maturity(args.wiki_root, as_json=args.json)
        return
    if args.command == "find":
        filters: list[tuple[str, str]] = []
        remaining = sys.argv[sys.argv.index("find") + 3 :]
        iterator = iter(remaining)
        for item in iterator:
            if not item.startswith("--"):
                continue
            field_name = item[2:]
            try:
                pattern = next(iterator)
            except StopIteration:
                break
            filters.append((field_name, pattern))
        find_entities(args.wiki_root, args.entity_type, filters)
        return
    if args.command == "find-similar-concept":
        aliases = [item.strip() for item in args.aliases.split(",") if item.strip()]
        find_similar_concept(args.wiki_root, args.title, aliases)
        return
    if args.command == "find-similar-theorem":
        aliases = [item.strip() for item in args.aliases.split(",") if item.strip()]
        find_similar_theorem(args.wiki_root, args.title, aliases)
        return
    if args.command == "query":
        try:
            if args.subquery == "orphans":
                query_orphans(args.wiki_root)
            else:
                query_deadends(args.wiki_root)
        except ValueError as exc:
            print(json.dumps({"status": "error", "message": str(exc)}))
            sys.exit(1)
        return
    if args.command == "transition":
        transition(args.path, args.new_status, args.reason)
        return
    if args.command == "checkpoint-save":
        checkpoint_save(args.wiki_root, args.task_id, args.item, "failed" if args.failed else "completed")
        return
    if args.command == "checkpoint-load":
        checkpoint_load(args.wiki_root, args.task_id)
        return
    if args.command == "checkpoint-clear":
        checkpoint_clear(args.wiki_root, args.task_id)
        return
    if args.command == "checkpoint-set-meta":
        checkpoint_set_meta(args.wiki_root, args.task_id, args.key, args.value)
        return
    if args.command == "checkpoint-get-meta":
        checkpoint_get_meta(args.wiki_root, args.task_id, args.key)
        return
    parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Lint helper for the Vicky LLM wiki."""

from __future__ import annotations

import argparse
import json as json_module
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from frontmatter import FRONTMATTER_RE, parse_frontmatter, parse_scalar as _parse_scalar, serialize_frontmatter as _serialize_frontmatter
from markdown import WIKILINK_RE, find_wikilinks, sanitize_markdown_links
from schema import (
    DEPRECATED_RELATION_FIELDS,
    FIELD_DEFAULTS,
    INDEXED_DIRS,
    RELATION_ALLOWED_TARGET_TYPES,
    RELATION_DISPLAY_NAMES,
    RELATION_FIELDS_BY_PAGE_TYPE,
    RELATION_FIELDS,
    REQUIRED_FIELDS,
    VALID_VALUES,
)
from support_files import SUPPORT_FILE_TEMPLATES, write_support_file

RELATION_LABEL_TO_FIELD = {label.lower(): field for field, label in RELATION_DISPLAY_NAMES.items()}
SOURCE_RELATION_FIELDS = {"relation_extends", "relation_contradicts", "relation_uses", "relation_compares_with"}


class LintIssue:
    def __init__(self, level: str, category: str, file: str, message: str, fixable: bool = False, suggestion: str = ""):
        self.level = level
        self.category = category
        self.file = file
        self.message = message
        self.fixable = fixable
        self.suggestion = suggestion

    def to_dict(self):
        result = {
            "level": self.level,
            "category": self.category,
            "file": self.file,
            "message": self.message,
        }
        if self.fixable:
            result["fixable"] = True
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class FixResult:
    def __init__(self, file: str, action: str):
        self.file = file
        self.action = action

    def to_dict(self):
        return {"file": self.file, "action": self.action}


def extract_frontmatter(content: str) -> dict:
    return parse_frontmatter(content)


def _collect_pages(wiki_dir: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    slug_map: dict[str, list[Path]] = defaultdict(list)
    for subdir in INDEXED_DIRS:
        directory = wiki_dir / subdir
        if not directory.exists():
            continue
        for file_path in directory.glob("*.md"):
            slug_map[file_path.stem].append(file_path)
    pages = {slug: paths[0] for slug, paths in slug_map.items() if len(paths) == 1}
    duplicates = {slug: paths for slug, paths in slug_map.items() if len(paths) > 1}
    return pages, duplicates


def find_all_pages(wiki_dir: Path) -> dict[str, Path]:
    pages, _ = _collect_pages(wiki_dir)
    return pages


def check_duplicate_slugs(wiki_dir: Path, duplicates: dict[str, list[Path]]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, paths in sorted(duplicates.items()):
        rendered = ", ".join(str(path.relative_to(wiki_dir)) for path in paths)
        issues.append(
            LintIssue(
                "🔴",
                "duplicate-slug",
                str(paths[0].relative_to(wiki_dir)),
                f"Slug '{slug}' appears in multiple pages: {rendered}",
            )
        )
    return issues


def check_support_files(wiki_dir: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for filename, template in SUPPORT_FILE_TEMPLATES.items():
        support_specs = {
            "template": template,
            "validators": [lambda content, expected=template: _contains_canonical_template(content, expected)],
            "message": "Support file does not match the current template",
        }
        path = wiki_dir / filename
        if not path.exists():
            issues.append(
                LintIssue(
                    "🔴",
                    "support-file",
                    filename,
                    "Required support file is missing",
                    fixable=True,
                    suggestion=f"Rewrite {filename} from the canonical template",
                )
            )
            continue
        content = path.read_text(encoding="utf-8")
        if all(check(content) for check in support_specs["validators"]):
            continue
        issues.append(
            LintIssue(
                "🔴",
                "support-file",
                filename,
                support_specs["message"],
                fixable=True,
                suggestion=f"Rewrite {filename} from the canonical template",
            )
        )
    return issues


def _contains_canonical_template(content: str, template: str) -> bool:
    try:
        expected = yaml.safe_load(template)
        actual = yaml.safe_load(content)
    except yaml.YAMLError:
        return False
    return _yaml_contains(actual, expected)


def _yaml_contains(actual, expected) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, expected_value in expected.items():
            if key not in actual:
                return False
            if not _yaml_contains(actual[key], expected_value):
                return False
        return True
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        return all(_yaml_contains(actual_item, expected_item) for actual_item, expected_item in zip(actual, expected))
    return actual == expected


def check_missing_fields(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        page_type = file_path.parent.name
        required = REQUIRED_FIELDS.get(page_type, [])
        if not required:
            continue
        frontmatter = extract_frontmatter(file_path.read_text(encoding="utf-8"))
        rel_path = str(file_path.relative_to(wiki_dir))
        for field in required:
            if field in frontmatter:
                continue
            fixable = field in FIELD_DEFAULTS.get(page_type, {})
            suggestion = f"Add required field '{field}'"
            if fixable:
                suggestion += f" with default {FIELD_DEFAULTS[page_type][field]!r}"
            issues.append(LintIssue("🔴", "missing-field", rel_path, f"Missing required field: {field}", fixable, suggestion))
    return issues


def check_slug_fields(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        frontmatter = extract_frontmatter(file_path.read_text(encoding="utf-8"))
        rel_path = str(file_path.relative_to(wiki_dir))
        field_slug = str(frontmatter.get("slug", "")).strip()
        if not field_slug:
            continue
        if field_slug != slug:
            issues.append(
                LintIssue(
                    "🔴",
                    "slug-field",
                    rel_path,
                    f"slug={field_slug!r} does not match filename {slug!r}",
                    fixable=True,
                    suggestion=f"Set slug to {slug!r}",
                )
            )
    return issues


def check_broken_links(
    wiki_dir: Path,
    pages: dict[str, Path],
    duplicates: dict[str, list[Path]] | None = None,
) -> tuple[list[LintIssue], dict[str, set[str]]]:
    issues: list[LintIssue] = []
    duplicate_slugs = duplicates or {}
    incoming = {slug: set() for slug in pages}
    for slug, file_path in pages.items():
        content = file_path.read_text(encoding="utf-8")
        rel_path = str(file_path.relative_to(wiki_dir))
        for target in find_wikilinks(content):
            link_target = _normalize_link_target(target)
            if _is_support_link(link_target):
                continue
            if target in duplicate_slugs:
                duplicate_paths = ", ".join(str(path.relative_to(wiki_dir)) for path in duplicate_slugs[target])
                issues.append(LintIssue("🔴", "ambiguous-link", rel_path, f"[[{target}]] matches multiple pages: {duplicate_paths}"))
                continue
            if link_target in duplicate_slugs:
                duplicate_paths = ", ".join(str(path.relative_to(wiki_dir)) for path in duplicate_slugs[link_target])
                issues.append(LintIssue("🔴", "ambiguous-link", rel_path, f"[[{target}]] matches multiple pages: {duplicate_paths}"))
                continue
            if link_target in pages:
                incoming[link_target].add(slug)
            else:
                issues.append(LintIssue("🟡", "broken-link", rel_path, f"[[{target}]] -> file not found", suggestion=f"Remove [[{target}]] or create {target}.md"))
    return issues, incoming


def check_orphan_pages(wiki_dir: Path, pages: dict[str, Path], incoming: dict[str, set[str]]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        if file_path.parent.name == "outputs":
            continue
        if incoming.get(slug):
            continue
        issues.append(LintIssue("🔵", "orphan", str(file_path.relative_to(wiki_dir)), "No incoming links"))
    return issues


def check_field_values(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    field_map: dict[str, list[tuple[str, str]]] = {}
    for key in VALID_VALUES:
        entity, field = key.split(".", 1)
        field_map.setdefault(entity, []).append((field, key))

    for slug, file_path in pages.items():
        page_type = file_path.parent.name
        rel_path = str(file_path.relative_to(wiki_dir))
        frontmatter = extract_frontmatter(file_path.read_text(encoding="utf-8"))
        for field, key in field_map.get(page_type, []):
            if field not in frontmatter:
                continue
            value = frontmatter[field]
            if str(value) not in VALID_VALUES[key]:
                issues.append(LintIssue("🔴", "invalid-value", rel_path, f"{field}={value!r} is invalid for {key}"))
    return issues


def _as_list(value) -> list:
    if value in ("", None):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_link_target(value) -> str:
    text = str(value).strip().strip('"').strip("'")
    match = WIKILINK_RE.fullmatch(text)
    if match:
        text = match.group(1)
    return text.split("#", 1)[0]


def _is_support_link(target: str) -> bool:
    return target.endswith(".base") or target.startswith("raw/")


def _section_body(content: str, heading: str) -> str:
    heading_match = re.search(rf"^{re.escape(heading)}\s*$", content, re.MULTILINE)
    if not heading_match:
        return ""
    start = heading_match.end()
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    if not next_heading:
        return content[start:]
    return content[start : start + next_heading.start()]


def check_deprecated_relation_fields(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for file_path in pages.values():
        frontmatter = extract_frontmatter(file_path.read_text(encoding="utf-8"))
        rel_path = str(file_path.relative_to(wiki_dir))
        for field in DEPRECATED_RELATION_FIELDS:
            if field not in frontmatter:
                continue
            issues.append(
                LintIssue(
                    "🔴",
                    "deprecated-relation",
                    rel_path,
                    f"{field} is deprecated",
                    suggestion=f"Remove {field} and rewrite the edge with the remaining relation fields",
                )
            )
    return issues


def check_relation_target_ranges(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for file_path in pages.values():
        page_type = file_path.parent.name
        frontmatter = extract_frontmatter(file_path.read_text(encoding="utf-8"))
        rel_path = str(file_path.relative_to(wiki_dir))
        allowed_fields = RELATION_FIELDS_BY_PAGE_TYPE.get(page_type, set())
        for field in RELATION_FIELDS:
            if field in frontmatter and field not in allowed_fields:
                suggestion = f"Remove {field} from wiki/{page_type} pages"
                if page_type == "people":
                    suggestion = "Remove relation_* fields from people pages and keep source provenance in key_sources"
                issues.append(
                    LintIssue(
                        "🔴",
                        "relation-field",
                        rel_path,
                        f"{field} is not allowed on wiki/{page_type}",
                        suggestion=suggestion,
                    )
                )
                continue
            for raw_value in _as_list(frontmatter.get(field)):
                target = _normalize_link_target(raw_value)
                if not target or target not in pages:
                    continue
                allowed_types = set(RELATION_ALLOWED_TARGET_TYPES.get(field, set()))
                if page_type == "sources" and field in SOURCE_RELATION_FIELDS:
                    allowed_types.add("sources")
                if not allowed_types:
                    continue
                target_type = pages[target].parent.name
                if target_type in allowed_types:
                    continue
                label = RELATION_DISPLAY_NAMES[field]
                allowed_rendered = ", ".join(sorted(allowed_types))
                issues.append(
                    LintIssue(
                        "🔴",
                        "relation-range",
                        rel_path,
                        f"{label} points to [[{target}]] in wiki/{target_type}, allowed targets are: {allowed_rendered}",
                        suggestion=f"Move [[{target}]] to a matching relation field or change the target page type",
                    )
                )
    return issues


def check_relation_consistency(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        content = file_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        rel_path = str(file_path.relative_to(wiki_dir))
        relations_body = _section_body(content, "## Relations")
        sanitized_relations_body = sanitize_markdown_links(relations_body)
        body_targets_by_field: dict[str, set[str]] = {field: set() for field in RELATION_FIELDS}
        property_targets_by_field: dict[str, set[str]] = {field: set() for field in RELATION_FIELDS}

        for line in sanitized_relations_body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            line_targets = {
                normalized
                for target in find_wikilinks(stripped)
                if (normalized := _normalize_link_target(target))
            }
            if not line_targets:
                continue
            lowered = stripped.lower()
            field = None
            label_text = ""
            for relation_label, relation_field in RELATION_LABEL_TO_FIELD.items():
                if lowered.startswith(f"- {relation_label} ") or lowered.startswith(f"- {relation_label}:"):
                    field = relation_field
                    label_text = RELATION_DISPLAY_NAMES[relation_field]
                    break
            if field is None:
                label_match = re.match(r"^-\s*([^:\[]+?)(?:\s+\[\[|:)", stripped)
                label_text = label_match.group(1).strip() if label_match else stripped[2:].strip()
                internal_targets = sorted(target for target in line_targets if target in pages)
                if internal_targets:
                    rendered = ", ".join(f"[[{target}]]" for target in internal_targets)
                    issues.append(
                        LintIssue(
                            "🟡",
                            "relation",
                            rel_path,
                            f"## Relations uses unknown relation label '{label_text}' for {rendered}",
                            suggestion="Use one of: Derived from, Extends, Contradicts, Uses, Compares with",
                        )
                    )
                continue
            body_targets_by_field[field].update(target for target in line_targets if target in pages)

        for field in RELATION_FIELDS:
            for raw_value in _as_list(frontmatter.get(field)):
                target = _normalize_link_target(raw_value)
                if not target:
                    continue
                property_targets_by_field[field].add(target)
                if target not in pages:
                    issues.append(
                        LintIssue(
                            "🟡",
                            "relation",
                            rel_path,
                            f"{field} points to missing page [[{target}]]",
                            suggestion=f"Create {target}.md or remove it from {field}",
                        )
                    )
                    continue
                if target not in body_targets_by_field[field]:
                    issues.append(
                        LintIssue(
                            "🟡",
                            "relation",
                            rel_path,
                            f"{field} includes [[{target}]] but ## Relations lacks a matching {RELATION_DISPLAY_NAMES[field]} explanation",
                            suggestion=f"Add a ## Relations bullet starting with '{RELATION_DISPLAY_NAMES[field]}:' for [[{target}]]",
                        )
                    )

        for field, body_targets in body_targets_by_field.items():
            for target in body_targets:
                if target in property_targets_by_field[field]:
                    continue
                matching_fields = [name for name, targets in property_targets_by_field.items() if target in targets]
                if matching_fields:
                    rendered = ", ".join(matching_fields)
                    issues.append(
                        LintIssue(
                            "🟡",
                            "relation",
                            rel_path,
                            f"## Relations labels [[{target}]] as {RELATION_DISPLAY_NAMES[field]} but the property stores it under {rendered}",
                            suggestion=f"Move [[{target}]] to {field} or change the ## Relations label",
                        )
                    )
                    continue
                issues.append(
                    LintIssue(
                        "🟡",
                        "relation",
                        rel_path,
                        f"## Relations labels [[{target}]] as {RELATION_DISPLAY_NAMES[field]} but no relation_* property includes it",
                        suggestion=f"Add [[{target}]] to {field}",
                    )
                )
    return issues


def check_cross_references(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        page_type = file_path.parent.name
        content = file_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        rel_path = str(file_path.relative_to(wiki_dir))
        if page_type == "sources":
            continue

        field_name = "key_sources" if page_type == "people" else "relation_derived_from"
        for source_slug in (_normalize_link_target(value) for value in _as_list(frontmatter.get(field_name))):
            if not source_slug:
                continue
            source_path = wiki_dir / "sources" / f"{source_slug}.md"
            if not source_path.exists():
                if page_type == "people":
                    issues.append(LintIssue("🟡", "xref", rel_path, f"{field_name} has {source_slug} but sources/{source_slug}.md is missing"))
                continue
            source_content = source_path.read_text(encoding="utf-8")
            if f"[[{slug}]]" not in source_content:
                issues.append(
                    LintIssue(
                        "🟡",
                        "xref",
                        rel_path,
                        f"{field_name} has {source_slug} but sources/{source_slug}.md does not link back to [[{slug}]]",
                        fixable=True,
                        suggestion=f"Add [[{slug}]] to sources/{source_slug}.md body text or ## Notes",
                    )
                )
    return issues


def _append_to_section(path: Path, heading: str, line: str) -> None:
    content = path.read_text(encoding="utf-8")
    if line in content:
        return
    heading_match = re.search(rf"^{re.escape(heading)}\s*$", content, re.MULTILINE)
    if not heading_match:
        content = content.rstrip() + f"\n\n{heading}\n\n{line}\n"
        path.write_text(content, encoding="utf-8")
        return
    insert_at = heading_match.end()
    while insert_at < len(content) and content[insert_at] == "\n":
        insert_at += 1
    updated = content[:insert_at] + line + "\n" + content[insert_at:]
    path.write_text(updated, encoding="utf-8")


def _fix_missing_field(wiki_dir: Path, issue: LintIssue) -> FixResult | None:
    match = re.search(r"Missing required field: (\w+)", issue.message)
    if not match:
        return None
    field = match.group(1)
    page_path = wiki_dir / issue.file
    page_type = page_path.parent.name
    default_value = FIELD_DEFAULTS.get(page_type, {}).get(field)
    if default_value is None:
        return None
    content = page_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(content)
    frontmatter[field] = _parse_scalar(default_value)
    match_fm = FRONTMATTER_RE.match(content)
    if not match_fm:
        return None
    updated = f"---\n{_serialize_frontmatter(frontmatter)}---{content[match_fm.end():]}"
    page_path.write_text(updated, encoding="utf-8")
    return FixResult(issue.file, f"Add {field}: {default_value}")


def _fix_slug_field(wiki_dir: Path, issue: LintIssue) -> FixResult | None:
    page_path = wiki_dir / issue.file
    content = page_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(content)
    match_fm = FRONTMATTER_RE.match(content)
    if not match_fm:
        return None
    frontmatter["slug"] = page_path.stem
    updated = f"---\n{_serialize_frontmatter(frontmatter)}---{content[match_fm.end():]}"
    page_path.write_text(updated, encoding="utf-8")
    return FixResult(issue.file, f"Set slug to {page_path.stem}")


def _fix_xref(wiki_dir: Path, issue: LintIssue) -> FixResult | None:
    match = re.search(r"sources/(\S+)\.md does not link back to \[\[(\S+)\]\]", issue.message)
    if not match:
        return None
    source_slug, target_slug = match.groups()
    source_path = wiki_dir / "sources" / f"{source_slug}.md"
    _append_to_section(source_path, "## Notes", f"- [[{target_slug}]]")
    return FixResult(f"sources/{source_slug}.md", f"Add [[{target_slug}]] to ## Notes")


def _fix_support_file(wiki_dir: Path, issue: LintIssue) -> FixResult | None:
    if issue.file not in SUPPORT_FILE_TEMPLATES:
        return None
    write_support_file(wiki_dir, issue.file, overwrite=True)
    return FixResult(issue.file, "Rewrite from canonical template")


def apply_fixes(wiki_dir: Path, issues: list[LintIssue], dry_run: bool = False) -> list[FixResult]:
    fixes: list[FixResult] = []
    for issue in issues:
        if not issue.fixable:
            continue
        if issue.category == "support-file":
            if dry_run:
                fixes.append(FixResult(issue.file, "Rewrite from canonical template"))
                continue
            result = _fix_support_file(wiki_dir, issue)
            if result:
                fixes.append(result)
            continue
        if "Missing required field" in issue.message:
            if dry_run:
                match = re.search(r"Missing required field: (\w+)", issue.message)
                if match:
                    fixes.append(FixResult(issue.file, f"Add {match.group(1)} with default value"))
                continue
            result = _fix_missing_field(wiki_dir, issue)
            if result:
                fixes.append(result)
            continue
        if issue.category == "slug-field":
            if dry_run:
                page_path = wiki_dir / issue.file
                fixes.append(FixResult(issue.file, f"Set slug to {page_path.stem}"))
                continue
            result = _fix_slug_field(wiki_dir, issue)
            if result:
                fixes.append(result)
            continue
        if "does not link back" in issue.message:
            if dry_run:
                fixes.append(FixResult(issue.file, issue.suggestion or "Repair reverse link"))
                continue
            result = _fix_xref(wiki_dir, issue)
            if result:
                fixes.append(result)
    return fixes


def run_lint(wiki_dir: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    issues.extend(check_support_files(wiki_dir))
    pages, duplicates = _collect_pages(wiki_dir)
    issues.extend(check_duplicate_slugs(wiki_dir, duplicates))
    issues.extend(check_missing_fields(wiki_dir, pages))
    issues.extend(check_slug_fields(wiki_dir, pages))
    broken, incoming = check_broken_links(wiki_dir, pages, duplicates)
    issues.extend(broken)
    issues.extend(check_orphan_pages(wiki_dir, pages, incoming))
    issues.extend(check_field_values(wiki_dir, pages))
    issues.extend(check_deprecated_relation_fields(wiki_dir, pages))
    issues.extend(check_relation_target_ranges(wiki_dir, pages))
    issues.extend(check_relation_consistency(wiki_dir, pages))
    issues.extend(check_cross_references(wiki_dir, pages))
    return issues


def print_human_report(issues: list[LintIssue], fixes: list[FixResult] | None = None) -> None:
    buckets = {"🔴": [], "🟡": [], "🔵": []}
    for issue in issues:
        buckets[issue.level].append(issue)
    print("## Lint Report")
    print(f"\n**Summary**: {len(buckets['🔴'])} 🔴, {len(buckets['🟡'])} 🟡, {len(buckets['🔵'])} 🔵")
    for level, title in (("🔴", "Fix Immediately"), ("🟡", "Recommended Fixes"), ("🔵", "Optional Improvements")):
        print(f"\n### {level} {title}")
        if not buckets[level]:
            print("- none")
            continue
        for issue in buckets[level]:
            print(f"- [{issue.file}] {issue.message}")
    if fixes:
        print("\n### Auto-fixes")
        for fix in fixes:
            print(f"- [{fix.file}] {fix.action}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-dir", default="wiki", help="Wiki directory to lint")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human report")
    parser.add_argument("--fix", action="store_true", help="Apply deterministic fixes")
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without applying them")
    parser.add_argument("--suggest", action="store_true", help="Include suggestions in JSON output")
    args = parser.parse_args()

    wiki_dir = Path(args.wiki_dir).resolve()
    if not wiki_dir.exists():
        print(json_module.dumps({"status": "error", "message": f"wiki directory not found: {wiki_dir}"}))
        sys.exit(1)

    issues = run_lint(wiki_dir)
    fixes: list[FixResult] = []
    if args.fix:
        fixes = apply_fixes(wiki_dir, issues, dry_run=args.dry_run)

    if args.json:
        payload = {
            "status": "ok",
            "issues": [issue.to_dict() for issue in issues],
            "summary": {
                "red": sum(1 for issue in issues if issue.level == "🔴"),
                "yellow": sum(1 for issue in issues if issue.level == "🟡"),
                "blue": sum(1 for issue in issues if issue.level == "🔵"),
            },
            "fixes": [fix.to_dict() for fix in fixes],
        }
        if args.suggest:
            payload["suggestions"] = [issue.to_dict() for issue in issues if issue.suggestion]
        print(json_module.dumps(payload, ensure_ascii=False, indent=2))
        return

    print_human_report(issues, fixes)


if __name__ == "__main__":
    main()

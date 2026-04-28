#!/usr/bin/env python3
"""Lint helper for the Vicky LLM wiki."""

from __future__ import annotations

import argparse
import json as json_module
import re
import sys
from collections import defaultdict
from pathlib import Path

from _schemas import FIELD_DEFAULTS, INDEXED_DIRS, RELATION_FIELDS, REQUIRED_FIELDS, VALID_VALUES
from _frontmatter import FRONTMATTER_RE, parse_frontmatter, parse_scalar as _parse_scalar, serialize_frontmatter as _serialize_frontmatter
from _support_files import LOG_TEMPLATE, SUPPORT_FILE_TEMPLATES, write_support_file

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


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
    support_specs = {
        "log.md": {
            "template": LOG_TEMPLATE,
            "validators": [lambda content: content.startswith("# Vicky Log\n")],
            "message": "Support file does not match the current wiki log template",
        },
    }
    for filename, template in SUPPORT_FILE_TEMPLATES.items():
        if filename == "log.md":
            continue
        support_specs[filename] = {
            "template": template,
            "validators": [
                lambda content: content.startswith("filters:\n"),
                lambda content: "formulas:\n" in content,
                lambda content: "views:\n" in content,
            ],
            "message": "Support base does not match the current base template",
        }
    for filename, spec in support_specs.items():
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
        if all(check(content) for check in spec["validators"]):
            continue
        issues.append(
            LintIssue(
                "🔴",
                "support-file",
                filename,
                spec["message"],
                fixable=True,
                suggestion=f"Rewrite {filename} from the canonical template",
            )
        )
    return issues


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
        for target in WIKILINK_RE.findall(content):
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


def _extract_inline_list(content: str, field: str) -> list[str]:
    match = re.search(rf"{re.escape(field)}:\s*\[(.*?)\]", content, re.DOTALL)
    if not match:
        return []
    inner = match.group(1)
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


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
    return target.endswith(".base")


def _section_body(content: str, heading: str) -> str:
    heading_match = re.search(rf"^{re.escape(heading)}\s*$", content, re.MULTILINE)
    if not heading_match:
        return ""
    start = heading_match.end()
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    if not next_heading:
        return content[start:]
    return content[start : start + next_heading.start()]


def check_relation_consistency(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        content = file_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        rel_path = str(file_path.relative_to(wiki_dir))
        relations_body = _section_body(content, "## Relations")
        body_targets = set(WIKILINK_RE.findall(relations_body))
        property_targets: set[str] = set()

        for field in RELATION_FIELDS:
            for raw_value in _as_list(frontmatter.get(field)):
                target = _normalize_link_target(raw_value)
                if not target:
                    continue
                property_targets.add(target)
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
                if target not in body_targets:
                    issues.append(
                        LintIssue(
                            "🟡",
                            "relation",
                            rel_path,
                            f"{field} includes [[{target}]] but ## Relations lacks matching explanation",
                            suggestion=f"Add a ## Relations bullet explaining [[{target}]]",
                        )
                    )

        for target in body_targets - property_targets:
            if target not in pages:
                continue
            issues.append(
                LintIssue(
                    "🟡",
                    "relation",
                    rel_path,
                    f"## Relations mentions [[{target}]] but no relation_* property includes it",
                    suggestion=f"Add [[{target}]] to the matching relation_* field",
                )
            )
    return issues


def check_cross_references(wiki_dir: Path, pages: dict[str, Path]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for slug, file_path in pages.items():
        page_type = file_path.parent.name
        content = file_path.read_text(encoding="utf-8")
        rel_path = str(file_path.relative_to(wiki_dir))
        if page_type not in {"concepts", "theorems", "people"}:
            continue

        field_name = "key_sources"
        for source_slug in _extract_inline_list(content, field_name):
            source_path = wiki_dir / "sources" / f"{source_slug}.md"
            if not source_path.exists():
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
                        suggestion=f"Add [[{slug}]] to sources/{source_slug}.md ## Related",
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


def _fix_xref(wiki_dir: Path, issue: LintIssue) -> FixResult | None:
    match = re.search(r"sources/(\S+)\.md does not link back to \[\[(\S+)\]\]", issue.message)
    if not match:
        return None
    source_slug, target_slug = match.groups()
    source_path = wiki_dir / "sources" / f"{source_slug}.md"
    _append_to_section(source_path, "## Related", f"- [[{target_slug}]]")
    return FixResult(f"sources/{source_slug}.md", f"Add [[{target_slug}]] to ## Related")


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
    broken, incoming = check_broken_links(wiki_dir, pages, duplicates)
    issues.extend(broken)
    issues.extend(check_orphan_pages(wiki_dir, pages, incoming))
    issues.extend(check_field_values(wiki_dir, pages))
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

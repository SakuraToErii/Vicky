"""Tests for .tools/lint.py."""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / ".tools"
sys.path.insert(0, str(TOOLS_DIR))
import _schemas as schema_mod
import lint as lint_mod


def test_relation_schema_is_frozen():
    assert schema_mod.RELATION_SCHEMA_STATUS == "frozen"
    assert schema_mod.RELATION_FIELDS == [
        "relation_derived_from",
        "relation_extends",
        "relation_supports",
        "relation_contradicts",
        "relation_uses",
        "relation_compares_with",
    ]
    assert "six existing fields" in schema_mod.RELATION_SCHEMA_CHANGE_POLICY


@pytest.fixture
def wiki_dir(tmp_path):
    for name in lint_mod.INDEXED_DIRS:
        (tmp_path / name).mkdir()
    for relative_path, content in schema_mod.BASE_FILE_TEMPLATES.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (tmp_path / "log.md").write_text("# Vicky Log\n", encoding="utf-8")
    return tmp_path


def _write_page(wiki_dir, entity_type, slug, frontmatter_lines, body=""):
    frontmatter = "\n".join(frontmatter_lines)
    path = wiki_dir / entity_type / f"{slug}.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


class TestMissingFields:
    def test_source_missing_source_path(self, wiki_dir):
        _write_page(wiki_dir, "sources", "paper-a", ['title: "Paper A"', "slug: paper-a", "source_kind: paper"])
        issues = lint_mod.check_missing_fields(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("source_path" in issue.message for issue in issues)

    def test_theorem_missing_status(self, wiki_dir):
        _write_page(wiki_dir, "theorems", "bound", ['title: "Bound"', "slug: bound", "theorem_kind: theorem", "key_sources: [paper-a]"])
        issues = lint_mod.check_missing_fields(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("status" in issue.message for issue in issues)


class TestBrokenLinks:
    def test_broken_link_detected(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
            "See [[missing-page]]",
        )
        issues, _ = lint_mod.check_broken_links(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("missing-page" in issue.message for issue in issues)

    def test_base_embed_is_support_link(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: []", "maturity: seed", "key_sources: []"],
            "![[Current Page Neighbors.base#Semantic neighbors]]",
        )
        issues, _ = lint_mod.check_broken_links(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert not issues

    def test_code_block_link_is_ignored(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: []", "maturity: seed", "key_sources: []"],
            "```md\n[[missing-page]]\n```",
        )
        issues, _ = lint_mod.check_broken_links(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert not issues

    def test_html_comment_link_is_ignored(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: []", "maturity: seed", "key_sources: []"],
            "<!-- [[missing-page]] -->",
        )
        issues, _ = lint_mod.check_broken_links(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert not issues


class TestSupportFiles:
    def test_invalid_support_files_detected_and_fixed(self, wiki_dir):
        (wiki_dir / "log.md").write_text("# Wiki Log\n\nlegacy\n", encoding="utf-8")
        issues = lint_mod.run_lint(wiki_dir)
        support_issues = [issue for issue in issues if issue.category == "support-file"]
        assert {issue.file for issue in support_issues} == {"log.md"}

        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        assert any(fix.file == "log.md" for fix in fixes)
        assert (wiki_dir / "log.md").read_text(encoding="utf-8") == lint_mod.LOG_TEMPLATE

    def test_missing_base_support_file_detected_and_fixed(self, wiki_dir):
        missing_base = next(iter(schema_mod.BASE_FILE_TEMPLATES))
        (wiki_dir / missing_base).unlink()
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.file == missing_base for issue in issues)

        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        assert any(fix.file == missing_base for fix in fixes)
        assert (wiki_dir / missing_base).read_text(encoding="utf-8") == schema_mod.BASE_FILE_TEMPLATES[missing_base]

    def test_malformed_base_support_file_detected_and_fixed(self, wiki_dir):
        malformed_base = next(iter(schema_mod.BASE_FILE_TEMPLATES))
        (wiki_dir / malformed_base).write_text("filters:\n  and: []\nformulas:\nviews:\n", encoding="utf-8")
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.file == malformed_base for issue in issues)

        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        assert any(fix.file == malformed_base for fix in fixes)
        assert (wiki_dir / malformed_base).read_text(encoding="utf-8") == schema_mod.BASE_FILE_TEMPLATES[malformed_base]

    def test_base_support_file_allows_extra_ui_state(self, wiki_dir):
        base_name = next(iter(schema_mod.BASE_FILE_TEMPLATES))
        base_path = wiki_dir / base_name
        base_path.write_text(
            schema_mod.BASE_FILE_TEMPLATES[base_name] + "\nuiState:\n  columnSize:\n    file.path: 280\n",
            encoding="utf-8",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert not any(issue.file == base_name and issue.category == "support-file" for issue in issues)

    def test_duplicate_slug_detected(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "shared-slug",
            ['title: "Source A"', "slug: shared-slug", "source_kind: paper", "source_path: raw/papers/a.tex"],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "shared-slug",
            ['title: "Shared Slug"', "slug: shared-slug", "tags: [ml]", "maturity: working", "key_sources: []"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "duplicate-slug" for issue in issues)


class TestOrphans:
    def test_orphan_detected(self, wiki_dir):
        _write_page(
            wiki_dir,
            "people",
            "john-doe",
            ['name: "John Doe"', "slug: john-doe", "tags: [ml]", "key_sources: []"],
        )
        pages = lint_mod.find_all_pages(wiki_dir)
        _, incoming = lint_mod.check_broken_links(wiki_dir, pages)
        issues = lint_mod.check_orphan_pages(wiki_dir, pages, incoming)
        assert any("john-doe" in issue.file for issue in issues)


class TestFieldValues:
    def test_invalid_theorem_kind(self, wiki_dir):
        _write_page(
            wiki_dir,
            "theorems",
            "bound",
            ['title: "Bound"', "slug: bound", "theorem_kind: miracle", "status: draft", "key_sources: [paper-a]", "tags: [ml]"],
        )
        issues = lint_mod.check_field_values(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("theorem_kind" in issue.message for issue in issues)


class TestCrossReferences:
    def test_missing_source_backlink(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
            "## Summary\n\nSome text",
        )
        _write_page(
            wiki_dir,
            "concepts",
            "flash-attention",
            ['title: "Flash Attention"', "slug: flash-attention", "tags: [attention]", "maturity: working", "key_sources: [paper-a]"],
        )
        issues = lint_mod.check_cross_references(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("does not link back" in issue.message for issue in issues)

    def test_fix_adds_source_backlink(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
            "## Summary\n\nSome text",
        )
        _write_page(
            wiki_dir,
            "concepts",
            "flash-attention",
            ['title: "Flash Attention"', "slug: flash-attention", "tags: [attention]", "maturity: working", "key_sources: [paper-a]"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        content = (wiki_dir / "sources" / "paper-a.md").read_text(encoding="utf-8")
        assert "[[flash-attention]]" in content
        assert fixes


class TestRelationConsistency:
    def test_relation_property_requires_body_explanation(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            [
                'title: "Concept A"',
                "slug: concept-a",
                "tags: [ml]",
                "maturity: working",
                "key_sources: [paper-a]",
                'relation_derived_from: ["[[paper-a]]"]',
            ],
            "## Relations\n\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("lacks matching explanation" in issue.message for issue in issues)

    def test_relation_body_requires_property(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]", "maturity: working", "key_sources: [paper-a]"],
            "## Relations\n\n- Derived from [[paper-a]]: uses its setup.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("no relation_* property includes it" in issue.message for issue in issues)

    def test_relation_property_body_pair_passes(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex", 'relation_uses: []'],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            [
                'title: "Concept A"',
                "slug: concept-a",
                "tags: [ml]",
                "maturity: working",
                "key_sources: [paper-a]",
                'relation_derived_from: ["[[paper-a]]"]',
            ],
            "## Relations\n\n- Derived from [[paper-a]]: uses its setup.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert not any(issue.category == "relation" for issue in issues)

    def test_relation_block_list_pair_passes(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            [
                'title: "Concept A"',
                "slug: concept-a",
                "tags: [ml]",
                "maturity: working",
                "key_sources: [paper-a]",
                "relation_derived_from:",
                '  - "[[paper-a]]"',
            ],
            "## Relations\n\n- Derived from [[paper-a]]: uses its setup.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert not any(issue.category == "relation" for issue in issues)

    def test_relation_heading_link_pair_passes(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
            "## Summary\n\nKey detail.\n",
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            [
                'title: "Concept A"',
                "slug: concept-a",
                "tags: [ml]",
                "maturity: working",
                "key_sources: [paper-a]",
                'relation_derived_from: ["[[paper-a]]"]',
            ],
            "## Relations\n\n- Derived from [[paper-a#Summary]]: cites the relevant section.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert not any(issue.category == "relation" for issue in issues)

    def test_relation_code_block_link_does_not_count_as_explanation(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            [
                'title: "Concept A"',
                "slug: concept-a",
                "tags: [ml]",
                "maturity: working",
                "key_sources: [paper-a]",
                'relation_derived_from: ["[[paper-a]]"]',
            ],
            "## Relations\n\n```md\n- Derived from [[paper-a]]\n```\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("lacks matching explanation" in issue.message for issue in issues)


class TestCliJson:
    def test_json_payload_shape(self, wiki_dir, capsys):
        _write_page(wiki_dir, "sources", "paper-a", ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"])
        issues = lint_mod.run_lint(wiki_dir)
        payload = {
            "status": "ok",
            "issues": [issue.to_dict() for issue in issues],
            "summary": {
                "red": sum(1 for issue in issues if issue.level == "🔴"),
                "yellow": sum(1 for issue in issues if issue.level == "🟡"),
                "blue": sum(1 for issue in issues if issue.level == "🔵"),
            },
        }
        print(json.dumps(payload, ensure_ascii=False))
        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["status"] == "ok"

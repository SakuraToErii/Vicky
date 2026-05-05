"""Tests for check skill lint tool."""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
SCRIPTS_DIR = PROJECT_ROOT / ".codex" / "skills" / "check" / "scripts"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
import lint as lint_mod
import schema as schema_mod


def test_relation_schema_is_frozen():
    assert schema_mod.RELATION_SCHEMA_STATUS == "frozen"
    assert schema_mod.RELATION_FIELDS == [
        "relation_derived_from",
        "relation_extends",
        "relation_contradicts",
        "relation_uses",
        "relation_compares_with",
    ]
    assert "five existing fields" in schema_mod.RELATION_SCHEMA_CHANGE_POLICY


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

    def test_theorem_missing_tags(self, wiki_dir):
        _write_page(wiki_dir, "theorems", "bound", ['title: "Bound"', "slug: bound", "theorem_kind: theorem"])
        issues = lint_mod.check_missing_fields(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("tags" in issue.message for issue in issues)


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
        invalid_base = next(iter(schema_mod.BASE_FILE_TEMPLATES))
        (wiki_dir / invalid_base).write_text("filters:\n  and: []\n", encoding="utf-8")
        issues = lint_mod.run_lint(wiki_dir)
        support_issues = [issue for issue in issues if issue.category == "support-file"]
        assert {issue.file for issue in support_issues} == {invalid_base}

        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        assert any(fix.file == invalid_base for fix in fixes)
        assert (wiki_dir / invalid_base).read_text(encoding="utf-8") == schema_mod.BASE_FILE_TEMPLATES[invalid_base]

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

    def test_base_support_file_allows_unquoted_yaml_scalars(self, wiki_dir):
        base_name = next(iter(schema_mod.BASE_FILE_TEMPLATES))
        base_path = wiki_dir / base_name
        base_path.write_text(schema_mod.BASE_FILE_TEMPLATES[base_name].replace("'", ""), encoding="utf-8")
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
            ['title: "John Doe"', "slug: john-doe", "tags: [ml]", "key_sources: []"],
        )
        pages = lint_mod.find_all_pages(wiki_dir)
        _, incoming = lint_mod.check_broken_links(wiki_dir, pages)
        issues = lint_mod.check_orphan_pages(wiki_dir, pages, incoming)
        assert any("john-doe" in issue.file for issue in issues)


class TestSlugField:
    def test_slug_field_mismatch_detected_and_fixed(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "flash-attention",
            ['title: "Flash Attention"', "slug: flash-attention-v2", "tags: [attention]", "maturity: working", "key_sources: []"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "slug-field" for issue in issues)

        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        assert any(fix.action == "Set slug to flash-attention" for fix in fixes)
        content = (wiki_dir / "concepts" / "flash-attention.md").read_text(encoding="utf-8")
        assert "slug: flash-attention\n" in content


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
            ['title: "Flash Attention"', "slug: flash-attention", "tags: [attention]", 'relation_derived_from: ["[[paper-a]]"]'],
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
            ['title: "Flash Attention"', "slug: flash-attention", "tags: [attention]", 'relation_derived_from: ["[[paper-a]]"]'],
        )
        issues = lint_mod.run_lint(wiki_dir)
        fixes = lint_mod.apply_fixes(wiki_dir, issues, dry_run=False)
        content = (wiki_dir / "sources" / "paper-a.md").read_text(encoding="utf-8")
        assert "[[flash-attention]]" in content
        assert fixes

    def test_block_list_key_sources_are_checked(self, wiki_dir):
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
            [
                'title: "Flash Attention"',
                "slug: flash-attention",
                "tags: [attention]",
                "relation_derived_from:",
                "  - paper-a",
            ],
        )
        issues = lint_mod.check_cross_references(wiki_dir, lint_mod.find_all_pages(wiki_dir))
        assert any("does not link back" in issue.message for issue in issues)


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
        assert any("lacks a matching Derived from explanation" in issue.message for issue in issues)

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

    def test_relation_label_mismatch_detected(self, wiki_dir):
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
                'relation_derived_from: ["[[paper-a]]"]',
            ],
            "## Relations\n\n- Uses: [[paper-a]] provides the source material.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("labels [[paper-a]] as Uses" in issue.message for issue in issues)

    def test_unknown_relation_label_detected(self, wiki_dir):
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
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]"],
            "## Relations\n\n- Supports: [[paper-a]] carries a legacy label.\n",
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("unknown relation label 'Supports'" in issue.message for issue in issues)


class TestRelationRanges:
    def test_deprecated_relation_supports_is_rejected(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]", 'relation_supports: ["[[concept-b]]"]'],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-b",
            ['title: "Concept B"', "slug: concept-b", "tags: [ml]"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "deprecated-relation" for issue in issues)

    def test_relation_derived_from_requires_source_targets(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]", 'relation_derived_from: ["[[concept-b]]"]'],
        )
        _write_page(
            wiki_dir,
            "concepts",
            "concept-b",
            ['title: "Concept B"', "slug: concept-b", "tags: [ml]"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("allowed targets are: sources" in issue.message for issue in issues)

    def test_relation_uses_rejects_source_targets(self, wiki_dir):
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
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]", 'relation_uses: ["[[paper-a]]"]'],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any("Uses points to [[paper-a]] in wiki/sources" in issue.message for issue in issues)

    def test_people_pages_keep_source_provenance_in_key_sources(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "people",
            "john-doe",
            ['title: "John Doe"', "slug: john-doe", "tags: [ml]", 'relation_derived_from: ["[[paper-a]]"]'],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "relation-field" and "wiki/people" in issue.message for issue in issues)

    def test_source_pages_do_not_use_relation_derived_from(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            [
                'title: "Paper A"',
                "slug: paper-a",
                "source_kind: paper",
                "source_path: raw/papers/paper-a.tex",
                'relation_derived_from: ["[[paper-b]]"]',
            ],
        )
        _write_page(
            wiki_dir,
            "sources",
            "paper-b",
            ['title: "Paper B"', "slug: paper-b", "source_kind: paper", "source_path: raw/papers/paper-b.tex"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "relation-field" and "wiki/sources" in issue.message for issue in issues)

    def test_foundation_pages_do_not_use_relation_derived_from_or_contradicts(self, wiki_dir):
        _write_page(
            wiki_dir,
            "sources",
            "paper-a",
            ['title: "Paper A"', "slug: paper-a", "source_kind: paper", "source_path: raw/papers/paper-a.tex"],
        )
        _write_page(
            wiki_dir,
            "foundations",
            "foundation-a",
            [
                'title: "Foundation A"',
                "slug: foundation-a",
                "tags: [ml]",
                'relation_derived_from: ["[[paper-a]]"]',
                'relation_contradicts: ["[[foundation-b]]"]',
            ],
        )
        _write_page(
            wiki_dir,
            "foundations",
            "foundation-b",
            ['title: "Foundation B"', "slug: foundation-b", "tags: [ml]"],
        )
        issues = lint_mod.run_lint(wiki_dir)
        relation_field_messages = [issue.message for issue in issues if issue.category == "relation-field"]
        assert any("relation_derived_from is not allowed on wiki/foundations" == message for message in relation_field_messages)
        assert any("relation_contradicts is not allowed on wiki/foundations" == message for message in relation_field_messages)

    def test_output_pages_do_not_use_relation_extends(self, wiki_dir):
        _write_page(
            wiki_dir,
            "concepts",
            "concept-a",
            ['title: "Concept A"', "slug: concept-a", "tags: [ml]"],
        )
        _write_page(
            wiki_dir,
            "outputs",
            "output-a",
            [
                'title: "Output A"',
                "slug: output-a",
                "tags: [ml]",
                'relation_extends: ["[[concept-a]]"]',
            ],
        )
        issues = lint_mod.run_lint(wiki_dir)
        assert any(issue.category == "relation-field" and "relation_extends is not allowed on wiki/outputs" == issue.message for issue in issues)

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
        assert any("lacks a matching Derived from explanation" in issue.message for issue in issues)


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

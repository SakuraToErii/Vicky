"""Tests for check skill wiki graph diagnostics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
TOOLS_DIR = PROJECT_ROOT / ".codex" / "skills" / "check" / "tools"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(TOOLS_DIR))

import wiki_graph
from vicky.support_files import ensure_support_files


@pytest.fixture
def wiki(tmp_path):
    root = tmp_path / "wiki"
    for name in wiki_graph.INDEXED_DIRS:
        (root / name).mkdir(parents=True)
    ensure_support_files(root, missing_only=False)
    return root


def _write_page(wiki, entity_type, slug, frontmatter, body=""):
    path = wiki / entity_type / f"{slug}.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


class TestQueryOrphans:
    def test_reports_unlinked_pages(self, wiki, capsys):
        _write_page(wiki, "sources", "paper-a", 'title: "Paper A"\nslug: paper-a\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        _write_page(wiki, "concepts", "concept-b", 'title: "Concept B"\nslug: concept-b\ntags: [ml]\nmaturity: working\nkey_sources: [paper-a]', "See [[paper-a]]")
        _write_page(wiki, "people", "john-doe", 'name: "John Doe"\nslug: john-doe\ntags: [ml]\nkey_sources: []')
        wiki_graph.query_orphans(str(wiki))
        payload = json.loads(capsys.readouterr().out.strip())
        orphan_slugs = {item["slug"] for item in payload}
        assert "john-doe" in orphan_slugs
        assert "paper-a" not in orphan_slugs

    def test_rejects_duplicate_slugs(self, wiki):
        _write_page(wiki, "sources", "shared-slug", 'title: "Paper A"\nslug: shared-slug\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        _write_page(wiki, "concepts", "shared-slug", 'title: "Concept A"\nslug: shared-slug\ntags: [ml]\nmaturity: working\nkey_sources: []')
        with pytest.raises(ValueError, match="duplicate slug names"):
            wiki_graph.query_orphans(str(wiki))

    def test_heading_link_counts_as_inbound(self, wiki, capsys):
        _write_page(wiki, "people", "john-doe", 'name: "John Doe"\nslug: john-doe\ntags: [ml]\nkey_sources: []')
        _write_page(wiki, "topics", "topic-a", 'title: "Topic A"\nslug: topic-a\ntags: [ml]', "See [[john-doe#Biography]]")
        wiki_graph.query_orphans(str(wiki))
        payload = json.loads(capsys.readouterr().out.strip())
        orphan_slugs = {item["slug"] for item in payload}
        assert "john-doe" not in orphan_slugs


class TestQueryDeadends:
    def test_reports_pages_without_outgoing_links(self, wiki, capsys):
        _write_page(wiki, "sources", "paper-a", 'title: "Paper A"\nslug: paper-a\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        _write_page(wiki, "concepts", "concept-b", 'title: "Concept B"\nslug: concept-b\ntags: [ml]\nmaturity: working\nkey_sources: [paper-a]', "See [[paper-a]]")
        _write_page(wiki, "outputs", "answer-a", 'title: "Answer A"\nslug: answer-a\ntags: [ml]', "")
        wiki_graph.query_deadends(str(wiki))
        payload = json.loads(capsys.readouterr().out.strip())
        deadend_slugs = {item["slug"] for item in payload}
        assert "paper-a" in deadend_slugs
        assert "concept-b" not in deadend_slugs
        assert "answer-a" not in deadend_slugs

    def test_heading_link_counts_as_outgoing(self, wiki, capsys):
        _write_page(wiki, "people", "john-doe", 'name: "John Doe"\nslug: john-doe\ntags: [ml]\nkey_sources: []')
        _write_page(wiki, "topics", "topic-a", 'title: "Topic A"\nslug: topic-a\ntags: [ml]', "See [[john-doe#Biography]]")
        wiki_graph.query_deadends(str(wiki))
        payload = json.loads(capsys.readouterr().out.strip())
        deadend_slugs = {item["slug"] for item in payload}
        assert "topic-a" not in deadend_slugs


class TestCli:
    def test_cli_json_output(self, wiki):
        script = TOOLS_DIR / "wiki_graph.py"
        result = __import__("subprocess").run(
            [sys.executable, str(script), str(wiki), "orphans"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            check=True,
        )
        assert json.loads(result.stdout) == []

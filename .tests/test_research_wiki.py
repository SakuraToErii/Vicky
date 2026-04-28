"""Tests for .tools/research_wiki.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".tools"))
import _schemas as schema_mod
import research_wiki as rw


@pytest.fixture
def wiki(tmp_path):
    root = tmp_path / "wiki"
    rw.init_wiki(str(root))
    return root


def _write_page(wiki, entity_type, slug, frontmatter, body=""):
    path = wiki / entity_type / f"{slug}.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


class TestSlugify:
    def test_basic_title(self):
        assert rw.slugify("Flash Attention") == "flash-attention"

    def test_drops_stop_words(self):
        assert rw.slugify("The Structure of Scientific Revolutions").startswith("structure")

    def test_empty_title(self):
        assert rw.slugify("") == "untitled"


class TestInitWiki:
    def test_creates_expected_dirs(self, tmp_path):
        wiki = tmp_path / "wiki"
        rw.init_wiki(str(wiki))
        for name in rw.INDEXED_DIRS:
            assert (wiki / name).is_dir()
        for name in schema_mod.SUPPORT_DIRS:
            assert (wiki / name).is_dir()
        for relative_path in schema_mod.BASE_FILE_TEMPLATES:
            assert (wiki / relative_path).exists()
        assert not (wiki / "index.md").exists()
        assert (wiki / "log.md").exists()

    def test_writes_one_init_log(self, tmp_path):
        wiki = tmp_path / "wiki"
        rw.init_wiki(str(wiki))
        log = (wiki / "log.md").read_text(encoding="utf-8")
        assert log.count("init | wiki initialized") == 1


class TestSimilarity:
    def test_find_similar_concept_prefers_foundation(self, wiki, capsys):
        _write_page(wiki, "foundations", "gradient-descent", 'title: "Gradient Descent"\nslug: gradient-descent\ndomain: optimization\nstatus: canonical')
        _write_page(wiki, "concepts", "stochastic-gradient-descent", 'title: "Stochastic Gradient Descent"\nslug: stochastic-gradient-descent\ntags: [optimization]\nmaturity: working\nkey_sources: []')
        rw.find_similar_concept(str(wiki), "Gradient Descent")
        payload = json.loads(capsys.readouterr().out.strip())
        assert payload[0]["entity_type"] == "foundation"
        assert payload[0]["slug"] == "gradient-descent"

    def test_find_similar_theorem(self, wiki, capsys):
        _write_page(wiki, "theorems", "banach-fixed-point", 'title: "Banach Fixed Point Theorem"\nslug: banach-fixed-point\ntheorem_kind: theorem\nstatus: stable\nkey_sources: []\ntags: [analysis]')
        rw.find_similar_theorem(str(wiki), "Banach Fixed Point Theorem")
        payload = json.loads(capsys.readouterr().out.strip())
        assert payload[0]["slug"] == "banach-fixed-point"


class TestQueryOrphans:
    def test_reports_unlinked_pages(self, wiki, capsys):
        _write_page(wiki, "sources", "paper-a", 'title: "Paper A"\nslug: paper-a\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        _write_page(wiki, "concepts", "concept-b", 'title: "Concept B"\nslug: concept-b\ntags: [ml]\nmaturity: working\nkey_sources: [paper-a]', "See [[paper-a]]")
        _write_page(wiki, "people", "john-doe", 'name: "John Doe"\nslug: john-doe\ntags: [ml]\nkey_sources: []')
        rw.query_orphans(str(wiki))
        payload = json.loads(capsys.readouterr().out.strip())
        orphan_slugs = {item["slug"] for item in payload}
        assert "john-doe" in orphan_slugs
        assert "paper-a" not in orphan_slugs

    def test_rejects_duplicate_slugs(self, wiki):
        _write_page(wiki, "sources", "shared-slug", 'title: "Paper A"\nslug: shared-slug\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        _write_page(wiki, "concepts", "shared-slug", 'title: "Concept A"\nslug: shared-slug\ntags: [ml]\nmaturity: working\nkey_sources: []')
        with pytest.raises(ValueError, match="duplicate slug names"):
            rw.query_orphans(str(wiki))


class TestMetaRoundtrip:
    def test_set_meta_preserves_nested_frontmatter(self, wiki):
        path = _write_page(
            wiki,
            "sources",
            "paper-a",
            'title: "Paper A"\nslug: paper-a\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex\nauthors: ["Alice"]\nsource_ids:\n  doi: 10.1000/example\n  s2: abc123\nyear: 2023',
        )
        rw.set_meta(str(path), "year", "2024")
        frontmatter = rw._parse_frontmatter(path)
        assert frontmatter["year"] == 2024
        assert frontmatter["source_ids"] == {"doi": "10.1000/example", "s2": "abc123"}


class TestCheckpoint:
    def test_checkpoint_roundtrip(self, wiki, capsys):
        rw.checkpoint_save(str(wiki), "ingest-batch", "item-a")
        rw.checkpoint_set_meta(str(wiki), "ingest-batch", "mode", "manual")
        rw.checkpoint_load(str(wiki), "ingest-batch")
        payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert payload["exists"] is True
        assert payload["completed"] == ["item-a"]
        assert payload["metadata"]["mode"] == "manual"


class TestStats:
    def test_stats_json(self, wiki, capsys):
        _write_page(wiki, "sources", "paper-a", 'title: "Paper A"\nslug: paper-a\nsource_kind: paper\nsource_path: raw/papers/paper-a.tex')
        rw.get_stats(str(wiki), as_json=True)
        payload = json.loads(capsys.readouterr().out.strip())
        assert payload["sources"] == 1

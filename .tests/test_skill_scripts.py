"""Tests for restored skill-local helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
INIT_SCRIPTS = PROJECT_ROOT / ".codex" / "skills" / "init" / "scripts"
ASK_SCRIPTS = PROJECT_ROOT / ".codex" / "skills" / "ask" / "scripts"
INGEST_SCRIPTS = PROJECT_ROOT / ".codex" / "skills" / "ingest" / "scripts"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(INIT_SCRIPTS))
sys.path.insert(0, str(ASK_SCRIPTS))
sys.path.insert(0, str(INGEST_SCRIPTS))

import frontmatter_find
import init_wiki
import similar_pages
from vicky.schema import BASE_FILE_TEMPLATES, INDEXED_DIRS, RAW_DIRS
from vicky.slug import slugify


def _write_page(wiki, entity_type, slug, frontmatter, body=""):
    path = wiki / entity_type / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


def test_slugify_matches_legacy_behavior():
    assert slugify("The Structure of Scientific Revolutions") == "structure-scientific-revolutions"
    assert slugify("") == "untitled"


def test_init_wiki_creates_scaffold_and_log(tmp_path):
    result = init_wiki.init_wiki(tmp_path)
    wiki = tmp_path / "wiki"
    assert result["status"] == "ok"
    for name in INDEXED_DIRS:
        assert (wiki / name).is_dir()
        assert (wiki / name / ".gitkeep").exists()
    for name in RAW_DIRS:
        assert (tmp_path / "raw" / name / ".gitkeep").exists()
    for relative_path in BASE_FILE_TEMPLATES:
        assert (wiki / relative_path).exists()
    assert "init | wiki initialized" in (wiki / "log.md").read_text(encoding="utf-8")


def test_slug_cli(tmp_path):
    result = subprocess.run(
        [sys.executable, str(INIT_SCRIPTS / "slug.py"), "Flash Attention"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    assert result.stdout.strip() == "flash-attention"


def test_frontmatter_find_filters_lists_and_wikilinks(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "concepts",
        "flash-attention",
        'title: "Flash Attention"\nslug: flash-attention\ntags: [attention]\nmaturity: working\nkey_sources: [paper-a]\nrelation_derived_from: ["[[paper-a]]"]',
    )
    _write_page(
        wiki,
        "concepts",
        "lora",
        'title: "LoRA"\nslug: lora\ntags: [adaptation]\nmaturity: seed\nkey_sources: [paper-b]',
    )

    matches = frontmatter_find.find_entities(wiki, "concepts", [("relation_derived_from", "paper-a")])
    assert [item["slug"] for item in matches] == ["flash-attention"]


def test_frontmatter_find_cli(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "ideas",
        "open-question",
        'title: "Open Question"\nslug: open-question\nstatus: working\ntags: [ml]\npriority: 2',
    )
    result = subprocess.run(
        [sys.executable, str(ASK_SCRIPTS / "frontmatter_find.py"), str(wiki), "ideas", "--priority", "<3"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload[0]["slug"] == "open-question"


def test_similar_pages_prefers_foundations(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(wiki, "foundations", "gradient-descent", 'title: "Gradient Descent"\nslug: gradient-descent\ndomain: optimization\nstatus: canonical')
    _write_page(
        wiki,
        "concepts",
        "stochastic-gradient-descent",
        'title: "Stochastic Gradient Descent"\nslug: stochastic-gradient-descent\ntags: [optimization]\nmaturity: working\nkey_sources: []',
    )
    matches = similar_pages.find_similar_concept(wiki, "Gradient Descent")
    assert matches[0]["entity_type"] == "foundation"
    assert matches[0]["slug"] == "gradient-descent"


def test_similar_pages_cli_theorem(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "theorems",
        "banach-fixed-point",
        'title: "Banach Fixed Point Theorem"\nslug: banach-fixed-point\ntheorem_kind: theorem\nstatus: stable\nkey_sources: []\ntags: [analysis]',
    )
    result = subprocess.run(
        [sys.executable, str(INGEST_SCRIPTS / "similar_pages.py"), str(wiki), "theorem", "Banach Fixed Point Theorem"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload[0]["slug"] == "banach-fixed-point"

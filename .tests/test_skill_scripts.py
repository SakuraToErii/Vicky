"""Tests for restored skill-local helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
ASK_SCRIPTS = PROJECT_ROOT / ".codex" / "skills" / "ask" / "scripts"
INGEST_SCRIPTS = PROJECT_ROOT / ".codex" / "skills" / "ingest" / "scripts"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(ASK_SCRIPTS))
sys.path.insert(0, str(INGEST_SCRIPTS))

import frontmatter_find
import retrieve
import similar_pages
from slug_utils import slugify


def _write_page(wiki, entity_type, slug, frontmatter, body=""):
    path = wiki / entity_type / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


def test_slugify_matches_legacy_behavior():
    assert slugify("The Structure of Scientific Revolutions") == "structure-scientific-revolutions"
    assert slugify("") == "untitled"


def test_slug_cli(tmp_path):
    result = subprocess.run(
        [sys.executable, str(INGEST_SCRIPTS / "slug.py"), "Flash Attention"],
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


def test_retrieve_prefers_slug_and_collects_one_hop_relation_evidence(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "foundations",
        "bellman-equation",
        '\n'.join(
            [
                'title: "Bellman Equation"',
                "slug: bellman-equation",
                "tags: [reinforcement-learning]",
                'aliases: ["BE", "Bellman recursion"]',
                "relation_extends: []",
                'relation_uses: ["[[state-value-function]]"]',
                "relation_compares_with: []",
            ]
        ),
        body="""
Bellman equation page.

## Relations
- Uses: [[state-value-function]] supplies the recursive value target in the Bellman equation.
""".strip(),
    )
    _write_page(
        wiki,
        "concepts",
        "state-value-function",
        '\n'.join(
            [
                'title: "State Value Function"',
                "slug: state-value-function",
                "tags: [reinforcement-learning]",
                "aliases: []",
                "relation_derived_from: []",
                "relation_extends: []",
                "relation_uses: []",
                "relation_compares_with: []",
            ]
        ),
        body="""
State value function page.

## Relations
""".strip(),
    )
    _write_page(
        wiki,
        "theorems",
        "bellman-optimality-equation",
        '\n'.join(
            [
                'title: "Bellman Optimality Equation"',
                "slug: bellman-optimality-equation",
                "tags: [reinforcement-learning]",
                "theorem_kind: theorem",
                "aliases: []",
                "relation_derived_from: []",
                'relation_extends: ["[[bellman-equation]]"]',
                "relation_contradicts: []",
                "relation_uses: []",
                "relation_compares_with: []",
            ]
        ),
        body="""
Bellman optimality equation page.

## Relations
- Extends: [[bellman-equation]] adds the max operator over actions.
""".strip(),
    )

    payload = retrieve.build_candidate_package(wiki, ["bellman-equation", "BE"])

    assert payload["seed_count"] == 1
    seed = payload["seeds"][0]
    assert seed["slug"] == "bellman-equation"
    assert seed["page_type"] == "foundations"
    assert seed["matched_terms"] == ["bellman-equation", "BE"]
    assert seed["outgoing_neighbors"] == [
        {
            "slug": "state-value-function",
            "page_type": "concepts",
            "path": "wiki/concepts/state-value-function.md",
            "direction": "outgoing",
            "relation_field": "relation_uses",
            "relation_weight": 4,
            "relations_sentences": [
                "- Uses: [[state-value-function]] supplies the recursive value target in the Bellman equation."
            ],
        }
    ]
    assert seed["incoming_neighbors"] == [
        {
            "slug": "bellman-optimality-equation",
            "page_type": "theorems",
            "path": "wiki/theorems/bellman-optimality-equation.md",
            "direction": "incoming",
            "relation_field": "relation_extends",
            "relation_weight": 3,
            "relations_sentences": [
                "- Extends: [[bellman-equation]] adds the max operator over actions."
            ],
        }
    ]


def test_retrieve_cli_returns_empty_seed_package(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "foundations",
        "gradient-descent",
        '\n'.join(
            [
                'title: "Gradient Descent"',
                "slug: gradient-descent",
                "tags: [optimization]",
                "aliases: []",
                "relation_extends: []",
                "relation_uses: []",
                "relation_compares_with: []",
            ]
        ),
        body="## Relations\n",
    )

    result = subprocess.run(
        [sys.executable, str(ASK_SCRIPTS / "retrieve.py"), str(wiki), "occupancy-measure"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["candidate_terms"] == ["occupancy-measure"]
    assert payload["seed_count"] == 0
    assert payload["seeds"] == []


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


def test_similar_pages_cli_idea(tmp_path):
    wiki = tmp_path / "wiki"
    _write_page(
        wiki,
        "ideas",
        "open-questions-in-linear-attention",
        'title: "Open Questions in Linear Attention"\nslug: open-questions-in-linear-attention\nstatus: working\npriority: 2\ntags: [attention, open-question]',
    )
    result = subprocess.run(
        [sys.executable, str(INGEST_SCRIPTS / "similar_pages.py"), str(wiki), "idea", "Open Question in Linear Attention"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload[0]["slug"] == "open-questions-in-linear-attention"
    assert payload[0]["entity_type"] == "idea"

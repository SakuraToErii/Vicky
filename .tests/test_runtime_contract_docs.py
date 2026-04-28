"""Lock the new-page post-processing contract across runtime docs."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_agents_contract_covers_new_page_post_processing():
    content = _read("AGENTS.md")
    for snippet in [
        "New Page Post-Processing Contract",
        'similar_pages.py wiki concept "<title>"',
        'similar_pages.py wiki theorem "<title>"',
        'similar_pages.py wiki idea "<title>"',
        "key_sources",
        "wiki/log.md",
        ".codex/skills/check/scripts/lint.py --wiki-dir wiki --json",
    ]:
        assert snippet in content


def test_ingest_skill_requires_one_page_at_a_time_completion():
    content = _read(".codex/skills/ingest/SKILL.md")
    for snippet in [
        "Process approved knowledge pages one at a time.",
        'similar_pages.py wiki idea "<title>"',
        "add or confirm `key_sources`",
        "Append one log line",
        "Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json` as the completion signal",
    ]:
        assert snippet in content


def test_edit_skill_requires_post_processing_and_lint():
    content = _read(".codex/skills/edit/SKILL.md")
    for snippet in [
        'similar_pages.py wiki idea "<title>"',
        "finish one page at a time through the full post-processing path",
        "add `key_sources`",
        "wiki/log",
        ".codex/skills/check/scripts/lint.py --wiki-dir wiki --json",
    ]:
        assert snippet in content

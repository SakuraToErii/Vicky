"""Shared support-file templates and helpers for the Vicky wiki."""

from __future__ import annotations

from pathlib import Path

from schema import BASE_FILE_TEMPLATES

LOG_TEMPLATE = "# Vicky Log\n\n"

SUPPORT_FILE_TEMPLATES = {
    "log.md": LOG_TEMPLATE,
    **BASE_FILE_TEMPLATES,
}


def write_support_file(wiki_dir: Path, relative_path: str, overwrite: bool = True) -> Path:
    """Write one canonical support file into the wiki directory."""
    path = wiki_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not path.exists():
        path.write_text(SUPPORT_FILE_TEMPLATES[relative_path], encoding="utf-8")
    return path


def ensure_support_files(wiki_dir: Path, missing_only: bool = False) -> None:
    """Create or refresh all canonical support files."""
    for relative_path in SUPPORT_FILE_TEMPLATES:
        write_support_file(wiki_dir, relative_path, overwrite=not missing_only)

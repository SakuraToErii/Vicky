#!/usr/bin/env python3
"""Initialize the Vicky wiki scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.schema import INDEXED_DIRS, RAW_DIRS, SUPPORT_DIRS
from vicky.support_files import LOG_TEMPLATE, ensure_support_files


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def append_log(wiki_root: Path, message: str) -> None:
    log_path = wiki_root / "log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(LOG_TEMPLATE, encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"## [{_today()}] {message}\n")


def init_wiki(project_root: Path, log: bool = True) -> dict:
    wiki_root = project_root / "wiki"
    raw_root = project_root / "raw"
    created_dirs: list[str] = []
    created_files: list[str] = []

    for directory in [wiki_root / name for name in INDEXED_DIRS]:
        if not directory.exists():
            created_dirs.append(str(directory.relative_to(project_root)))
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            created_files.append(str(gitkeep.relative_to(project_root)))

    for directory in [wiki_root / name for name in SUPPORT_DIRS]:
        if not directory.exists():
            created_dirs.append(str(directory.relative_to(project_root)))
        directory.mkdir(parents=True, exist_ok=True)

    for directory in [raw_root / name for name in RAW_DIRS]:
        if not directory.exists():
            created_dirs.append(str(directory.relative_to(project_root)))
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            created_files.append(str(gitkeep.relative_to(project_root)))

    before_support = {path for path in (wiki_root.rglob("*") if wiki_root.exists() else []) if path.is_file()}
    ensure_support_files(wiki_root, missing_only=True)
    after_support = {path for path in wiki_root.rglob("*") if path.is_file()}
    created_files.extend(str(path.relative_to(project_root)) for path in sorted(after_support - before_support))

    if log:
        append_log(wiki_root, "init | wiki initialized")

    return {
        "status": "ok",
        "wiki_root": str(wiki_root.relative_to(project_root)),
        "created_dirs": sorted(set(created_dirs)),
        "created_files": sorted(set(created_files)),
        "logged": log,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Vault project root")
    parser.add_argument("--no-log", action="store_true", help="Skip appending an init log line")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    result = init_wiki(project_root, log=not args.no_log)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

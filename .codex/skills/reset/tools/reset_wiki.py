#!/usr/bin/env python3
"""Reset wiki state for the Vicky note vault."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.schema import INDEXED_DIRS, RAW_DIRS, SUPPORT_DIRS
from vicky.support_files import LOG_TEMPLATE, SUPPORT_FILE_TEMPLATES, write_support_file

ALL_SCOPES = ["wiki", "raw", "log", "checkpoints"]


def _list_md(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [path for path in directory.glob("*.md") if path.is_file()]


def _list_entries(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [path for path in directory.iterdir() if path.name != ".gitkeep"]


def plan(project_root: Path, scopes: list[str]) -> dict:
    data: dict = {"scopes": scopes, "delete_files": [], "reset_files": [], "actions": []}
    wiki = project_root / "wiki"

    if "wiki" in scopes:
        for entity in INDEXED_DIRS:
            for file_path in _list_md(wiki / entity):
                data["delete_files"].append(str(file_path.relative_to(project_root)))
        if (wiki / "log.md").exists():
            data["delete_files"].append("wiki/log.md")
        data["reset_files"].append("wiki/log.md")
        for support_dir in SUPPORT_DIRS:
            for file_path in _list_entries(wiki / support_dir):
                data["delete_files"].append(str(file_path.relative_to(project_root)))
        data["reset_files"].extend(f"wiki/{relative_path}" for relative_path in SUPPORT_FILE_TEMPLATES if relative_path != "log.md")

    if "raw" in scopes:
        for subdir in RAW_DIRS:
            for file_path in _list_entries(project_root / "raw" / subdir):
                data["delete_files"].append(str(file_path.relative_to(project_root)))

    if "log" in scopes and "wiki" not in scopes:
        data["reset_files"].append("wiki/log.md")

    if "checkpoints" in scopes:
        data["actions"].append("clear wiki/.checkpoints/*.json")

    return data


def execute(project_root: Path, scopes: list[str]) -> dict:
    deleted = 0
    reset = 0
    wiki = project_root / "wiki"

    if "wiki" in scopes:
        for entity in INDEXED_DIRS:
            directory = wiki / entity
            for file_path in _list_md(directory):
                file_path.unlink()
                deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
        for scaffold in ("log.md",):
            scaffold_path = wiki / scaffold
            if scaffold_path.exists():
                scaffold_path.unlink()
                deleted += 1
        (wiki / "log.md").write_text(LOG_TEMPLATE, encoding="utf-8")
        for support_dir in SUPPORT_DIRS:
            directory = wiki / support_dir
            for entry in _list_entries(directory):
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
        for relative_path in SUPPORT_FILE_TEMPLATES:
            if relative_path == "log.md":
                continue
            write_support_file(wiki, relative_path, overwrite=True)
        reset += len(SUPPORT_FILE_TEMPLATES)

    if "raw" in scopes:
        for subdir in RAW_DIRS:
            directory = project_root / "raw" / subdir
            for entry in _list_entries(directory):
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    if "log" in scopes and "wiki" not in scopes:
        (wiki / "log.md").write_text(LOG_TEMPLATE, encoding="utf-8")
        reset += 1

    if "checkpoints" in scopes:
        checkpoint_dir = wiki / ".checkpoints"
        if checkpoint_dir.exists():
            for checkpoint in checkpoint_dir.glob("*.json"):
                checkpoint.unlink()
                deleted += 1

    return {"deleted_files": deleted, "reset_files": reset}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, help="Comma-separated scopes or 'all'")
    parser.add_argument("--project-root", default=".", help="Project root")
    parser.add_argument("--yes", action="store_true", help="Apply changes")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan and exit")
    args = parser.parse_args()

    if args.scope == "all":
        scopes = list(ALL_SCOPES)
    else:
        scopes = [item.strip() for item in args.scope.split(",") if item.strip()]
        for scope in scopes:
            if scope not in ALL_SCOPES:
                print(json.dumps({"status": "error", "message": f"unknown scope: {scope}", "valid": ALL_SCOPES}))
                sys.exit(1)

    project_root = Path(args.project_root).resolve()
    data = plan(project_root, scopes)
    if not args.yes or args.dry_run:
        print(json.dumps({"status": "plan", **data}, ensure_ascii=False, indent=2))
        return

    result = execute(project_root, scopes)
    print(json.dumps({"status": "ok", "scopes": scopes, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()

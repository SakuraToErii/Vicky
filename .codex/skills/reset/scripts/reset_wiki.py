#!/usr/bin/env python3
"""Reset wiki state for the Vicky note vault."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from schema import INDEXED_DIRS, RAW_DIRS, SUPPORT_DIRS
from support_files import LOG_TEMPLATE, SUPPORT_FILE_TEMPLATES, write_support_file

ALL_SCOPES = ["wiki", "log", "checkpoints"]
RAW_SCOPE = "raw"
VALID_SCOPES = ALL_SCOPES + [RAW_SCOPE]
SENTINEL_PATHS = ["AGENTS.md", ".obsidian/types.json", "wiki"]
TRASH_DIR = ".trash"


def _list_md(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.md") if path.is_file())


def _list_entries(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.name != ".gitkeep")


def resolve_scopes(scope_arg: str, include_raw: bool = False) -> list[str]:
    if scope_arg == "all":
        scopes = list(ALL_SCOPES)
        if include_raw:
            scopes.append(RAW_SCOPE)
        return scopes

    scopes = []
    for item in (part.strip() for part in scope_arg.split(",")):
        if not item:
            continue
        if item not in VALID_SCOPES:
            raise ValueError(f"unknown scope: {item}")
        if item == RAW_SCOPE and not include_raw:
            raise ValueError("raw scope requires --include-raw")
        if item not in scopes:
            scopes.append(item)
    if not scopes:
        raise ValueError("scope cannot be empty")
    return scopes


def validate_project_root(project_root: Path) -> None:
    missing = [path for path in SENTINEL_PATHS if not (project_root / path).exists()]
    if missing:
        raise ValueError(f"project root sentinel check failed: missing {', '.join(missing)}")
    if not (project_root / "wiki").is_dir():
        raise ValueError("project root sentinel check failed: wiki is not a directory")


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


def plan_hash(data: dict) -> str:
    stable = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]


def with_plan_hash(data: dict) -> dict:
    return {**data, "plan_hash": plan_hash(data)}


def _trash_run_dir(project_root: Path) -> Path:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = project_root / TRASH_DIR / f"vicky-reset-{timestamp}"
    suffix = 1
    while candidate.exists():
        candidate = project_root / TRASH_DIR / f"vicky-reset-{timestamp}-{suffix}"
        suffix += 1
    return candidate


def _move_to_trash(path: Path, project_root: Path, trash_dir: Path, manifest: dict) -> bool:
    if not path.exists():
        return False
    relative_path = path.relative_to(project_root)
    target = trash_dir / "files" / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(target))
    manifest["moved"].append(
        {
            "path": str(relative_path),
            "trash_path": str(target.relative_to(project_root)),
        }
    )
    return True


def _write_manifest(trash_dir: Path, manifest: dict) -> None:
    trash_dir.mkdir(parents=True, exist_ok=True)
    (trash_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _delete_path(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


def execute(project_root: Path, scopes: list[str]) -> dict:
    validate_project_root(project_root)
    deleted = 0
    reset = 0
    wiki = project_root / "wiki"
    current_plan = plan(project_root, scopes)
    current_hash = plan_hash(current_plan)
    trash_dir = _trash_run_dir(project_root) if RAW_SCOPE in scopes else None
    manifest = None
    if trash_dir is not None:
        manifest = {
            "tool": "vicky-reset",
            "scopes": scopes,
            "plan_hash": current_hash,
            "moved": [],
        }

    if "wiki" in scopes:
        for entity in INDEXED_DIRS:
            directory = wiki / entity
            for file_path in _list_md(directory):
                if _delete_path(file_path):
                    deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
        for scaffold in ("log.md",):
            scaffold_path = wiki / scaffold
            if _delete_path(scaffold_path):
                deleted += 1
        (wiki / "log.md").write_text(LOG_TEMPLATE, encoding="utf-8")
        for support_dir in SUPPORT_DIRS:
            directory = wiki / support_dir
            for entry in _list_entries(directory):
                if _delete_path(entry):
                    deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
        for relative_path in SUPPORT_FILE_TEMPLATES:
            if relative_path == "log.md":
                continue
            write_support_file(wiki, relative_path, overwrite=True)
        reset += len(SUPPORT_FILE_TEMPLATES)

    if "raw" in scopes:
        assert trash_dir is not None
        assert manifest is not None
        for subdir in RAW_DIRS:
            directory = project_root / "raw" / subdir
            for entry in _list_entries(directory):
                if _move_to_trash(entry, project_root, trash_dir, manifest):
                    deleted += 1
            directory.mkdir(parents=True, exist_ok=True)
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    if "log" in scopes and "wiki" not in scopes:
        if _delete_path(wiki / "log.md"):
            deleted += 1
        (wiki / "log.md").write_text(LOG_TEMPLATE, encoding="utf-8")
        reset += 1

    if "checkpoints" in scopes:
        checkpoint_dir = wiki / ".checkpoints"
        if checkpoint_dir.exists():
            for checkpoint in checkpoint_dir.glob("*.json"):
                if _delete_path(checkpoint):
                    deleted += 1

    result = {
        "deleted_files": deleted,
        "reset_files": reset,
        "plan_hash": current_hash,
    }
    if trash_dir is not None and manifest is not None:
        _write_manifest(trash_dir, manifest)
        result["trash_dir"] = str(trash_dir.relative_to(project_root))
    return result


def rollback(project_root: Path, trash_ref: str) -> dict:
    validate_project_root(project_root)
    trash_dir = Path(trash_ref)
    if not trash_dir.is_absolute():
        trash_dir = project_root / trash_ref
    if not trash_dir.exists():
        trash_dir = project_root / TRASH_DIR / trash_ref
    manifest_path = trash_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"rollback manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored = 0
    replaced = 0
    replacement_root = trash_dir / "rollback-replaced"
    for item in reversed(manifest.get("moved", [])):
        original_path = project_root / item["path"]
        trashed_path = project_root / item["trash_path"]
        if not trashed_path.exists():
            continue
        if original_path.exists():
            replacement_path = replacement_root / item["path"]
            replacement_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(original_path), str(replacement_path))
            replaced += 1
        original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trashed_path), str(original_path))
        restored += 1
    return {"restored_files": restored, "replaced_files": replaced, "trash_dir": str(trash_dir.relative_to(project_root))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", help="Comma-separated scopes or 'all'")
    parser.add_argument("--project-root", default=".", help="Project root")
    parser.add_argument("--yes", action="store_true", help="Apply changes")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan and exit")
    parser.add_argument("--include-raw", action="store_true", help="Allow raw scope deletion")
    parser.add_argument("--plan-hash", help="Hash from the preview plan required with --yes")
    parser.add_argument("--rollback", help="Restore files from a .trash/vicky-reset-* directory")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    try:
        if args.rollback:
            result = rollback(project_root, args.rollback)
            print(json.dumps({"status": "ok", "action": "rollback", **result}, ensure_ascii=False))
            return
        if not args.scope:
            raise ValueError("--scope is required unless --rollback is used")
        scopes = resolve_scopes(args.scope, args.include_raw)
        data = with_plan_hash(plan(project_root, scopes))
    except ValueError as error:
        print(json.dumps({"status": "error", "message": str(error), "valid": VALID_SCOPES}))
        sys.exit(1)

    if not args.yes or args.dry_run:
        print(json.dumps({"status": "plan", **data}, ensure_ascii=False, indent=2))
        return

    if args.plan_hash != data["plan_hash"]:
        print(json.dumps({"status": "error", "message": "plan hash mismatch", "expected": data["plan_hash"]}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = execute(project_root, scopes)
    except ValueError as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps({"status": "ok", "scopes": scopes, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dependency preflight helpers for Vicky setup and local checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys

COMMAND_LABELS = {
    "python3": "Python 3",
    "codex": "Codex CLI",
    "obsidian": "Obsidian CLI",
    "rg": "ripgrep",
}

MODULE_LABELS = {
    "pytest": "pytest",
    "requests": "requests",
    "yaml": "PyYAML",
}


def missing_commands(commands: list[str]) -> list[str]:
    return [command for command in commands if shutil.which(command) is None]


def missing_modules(modules: list[str]) -> list[str]:
    return [module for module in modules if importlib.util.find_spec(module) is None]


def _payload(kind: str, checked: list[str], missing: list[str]) -> dict:
    return {
        "status": "ok" if not missing else "error",
        "kind": kind,
        "checked": checked,
        "missing": missing,
    }


def _render_label(kind: str, item: str) -> str:
    if kind == "commands":
        return COMMAND_LABELS.get(item, item)
    return MODULE_LABELS.get(item, item)


def _print_human(payload: dict) -> None:
    kind = payload["kind"]
    checked = payload["checked"]
    missing = set(payload["missing"])
    title = "commands" if kind == "commands" else "Python modules"
    print(f"Preflight {title}:")
    for item in checked:
        status = "OK" if item not in missing else "MISSING"
        print(f"  [{status}] {_render_label(kind, item)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["commands", "modules"], help="Dependency kind to verify")
    parser.add_argument("names", nargs="+", help="Commands or Python modules to verify")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human report")
    args = parser.parse_args()

    if args.kind == "commands":
        missing = missing_commands(args.names)
    else:
        missing = missing_modules(args.names)

    payload = _payload(args.kind, args.names, missing)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(payload)

    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()

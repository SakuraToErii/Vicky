#!/usr/bin/env python3
"""Generate a Vicky slug."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vicky.slug import slugify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Title to slugify")
    args = parser.parse_args()
    print(slugify(args.title))


if __name__ == "__main__":
    main()

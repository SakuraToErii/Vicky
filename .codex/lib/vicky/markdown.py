#!/usr/bin/env python3
"""Markdown helpers shared by wiki tools."""

from __future__ import annotations

import re

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1", re.DOTALL)
FENCE_RE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})(?P<tail>.*)$")


def _strip_fenced_code_blocks(content: str) -> str:
    kept_lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in content.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if fence_char is None:
            if match:
                fence = match.group("fence")
                fence_char = fence[0]
                fence_length = len(fence)
                continue
            kept_lines.append(line)
            continue
        if match:
            fence = match.group("fence")
            if fence[0] == fence_char and len(fence) >= fence_length and not match.group("tail").strip():
                fence_char = None
                fence_length = 0
        continue
    return "".join(kept_lines)


def sanitize_markdown_links(content: str) -> str:
    content = HTML_COMMENT_RE.sub("", content)
    content = _strip_fenced_code_blocks(content)
    return INLINE_CODE_RE.sub("", content)


def find_wikilinks(content: str) -> list[str]:
    return WIKILINK_RE.findall(sanitize_markdown_links(content))

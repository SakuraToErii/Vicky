"""Slug and lightweight text-matching helpers for Vicky scripts."""

from __future__ import annotations

import re

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "this",
        "to",
        "with",
    }
)


def slugify(title: str) -> str:
    """Generate a short kebab-case slug from an English title."""
    text = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    words = [word for word in text.split() if word and word not in STOP_WORDS]
    if not words:
        words = [word for word in text.split() if word]
    if not words:
        return "untitled"
    return "-".join(words[:6])


def normalize_text(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return " ".join(normalized.split())


def content_tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {token for token in normalized.split() if len(token) >= 3 and token not in STOP_WORDS}


def phrase_match_score(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    normalized_left = normalize_text(left)
    normalized_right = normalize_text(right)
    if not normalized_left or not normalized_right:
        return 0.0
    if normalized_left == normalized_right:
        return 1.0
    if normalized_left in normalized_right or normalized_right in normalized_left:
        shorter = normalized_left if len(normalized_left) < len(normalized_right) else normalized_right
        if len(shorter.split()) >= 2:
            return 0.85
    left_tokens = content_tokens(left)
    right_tokens = content_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    score = len(left_tokens & right_tokens) / len(union)
    return score if score >= 0.4 else 0.0

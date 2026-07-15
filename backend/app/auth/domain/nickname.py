"""Nickname normalization and public-data-derived suggestion rules."""

import re
import unicodedata
from collections.abc import Iterator

FORBIDDEN_NICKNAME_TOKENS = frozenset(
    {
        "admin",
        "administrator",
        "system",
        "관리자",
        "운영자",
        "사이42",
    }
)
SUGGESTION_SUFFIXES = ("짝", "두근이", "데이트")
WHITESPACE_PATTERN = re.compile(r"\s+")


def prepare_nickname(value: str) -> str:
    """Normalize Unicode and surrounding whitespace for display and validation."""
    normalized = unicodedata.normalize("NFKC", value)
    return WHITESPACE_PATTERN.sub(" ", normalized).strip()


def normalize_nickname(value: str) -> str:
    """Return the stable unique-key representation of a nickname."""
    return prepare_nickname(value).casefold()


def nickname_contains_forbidden_token(value: str) -> bool:
    """Return whether a normalized nickname contains a reserved service token."""
    normalized = normalize_nickname(value).replace(" ", "")
    return any(token in normalized for token in FORBIDDEN_NICKNAME_TOKENS)


def _suggestion_token(value: str) -> str:
    return "".join(character for character in prepare_nickname(value) if character.isalnum())


def nickname_candidates(place_title: str, seed: str | None = None) -> Iterator[str]:
    """Build nickname candidates whose source text comes from a stored place title."""
    place_token = _suggestion_token(place_title)
    seed_token = _suggestion_token(seed or "")
    source = f"{seed_token}{place_token}" if seed_token else place_token
    if not source:
        return

    for suffix in SUGGESTION_SUFFIXES:
        prefix_length = 14 - len(suffix)
        candidate = f"{source[:prefix_length]}{suffix}"
        if 2 <= len(candidate) <= 14 and not nickname_contains_forbidden_token(candidate):
            yield candidate

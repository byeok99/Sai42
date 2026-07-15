"""Deterministic prohibited-language checks for user-authored chat input."""

import re
import unicodedata

ZERO_WIDTH_CHARACTERS = frozenset({"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"})

# Patterns run against a Unicode-normalized representation with separators removed so that
# simple spacing and punctuation do not bypass the filter. Keep this list intentionally narrow
# to avoid rejecting ordinary date-course requests.
PROHIBITED_INPUT_PATTERNS = (
    re.compile(r"씨+발+"),
    re.compile(r"시+발+(?!(?:점|역|하다|되다))"),
    re.compile(r"개+(?:새|세|색)+(?:끼|기)+"),
    re.compile(r"병+신+"),
    re.compile(r"좆+"),
    re.compile(r"존+나+"),
    re.compile(r"지+랄+"),
    re.compile(r"느+금+마+"),
    re.compile(r"(?:ㅅ|ᄉ)+(?:ㅂ|ᄇ)+"),
    re.compile(r"(?:ㅂ|ᄇ)+(?:ㅅ|ᄉ)+"),
    re.compile(r"(?:ㅈ|ᄌ)+(?:ㄴ|ᄂ)+"),
    re.compile(r"(?:ㅈ|ᄌ)+(?:ㄹ|ᄅ)+"),
    re.compile(r"f+u+c+k+(?:i+n+g+|e+r+|e+d+|s+)?"),
    re.compile(r"m+o+t+h+e+r+f+u+c+k+e+r+"),
    re.compile(r"b+i+t+c+h+"),
    re.compile(r"a+s+s+h+o+l+e+"),
    re.compile(r"n+i+g+(?:g+e+r+|g+a+)"),
)


def normalize_filter_text(value: str) -> str:
    """Return a stable representation used only for prohibited-language matching."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(
        character
        for character in normalized
        if character not in ZERO_WIDTH_CHARACTERS and character.isalnum()
    )


def contains_prohibited_language(value: str) -> bool:
    """Return whether a user-authored message contains a prohibited expression."""

    normalized = normalize_filter_text(value)
    return any(pattern.search(normalized) is not None for pattern in PROHIBITED_INPUT_PATTERNS)

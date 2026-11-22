"""Shared eligibility for dated, independently classified races."""
import re

MIN_ACTIVE_RUNNERS = 3

RESTRICTED = re.compile(
    r"\b(?:maiden|mdn|maid|2[ -]?y[ -]?o|juvenile|(?:two|2)[ -]*year[ -]*olds?|"
    r"hurdles?|steeple(?:chase)?s?|chase|jumps?|jumping)\b",
    re.IGNORECASE,
)


def eligibility(country, classification, *, class_verified=False, allow_restricted=False):
    """Return the reason a race is excluded or provisional, or None."""
    if country not in ("AU", "NZ"):
        return "country unresolved"
    if isinstance(classification, str) and RESTRICTED.search(classification):
        if not allow_restricted:
            return "restricted race class"
    if class_verified is not True or not isinstance(classification, str) or not classification.strip():
        return "race class unverified"
    return None

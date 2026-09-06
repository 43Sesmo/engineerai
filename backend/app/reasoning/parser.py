"""
Reasoning engine — defensive parsing and schema validation.

try_parse_guidance() NEVER raises on a parsing or validation failure —
it returns None, which Task 6 wires into the approved graceful-
degradation behavior (raw text preserved, structured_output left null).
This is the one contract this entire file exists to uphold.

A layered cascade is used, cheapest/most-likely-to-succeed attempt
first:
  1. Direct JSON parse (handles a fully compliant response)
  2. Markdown-fence-stripped parse (handles the most common deviation)
  3. First-brace-to-last-brace extraction (handles stray prose)
  4. Schema validation against EngineeringGuidance

Exception handling is deliberately narrow — only json.JSONDecodeError
and Pydantic's ValidationError are caught, matching the explicit,
never-bare-except discipline used everywhere else in this codebase.
"""

import json
import logging
import re
from typing import Iterator, Optional, Tuple

from pydantic import ValidationError

from app.reasoning.schemas import EngineeringGuidance

logger = logging.getLogger(__name__)

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def try_parse_guidance(raw_text: str) -> Optional[EngineeringGuidance]:
    """
    Attempt to parse and validate raw AI output as an EngineeringGuidance
    instance, via the layered cascade described above. Never raises —
    returns None if every attempt fails.
    """
    for stage_name, candidate in _extraction_attempts(raw_text):
        if candidate is None:
            continue

        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            logger.debug(
                "try_parse_guidance: %s stage failed JSON parse: %s",
                stage_name,
                exc,
            )
            continue

        try:
            return EngineeringGuidance(**data)
        except ValidationError as exc:
            logger.debug(
                "try_parse_guidance: %s stage failed schema validation: %s",
                stage_name,
                exc,
            )
            continue

    logger.debug(
        "try_parse_guidance: all extraction attempts exhausted, returning None"
    )
    return None


def _extraction_attempts(raw_text: str) -> Iterator[Tuple[str, Optional[str]]]:
    """
    Yields (stage_name, candidate_string) pairs in cascade order.
    candidate_string is None if that stage's precondition isn't met
    (e.g. no fences found, no valid brace pair found) — try_parse_guidance
    skips those without attempting a parse.
    """
    yield "direct", raw_text.strip()
    yield "fence_stripped", _strip_markdown_fences(raw_text)
    yield "brace_extracted", _extract_braces(raw_text)


def _strip_markdown_fences(raw_text: str) -> Optional[str]:
    """Strips a leading/trailing ```json ... ``` or ``` ... ``` fence, if present."""
    match = _FENCE_PATTERN.match(raw_text.strip())
    if match is None:
        return None
    return match.group(1).strip()


def _extract_braces(raw_text: str) -> Optional[str]:
    """
    Takes everything from the first '{' to the last '}' in the text.
    Returns None if either brace is missing, or if the first '{' does
    not appear before the last '}' (a malformed/reversed case) —
    deliberately guarded before slicing, not left to fail downstream.
    """
    first = raw_text.find("{")
    last = raw_text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        return None
    return raw_text[first : last + 1]

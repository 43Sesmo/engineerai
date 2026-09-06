"""
Reasoning engine — orchestration only.

generate_guidance() builds the full prompt (Task 2) and sends it via the
existing send_prompt() (AI Provider Abstraction), returning the raw text
response, completely unparsed. No JSON parsing, no schema validation
happens in that function — that's try_parse_guidance() (Task 4).
AIProviderError passes through unchanged from every function in this
file, not re-wrapped, since send_prompt() already raises a clear,
correctly-named error and wrapping it again would only add ceremony
without adding information.

run_reasoning() (Task 5) composes generate_guidance() and
try_parse_guidance() into the one combined result Task 6 persists — the
raw response always, and the structured result if parsing succeeded, or
None if it gracefully didn't. No new exception handling is introduced
here either: a failure to parse is not an error at this layer, and a
failure to reach the AI provider at all still propagates exactly as it
always has.
"""

from dataclasses import dataclass
from typing import Optional

from app.ai.client import send_prompt
from app.reasoning.parser import try_parse_guidance
from app.reasoning.prompts.engineering_guidance_prompt import build_prompt
from app.reasoning.schemas import EngineeringGuidance


def generate_guidance(user_input: str, model: str | None = None) -> str:
    """
    Send a user's raw engineering idea through the reasoning prompt and
    return the AI's raw text response, unparsed.

    Raises ValueError if user_input is empty or whitespace-only — fails
    clearly rather than silently sending a prompt built around nothing.
    Raises AIProviderError (unmodified, passed through from send_prompt)
    if the underlying AI call fails.
    """
    if not user_input.strip():
        raise ValueError("user_input must not be empty or whitespace-only.")

    prompt = build_prompt(user_input)
    return send_prompt(prompt, model=model)


@dataclass(frozen=True)
class ReasoningResult:
    """
    The combined result of a full reasoning pass: the raw AI response
    (always present) and the structured guidance (present only if
    parsing succeeded — None is a normal, successful outcome, not an
    error, per the approved graceful-degradation design).
    """

    raw_text: str
    structured: Optional[EngineeringGuidance]


def run_reasoning(user_input: str, model: str | None = None) -> ReasoningResult:
    """
    Run the full reasoning path: generate a raw response, then attempt
    to parse it into structured guidance. Always returns both values
    together, ready for Task 6 to persist. Raises exactly the same
    exceptions generate_guidance() does (ValueError for invalid input,
    AIProviderError for a failed AI call) — both propagate unchanged; a
    parsing failure never raises anything at all, it simply results in
    structured=None.
    """
    raw_text = generate_guidance(user_input, model=model)
    structured = try_parse_guidance(raw_text)
    return ReasoningResult(raw_text=raw_text, structured=structured)

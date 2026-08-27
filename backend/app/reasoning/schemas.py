"""
Structured engineering guidance schema — the six fields the architecture
doc has described since v0.1.

Every field is required, with no defaults. This is deliberate: this
schema represents a COMPLETE structured response. The approved
graceful-degradation design (Sprint 2 planning, Section 6c) depends on a
clean signal here — either an AI response fully matches this schema, or
it doesn't. A response that only partially matches should fall all the
way back to raw-text storage (structured_output = null), not be accepted
as a partially-populated EngineeringGuidance with gaps papered over by
defaults.

`preliminary_calculations` is constrained to primitive values
(str | int | float | bool), not a fully generic dict. Most engineering
calculations naturally serialize to primitives (a number, a unit label,
a pass/fail flag); constraining to primitives keeps real validation in
place and avoids committing to arbitrary nested structures before any
real AI output has been seen. This can be revisited in a later sprint,
informed by real output, not guessed at now.
"""

from typing import Dict, List

from sqlmodel import Field, SQLModel


class EngineeringGuidance(SQLModel):
    clarifying_questions: List[str]
    engineering_reasoning: str = Field(min_length=1)
    preliminary_calculations: Dict[str, str | int | float | bool]
    material_suggestions: List[str]
    manufacturing_suggestions: List[str]
    recommended_next_steps: List[str]

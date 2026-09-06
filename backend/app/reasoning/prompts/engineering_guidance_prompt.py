"""
Reasoning prompt template — asks the model to respond with JSON matching
app.reasoning.schemas.EngineeringGuidance exactly.

WORKED_EXAMPLE is a module-level constant (not embedded inline in
build_prompt) specifically so it can be validated directly against
EngineeringGuidance during verification, and so the prompt text always
embeds well-formed JSON generated via json.dumps rather than a
hand-typed block that could drift out of sync or contain a typo.

Approved design decisions this template is built around:
- One complete worked example is included (few-shot), prioritizing
  reliability over the extra prompt tokens — this is the single highest-
  leverage thing this prompt can do, especially for the primitive-only
  preliminary_calculations constraint, which a model has no strong prior
  reason to respect unless shown, not just told.
- build_prompt() returns a single flat string. send_prompt()'s existing
  interface (app/ai/client.py) is untouched — no system/developer-role
  split was added.
"""

import json

# Uses the exact scenario referenced throughout this project since the
# original architecture document ("I need a shaft to transmit 5 kW at
# 300 rpm") — not an arbitrary choice, a deliberate continuity with the
# example that's anchored this system's design from the start.
WORKED_EXAMPLE: dict = {
    "clarifying_questions": [
        "What is the expected duty cycle (continuous vs. intermittent)?",
        "Is there a preferred keyway or coupling type at the shaft ends?",
    ],
    "engineering_reasoning": (
        "Torque was calculated from the given power and speed using "
        "T = P / omega. A solid circular shaft was sized against an "
        "allowable shear stress for a common medium-carbon steel, "
        "applying a standard service factor to account for typical "
        "torsional and minor bending loads in a general-purpose drive."
    ),
    "preliminary_calculations": {
        "power_kw": 5,
        "speed_rpm": 300,
        "torque_nm": 159.15,
        "shaft_diameter_mm": 25,
        "material_grade": "AISI 1045",
        "allowable_shear_stress_mpa": 42,
        "service_factor": 1.5,
    },
    "material_suggestions": [
        "AISI 1045 medium-carbon steel (cost-effective, good machinability)",
        "AISI 4140 alloy steel (higher strength if duty cycle proves severe)",
    ],
    "manufacturing_suggestions": [
        "Turn from round bar stock on a lathe",
        "Add a keyway via broaching or end milling for coupling attachment",
    ],
    "recommended_next_steps": [
        "Confirm duty cycle and any shock or impact loading",
        "Select a specific bearing and coupling to finalize shaft-end geometry",
        "Perform a fatigue check if the shaft will see reversing loads",
    ],
}


def build_prompt(user_input: str) -> str:
    """
    Compose the full prompt: role framing, per-field instructions, the
    primitive-only constraint on preliminary_calculations, the worked
    example, and the user's actual input — one flat string, matching
    send_prompt()'s existing, unchanged interface.
    """
    example_json = json.dumps(WORKED_EXAMPLE, indent=2)

    return f"""You are EngineerAI's engineering reasoning layer. Given an engineering idea, requirement, or question, respond with a single JSON object with exactly these six fields:

- "clarifying_questions": a list of strings. Intelligent questions you would want answered before finalizing a design. Use an empty list [] if none are needed — that is a legitimate answer, not a failure to think of any.
- "engineering_reasoning": a non-empty string. Your engineering analysis and reasoning process, explaining the approach taken.
- "preliminary_calculations": a JSON object whose values are ONLY primitives — a string, number, or boolean. NEVER a nested object or array as a value. For example, write "shaft_diameter_mm": 25, not "shaft_diameter": {{"value": 25, "unit": "mm"}}. If a value has units, put the unit in the key name (e.g. "torque_nm") or combine it into a single string value (e.g. "diameter": "25 mm") — never as a nested structure.
- "material_suggestions": a list of strings, each a suggested material.
- "manufacturing_suggestions": a list of strings, each a suggested manufacturing method or process.
- "recommended_next_steps": a list of strings, each a concrete next action.

Respond with the JSON object only — no prose before or after it, no markdown code fences.

Example:

Input: "I need a shaft to transmit 5 kW at 300 rpm."

Output:
{example_json}

Now respond to this request, in the exact same format:

{user_input}
"""

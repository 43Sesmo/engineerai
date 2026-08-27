"""
ONE-OFF VERIFICATION SCRIPT — not part of Task 1's tracked files.

This is a scratch script to run once on the real machine, where sqlmodel
is actually installed, then discard. It was not committed as a repo file
because Task 1's approved file list was exactly __init__.py and
schemas.py — adding a permanent third file wasn't in scope.

Run from backend/, with the venv activated:
    python verify_task1_schema.py
"""

import json

from app.reasoning.schemas import EngineeringGuidance
from pydantic import ValidationError

passed = 0
failed = 0


def check(label, fn):
    global passed, failed
    try:
        fn()
        print(f"PASS: {label}")
        passed += 1
    except AssertionError as exc:
        print(f"FAIL: {label} -- {exc}")
        failed += 1
    except Exception as exc:
        print(f"FAIL: {label} -- unexpected {type(exc).__name__}: {exc}")
        failed += 1


valid_kwargs = dict(
    clarifying_questions=[],
    engineering_reasoning="Sizing based on torque and allowable shear stress.",
    preliminary_calculations={
        "torque_nm": 159.15,
        "shaft_diameter_mm": 25,
        "material_grade": "AISI 1045",
        "meets_requirement": True,
    },
    material_suggestions=[],
    manufacturing_suggestions=[],
    recommended_next_steps=[],
)


def valid_instance():
    instance = EngineeringGuidance(**valid_kwargs)
    assert instance.clarifying_questions == []


check("Valid instance with empty lists and mixed-primitive dict", valid_instance)


def missing_field():
    kwargs = {k: v for k, v in valid_kwargs.items() if k != "engineering_reasoning"}
    try:
        EngineeringGuidance(**kwargs)
        raise AssertionError("expected ValidationError, got a valid instance")
    except ValidationError:
        pass


check("Missing field is rejected", missing_field)


def empty_reasoning():
    kwargs = {**valid_kwargs, "engineering_reasoning": ""}
    try:
        EngineeringGuidance(**kwargs)
        raise AssertionError("expected ValidationError, got a valid instance")
    except ValidationError:
        pass


check("Empty engineering_reasoning is rejected (min_length=1)", empty_reasoning)


def wrong_type():
    kwargs = {**valid_kwargs, "clarifying_questions": "not a list"}
    try:
        EngineeringGuidance(**kwargs)
        raise AssertionError("expected ValidationError, got a valid instance")
    except ValidationError:
        pass


check("Wrong type (str instead of list) is rejected", wrong_type)


# --- The two checks your review specifically asked to confirm empirically ---

def non_primitive_value_rejected():
    kwargs = {
        **valid_kwargs,
        "preliminary_calculations": {"nested": {"this": "should not be allowed"}},
    }
    try:
        EngineeringGuidance(**kwargs)
        raise AssertionError(
            "A nested dict value was ACCEPTED inside preliminary_calculations. "
            "The primitive-only constraint is NOT being enforced by this "
            "SQLModel/Pydantic version as written. Per instructions: do not "
            "widen the schema silently -- report this back."
        )
    except ValidationError:
        pass


check(
    "Non-primitive value (nested dict) inside preliminary_calculations is rejected",
    non_primitive_value_rejected,
)


def bool_preserved_not_coerced_to_int():
    kwargs = {
        **valid_kwargs,
        "preliminary_calculations": {"meets_requirement": True},
    }
    instance = EngineeringGuidance(**kwargs)
    value = instance.preliminary_calculations["meets_requirement"]
    assert value is True, (
        f"Expected True (bool) preserved as-is, got {value!r} "
        f"(type {type(value).__name__}). If this prints an int (1) instead "
        f"of a bool, the union is coercing bool->int before matching bool -- "
        f"report this back, do not silently accept it."
    )


check(
    "Bool value in preliminary_calculations stays a bool (not coerced to int)",
    bool_preserved_not_coerced_to_int,
)


def json_round_trip():
    original = EngineeringGuidance(**valid_kwargs)
    as_json = original.model_dump_json()
    reconstructed = EngineeringGuidance.model_validate_json(as_json)
    assert reconstructed == original, (
        f"Round-trip mismatch.\nOriginal: {original}\nReconstructed: {reconstructed}"
    )
    # Extra explicit check on the trickiest field for round-trip fidelity
    assert (
        reconstructed.preliminary_calculations
        == original.preliminary_calculations
    )


check("JSON serialize -> deserialize round trip, no data loss", json_round_trip)


print()
print(f"{passed} passed, {failed} failed")
if failed:
    raise SystemExit(1)

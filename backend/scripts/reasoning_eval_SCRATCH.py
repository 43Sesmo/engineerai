"""
SCRATCH — Sprint 8 reasoning eval. Not production code; lives outside app/.

Runs the same problems through run_reasoning() and checks (a) schema
validity, (b) whether any number in preliminary_calculations matches the
expected value within tolerance (key-agnostic, since the model picks its
own key names), and (c) as a separate secondary metric, whether any
number in the RAW response text matches — so a truncated, unparseable
response is not silently counted as "wrong answer".

  python scripts/reasoning_eval_SCRATCH.py --mode baseline
  python scripts/reasoning_eval_SCRATCH.py --mode retrieval --project-id <ID>

baseline never imports retrieval, so it also runs BEFORE Sprint 8 code
exists. P7 is context-dependent: it should fail at baseline and can only
pass if the seeded Vault entry reaches the prompt. P7's tolerance is 1%
so that a guessed-then-rounded answer (30 mm) cannot pass as 30.76.

Sprint 8 eval adds repeated runs and one context-dependent problem as
implementation-level extensions, approved by the Project Lead on review.
"""

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.reasoning.engine import run_reasoning  # noqa: E402

PROBLEMS = [
    {"id": "P1_torque", "needs_context": False, "expected": 49.39, "rel_tol": 0.02,
     "prompt": "A motor delivers 7.5 kW at 1450 rpm. What torque does it transmit to its shaft, in N·m?"},
    {"id": "P2_shaft_dia", "needs_context": False, "expected": 29.42, "rel_tol": 0.03,
     "prompt": "Size a solid circular steel shaft to transmit a pure torque of 200 N·m. Allowable shear stress is 40 MPa. Ignore bending, service factors and safety factors. What minimum diameter in mm?"},
    {"id": "P3_beam_moment", "needs_context": False, "expected": 750.0, "rel_tol": 0.02,
     "prompt": "A simply supported beam of 1.5 m span carries a single 2 kN point load at midspan. What is the maximum bending moment in N·m?"},
    {"id": "P4_tensile_stress", "needs_context": False, "expected": 132.63, "rel_tol": 0.02,
     "prompt": "A 12 mm diameter round steel rod carries a 15 kN axial tensile load. What is the tensile stress in MPa?"},
    {"id": "P5_gear_speed", "needs_context": False, "expected": 400.0, "rel_tol": 0.01,
     "prompt": "A 20-tooth pinion rotating at 1200 rpm drives a 60-tooth gear. What is the gear's speed in rpm?"},
    {"id": "P6_cutting_speed", "needs_context": False, "expected": 94.25, "rel_tol": 0.02,
     "prompt": "A workpiece of 50 mm diameter is turned on a lathe at 600 rpm. What is the cutting speed in m/min?"},
    {"id": "P7_context_dependent", "needs_context": True, "expected": 30.76, "rel_tol": 0.01,
     "prompt": "Size a solid circular shaft to transmit a pure torque of 200 N·m, using this project's standard allowable shear stress. Ignore bending and safety factors. What minimum diameter in mm?"},
]

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _numbers(calcs: dict) -> list[float]:
    out: list[float] = []
    for v in calcs.values():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out.append(float(v))
        elif isinstance(v, str):
            out.extend(float(m) for m in _NUM.findall(v.replace(",", "")))
    return out


def _raw_hit(text: str, exp: float, tol: float) -> bool:
    nums = [float(m) for m in _NUM.findall(text.replace(",", ""))]
    return any(abs(n - exp) <= abs(exp) * tol for n in nums)


def run_once(problem, model, context):
    kwargs = {"retrieved_context": context} if context is not None else {}
    start = time.perf_counter()
    try:
        result = run_reasoning(problem["prompt"], model=model, **kwargs)
    except Exception as exc:  # scratch script: record, don't crash the run
        return {"error": str(exc), "schema": False, "numeric": False, "raw": False, "ms": 0}
    ms = int((time.perf_counter() - start) * 1000)
    exp, tol = problem["expected"], problem["rel_tol"]
    raw = _raw_hit(result.raw_text, exp, tol)
    if result.structured is None:
        return {"error": None, "schema": False, "numeric": False, "raw": raw, "ms": ms}
    hit = any(abs(n - exp) <= abs(exp) * tol for n in _numbers(result.structured.preliminary_calculations))
    return {"error": None, "schema": True, "numeric": hit, "raw": raw, "ms": ms}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["baseline", "retrieval"], required=True)
    ap.add_argument("--project-id", type=int)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    context = None
    if args.mode == "retrieval":
        if args.project_id is None:
            sys.exit("--project-id is required for --mode retrieval")
        from app.db.session import get_session
        from app.reasoning.retrieval import build_retrieved_context

        session = next(get_session())
        try:
            context = build_retrieved_context(session, args.project_id)
        finally:
            session.close()
        if context is None:
            sys.exit("No retrievable context for that project — comparison would be meaningless.")
        print("=== INJECTED CONTEXT ===")
        print(context)
        print("========================\n")

    print(f"mode={args.mode} runs={args.runs} model={args.model or 'default'}")
    totals = {"general": [0, 0, 0, 0], "context": [0, 0, 0, 0]}  # schema, numeric, raw, attempts
    for p in PROBLEMS:
        runs = [run_once(p, args.model, context) for _ in range(args.runs)]
        s = sum(r["schema"] for r in runs)
        n = sum(r["numeric"] for r in runs)
        rw = sum(r["raw"] for r in runs)
        errs = sum(1 for r in runs if r["error"])
        avg_ms = sum(r["ms"] for r in runs) // max(len(runs), 1)
        print(f"{p['id']:<22} schema {s}/{args.runs}  numeric {n}/{args.runs}  raw-text {rw}/{args.runs}  errors {errs}  ~{avg_ms} ms")
        bucket = totals["context" if p["needs_context"] else "general"]
        bucket[0] += s
        bucket[1] += n
        bucket[2] += rw
        bucket[3] += args.runs
    for name, (s, n, rw, a) in totals.items():
        print(f"[{name}] schema {s}/{a}  numeric {n}/{a}  raw-text {rw}/{a}")


if __name__ == "__main__":
    main()
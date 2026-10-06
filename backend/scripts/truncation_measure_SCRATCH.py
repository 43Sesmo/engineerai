"""
SCRATCH — Sprint 9 truncation measurement. Not production code; lives
outside app/ and changes nothing in it.

Measures stop_reason and input/output tokens for the real six-field
prompt, with and without Vault context, calling the Anthropic SDK
directly with the same inputs production uses: one user message, no
system prompt, no temperature, settings.anthropic_model, and the
provider's max_tokens.

PRE-REGISTERED BEFORE ANY RUN — do not edit after seeing results.

Context project: 7 ("Sprint 8 Eval"), the same project and entries as the
Sprint 8 final eval pair. The injected block is printed at run start.

Cap-drift guard: MAX_TOKENS below must equal the max_tokens literal in
app/ai/providers/anthropic_provider.py, or the run aborts.

Parity gate (P1-P7 from reasoning_eval_SCRATCH.py, 3 runs, both modes):
  P1-P6 schema 18/18 in BOTH modes; P7 baseline schema 3/3 and numeric
  0/3; P7 retrieval schema 3/3 and numeric 3/3.
  If the gate fails the run stops before D1-D4 and nothing is interpreted.

Open-ended prompts D1-D4: fixed below, no swaps after results.

Trip rule (applied to all calls, parity problems included):
  TIER 1: any call with stop_reason == "max_tokens".
  TIER 2: no Tier 1, but any call with output_tokens > 3072 (75% of 4096).
  CLEAR:  neither.
Informational only (not a trip): calls above 1024 output tokens, the old
cap, to show how many would have truncated before Sprint 8's fix.

Usage (from backend/, venv active):
  python scripts/truncation_measure_SCRATCH.py
"""

import argparse
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.reasoning.parser import try_parse_guidance  # noqa: E402
from app.reasoning.prompts.engineering_guidance_prompt import build_prompt  # noqa: E402
from reasoning_eval_SCRATCH import PROBLEMS, _numbers  # noqa: E402

MAX_TOKENS = 4096
TIER2_THRESHOLD = 3072  # 75% of MAX_TOKENS
OLD_CAP = 1024
RUNS = 3

DESIGN_PROMPTS = [
    {"id": "D1_motor_bracket",
     "prompt": "Design a mounting bracket to hold a 50 kg electric motor on a steel workshop bench. I want it fabricated from sheet metal and bar stock."},
    {"id": "D2_screw_jack",
     "prompt": "I need a hand-operated screw jack to lift 2 tonnes by 300 mm. Propose the screw, nut and handle design."},
    {"id": "D3_belt_drive",
     "prompt": "Design a belt drive to connect a 3 kW motor at 1440 rpm to a conveyor shaft that must turn at about 120 rpm. Cover pulley sizing, belt selection and shaft loads."},
    {"id": "D4_bending_brake",
     "prompt": "Plan a campus-workshop project to build a small bench-top sheet metal bending brake: mechanism, materials, manufacturing steps and the main risks."},
]


def check_cap_parity() -> None:
    src_path = Path(__file__).resolve().parents[1] / "app" / "ai" / "providers" / "anthropic_provider.py"
    src = src_path.read_text(encoding="utf-8")
    found = re.findall(r"max_tokens\s*=\s*(\d+)", src)
    if found != [str(MAX_TOKENS)]:
        sys.exit(
            f"CAP DRIFT: harness MAX_TOKENS={MAX_TOKENS} but provider source "
            f"shows {found}. Update the harness (and re-register thresholds) "
            "before running."
        )
    print(f"cap parity OK: provider max_tokens={MAX_TOKENS}, model={settings.anthropic_model}")


def build_context(project_id: int) -> str:
    from app.db.session import get_session
    from app.reasoning.retrieval import build_retrieved_context

    session = next(get_session())
    try:
        ctx = build_retrieved_context(session, project_id)
    finally:
        session.close()
    if ctx is None:
        sys.exit(f"No retrievable context for project {project_id}.")
    return ctx


def one_call(client, user_text: str, context):
    full_prompt = build_prompt(user_text, retrieved_context=context)
    start = time.perf_counter()
    try:
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": full_prompt}],
        )
    except Exception as exc:  # scratch: record and continue
        return {"stop": f"ERROR:{type(exc).__name__}", "in": 0, "out": 0,
                "ms": 0, "structured": None, "text": ""}
    ms = int((time.perf_counter() - start) * 1000)
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {"stop": resp.stop_reason, "in": resp.usage.input_tokens,
            "out": resp.usage.output_tokens, "ms": ms,
            "structured": try_parse_guidance(text), "text": text}


def run_items(client, items, context, ctx_label_runs=RUNS):
    records = []
    for item in items:
        for mode, ctx in (("baseline", None), ("retrieval", context)):
            for run in range(1, ctx_label_runs + 1):
                r = one_call(client, item["prompt"], ctx)
                schema = r["structured"] is not None
                numeric = None
                if "expected" in item:
                    numeric = bool(schema and any(
                        abs(n - item["expected"]) <= abs(item["expected"]) * item["rel_tol"]
                        for n in _numbers(r["structured"].preliminary_calculations)))
                rec = {"id": item["id"], "mode": mode, "run": run, "stop": r["stop"],
                       "in": r["in"], "out": r["out"], "ms": r["ms"],
                       "schema": schema, "numeric": numeric}
                records.append(rec)
                print(f"{rec['id']:<22} {mode:<9} run{run}  stop={rec['stop']:<10} "
                      f"in={rec['in']:<5} out={rec['out']:<5} {rec['ms']:>6} ms  "
                      f"schema={schema}" + (f"  numeric={numeric}" if numeric is not None else ""),
                      flush=True)
    return records


def gate(records) -> bool:
    ok = True
    for mode in ("baseline", "retrieval"):
        gen = [r for r in records if r["mode"] == mode and not r["id"].startswith("P7")]
        s = sum(r["schema"] for r in gen)
        print(f"  gate P1-P6 {mode}: schema {s}/{len(gen)} (need 18/18)")
        ok &= (len(gen) == 18 and s == 18)
    p7b = [r for r in records if r["id"].startswith("P7") and r["mode"] == "baseline"]
    p7r = [r for r in records if r["id"].startswith("P7") and r["mode"] == "retrieval"]
    bs, bn = sum(r["schema"] for r in p7b), sum(bool(r["numeric"]) for r in p7b)
    rs, rn = sum(r["schema"] for r in p7r), sum(bool(r["numeric"]) for r in p7r)
    print(f"  gate P7 baseline: schema {bs}/3 (need 3), numeric {bn}/3 (need 0)")
    print(f"  gate P7 retrieval: schema {rs}/3 (need 3), numeric {rn}/3 (need 3)")
    ok &= (bs == 3 and bn == 0 and rs == 3 and rn == 3)
    return ok


def summarize(records) -> None:
    # Error rows (API connection failures) carry zero tokens and must not be
    # averaged in; they are reported separately below.
    ok = [r for r in records if not str(r["stop"]).startswith("ERROR")]
    print("\n=== PER PROMPT / MODE (mean in, mean out, max out, mean ms; completed calls only) ===")
    keys = sorted({(r["id"], r["mode"]) for r in records}, key=lambda k: (k[0], k[1] != "baseline"))
    for pid, mode in keys:
        rs = [r for r in ok if r["id"] == pid and r["mode"] == mode]
        n = len(rs)
        if n == 0:
            print(f"{pid:<22} {mode:<9} NO COMPLETED CALLS (all errored)")
            continue
        print(f"{pid:<22} {mode:<9} n={n} in~{sum(r['in'] for r in rs)//n:<5} "
              f"out~{sum(r['out'] for r in rs)//n:<5} maxout={max(r['out'] for r in rs):<5} "
              f"~{sum(r['ms'] for r in rs)//n} ms")
    print("\n=== OVERALL BY MODE ===")
    for mode in ("baseline", "retrieval"):
        rs = [r for r in ok if r["mode"] == mode]
        n = len(rs)
        if n == 0:
            print(f"{mode:<9} no completed calls")
            continue
        print(f"{mode:<9} completed calls={n}  in~{sum(r['in'] for r in rs)//n}  "
              f"out~{sum(r['out'] for r in rs)//n}  ~{sum(r['ms'] for r in rs)//n} ms  "
              f"maxout={max(r['out'] for r in rs)}")

    stops = [r for r in records if r["stop"] == "max_tokens"]
    near = [r for r in records if r["out"] > TIER2_THRESHOLD]
    over_old = [r for r in records if r["out"] > OLD_CAP]
    errors = [r for r in records if str(r["stop"]).startswith("ERROR")]
    print(f"\ncalls total={len(records)}  errors={len(errors)}  "
          f"max_tokens stops={len(stops)}  out>{TIER2_THRESHOLD}={len(near)}  "
          f"(info) out>{OLD_CAP}={len(over_old)}")
    if stops:
        print("RESULT: TIER 1 — at least one call stopped on max_tokens.")
    elif near:
        print(f"RESULT: TIER 2 — no truncation, but output exceeded {TIER2_THRESHOLD} tokens.")
    else:
        print(f"RESULT: CLEAR — no truncation; max output {max(r['out'] for r in records)} tokens.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", type=int, default=7)
    args = ap.parse_args()

    check_cap_parity()
    context = build_context(args.project_id)
    print("=== INJECTED CONTEXT (project %d) ===" % args.project_id)
    print(context)
    print("=====================================\n")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    print("--- PHASE 1: parity problems P1-P7 (42 calls) ---")
    records = run_items(client, PROBLEMS, context)
    print("\n--- PARITY GATE ---")
    if not gate(records):
        print("GATE FAILED — the harness does not reproduce Sprint 8's results. "
              "Stopping before D1-D4. Do not interpret these numbers.")
        sys.exit(2)
    print("GATE PASSED\n")

    print("--- PHASE 2: open-ended prompts D1-D4 (24 calls) ---")
    records += run_items(client, DESIGN_PROMPTS, context)
    summarize(records)


if __name__ == "__main__":
    main()

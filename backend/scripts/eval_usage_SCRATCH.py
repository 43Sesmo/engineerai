"""
SCRATCH — Sprint 9 V10 eval re-run. Not production code; lives outside app/.
Reads the database (project 7's context) and writes nothing to it.

Runs the Sprint 8 problems P1-P7 (from reasoning_eval_SCRATCH.py), both
modes (baseline, retrieval with project 7's context), 3 runs per cell =
42 calls in the first pass, through the PRODUCTION path: run_reasoning ->
generate_guidance -> build_prompt -> send_prompt -> the real
anthropic_provider.send_prompt. (run_reasoning is called with
retrieved_context=None for baseline and without a model argument; engine.py
defaults both to None, which is what the Sprint 8 eval's call resolves to.)

HOW USAGE IS CAPTURED: the script replaces anthropic.Anthropic for the
duration of the process with a recording proxy. The real client does the
real call; the proxy only reads resp.usage (input tokens, output tokens,
thinking_tokens) and stop_reason and appends them to a list. The provider
code is not touched or modified.

PRE-REGISTERED MISMATCH RULE (fixed before running; no change after seeing
results without the Project Lead's approval).
A CELL is one problem in one mode (3 runs). Expected per cell:
  - P1-P6, both modes, and P7 retrieval: schema 3/3 and numeric 3/3.
  - P7 baseline: schema 3/3 and numeric 0/3 (that is the point of P7).
A MISS is a call that completed and whose schema or numeric result differs
from its cell's expectation. An exception is NOT a miss:
  - a connection or rate-limit error (AIProviderError whose message starts
    "Anthropic API request timed out" or "Anthropic API returned an error")
    is retried once after 10 seconds; if the retry also fails, the call is
    recorded as FAILED, reported separately from misses, and never counted
    as a pass or silently replaced by another result;
  - a max_tokens or no-text failure ("The model used its whole output
    budget..." / "The model returned no text...") is a FINDING and stops the
    run for the Project Lead;
  - any other exception is recorded as a failed call (not retried).
Rules for misses:
  - 1 miss in one cell: rerun that cell once (3 more calls, same mode). The
    first pass stays on the record.
  - "Repeating" means the rerun has any miss, OR a second cell has a miss
    in the same pass. Two or more misses in one cell, or anything repeating:
    STOP and bring the numbers to the Project Lead.
After 3 consecutive failed calls the run also stops (INCOMPLETE).
Worst-case extra spend from the single allowed rerun is 3 calls.

RERUNNING ONE CELL without paying for all 42 calls:
  python scripts/eval_usage_SCRATCH.py --only P3_beam_moment --mode baseline
This runs that one cell once (3 calls), prints misses and failed calls
separately, and does not rerun automatically.

COMPARISONS (reported side by side, informational):
  - Latency, per problem and mode, against Sprint 8's final pair.
    SOURCE: Sprint 8 closure report (project file sprint_8_closure_report.md),
    section 5, "Average latency (ms), baseline -> retrieval".
  - Output tokens, per problem and mode, against the Sprint 9 first
    measurement. SOURCE: the output of `python scripts\\truncation_measure_SCRATCH.py`
    (first run, Phase 1, P1-P7, 4,096 cap, 3 runs per cell), "PER PROMPT / MODE"
    table, `out~` column, as pasted by the Project Lead in the Sprint 9 chat.
    These are a transcription of that pasted output (integer means, thinking
    tokens included), not a file in the repository.
  - Thinking tokens have no earlier baseline.
  - The 25% flag is INFORMATIONAL only.

REVISED 2026-10-23, before any call at medium was made: added --effort
{default,medium} (default leaves the script's behavior unchanged; medium makes
the recording proxy add output_config={"effort": "medium"} to every request
and nothing else; max_tokens is never rewritten, it stays the provider's
MAX_OUTPUT_TOKENS), a request-shape guard (the script exits before any spend
if a request does not have exactly the production keys, plus output_config
for medium, or if max_tokens is not the provider's MAX_OUTPUT_TOKENS), a
spend guard, and a maximum-thinking-tokens line. Nothing else changed.

SPEND GUARD (ceiling 0.75 USD, approved by the Project Lead). Every response
the proxy records is priced at 2 USD per million input tokens and 10 USD per
million output tokens (an estimate, not billing; the Project Lead chose these
rates after the D2 measurement, where the recorded tokens at these rates gave
0.349 USD against a 0.35 USD Console delta), and rerun calls count too.
Before each call the script adds a worst-case next call (the provider's
MAX_OUTPUT_TOKENS at the output rate plus the last seen input tokens, or 3,000
before any, at the input rate) and stops if the sum would exceed the ceiling. A guard stop is an INCOMPLETE run,
neither pass nor fail: the numbers so far are reported, the Project Lead
decides, and there is no automatic resume. A retry after a transient error is
not separately checked.

Usage (from backend/, venv active):
  python scripts/eval_usage_SCRATCH.py                   (effort default, as before)
  python scripts/eval_usage_SCRATCH.py --effort medium   (V10 at medium)
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: E402

from app.ai.providers import anthropic_provider as prov  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.reasoning.engine import run_reasoning  # noqa: E402
from app.reasoning.retrieval import build_retrieved_context  # noqa: E402
from reasoning_eval_SCRATCH import PROBLEMS, _numbers  # noqa: E402

RUNS = 3
PROJECT_ID = 7
MODES = ("baseline", "retrieval")
ABORT_AFTER_CONSECUTIVE_FAILURES = 3
RETRY_PAUSE_S = 10
FLAG_PCT = 25.0
FIRST_PASS_CALLS = 42
SPEND_CEILING_USD = 0.75
USD_PER_MTOK_IN = 2.0    # estimate rates approved by the Project Lead (not billing)
USD_PER_MTOK_OUT = 10.0
PRODUCTION_KEYS = {"model", "max_tokens", "messages"}
FALLBACK_INPUT_TOKENS = 3000
EFFORT = "default"

FINDING_PREFIXES = ("The model used its whole output budget", "The model returned no text")
TRANSIENT_PREFIXES = ("Anthropic API request timed out", "Anthropic API returned an error")

# The script depends on every problem having these fields, with numeric tolerances.
REQUIRED_KEYS = ("id", "prompt", "expected", "rel_tol")
assert len(PROBLEMS) == 7, f"expected 7 problems, found {len(PROBLEMS)}"
for _p in PROBLEMS:
    _missing = [k for k in REQUIRED_KEYS if k not in _p]
    assert not _missing, f"problem {_p.get('id', '?')} is missing {_missing}"
    assert isinstance(_p["expected"], (int, float)) and isinstance(_p["rel_tol"], (int, float)), (
        f"problem {_p['id']}: expected and rel_tol must be numbers")

# Self-test of the numeric helper the miss rule depends on (a bool is skipped, numbers inside strings count).
assert _numbers({"d_mm": 30.77, "note": "25 mm", "flag": True}) == [30.77, 25.0], "numeric helper changed"

# Sprint 8 final pair, average latency in ms (Sprint 8 closure report, section 5).
SPRINT8_LATENCY_MS = {
    "baseline": {"P1_torque": 8219, "P2_shaft_dia": 11336, "P3_beam_moment": 6320,
                 "P4_tensile_stress": 8753, "P5_gear_speed": 6971, "P6_cutting_speed": 6728,
                 "P7_context_dependent": 10923},
    "retrieval": {"P1_torque": 13785, "P2_shaft_dia": 13456, "P3_beam_moment": 8797,
                  "P4_tensile_stress": 12324, "P5_gear_speed": 8511, "P6_cutting_speed": 7327,
                  "P7_context_dependent": 12701},
}

# Sprint 9 first measurement, P1-P7 phase at the 4,096 cap: mean output tokens per
# problem and mode. Transcribed from the pasted `out~` column; see the header for the source.
S9_FIRST_OUTPUT_TOKENS = {
    "baseline": {"P1_torque": 691, "P2_shaft_dia": 756, "P3_beam_moment": 721,
                 "P4_tensile_stress": 797, "P5_gear_speed": 506, "P6_cutting_speed": 619,
                 "P7_context_dependent": 1110},
    "retrieval": {"P1_torque": 1208, "P2_shaft_dia": 1274, "P3_beam_moment": 755,
                  "P4_tensile_stress": 1048, "P5_gear_speed": 653, "P6_cutting_speed": 564,
                  "P7_context_dependent": 1345},
}

CAPTURED = []  # usage records appended by the recording proxy
SPEND = {"usd": 0.0, "last_in": None}  # running estimate, updated by the proxy


class _RecMessages:
    def __init__(self, inner):
        self._inner = inner

    def create(self, **kwargs):
        kwargs = dict(kwargs)
        if EFFORT == "medium":
            kwargs["output_config"] = {"effort": "medium"}
        expected_keys = set(PRODUCTION_KEYS) | ({"output_config"} if EFFORT == "medium" else set())
        if set(kwargs) != expected_keys or kwargs.get("max_tokens") != prov.MAX_OUTPUT_TOKENS:
            sys.exit(f"REQUEST SHAPE CHANGED before any spend: effort {EFFORT} would send keys "
                     f"{sorted(kwargs)} with max_tokens={kwargs.get('max_tokens')}; expected keys "
                     f"{sorted(expected_keys)} and max_tokens={prov.MAX_OUTPUT_TOKENS}. Stop and report.")
        resp = self._inner.create(**kwargs)
        usage = getattr(resp, "usage", None)
        details = getattr(usage, "output_tokens_details", None)
        rec = {
            "in": getattr(usage, "input_tokens", None),
            "out": getattr(usage, "output_tokens", None),
            "think": getattr(details, "thinking_tokens", None),
            "stop": getattr(resp, "stop_reason", None),
        }
        CAPTURED.append(rec)
        SPEND["usd"] += ((rec["in"] or 0) * USD_PER_MTOK_IN + (rec["out"] or 0) * USD_PER_MTOK_OUT) / 1e6
        if rec["in"]:
            SPEND["last_in"] = rec["in"]
        return resp


class _RecClient:
    def __init__(self, real):
        self.messages = _RecMessages(real.messages)


def install_recorder():
    real_cls = anthropic.Anthropic

    def factory(*args, **kwargs):
        return _RecClient(real_cls(*args, **kwargs))

    prov.anthropic.Anthropic = factory


def is_general(problem):
    return not problem["id"].startswith("P7")


def one_call(problem, context):
    CAPTURED.clear()
    start = time.perf_counter()
    try:
        result = run_reasoning(problem["prompt"], retrieved_context=context)
        structured = result.structured
        schema = structured is not None
        numeric = False
        if schema:
            calcs = structured.preliminary_calculations
            assert isinstance(calcs, dict), "preliminary_calculations is not a dict"
            numeric = any(abs(n - problem["expected"]) <= abs(problem["expected"]) * problem["rel_tol"]
                          for n in _numbers(calcs))
    except Exception as exc:  # noqa: BLE001 — recorded, never crashes the run
        return {"failed": True, "exc_cls": type(exc).__name__, "exc_msg": str(exc)[:300],
                "ms": int((time.perf_counter() - start) * 1000),
                "usage": CAPTURED[-1] if CAPTURED else None, "schema": False, "numeric": False}
    return {"failed": False, "exc_cls": None, "exc_msg": None,
            "ms": int((time.perf_counter() - start) * 1000),
            "usage": CAPTURED[-1] if CAPTURED else None, "schema": schema, "numeric": numeric}


def error_kind(r):
    if not r["failed"]:
        return None
    if r["exc_cls"] == "AIProviderError":
        if r["exc_msg"].startswith(FINDING_PREFIXES):
            return "finding"
        if r["exc_msg"].startswith(TRANSIENT_PREFIXES):
            return "transient"
    return "other"


def call_with_retry(problem, context):
    r = one_call(problem, context)
    r["attempts"] = 1
    if error_kind(r) == "transient":
        print(f"   transient error ({r['exc_msg'][:80]}); retrying once in {RETRY_PAUSE_S} s", flush=True)
        time.sleep(RETRY_PAUSE_S)
        first = r
        r = one_call(problem, context)
        r["attempts"] = 2
        r["first_error"] = f"{first['exc_cls']}: {first['exc_msg']}"
    return r


def is_miss(problem, mode, r):
    """A completed call whose schema or numeric result differs from its cell's expectation."""
    if r["failed"]:
        return False
    if not r["schema"]:
        return True
    if not is_general(problem) and mode == "baseline":
        return r["numeric"]  # P7 baseline must NOT match numerically
    return not r["numeric"]


class _State:
    def __init__(self):
        self.rows = []
        self.consecutive_failures = 0
        self.aborted = False
        self.stop_reason = None
        self.guard_stopped = False
        self.isolated = []      # cells with exactly one miss whose rerun was clean
        self.miss_cells = []    # cells with a miss in the first pass


def run_cell(state, problem, mode, context, phase):
    cell = []
    for run in range(1, RUNS + 1):
        worst = (prov.MAX_OUTPUT_TOKENS * USD_PER_MTOK_OUT
                 + (SPEND["last_in"] or FALLBACK_INPUT_TOKENS) * USD_PER_MTOK_IN) / 1e6
        if SPEND["usd"] + worst > SPEND_CEILING_USD:
            state.guard_stopped = True
            print(f"\nSPEND GUARD: estimated spend {SPEND['usd']:.2f} + worst-case next call {worst:.2f} "
                  f"would exceed {SPEND_CEILING_USD:.2f} USD. Run stopped before {problem['id']} {mode} "
                  f"run{run}. INCOMPLETE: neither pass nor fail.")
            return cell
        r = call_with_retry(problem, context)
        r.update({"id": problem["id"], "mode": mode, "run": run, "phase": phase})
        state.rows.append(r)
        cell.append(r)
        u = r["usage"] or {}
        if r["failed"]:
            status = f"FAILED ({error_kind(r)}, {r['attempts']} attempt(s)): {r['exc_cls']}: {r['exc_msg'][:120]}"
        else:
            status = f"schema={r['schema']} numeric={r['numeric']}" + (
                "  MISS" if is_miss(problem, mode, r) else "")
        tag = "" if phase == "first" else " [RERUN]"
        print(f"{problem['id']:<22} {mode:<9} run{run}  {r['ms']:>6} ms  out={u.get('out')} "
              f"think={u.get('think')} stop={u.get('stop')}  {status}{tag}", flush=True)
        if error_kind(r) == "finding":
            state.stop_reason = (f"FINDING in {problem['id']} {mode} run{run}: {r['exc_msg'][:160]} "
                                 "(a max_tokens or no-text failure stops the run)")
            print(f"\nSTOP: {state.stop_reason}")
            return cell
        state.consecutive_failures = state.consecutive_failures + 1 if r["failed"] else 0
        if state.consecutive_failures >= ABORT_AFTER_CONSECUTIVE_FAILURES:
            print(f"\nABORT: {state.consecutive_failures} consecutive failed calls.")
            state.aborted = True
            return cell
    return cell


def run_all(context):
    state = _State()
    for p in PROBLEMS:
        for mode in MODES:
            ctx = None if mode == "baseline" else context
            cell = run_cell(state, p, mode, ctx, "first")
            if state.aborted or state.stop_reason or state.guard_stopped:
                return state
            misses = [r for r in cell if is_miss(p, mode, r)]
            if not misses:
                continue
            if len(misses) >= 2:
                state.stop_reason = f"{p['id']} {mode}: {len(misses)} misses in one cell"
                print(f"\nSTOP: {state.stop_reason}")
                return state
            if state.miss_cells:
                other = state.miss_cells[0]
                state.stop_reason = (f"repeating: a second cell has a miss in the same pass "
                                     f"({other[0]} {other[1]}, then {p['id']} {mode})")
                state.miss_cells.append((p["id"], mode))
                print(f"\nSTOP: {state.stop_reason}")
                return state
            state.miss_cells.append((p["id"], mode))
            print(f"\n1 miss in {p['id']} {mode}: rerunning that cell once.")
            rerun = run_cell(state, p, mode, ctx, "rerun")
            if state.aborted or state.stop_reason or state.guard_stopped:
                return state
            if any(is_miss(p, mode, r) for r in rerun):
                state.stop_reason = f"{p['id']} {mode}: the rerun has a miss (repeating)"
                print(f"\nSTOP: {state.stop_reason}")
                return state
            state.isolated.append((p["id"], mode))
            print(f"Rerun clean: the miss in {p['id']} {mode} is recorded as isolated.\n")
    return state


def run_only(context, problem_id, mode):
    problem = next((p for p in PROBLEMS if p["id"] == problem_id), None)
    if problem is None:
        sys.exit(f"unknown problem id {problem_id!r}; choose from {[p['id'] for p in PROBLEMS]}")
    state = _State()
    run_cell(state, problem, mode, None if mode == "baseline" else context, "only")
    return state, problem, mode


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def _pct(new, old):
    if new is None or not old:
        return None
    return (new - old) / old * 100.0


def _fmt_pct(p):
    if p is None:
        return "   n/a"
    flag = "*" if abs(p) > FLAG_PCT else " "
    return f"{p:+5.0f}%{flag}"


def print_misses_and_failures(state):
    rows = state.rows
    by_id = {p["id"]: p for p in PROBLEMS}
    misses = [r for r in rows if is_miss(by_id[r["id"]], r["mode"], r)]
    failed = [r for r in rows if r["failed"]]
    print(f"\n=== MISSES (completed calls whose result differs from the cell's expectation): {len(misses)} ===")
    for r in misses:
        print(f"  {r['id']} {r['mode']} run{r['run']} ({r['phase']}): schema={r['schema']} numeric={r['numeric']}")
    print(f"\n=== FAILED CALLS (exceptions; NOT misses, NOT passes): {len(failed)} ===")
    for r in failed:
        extra = f"; first attempt: {r['first_error']}" if r.get("first_error") else ""
        print(f"  {r['id']} {r['mode']} run{r['run']} ({r['phase']}), {error_kind(r)}, {r['attempts']} attempt(s): "
              f"{r['exc_cls']}: {r['exc_msg'][:160]}{extra}")
    return misses, failed


def print_spend():
    print(f"effort: {EFFORT}; estimated spend {SPEND['usd']:.2f} USD of the {SPEND_CEILING_USD:.2f} ceiling "
          f"(estimate at ${USD_PER_MTOK_IN:.0f}/M input and ${USD_PER_MTOK_OUT:.0f}/M output; not billing)")


def summarize(state):
    rows = state.rows
    first = [r for r in rows if r["phase"] == "first"]
    print("\n=== PER PROBLEM / MODE (first pass only; means over completed calls) ===")
    print(f"{'problem':<22} {'mode':<9} {'done/failed':<12} {'schema':<7} {'numeric':<8} {'misses':<7} "
          f"{'lat ms':>7} {'vs S8':>8} {'out tok':>8} {'vs S9a':>8} {'think':>6}")
    for p in PROBLEMS:
        for mode in MODES:
            rs = [r for r in first if r["id"] == p["id"] and r["mode"] == mode]
            if not rs:
                print(f"{p['id']:<22} {mode:<9} (not run)")
                continue
            done = [r for r in rs if not r["failed"]]
            lat = _mean([r["ms"] for r in done])
            out = _mean([r["usage"]["out"] for r in done if r["usage"]])
            think = _mean([r["usage"]["think"] for r in done if r["usage"]])
            miss_n = sum(is_miss(p, mode, r) for r in rs)
            print(f"{p['id']:<22} {mode:<9} {len(done)}/{len(rs) - len(done):<10} "
                  f"{sum(r['schema'] for r in done)}/{len(done):<5} {sum(r['numeric'] for r in done)}/{len(done):<6} "
                  f"{miss_n:<7} {(lat or 0):>7.0f} {_fmt_pct(_pct(lat, SPRINT8_LATENCY_MS[mode][p['id']])):>8} "
                  f"{(out or 0):>8.0f} {_fmt_pct(_pct(out, S9_FIRST_OUTPUT_TOKENS[mode][p['id']])):>8} "
                  f"{(think or 0):>6.0f}")
    print("\n'vs S8' = mean latency against Sprint 8's final pair (Sprint 8 closure report, section 5).")
    print("'vs S9a' = mean output tokens against the Sprint 9 first measurement at the 4,096 cap "
          "(transcribed from the Project Lead's pasted `out~` column; not a repository file).")
    print("'*' marks a move above 25%: informational only. P7 baseline numeric is EXPECTED to be 0/3.")

    reruns = [r for r in rows if r["phase"] == "rerun"]
    by_id = {p["id"]: p for p in PROBLEMS}
    if reruns:
        print("\n=== RERUNS ===")
        for key in sorted({(r["id"], r["mode"]) for r in reruns}):
            rs = [r for r in reruns if (r["id"], r["mode"]) == key]
            print(f"{key[0]:<22} {key[1]:<9} misses in rerun: "
                  f"{sum(is_miss(by_id[key[0]], key[1], r) for r in rs)}/{len(rs)}; failed {sum(r['failed'] for r in rs)}")

    misses, failed = print_misses_and_failures(state)
    outs = [r["usage"]["out"] for r in rows if r["usage"] and r["usage"]["out"] is not None]
    near = [o for o in outs if o >= prov.NEAR_MISS_TOKENS]
    print(f"\ncalls made {len(rows)} (first pass {len(first)}/{FIRST_PASS_CALLS}, reruns {len(reruns)}); "
          f"max output tokens {max(outs) if outs else 'n/a'}; near-miss (>= {prov.NEAR_MISS_TOKENS}) {len(near)}")
    thinks = [r["usage"]["think"] for r in rows if r["usage"] and r["usage"].get("think") is not None]
    print(f"max thinking tokens {max(thinks) if thinks else 'n/a'} (over {len(thinks)} calls with a thinking count)")
    print_spend()

    print()
    if state.stop_reason:
        print(f"RESULT: STOPPED — {state.stop_reason}. Bring the numbers to the Project Lead.")
    elif state.guard_stopped:
        print("RESULT: INCOMPLETE — the spend guard stopped the run. Neither pass nor fail. "
              "The numbers so far are above; the Project Lead decides. No automatic resume.")
    elif state.aborted:
        print("RESULT: INCOMPLETE — stopped after consecutive failed calls. Bring the numbers to the Project Lead.")
    elif failed or len(first) != FIRST_PASS_CALLS:
        cells = sorted({(r['id'], r['mode']) for r in failed})
        print(f"RESULT: INCOMPLETE — {len(failed)} failed call(s) in {cells}, reported separately from misses and "
              "not counted as passes. Rerun each affected cell with --only and --mode.")
    elif state.isolated:
        cells = ", ".join(f"{pid} {mode}" for pid, mode in state.isolated)
        print(f"RESULT: PASS RATES MATCH Sprint 8 WITH {len(state.isolated)} ISOLATED MISS(ES), each rerun clean: {cells}.")
    else:
        print("RESULT: PASS RATES MATCH Sprint 8. Latency and token differences are reported above.")


def summarize_only(state, problem, mode):
    misses, failed = print_misses_and_failures(state)
    done = [r for r in state.rows if not r["failed"]]
    print(f"\nCELL {problem['id']} {mode}: completed {len(done)}/{RUNS}, misses {len(misses)}, failed {len(failed)}")
    print_spend()
    if state.stop_reason:
        print(f"RESULT: STOPPED — {state.stop_reason}. Bring the numbers to the Project Lead.")
    elif state.guard_stopped:
        print("RESULT: INCOMPLETE — the spend guard stopped the run. Neither pass nor fail. "
              "The numbers so far are above; the Project Lead decides. No automatic resume.")
    elif failed:
        print("RESULT: CELL INCOMPLETE — failed calls are reported above and are not counted as passes.")
    elif not misses:
        print("RESULT: CELL CLEAN — every call matched the cell's expectation.")
    else:
        print(f"RESULT: CELL HAS {len(misses)} MISS(ES) — bring the numbers to the Project Lead.")


def main():
    global EFFORT
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", type=int, default=PROJECT_ID)
    ap.add_argument("--only", help="problem id: run just that cell once (needs --mode)")
    ap.add_argument("--mode", choices=MODES, help="mode for --only")
    ap.add_argument("--effort", choices=("default", "medium"), default="default",
                    help="medium: the proxy adds output_config={'effort': 'medium'} to every request")
    args = ap.parse_args()
    EFFORT = args.effort
    if bool(args.only) != bool(args.mode):
        sys.exit("--only and --mode must be given together")

    session = next(get_session())
    try:
        context = build_retrieved_context(session, args.project_id)
    finally:
        session.close()
    lines = [ln for ln in (context or "").splitlines() if ln.strip()]
    assert len(lines) == 3, f"project {args.project_id} context has {len(lines)} lines, expected 3"
    print(f"=== INJECTED CONTEXT (project {args.project_id}) ===\n{context}\n"
          f"=====================================\n")
    print(f"provider MAX_OUTPUT_TOKENS={prov.MAX_OUTPUT_TOKENS}; "
          + (f"single cell {args.only} {args.mode} (3 calls)\n" if args.only
             else f"first pass {FIRST_PASS_CALLS} calls, plus at most one cell rerun\n"))

    print(f"EFFORT = {EFFORT}"
          + (" (the proxy adds output_config={'effort': 'medium'} to every request)" if EFFORT == "medium"
             else " (no output_config; unchanged behavior)"))
    print(f"spend ceiling {SPEND_CEILING_USD:.2f} USD (estimate at ${USD_PER_MTOK_IN:.0f}/M input and "
          f"${USD_PER_MTOK_OUT:.0f}/M output)\n")

    install_recorder()
    if args.only:
        state, problem, mode = run_only(context, args.only, args.mode)
        summarize_only(state, problem, mode)
    else:
        summarize(run_all(context))


if __name__ == "__main__":
    main()

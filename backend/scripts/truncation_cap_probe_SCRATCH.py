"""
SCRATCH — Sprint 9 cap probe, v3 (small sample). Not production code; lives
outside app/ and changes nothing in it. Anthropic only: xKiro measures a
different model and is out of scope for this probe.

Purpose: find the REAL total output (thinking + text) of the open-ended
design prompts, which the first measurement could not see because 8 of 15
completed calls hit the 4096 ceiling (censored data). Calls the Anthropic
SDK directly with production inputs (one user message, no system prompt,
no temperature, no thinking option, no effort setting, settings.anthropic_model)
and ONLY max_tokens raised.

STATUS: PROPOSED. Do not run until the Project Lead approves this
registration. Once approved, do not edit after seeing results.

RE-REGISTERED TOGETHER (replaces the 24-call v2 registration):

Model: aborts unless settings.anthropic_model == "claude-sonnet-5".

Mode: retrieval only (context from project 7), the production-like case
for a project with Vault entries.

Sample: 7 calls in this order: D1 control x1, D2 x2, D3 x2, D4 x2
(prompts from truncation_measure_SCRATCH.py, unchanged).

Probe cap: 16000. A cheap capability call at 16000 runs first; if the SDK
refuses a non-streaming request at that size, the probe cap becomes 12000.
A connection error during the capability call stops the run.

Retries and timing: max_retries=0 on the client so timings stay clean (this
differs from production, which uses the SDK default, in retry behavior only).
The script retries once itself, 10 s after a connection error; every
attempt's exception class and elapsed time are recorded. HTTP 429, 5xx and
529 failures are non-completion, recorded with the status code, not retried.

Abort rule: after 3 consecutive calls that fail with a connection error
(after their retry), stop, print the partial summary, mark INCOMPLETE.

Completeness bar: the D1 control must complete; at least 6 of 7 calls
complete; each of D2, D3 and D4 has at least 1 completed call. Otherwise
INCOMPLETE and no cap is derived.

Control rule (a single D1 call is a tripwire, not evidence of variance):
  PASS if the D1 call stops on end_turn with at most 4096 output tokens
  (it used at most 2,792 before). FAIL otherwise: the script prints the D1
  numbers, derives no cap, and the Project Lead decides.

R1: if any completed call stops on max_tokens at the probe cap, NO cap is
    derived; escalate to a separate thinking-control decision.
R2: otherwise T_max = largest output_tokens among completed calls.
    Candidate production cap = T_max x 2.0 (margin widened from 1.5
    because the sample is smaller), rounded UP to the next multiple of 1024.
UNTESTED: a candidate above the probe cap actually used is never shipped
    untested; it needs a new probe at or above the candidate.
R3: estimated worst case = candidate cap x median (ms per output token)
    over completed calls. If above 120 s, R3 has TRIPPED: the raise does
    NOT ship as written, and the Lead brings two options:
    (A) a lower cap that keeps the estimate at or under 120 s, with visible
        failures. Option A is valid only if it is at least T_max.
    (B) a streaming sprint.

The capability call prints the organization's rate-limit headers
(informational; max_tokens does not count toward OTPM).
Informational only: thinking share, count of empty-text calls, count of
calls that fit under 4096.

Thinking limits (effort, disabling thinking) are NOT tested here; they are
held until an eval shows P7 numeric accuracy holds.

Usage (from backend/, venv active):
  python scripts/truncation_cap_probe_SCRATCH.py
"""

import argparse
import math
import re
import statistics
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.reasoning.prompts.engineering_guidance_prompt import build_prompt  # noqa: E402
from truncation_measure_SCRATCH import DESIGN_PROMPTS, build_context  # noqa: E402

EXPECTED_MODEL = "claude-sonnet-5"
PROD_CAP_EXPECTED = 4096
PROBE_CAP = 16000
FALLBACK_CAP = 12000
MARGIN = 2.0
LATENCY_FLAG_S = 120
MODES = ("retrieval",)
CALL_PLAN = (
    ("D1_motor_bracket", 1),
    ("D2_screw_jack", 2),
    ("D3_belt_drive", 2),
    ("D4_bending_brake", 2),
)
TOTAL_CALLS = 7
MIN_COMPLETED = 6
ABORT_AFTER_CONSECUTIVE = 3
RETRY_PAUSE_S = 10
EXPECTED_CONTEXT_LINES = 3

PROMPTS_BY_ID = {p["id"]: p for p in DESIGN_PROMPTS}
assert [pid for pid, _ in CALL_PLAN] == [p["id"] for p in DESIGN_PROMPTS], (
    f"prompt ids drifted: plan {[pid for pid, _ in CALL_PLAN]} vs "
    f"prompts {[p['id'] for p in DESIGN_PROMPTS]}")
assert sum(n for _, n in CALL_PLAN) == TOTAL_CALLS == 7, "call plan must total 7"
assert MODES == ("retrieval",), "this registration is retrieval-only"


def check_environment() -> None:
    src_path = Path(__file__).resolve().parents[1] / "app" / "ai" / "providers" / "anthropic_provider.py"
    found = re.findall(r"max_tokens\s*=\s*(\d+)", src_path.read_text(encoding="utf-8"))
    if found != [str(PROD_CAP_EXPECTED)]:
        sys.exit(f"PROD CAP CHANGED: expected provider max_tokens={PROD_CAP_EXPECTED}, "
                 f"found {found}. Re-register this probe before running.")
    if settings.anthropic_model != EXPECTED_MODEL:
        sys.exit(f"MODEL CHANGED: expected {EXPECTED_MODEL!r}, settings has "
                 f"{settings.anthropic_model!r}. The docs checks apply to {EXPECTED_MODEL!r} only.")
    print(f"environment OK: provider max_tokens={PROD_CAP_EXPECTED}, model={settings.anthropic_model}")


RATE_LIMIT_HEADERS = (
    "anthropic-ratelimit-requests-limit",
    "anthropic-ratelimit-input-tokens-limit",
    "anthropic-ratelimit-output-tokens-limit",
    "anthropic-ratelimit-output-tokens-remaining",
)


def capability_call(client, cap):
    """Cheap call; returns the response headers when the SDK exposes them, else None."""
    kwargs = dict(model=settings.anthropic_model, max_tokens=cap,
                  messages=[{"role": "user", "content": "Reply with the single word OK."}])
    try:
        raw = client.messages.with_raw_response.create(**kwargs)
    except AttributeError:
        client.messages.create(**kwargs)
        return None
    return raw.headers


def print_rate_limits(headers) -> None:
    if headers is None:
        print("rate-limit headers: not available from this SDK version")
        return
    for name in RATE_LIMIT_HEADERS:
        print(f"  {name}: {headers.get(name, '(absent)')}")


def pick_cap(client) -> int:
    for cap in (PROBE_CAP, FALLBACK_CAP):
        try:
            headers = capability_call(client, cap)
            print(f"capability check OK at max_tokens={cap}")
            print_rate_limits(headers)
            return cap
        except anthropic.APIConnectionError as exc:
            sys.exit(f"Connection problem during the capability check ({type(exc).__name__}: {exc}). "
                     "Retry when the connection is stable; not a reason to change the cap.")
        except Exception as exc:  # noqa: BLE001
            print(f"capability check FAILED at max_tokens={cap}: {type(exc).__name__}: {exc}")
    sys.exit("Neither probe cap is usable non-streaming. Stop and report.")


def thinking_tokens(usage):
    details = getattr(usage, "output_tokens_details", None)
    return getattr(details, "thinking_tokens", None)


def one_call(client, text, context, cap):
    full_prompt = build_prompt(text, retrieved_context=context)
    log = []  # one entry per failed attempt
    for attempt in (1, 2):
        start = time.perf_counter()
        try:
            resp = client.messages.create(
                model=settings.anthropic_model, max_tokens=cap,
                messages=[{"role": "user", "content": full_prompt}])
        except anthropic.APIConnectionError as exc:  # includes timeouts
            log.append({"cls": type(exc).__name__, "elapsed_ms": int((time.perf_counter() - start) * 1000),
                        "msg": str(exc)})
            if attempt == 1:
                time.sleep(RETRY_PAUSE_S)
                continue
            return {"error": True, "conn": True, "attempts": attempt, "log": log}
        except anthropic.APIStatusError as exc:  # 429, 5xx, 529 and other HTTP errors
            log.append({"cls": type(exc).__name__, "status": getattr(exc, "status_code", None),
                        "elapsed_ms": int((time.perf_counter() - start) * 1000), "msg": str(exc)})
            return {"error": True, "conn": False, "attempts": attempt, "log": log}
        except Exception as exc:  # noqa: BLE001
            log.append({"cls": type(exc).__name__, "elapsed_ms": int((time.perf_counter() - start) * 1000),
                        "msg": str(exc)})
            return {"error": True, "conn": False, "attempts": attempt, "log": log}
        ms = int((time.perf_counter() - start) * 1000)
        text_out = "".join(b.text for b in resp.content if b.type == "text")
        return {
            "error": False, "conn": False, "attempts": attempt, "log": log, "stop": resp.stop_reason,
            "in": resp.usage.input_tokens, "out": resp.usage.output_tokens,
            "think": thinking_tokens(resp.usage), "chars": len(text_out),
            "blocks": [b.type for b in resp.content], "ms": ms,
        }
    return {"error": True, "conn": True, "attempts": 2, "log": log}


def collect(client, context, cap):
    rows = []
    consecutive = 0
    for pid, n in CALL_PLAN:
        item = PROMPTS_BY_ID[pid]
        for run in range(1, n + 1):
            r = one_call(client, item["prompt"], context, cap)
            r.update({"id": pid, "run": run})
            rows.append(r)
            if r["error"]:
                detail = "; ".join(
                    f"{e['cls']}{' status=' + str(e['status']) if e.get('status') else ''} after {e['elapsed_ms']} ms"
                    for e in r["log"])
                print(f"{pid:<18} run{run}  NON-COMPLETION attempts={r['attempts']}: {detail}  "
                      f"msg={r['log'][-1]['msg'][:120]!r}", flush=True)
                consecutive = consecutive + 1 if r["conn"] else 0
            else:
                consecutive = 0
                print(f"{pid:<18} run{run}  stop={r['stop']:<10} in={r['in']:<5} "
                      f"out={r['out']:<6} think={r['think']!s:<6} chars={r['chars']:<6} "
                      f"blocks={'+'.join(r['blocks'])}  {r['ms']:>6} ms  attempts={r['attempts']}", flush=True)
            if consecutive >= ABORT_AFTER_CONSECUTIVE:
                print(f"\nABORT: {consecutive} consecutive connection errors.")
                return rows, True
    return rows, False


def summarize(rows, cap, aborted) -> None:
    done = [r for r in rows if not r["error"]]
    print(f"\n=== SUMMARY (cap {cap}, retrieval mode) ===")
    print(f"calls attempted {len(rows)}/{TOTAL_CALLS}; completed {len(done)} (need {MIN_COMPLETED}); aborted={aborted}")
    for pid, _ in CALL_PLAN:
        rs = [r for r in done if r["id"] == pid]
        if not rs:
            print(f"{pid:<18} NO COMPLETED CALLS")
            continue
        outs = [r["out"] for r in rs]
        print(f"{pid:<18} n={len(rs)} out min/max = {min(outs)}/{max(outs)}")
    if done:
        shares = [r["think"] / r["out"] for r in done if r["think"] is not None and r["out"]]
        empty = sum(1 for r in done if r["chars"] == 0)
        fit = sum(1 for r in done if r["out"] <= PROD_CAP_EXPECTED and r["stop"] != "max_tokens")
        print(f"(info) calls with empty text: {empty}; calls fitting under {PROD_CAP_EXPECTED}: {fit}/{len(done)}")
        if shares:
            print(f"(info) thinking share of output: median {statistics.median(shares):.0%}, max {max(shares):.0%}")

    d1_done = [r for r in done if r["id"] == "D1_motor_bracket"]
    each_ok = all(any(r["id"] == pid for r in done) for pid in ("D2_screw_jack", "D3_belt_drive", "D4_bending_brake"))
    if aborted or not d1_done or len(done) < MIN_COMPLETED or not each_ok:
        if aborted:
            why = "aborted after consecutive connection errors"
        elif not d1_done:
            why = "the D1 control did not complete"
        elif len(done) < MIN_COMPLETED:
            why = f"fewer than {MIN_COMPLETED} of {TOTAL_CALLS} completed"
        else:
            why = "one of D2, D3, D4 has no completed call"
        print(f"\nRESULT: INCOMPLETE — {why}. No cap derived.")
        return

    d1 = d1_done[0]
    control_ok = d1["stop"] == "end_turn" and d1["out"] <= PROD_CAP_EXPECTED
    print(f"\nCONTROL (D1, single call): {'PASSED' if control_ok else 'FAILED'} — "
          f"stop={d1['stop']}, out={d1['out']}, think={d1['think']}, chars={d1['chars']}")
    if not control_ok:
        print("RESULT: CONTROL FAILED — a prompt that fitted under 4096 changed behavior at the higher cap. "
              "D1 numbers are above. No cap derived; the Project Lead decides.")
        return

    stops = [r for r in done if r["stop"] == "max_tokens"]
    if stops:
        print(f"RESULT (R1): {len(stops)} call(s) still stopped on max_tokens at {cap}. "
              "No cap derived; escalate to a thinking-control decision.")
        return

    t_max = max(r["out"] for r in done)
    candidate = math.ceil(t_max * MARGIN / 1024) * 1024
    print(f"RESULT (R2): T_max = {t_max} output tokens; candidate production cap = {candidate} "
          f"(T_max x {MARGIN}, rounded up to a multiple of 1024).")
    if candidate > cap:
        print(f"UNTESTED: candidate {candidate} is above the probe cap {cap}. It does not ship untested; "
              f"a new probe at or above {candidate} is required.")
        return

    per_tok = statistics.median(r["ms"] / r["out"] for r in done if r["out"])
    est_s = candidate * per_tok / 1000
    print(f"R3: median {per_tok:.1f} ms per output token; estimated worst case at the candidate cap = {est_s:.0f} s.")
    if est_s <= LATENCY_FLAG_S:
        print(f"R3 OK: at or below {LATENCY_FLAG_S} s. The candidate may be proposed.")
        return
    lower = int(LATENCY_FLAG_S * 1000 / per_tok // 1024 * 1024)
    print(f"R3 TRIPPED: above {LATENCY_FLAG_S} s. The raise does NOT ship as written.")
    if lower >= t_max:
        print(f"  Option A: a lower cap of {lower} (estimate at or under {LATENCY_FLAG_S} s), with visible failures. "
              f"Valid: it is at least T_max ({t_max}).")
    else:
        print(f"  Option A: INVALID. The largest cap that stays under {LATENCY_FLAG_S} s ({lower}) is below "
              f"T_max ({t_max}), so it would still cut off runs already observed.")
    print("  Option B: a streaming sprint.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", type=int, default=7)
    args = ap.parse_args()

    check_environment()
    context = build_context(args.project_id)
    lines = [ln for ln in context.splitlines() if ln.strip()]
    assert len(lines) == EXPECTED_CONTEXT_LINES, (
        f"project {args.project_id} context has {len(lines)} lines, expected {EXPECTED_CONTEXT_LINES}")
    print(f"=== INJECTED CONTEXT (project {args.project_id}) ===")
    print(context)
    print("=====================================")
    print(f"call plan: {', '.join(f'{pid} x{n}' for pid, n in CALL_PLAN)}  ({TOTAL_CALLS} calls)\n")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, max_retries=0)
    cap = pick_cap(client)
    print(f"\nPROBE CAP IN USE: {cap}\n")

    rows, aborted = collect(client, context, cap)
    summarize(rows, cap, aborted)


if __name__ == "__main__":
    main()

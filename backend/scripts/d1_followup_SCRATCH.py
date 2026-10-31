"""
SCRATCH — Sprint 9 D1 follow-up. Not production code; changes nothing in
app/. Anthropic only (xKiro measures a different model and is out of scope).

STATUS: APPROVED by the Project Lead on condition of the amendment below
(applied). Do not edit after seeing results.

WHY: probe v3's D1 control failed. D1 used 4,647 output tokens at a
16,000 cap, after six earlier runs at a 4,096 cap that ended between 1,719
and 2,792. Two explanations: (a) D1 simply varies, and it sometimes needs
more than 4,096; (b) output grows with the available budget (the model
uses the room it is given). This follow-up separates them.

SAMPLE: D1_motor_bracket only, retrieval mode (project 7 context), 6 calls,
interleaved so time drift cannot favor one cap:
  16000, 4096, 16000, 4096, 16000, 4096.
Everything else as production (one user message, no system prompt, no
temperature, no thinking or effort option, claude-sonnet-5); only
max_tokens differs between the two groups. max_retries=0; one script-side
retry after a connection error; abort after 3 consecutive connection
errors; 429/5xx/529 failures are non-completion, recorded, not retried.

COMPLETENESS: at least 2 of 3 calls complete at EACH cap. Otherwise
INCOMPLETE and no classification.

PASS RULE (written before any run). Let
  X = number of completed 16000-cap runs with output_tokens > 4096
  Y = number of completed 4096-cap runs with stop_reason == max_tokens
Classification, in this order (a statement about D1 ONLY; D1 cannot speak
for D2, D3 or D4):
  DRIFT-SUSPECTED   if Y >= 2.
      Two or more 4096-cap D1 runs truncated, although six earlier runs at
      the same cap ended between 1,719 and 2,792. The old numbers (Sprint 8
      evals, the first measurement, v3) are NOT trusted until the change is
      explained. Sizing is BLOCKED; the Project Lead decides.
  VARIANCE          if Y == 1.
      D1 itself sometimes needs more than 4096, so the control's premise
      was wrong, not the model's behavior. The D1 control no longer
      objects to sizing from the v3 numbers; the Project Lead picks the cap.
  BUDGET-SENSITIVE  if Y == 0 and X >= 2.
      D1 finishes inside 4096 when constrained but exceeds it when allowed,
      so its output grows with the cap. Sizing from the v3 numbers is
      BLOCKED; the Project Lead decides, and a thinking-control decision
      comes first. Proven for D1 only; a warning for D2-D4, not a finding.
  INCONCLUSIVE      if Y == 0 and X == 1.
      One high-cap run above 4096 cannot separate a tail event from budget
      growth. No conclusion; the Project Lead decides whether to sample
      more or proceed on judgment.
  OUTLIER           if Y == 0 and X == 0.
      No D1 run exceeded 4096 at either cap; the 4,647 was a tail event.
      The D1 control no longer objects to sizing from the v3 numbers; the
      Project Lead picks the cap.
In every outcome: D1 cannot clear or condemn D2-D4's own behavior at any
cap. The visible-failure change is not shipped alone at 4096. The 10,240
fallback cap is acceptable only together with the visible-failure change
in the same change, a real UI run at the new cap, and a forced-failure
check. A raised cap still needs the R3 latency check. If any 16000-cap run
stops on max_tokens, the script prints ANOMALY and the Project Lead decides.

Usage (from backend/, venv active):
  python scripts/d1_followup_SCRATCH.py
"""

import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: E402

from truncation_cap_probe_SCRATCH import (  # noqa: E402
    ABORT_AFTER_CONSECUTIVE,
    EXPECTED_CONTEXT_LINES,
    PROMPTS_BY_ID,
    build_context,
    check_environment,
    one_call,
    settings,
)

PROMPT_ID = "D1_motor_bracket"
HIGH_CAP = 16000
LOW_CAP = 4096
CAPS_IN_ORDER = (HIGH_CAP, LOW_CAP, HIGH_CAP, LOW_CAP, HIGH_CAP, LOW_CAP)
MIN_PER_CAP = 2
BUDGET_X = 2

assert PROMPT_ID in PROMPTS_BY_ID, "D1 prompt id drifted"
assert len(CAPS_IN_ORDER) == 6
assert CAPS_IN_ORDER.count(HIGH_CAP) == 3 and CAPS_IN_ORDER.count(LOW_CAP) == 3


def classify(rows) -> None:
    done = [r for r in rows if not r["error"]]
    hi = [r for r in done if r["cap"] == HIGH_CAP]
    lo = [r for r in done if r["cap"] == LOW_CAP]
    print("\n=== SUMMARY (D1, retrieval mode) ===")
    for label, group in (("16000 cap", hi), ("4096 cap", lo)):
        outs = [r["out"] for r in group]
        if outs:
            print(f"{label}: n={len(outs)} out={sorted(outs)} stops={sorted({r['stop'] for r in group})}")
        else:
            print(f"{label}: no completed calls")
        thinks = [r["think"] for r in group if r["think"] is not None]
        if thinks:
            print(f"   thinking tokens: {sorted(thinks)}; empty-text calls: {sum(1 for r in group if r['chars'] == 0)}")

    if len(hi) < MIN_PER_CAP or len(lo) < MIN_PER_CAP:
        print(f"\nRESULT: INCOMPLETE — need at least {MIN_PER_CAP} completed calls at each cap "
              f"(got {len(hi)} at {HIGH_CAP}, {len(lo)} at {LOW_CAP}). No classification.")
        return
    if any(r["stop"] == "max_tokens" for r in hi):
        print(f"\nANOMALY: a {HIGH_CAP}-cap run stopped on max_tokens. The Project Lead decides.")
        return

    x = sum(1 for r in hi if r["out"] > LOW_CAP)
    y = sum(1 for r in lo if r["stop"] == "max_tokens")
    print(f"\nX (16000-cap runs above 4096) = {x}; Y (4096-cap runs stopped on max_tokens) = {y}")
    if y >= 2:
        print("RESULT: DRIFT-SUSPECTED — two or more 4096-cap D1 runs truncated, though six earlier runs at the "
              "same cap ended between 1,719 and 2,792. The old numbers are NOT trusted until explained. "
              "Sizing is BLOCKED; the Project Lead decides.")
    elif y == 1:
        print("RESULT: VARIANCE — D1 sometimes needs more than 4096. The D1 control no longer objects to sizing "
              "from the v3 numbers; the Project Lead picks the cap.")
    elif x >= BUDGET_X:
        print("RESULT: BUDGET-SENSITIVE — D1 output grows with the cap. Sizing from the v3 numbers is BLOCKED; "
              "the Project Lead decides, thinking-control decision first. Proven for D1 only.")
    elif x == 1:
        print("RESULT: INCONCLUSIVE — one high-cap run above 4096 cannot separate a tail event from budget "
              "growth. The Project Lead decides whether to sample more or proceed on judgment.")
    else:
        print("RESULT: OUTLIER — no D1 run exceeded 4096 at either cap; the 4,647 was a tail event. The D1 "
              "control no longer objects to sizing from the v3 numbers; the Project Lead picks the cap.")
    print("Note: this classifies D1 only; it cannot speak for D2, D3 or D4.")


def main() -> None:
    check_environment()
    context = build_context(7)
    lines = [ln for ln in context.splitlines() if ln.strip()]
    assert len(lines) == EXPECTED_CONTEXT_LINES, f"context has {len(lines)} lines"
    print(f"model={settings.anthropic_model}; caps in order: {list(CAPS_IN_ORDER)}\n")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, max_retries=0)
    prompt = PROMPTS_BY_ID[PROMPT_ID]["prompt"]
    rows, consecutive = [], 0
    for i, cap in enumerate(CAPS_IN_ORDER, start=1):
        r = one_call(client, prompt, context, cap)
        r.update({"cap": cap, "i": i})
        rows.append(r)
        if r["error"]:
            detail = "; ".join(
                f"{e['cls']}{' status=' + str(e['status']) if e.get('status') else ''} after {e['elapsed_ms']} ms"
                for e in r["log"])
            print(f"call {i} cap={cap:<6} NON-COMPLETION attempts={r['attempts']}: {detail}", flush=True)
            consecutive = consecutive + 1 if r["conn"] else 0
        else:
            consecutive = 0
            print(f"call {i} cap={cap:<6} stop={r['stop']:<10} in={r['in']:<5} out={r['out']:<6} "
                  f"think={r['think']!s:<6} chars={r['chars']:<6} {r['ms']:>6} ms", flush=True)
        if consecutive >= ABORT_AFTER_CONSECUTIVE:
            print(f"\nABORT: {consecutive} consecutive connection errors.")
            break
    classify(rows)


if __name__ == "__main__":
    main()

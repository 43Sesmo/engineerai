"""
SCRATCH — Sprint 9 forced-failure check. Not production code; lives outside
app/ and edits nothing in it (no production edit means nothing to restore).

Provider mode (V2): runs the REAL send_prompt from anthropic_provider.py
against (a) fake responses, free, covering a max_tokens stop, empty text,
whitespace-only text, a normal reply, and the near-miss threshold; and
(b) one real call whose max_tokens is forced very low by a scratch-side
client proxy (default 16; use --cap 256 if the API rejects 16).

  python scripts/forced_failure_check_SCRATCH.py provider
  python scripts/forced_failure_check_SCRATCH.py provider --cap 256
  python scripts/forced_failure_check_SCRATCH.py provider --skip-real

Serve mode (V3, V4): a backend on port 8001 in which EVERY Anthropic call is
capped at FORCED_CAP tokens (default 16). Started with python -m (no .exe
launcher), from backend/:

  python -m uvicorn forced_failure_check_SCRATCH:make_app --factory --app-dir scripts --port 8001

To use 256 instead: set FORCED_CAP=256 first, in the same shell.
Messages sent to this backend are written to the real database; use a
throwaway conversation in project 7 and never save the replies to the Vault.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: E402

from app.ai.errors import AIProviderError  # noqa: E402
from app.ai.providers import anthropic_provider as prov  # noqa: E402
from app.core.config import settings  # noqa: E402

_RealAnthropic = anthropic.Anthropic  # captured before any patching


# Requests the provider built, recorded so each case can check what it carried.
SEEN = []

EXPECTED_KEYS = {"model", "max_tokens", "messages", "output_config"}


def request_problems():
    """Problems with the LAST request the provider built (empty list = it carried what it should)."""
    if not SEEN:
        return ["no request was recorded"]
    req = SEEN[-1]
    out = []
    if set(req) != EXPECTED_KEYS:
        out.append(f"request keys {sorted(req)}, expected {sorted(EXPECTED_KEYS)}")
    if req.get("output_config") != {"effort": "medium"}:
        out.append(f"output_config is {req.get('output_config')!r}, expected {{'effort': 'medium'}}")
    if req.get("max_tokens") != prov.MAX_OUTPUT_TOKENS:
        out.append(f"max_tokens is {req.get('max_tokens')!r}, expected {prov.MAX_OUTPUT_TOKENS}")
    return out


# --- scratch-side client proxy: forces a very low cap, nothing else ---------

class _CapMessages:
    def __init__(self, inner, cap):
        self._inner, self._cap = inner, cap

    def create(self, **kwargs):
        SEEN.append(dict(kwargs))  # what the provider built, before the cap is forced
        kwargs["max_tokens"] = self._cap
        return self._inner.create(**kwargs)


class _CapClient:
    def __init__(self, real, cap):
        self.messages = _CapMessages(real.messages, cap)


def low_cap_factory(cap):
    def factory(*args, **kwargs):
        return _CapClient(_RealAnthropic(*args, **kwargs), cap)
    return factory


# --- fakes ------------------------------------------------------------------

def fake_response(*, text, stop, out_tokens, thinking=0, with_thinking_block=True):
    content = []
    if with_thinking_block:
        content.append(SimpleNamespace(type="thinking"))
    if text is not None:
        content.append(SimpleNamespace(type="text", text=text))
    usage = SimpleNamespace(
        output_tokens=out_tokens,
        output_tokens_details=SimpleNamespace(thinking_tokens=thinking),
    )
    return SimpleNamespace(content=content, stop_reason=stop, usage=usage)


def fake_factory(response):
    class _Msgs:
        def create(self, **kwargs):
            SEEN.append(dict(kwargs))
            return response

    class _Client:
        def __init__(self, *args, **kwargs):
            self.messages = _Msgs()

    return _Client


class _LogCapture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def run_case(name, response, *, expect_error=None, expect_text=None,
             expect_log=(), forbid_in_message=(), expect_no_log=False):
    """Run send_prompt against a fake response and check the outcome."""
    SEEN.clear()  # so a case that makes no request cannot pass on an earlier case's request
    capture = _LogCapture()
    prov.logger.addHandler(capture)
    old_level = prov.logger.level
    prov.logger.setLevel(logging.WARNING)
    outcome, message, returned = "returned", "", None
    saved = prov.anthropic.Anthropic
    prov.anthropic.Anthropic = fake_factory(response)
    try:
        returned = prov.send_prompt("test prompt")
    except AIProviderError as exc:
        outcome, message = "raised", str(exc)
    finally:
        prov.anthropic.Anthropic = saved
        prov.logger.removeHandler(capture)
        prov.logger.setLevel(old_level)

    problems = request_problems()
    if expect_error is not None:
        if outcome != "raised":
            problems.append("expected AIProviderError, got a return value")
        elif not message.startswith(expect_error):
            problems.append(f"message does not start with {expect_error!r}: {message!r}")
        for banned in forbid_in_message:
            if banned in message:
                problems.append(f"user-facing message must not contain {banned!r}")
    if expect_text is not None:
        if outcome != "returned":
            problems.append(f"expected text back, got an error: {message!r}")
        elif returned != expect_text:
            problems.append(f"text changed: {returned!r}")
    joined = " | ".join(capture.lines)
    for needle in expect_log:
        if needle not in joined:
            problems.append(f"log is missing {needle!r}")
    if expect_no_log and capture.lines:
        problems.append(f"expected no warning, got: {joined}")

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] {name}")
    if message:
        print(f"        user-facing message: {message}")
    for line in capture.lines:
        print(f"        LOG: {line}")
    for p in problems:
        print(f"        PROBLEM: {p}")
    return not problems


def fake_cases():
    ok = True
    ok &= run_case(
        "fake: stop at max_tokens (10,240 tokens, 9,800 thinking)",
        fake_response(text='{"partial": ', stop="max_tokens", out_tokens=10240, thinking=9800),
        expect_error="The model used its whole output budget",
        expect_log=("truncated at max_tokens", "thinking_tokens=9800", "blocks=['thinking', 'text']"),
    )
    ok &= run_case(
        "fake: no text block at all, normal stop",
        fake_response(text=None, stop="end_turn", out_tokens=500, thinking=500),
        expect_error="The model returned no text. Try again.",
        forbid_in_message=("end_turn", "stop reason", "stop_reason"),
        expect_log=("returned no text", "stop_reason=end_turn"),
    )
    ok &= run_case(
        "fake: whitespace-only text, normal stop",
        fake_response(text="  \n ", stop="end_turn", out_tokens=300, thinking=250),
        expect_error="The model returned no text. Try again.",
        forbid_in_message=("end_turn", "stop reason", "stop_reason"),
        expect_log=("returned no text",),
    )
    ok &= run_case(
        "fake: normal reply (1,200 tokens) is returned unchanged, no warning",
        fake_response(text="hello", stop="end_turn", out_tokens=1200, thinking=700),
        expect_text="hello",
        expect_no_log=True,
    )
    ok &= run_case(
        "fake: near miss (9,000 tokens) warns and still returns the text",
        fake_response(text="ok", stop="end_turn", out_tokens=9000, thinking=6500),
        expect_text="ok",
        expect_log=("near miss", "9000"),
    )
    ok &= run_case(
        "fake: exactly 8,192 tokens warns",
        fake_response(text="ok", stop="end_turn", out_tokens=8192, thinking=5000),
        expect_text="ok",
        expect_log=("near miss",),
    )
    ok &= run_case(
        "fake: 8,191 tokens does not warn",
        fake_response(text="ok", stop="end_turn", out_tokens=8191, thinking=5000),
        expect_text="ok",
        expect_no_log=True,
    )
    return ok


def real_forced_case(cap):
    """One real call, max_tokens forced to `cap` by the scratch-side proxy."""
    SEEN.clear()
    capture = _LogCapture()
    prov.logger.addHandler(capture)
    old_level = prov.logger.level
    prov.logger.setLevel(logging.WARNING)
    saved = prov.anthropic.Anthropic
    prov.anthropic.Anthropic = low_cap_factory(cap)
    outcome, message = "returned", ""
    try:
        prov.send_prompt("Write a 300-word explanation of how to size a solid circular shaft for torsion.")
    except AIProviderError as exc:
        outcome, message = "raised", str(exc)
    finally:
        prov.anthropic.Anthropic = saved
        prov.logger.removeHandler(capture)
        prov.logger.setLevel(old_level)

    print(f"\nreal forced call (max_tokens forced to {cap}):")
    req_problems = request_problems()
    print(f"        request the provider built: keys {sorted(SEEN[-1]) if SEEN else '(none)'}; "
          f"output_config {SEEN[-1].get('output_config') if SEEN else '(none)'}")
    if req_problems:
        for p in req_problems:
            print(f"        PROBLEM: {p}")
        print("[FAIL] the request did not carry what it should")
        return False
    for line in capture.lines:
        print(f"        LOG: {line}")
    if outcome == "returned":
        print(f"[FAIL] the call returned text, so the cap did not force a failure at {cap}")
        return False
    print(f"        user-facing message: {message}")
    if "returned an error" in message:
        print(f"[NEEDS-RERUN] the API rejected a cap of {cap}. Rerun with --cap 256.")
        return False
    if message.startswith("The model used its whole output budget"):
        print("[PASS] real response stopped at the forced cap and raised the visible failure")
        return True
    if message == "The model returned no text. Try again.":
        print("[PASS] real response carried no text and raised the visible failure "
              "(the max_tokens branch is covered by the fake case above)")
        return True
    print("[FAIL] unexpected message")
    return False


def make_app():
    """ASGI app factory for serve mode: every Anthropic call is capped at FORCED_CAP."""
    cap = int(os.environ.get("FORCED_CAP", "16"))
    prov.anthropic.Anthropic = low_cap_factory(cap)  # process-wide, on purpose
    logging.basicConfig(level=logging.WARNING)
    print(f"*** FORCED-FAILURE BACKEND: every Anthropic call is capped at {cap} tokens ***", flush=True)
    from app.main import app
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["provider"])
    ap.add_argument("--cap", type=int, default=16)
    ap.add_argument("--skip-real", action="store_true")
    args = ap.parse_args()

    if not settings.anthropic_api_key:
        sys.exit("ANTHROPIC_API_KEY is not configured.")
    print(f"model={settings.anthropic_model}; provider MAX_OUTPUT_TOKENS={prov.MAX_OUTPUT_TOKENS}; "
          f"NEAR_MISS_TOKENS={prov.NEAR_MISS_TOKENS}\n")

    ok = fake_cases()
    if not args.skip_real:
        ok &= real_forced_case(args.cap)
    print("\nALL PASSED" if ok else "\nSOMETHING DID NOT PASS — see above")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

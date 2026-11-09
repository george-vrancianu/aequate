PROTOTYPE (throwaway, issue #31): do not build on this code. Answer = RESULTS.md (when phase C is done).

# Hint model bake-off

Question: which local model should be the default hint phraser? Runs every model through the same contract the product will use
(ADR 0005 / #48): OpenAI-compatible `/v1/chat/completions`, one English system prompt (`PROMPT_VERSION` v1) with output language
from the locale, the rung's CAS facts as JSON (never the next step or the answer), JSON `{hint, math[]}` via `response_format`,
temperature 0, thinking off, 20 s budget over both attempts, deterministic leak check (`LEAK_CHECK_VERSION` v1), one retry if at
least 5 s are left, template fallback. Rungs 1-3 only: rung 4 is the CAS's next step shown as math and never comes from the LLM (ADR 0001).

Design notes live in the ticket; the step set has 13 items (see `steps_bakeoff.py`), sources cited per item.

## Files

- `steps_bakeoff.py` steps, hidden next step/answer, `payload()`, hand-written en/ro templates.
- `verify_steps.py` SymPy check of every hidden next step and answer.
- `leakcheck.py`, `test_leakcheck.py` the gate and its fixtures. `parsing.py` copied from `prototypes/cas-equivalence` (origin/prototype/cas-equivalence).
- `bakeoff.py` the harness. `report.py` results/*.jsonl -> markdown tables.

## Run

```
cd prototypes/hint-model-bakeoff
uv sync
uv run python verify_steps.py          # must print PASS
uv run pytest -q test_leakcheck.py     # must pass

# against any OpenAI-compatible server (llama-server, vLLM, ...). Qwen3.5 needs thinking off via chat_template_kwargs:
uv run python bakeoff.py --base-url http://127.0.0.1:8080 --model qwen3.5-4b --label q35-4b-cpu \
    --locales en,ro --rungs 1,2,3 --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}'
# --steps lin2,quad   only these steps      --limit 6   six combinations spread over the full list
uv run python report.py                # all results/*.jsonl; paste into RESULTS.md
```

Phase A (this commit) was smoke-tested on CPU with `llama-server` (see below); no GPU/Modal runs yet.

## Local CPU server (phase A smoke test, and the 4B CPU measurement)

```
# llama.cpp prebuilt CPU release (Linux x64) and the ungated GGUF are NOT in git:
gh release download b12211 -R ggml-org/llama.cpp -p 'llama-b12211-bin-ubuntu-x64.tar.gz' -D /tmp/aq-31-llama/bin
curl -L -o /tmp/aq-31-llama/models/Qwen3.5-4B-Q4_K_M.gguf https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf
/tmp/aq-31-llama/bin/llama-b12211/llama-server -m /tmp/aq-31-llama/models/Qwen3.5-4B-Q4_K_M.gguf --host 127.0.0.1 --port 8089 \
    --jinja -t 16 -c 4096 --parallel 1 --alias qwen3.5-4b
```

## Deviations from the design

- Forbidden numbers exclude 0 and 1 from the next step (too common in "= 0"), unless they are an answer value.
- Bare relations in prose ("so x=2.", "x = y/2 - 3/2.") are also parsed as formulas (models often skip the `$`).
- Numbers are compared by absolute value, so -3 and 3 are the same number. "2,3" is read both as a decimal and as a list.
- Step indices and the equation numbers of a system ("equation 2") are allowed numbers.
- Formula operands are parsed separately and compared as (op, lhs, rhs), because SymPy auto-evaluates `Eq(a, a)` to True. Atoms that
  equal a parsed student step are dropped from the hidden set (SymPy auto-evaluates `3(x-2)` to `3x-6`, so brack, frac and dec would
  otherwise reject the current step); those items rely on the number rule. Each side of a relation is compared to an expression-typed
  hidden step (dom item), and to non-trivial hidden sides and a moved-terms form of the next step (`x^2-2x=3` for `x^2-2x-3=0`).
  A bare number, symbol or `c*x` side is too trivial to match, because `(x+y)+(x-y)` auto-evaluates to `2x`.
- Known gate limit: a hint stating `x^2-1=(x-1)(x+1)` for the dom item is not flagged. Catching it needs `sympy.evaluate(False)`, which
  does not work through the parsing.py pipeline (ValueError). Count it in the human review.
- The gate-miss audit also covers answer values written as words, "x is N" and "the solutions are". Number words that the payload uses
  itself or that count a noun ("the two equations") are skipped.
- The frac item is `x/2+x/3=10` (answer 12) so that naming the common denominator 6 in rung 3 is not a leak.
- Rung 1 payload for the one-way items puts the "check for extra solutions" note in goal_status (as design.md says).
- The 20 s budget is enforced via the httpx timeout = remaining budget; that is a per-read timeout, so an attempt can end a little
  after 20 s. A valid reply that arrives after the budget counts as template (cause "over budget" in the report).
- The warm-up request uses an item that is not measured (`WARMUP_ITEM`), so caching cannot speed up the first measured hint.

## Report metrics (`report.py`)

leak a1 = leaking / valid attempt-1 replies (timeouts, request errors and invalid JSON are counted next to it). leak a2 = of the hints
whose attempt 1 leaked and whose attempt 2 ran, the share where attempt 2 leaked again; residual = of the hints whose attempt 1 leaked,
the share that ended on the template. Fallback causes (timeout, request error, no time to retry, over budget, rejected twice) add up to
the template count. Request errors are not JSON-validity failures. "attempts with reasoning" must be 0 (thinking really off). p95 over
fewer than 30 hints is the maximum, so it is shown as max; read p95 on the per-language and overall rows (n = 39 / 78).

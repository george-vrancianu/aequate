PROTOTYPE (throwaway, issue #31): do not build on this code. Answer = RESULTS.md (provisional recommendation until the human ratings in rating/ are in).

# Hint model bake-off

Question: which local model should be the default hint phraser? Runs every model through the same contract the product will use
(ADR 0005 / #48): OpenAI-compatible `/v1/chat/completions`, one English system prompt (`PROMPT_VERSION` v1) with output language
from the locale, the rung's CAS facts as JSON (never the next step or the answer), JSON `{hint, math[]}` via `response_format`,
temperature 0, thinking off, 20 s budget over both attempts, deterministic leak check (`LEAK_CHECK_VERSION` v4), one retry if at
least 5 s are left, template fallback. Rungs 1-3 only: rung 4 is the CAS's next step shown as math and never comes from the LLM (ADR 0001).

Design notes live in the ticket; the step set has 13 items (see `steps_bakeoff.py`), sources cited per item.

## Files

- `steps_bakeoff.py` steps, hidden next step/answer, `payload()`, hand-written en/ro templates.
- `verify_steps.py` SymPy check of every hidden next step and answer.
- `leakcheck.py`, `test_leakcheck.py` the gate and its fixtures. `parsing.py` copied from `prototypes/cas-equivalence` (origin/prototype/cas-equivalence).
- `serve_modal.py` (vLLM on Modal), `serve_llamacpp_modal.py` (llama.cpp on Modal, Gemma Q4), `make_rating.py` (blind rating sheet).
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

Phase A was smoke-tested on CPU with `llama-server` (see below). Phase B (GPU on Modal, CPU full run, results, rating sheet) is below.

## Phase B: GPU runs on Modal, one app per model (vLLM on an L4, `serve_modal.py`)

```
# needs `modal` authenticated; AQ_MODEL = HF repo, AQ_APP = app name, AQ_EXTRA = extra `vllm serve` flags
AQ_MODEL=Qwen/Qwen3.5-4B AQ_APP=aq31-qwen35-4b modal deploy serve_modal.py
# URL printed by deploy: https://<workspace>--aq31-qwen35-4b-serve.us-east.modal.run (first request cold-starts the container, several minutes)
uv run python bakeoff.py --base-url $URL --model m --label gpu-l4-qwen35-4b \
    --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}'
modal app stop -y aq31-qwen35-4b        # always; then `modal app list` must show nothing running
```
Per model (AQ_MODEL / AQ_EXTRA; the harness `--extra-body` only for Qwen3.5):
- Qwen3.5-9B: `Qwen/Qwen3.5-9B`, `--limit-mm-per-prompt {"image":0,"video":0} --max-num-seqs 4 --max-num-batched-tokens 2048`
- Gemma 4 E4B: `google/gemma-4-E4B-it`, `--limit-mm-per-prompt {"image":0,"audio":0,"video":0} --max-num-seqs 4 --max-num-batched-tokens 2048`
- Ministral 3 8B: `mistralai/Ministral-3-8B-Instruct-2512-BF16`, `--tokenizer-mode mistral --config-format mistral --load-format mistral --limit-mm-per-prompt {"image":0} --max-num-seqs 4 --max-num-batched-tokens 2048`
- EuroLLM: `utter-project/EuroLLM-9B-Instruct-2512`, `--max-num-seqs 4 --max-num-batched-tokens 2048`

CPU run: start the llama-server from "Local CPU server" below, then
`uv run python bakeoff.py --base-url http://127.0.0.1:8089 --model qwen3.5-4b --label cpu-q35-4b-q4km --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}'`
and stop it by PID (`ps` for the real server PID).

## Round 4: Gemma 4 E4B at Q4 (what would ship), llama.cpp on Modal L4 and on the local CPU

```
# GGUF (official QAT q4_0, ungated, 4.8 GiB); keep it on disk, not on the tmpfs /tmp
curl -L -o ~/aq-31-models/gemma-4-E4B_q4_0-it.gguf https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-gguf/resolve/main/gemma-4-E4B_q4_0-it.gguf
# GPU: llama.cpp CUDA image (b12211) on an L4; the GGUF is downloaded into the volume by the container
modal deploy serve_llamacpp_modal.py        # app aq31-gemma4-e4b-q4-llamacpp
uv run python bakeoff.py --base-url $URL --model m --label gpu-l4-gemma4-e4b-q4-llamacpp \
    --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}'     # REQUIRED: Gemma 4 thinks by default under llama-server --jinja
modal app stop -y aq31-gemma4-e4b-q4-llamacpp
# CPU: same flags as the Qwen run
/tmp/aq-31-llama/bin/llama-b12211/llama-server -m ~/aq-31-models/gemma-4-E4B_q4_0-it.gguf --host 127.0.0.1 --port 8089 --jinja -t 16 -c 4096 --parallel 1 --alias gemma4-e4b-q4
uv run python bakeoff.py --base-url http://127.0.0.1:8089 --model gemma4-e4b-q4 --label cpu-gemma4-e4b-q4 --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}'
```

Tables and rating sheet:
```
uv run python report.py results/gpu-*.jsonl results/cpu-*.jsonl > results/report.md   # RESULTS.md embeds these (minus per-step tables)
uv run python make_rating.py            # rating/RATING.md, ratings.csv (blank), key.csv (do not open before rating); fixed seed 31
# make_rating.py shows every option as plain hint text (no math chips, no $ or backticks), adds the Gemma Q4 GPU run as an extra
# hidden source, and exits non-zero if a structural feature (code spans, $, question mark, sentence count) is unique to the template in more than 8 groups.
# Residual it only reports: the template is the shortest option in 36 of 51 groups.
# Also recognisable: the rung-1 template uses a fixed opener ("Scopul este" / "The goal"), so it reads as a recurring source in rung-1 groups.
```

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
- The frac item is `x/2+x/3=10` (answer 12) so that naming the common denominator 6 in rung 3 is not a leak. Its rung-3 operation is
  "add the two fractions over the common denominator 6", so carrying it out gives the hidden `5x/6=10`. A hint that only writes
  `3x/6+2x/6=10` is a partial step that the gate does not flag (SymPy evaluates it to the current step): a rung-adherence issue for the human rating, not a gate leak.
- Formulas written without `$` are checked too: besides `x = ...` relations, maximal runs of formula characters in the prose that contain
  one of the item's variable letters and an operator (`Expand to get x^2 - 2x - 3 = 0.`, `It simplifies to x + 1.`) are parsed; a run that does not parse is skipped silently.
  `x²` is read as `x^2`, `\boxed{..}`, `\text{..}` and `\mathrm{..}` (also `\mathbf`, `\mathit`, `\bm`) are unwrapped, one outer `$..$`, `\(..\)` and `\displaystyle` are stripped, `\Rightarrow`/`\implies`/`\iff`/`\to` chains are split, bare relations are also searched inside every math[] entry and span, and `x \in \{a, b\}` is read as `x=a \lor x=b`.
- Hidden `extraneous` field (log: -1, sqrt: 0): the extraneous roots of the one-way items are guarded like answer values in the
  "var op value" rule (not in the gate-miss audit). Never sent to the model.
- A request error (HTTP 4xx/5xx, connection error) ends the hint on the template with no retry, like a timeout.
- Rung 1 payload for the one-way items puts the "check for extra solutions" note in goal_status (as design.md says).
- The 20 s budget is enforced via the httpx timeout = remaining budget; that is a per-read timeout, so an attempt can end a little
  after 20 s. A valid reply that arrives after the budget counts as template (cause "over budget" in the report).
- The warm-up request uses an item that is not measured (`WARMUP_ITEM`), so caching cannot speed up the first measured hint.

## Report metrics (`report.py`)

leak a1 = leaking / valid attempt-1 replies (timeouts, request errors and invalid JSON are counted next to it). leak a2 = of the hints
whose attempt 1 leaked and whose attempt 2 returned a valid reply, the share where attempt 2 leaked again (attempt-2 timeouts / request errors / invalid replies are listed beside it); residual = of the hints whose attempt 1 leaked,
the share that ended on the template. Fallback causes (timeout, request error, no time to retry, over budget, rejected twice) add up to
the template count. Request errors are not JSON-validity failures. "attempts with reasoning" must be 0 (thinking really off). p95 over
fewer than 30 hints is the maximum, so it is shown as max; read p95 on the per-language and overall rows (n = 39 / 78).

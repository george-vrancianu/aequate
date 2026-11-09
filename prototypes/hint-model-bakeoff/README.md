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

## Deviations from the design (so far)

- Forbidden numbers exclude 0 and 1 from the next step (too common in "= 0"), unless they are an answer value.
- Bare relations in prose ("so x=2.") are also parsed as formulas (models often skip the `$`).
- Numbers are compared by absolute value, so -3 and 3 are the same number.

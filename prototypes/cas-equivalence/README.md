# PROTOTYPE (throwaway): CAS equivalence spike, issue #14

Answers: which SymPy equivalence strategy gets 20 typical algebra steps right, how long it takes under a hard timeout, and where strategies disagree. Not production code. Do not import from it.

Run (from this directory; needs `uv`, which fetches Python 3.12, SymPy 1.14.0, antlr4 4.11, Lark 1.3.1):

    uv run python run.py                 # default 2 s timeout per strategy call
    uv run python run.py --timeout 0.5   # or CAS_TIMEOUT=0.5

Writes `RESULTS.md` (tables generated from the run, plus the hand-written `analysis.md` appended) and `results.json` (named after `--out`). Takes about 15 s. Linux/macOS only (uses `fork`).

Files: `steps.py` (20 labelled steps), `parsing.py` (normalizer and guards copied verbatim from the parser research appendix), `rawparse.py` (small wrapper: same parse with `sympy.evaluate(False)`, a deliberate deviation so S0u and S7 see the unevaluated tree), `strategies.py` (S0-S7), `run.py` (isolated killable workers, tables).
No `sympify`/`eval`/`parse_expr` on any input string; input goes through `parse_latex(strict=True)`.

## Issue #40: harder step set and the timeout-budget sweep

Additive; `run.py`, `steps.py`, `strategies.py`, `RESULTS.md` are untouched. Needs the same `uv` environment.

    uv run python sweep.py run                         # 4 budgets (2 s, 500, 200, 100 ms) x 3 reps x all strategies x 20 + 35 steps, <= 4 worker processes; about 2-4 min
    uv run python sweep.py run --quick --budgets 2,0.5 # smoke test on 10 steps, 1 rep (writes results-hard.json too)
    uv run python sweep.py run --workers 1 --budgets 0.5 --out /tmp/serial.json   # serial comparison, does not overwrite results-hard.json
    uv run python sweep.py report                      # results-hard.json (+ analysis-hard.md) -> RESULTS-hard.md

Files: `steps_hard.py` (35 hand-labelled hard steps H1..H35, including 3 parse probes), `hardlib.py` (prototype-only adapters: inequalities, systems, the end-to-end stack), `sweep.py` (killable-worker sweep, fork floor, warm-worker datapoint), `sweep_report.py` (tables), `analysis-hard.md` (hand-written recommendation, appended to the report), `results-hard.json` (raw rows). Results and recommendation: `RESULTS-hard.md`.

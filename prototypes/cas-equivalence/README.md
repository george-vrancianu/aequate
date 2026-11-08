# PROTOTYPE (throwaway): CAS equivalence spike, issue #14

Answers: which SymPy equivalence strategy gets 20 typical algebra steps right, how long it takes under a hard timeout, and where strategies disagree. Not production code. Do not import from it.

Run (from this directory; needs `uv`, which fetches Python 3.12, SymPy 1.14.0, antlr4 4.11, Lark 1.3.1):

    uv run python run.py                 # default 2 s timeout per strategy call
    uv run python run.py --timeout 0.5   # or CAS_TIMEOUT=0.5

Writes `RESULTS.md` (tables generated from the run, plus the hand-written `analysis.md` appended) and `results.json` (named after `--out`). Takes about 15 s. Linux/macOS only (uses `fork`).

Files: `steps.py` (20 labelled steps), `parsing.py` (normalizer and guards copied verbatim from the parser research appendix), `rawparse.py` (small wrapper: same parse with `sympy.evaluate(False)`, a deliberate deviation so S0u and S7 see the unevaluated tree), `strategies.py` (S0-S7), `run.py` (isolated killable workers, tables).
No `sympify`/`eval`/`parse_expr` on any input string; input goes through `parse_latex(strict=True)`.

# CAS spike: SymPy equivalence on 20 typical algebra steps

Prototype for [#14](https://github.com/george-vrancianu/aequate/issues/14), part of the map in #1. Built on the research in `docs/research/sympy-equivalence.md` (#5). Feeds the equivalence-semantics decision in #15.

Throwaway code. It answers one question: which strategy gives the right verdict on each step, how long it takes under a hard timeout, and where the strategies disagree.

## What was run

- **Steps.** 20 hand-labelled core steps (`steps.py`): expansion, factoring, fractions, the `(x²−1)/(x−1)` trap, linear and quadratic equations, rearranging formulas, squaring both sides, inequalities, and one hard trig identity. There are also 4 edge cases (reorder only, `√(x²)`, floats, a log rule) and 4 physics steps with declared units. Each step has a relation label (`equiv`, `not_equiv`, `domain_changed`, `implies`, `lost_roots`, `same_roots`, `conditional`) and the tick a tutor would want to see.
- **Tentative tick policy, used only for labelling.** Real domain. A valid step that is not an equivalence is amber. An error is red. The real policy is for #15 to decide.
- **Strategies.** S0–S8 exactly as recommended in the research doc (`strategies.py`), plus `PIPELINE`, the combination this spike proposes. S6 is not a separate function: it is the complex (C), real (R) and positive (P) variants of S1, S2, S4 and S5.
- **Parsing.** Input goes only through SymPy's LaTeX parser (`parse_latex`, ANTLR backend), never `sympify` on strings.
- **Timeouts.** Every (step, strategy) check runs in a forked worker that is killed at 200 ms and, separately, at 1 s. A kill maps to amber.
- **Environment.** SymPy 1.14.0, Pint 0.26.1, mpmath 1.3.0, Python 3.13, a 2 vCPU cloud container. The packages came from their official GitHub release tags because PyPI was not reachable.
- **Stability.** Two full runs produced identical verdicts. Timings in this README come from the last run; maxima moved by up to about 30% between runs.

Full tables are in [`results/results.md`](results/results.md). Raw data with every verdict, detail and timing is in `results/results.json`.

```
pip install sympy==1.14.0 pint==0.26.1 antlr4-python3-runtime==4.11.1
python -I run.py && python -I report.py
```

## Results at a glance

| Strategy | Right (of applicable) | Dangerous¹ | Median / max ms | Timeouts at 200 ms |
|---|---|---|---|---|
| S1 `simplify(a−b)==0` | 17/26 | 7 | 11 / 115 | 0 |
| S2 `Expr.equals` | 17/26 | 5 | 15 / 346 | 1 (A20) |
| S3 numeric, real | 22/28 | 4 | 10 / 13 | 0 |
| S4 layered, real | 23/28 | 2 | 10 / 106 | 0 |
| S5 solution sets, real | 10/15 | 1 | 12 / 49 | 0 |
| S8 units | 4/4 | 0 | 3 / 6 | 0 |
| **PIPELINE** | **26/28** | **1** | **11 / 94** | **0** |

¹ Dangerous means the strategy shows green where the label is red, or red where the label is green.

LaTeX parsing of two lines took a median of 29 ms. The fork-per-check overhead was about 3 ms.

`PIPELINE` works as follows:

- **Expressions:** S4 on the reals. If S4 proves equivalence, S7 then checks the domain; a changed domain turns the tick amber.
- **Equations and inequalities:** S5 on the reals, with the unknown chosen as the symbol isolated on the left of the new line. Other symbols are sampled as positive rationals. If S5 is undecided, it falls back to S4's numerator-ratio test.
- **Physics:** S8 runs first, so a dimensional error is red regardless of the algebra.

## Findings

1. **No single SymPy call is good enough. The layered pipeline is, and it is fast.** `PIPELINE` got 26 of 28 steps right, with a worst case of about 100 ms and no timeouts even at 200 ms. A 200 ms budget is therefore enough for school algebra on a 2 vCPU box. Keep 1 s as a ceiling for heavier input.

2. **Equations must be compared as solution sets. The naive difference test is wrong on the most common step.** For `2x = 4 → x = 2`, S1 and S2 both say red. They compare `(2x−4) − (x−2) = x − 2 ≠ 0`. S5 says `{2} = {2}`. S5 is also the only strategy that tells apart the outcomes the tutor cares about:
   - `x² = 3x → x = 3` is `lost_roots` (red).
   - `√(x+3) = x+1 → x+3 = (x+1)²` is `implies`, with an extraneous root −2 (amber).
   - `(x−3)² = 0 → x = 3` is `same_roots` (green).
   - `−2x < −4 → x < 2` is a wrong sign flip (red).

   STACK's numerator-ratio test (in S4) agrees on linear steps. It wrongly turns `implies` and `same_roots` into red.

3. **The division-by-zero trap needs S7.** For `(x²−1)/(x−1) → x+1`, every equivalence test (S1–S4) says green. Only the domain check catches it: ℝ∖{1} becomes ℝ. S7 is cheap (median 3 ms) and should run whenever an expression step is proved equivalent. On equations, S5 already catches domain loss through the solution set.

4. **Numeric sampling is the best cheap filter, not a judge.** S3 is the fastest strategy (~10 ms, with a very flat p95). It rejected every wrong expression step within its first two sample points. Its errors are the expected ones:
   - It says yes on the removable singularity.
   - It says no on valid equation steps whose zero-form ratio is not constant, such as rearranging `v = u + at → a = (v−u)/t`.

   Keep it as stage 2 of S4, as STACK does.

5. **`simplify` alone misses the trig identity, and `rewrite(exp)` fixes it.** On `sin⁶x + cos⁶x → 1 − 3sin²x cos²x`, S1 leaves a residue (red, which is dangerous). S2 returns `None` after 350–520 ms (it varied across runs), so it times out at 200 ms. S4 proves the identity in about 95 ms through the `rewrite(exp)` stage. This confirms the research: a fixed chain of targeted rewrites beats one `simplify` call.

6. **Assumptions flip verdicts in both directions. That is the main policy question for #15.** The two pipeline misses are both "conditional" steps:
   - `A = πr² → r = √(A/π)`: correct when r is a length. Over ℝ it is `lost_roots`, so red.
   - `log(xy) → log x + log y`: correct for x, y > 0. Over ℝ it is undecided, so amber.

   Declaring symbols positive (the P variants) turns both green. Applied globally, though, the positive variants also turn `√(x²) → x` green, which is wrong, and accept dividing by x in `x² = 3x → x = 3`. **So positivity has to be per symbol and declared, from the problem bank or the tutor ("r is a length"), never a global switch.**

7. **Units catch physics errors that the algebra alone also catches, but they give a better reason.** S8 caught both dimensional mistakes:
   - `v = u + at²` adds a velocity to a length.
   - `E = mg + h` adds a force to a length.

   S8 takes about 3 ms and needs symbol-to-unit declarations. Its message ("adds [length] to [mass]·[length]/[time]²") is far more useful to a tutor than "not equivalent".

8. **The LaTeX parser contract needs work before #21.** These issues came up while running the spike:
   - SymPy 1.14's ANTLR parser returns `\pi` as `Symbol('pi')`, not the constant. The spike maps it back.
   - `e` parses as a plain symbol. In physics `e` may be the elementary charge, so the recogniser or the problem's symbol table must say which one is meant.
   - The `lark` backend returned an *ambiguous* parse tree for `\sin^2 x+\cos^2 x`.
   - `\log` parses as natural log.
   - Floats survive parsing (`0.5x`). S0 calls `0.5x` and `x/2` different; all other strategies agree that they are equal.

   This argues for the recogniser emitting a typed AST, as the research suggested, rather than LaTeX.

9. **S0 is a signal, not a judge.** Structural equality after evaluation catches "reorder only" steps (`2x+3 → 3+2x`) and trivial fractions. That is useful to detect "no real step taken", but it proves nothing else.

10. **Fork-per-check is affordable.** It costs about 3 ms of overhead, and SymPy caches are warmed before the fork. A production worker pool can keep this model, with `fork`, a warm parent and a kill on budget, and add the (prev, curr, policy) result cache from the handoff.

## Proposal for #15 (to grill, not decided)

- Use these verdict classes and ticks: `equiv` 🟢, `same_roots` 🟢, `not_equiv` 🔴, `lost_roots` 🔴, `implies` 🟠, `domain_changed` 🟠, `undecided` and `timeout` 🟠.
- Run S4 on the reals for expressions, followed by S7 when S4 proves equivalence. Run S5 on the reals for equations and inequalities, with the S4 ratio test as fallback. Run S8 first when units are declared.
- Make the domain real by default. Positivity should be declared per symbol (from the problem bank or a tutor toggle), and never inferred.
- Use a 200 ms budget per check. A timeout shows amber, and the check can be retried at 1 s in the background.
- Still open:
  - Whether `implies` (squaring) should be amber or green with an annotation.
  - Whether `same_roots` deserves a distinct marker, as STACK's "(Same roots)" does.
  - How to show a "conditional" step whose condition was not declared.

## Not covered

- Systems of equations (`linsolve`/Gröbner).
- Real recogniser output and its ambiguities (#12, #13).
- Caching.
- Concurrency under several students writing at once.
- Calculus steps.

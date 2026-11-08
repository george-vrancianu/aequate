## 4. Analysis (hand-written; facts first, recommendations labelled)

### 4.1 Facts from the run

- All 20 steps passed the parse stack (ANTLR strict, normalizer, whitelist, Lark cross-check). The Romanian inputs parsed as intended: `(4x+8):4` gave `x + 2` and `\tg(x)\cdot\cos(x)` gave `cos(x)*tan(x)`.
- No strategy hit the 2 s timeout, and none raised. Everything on these 20 easy steps finished in tens of milliseconds, so the table says little about hard inputs. The tight-budget pass (sensitivity section above) shows timeouts appear once the budget is cut to 50 ms, which is the only evidence about timeout handling here. The kill check shows the worker is really killed at the deadline. Undecided only appeared as `UND` from `Expr.equals` (see below) and never from timeouts.
- The three expression-level "equal" strategies and numerics all agree on every non-domain step: S1 (simplify), S2 (equals), S3r/S3c (numeric sampling) and S4 (layered) gave identical verdicts on 19 of 20 steps in the default (complex symbols) setting. They all missed the same three domain traps (#7, #17, #19) and said EQ.
- The three domain traps are only caught by S7 (special-point probe: one side undefined where the other is finite) and, for the equation trap #17, by S5 (solveset: empty set vs {1}). S5 is NA on the two expression traps (#7, #19), because an expression has no solution set.
- Dropped-root and squaring steps (#11, #14, #15, #16) are told apart only by S5: NARROW (roots lost, a mistake) vs WIDER (extra roots, one-way squaring). The residual-proportionality meaning used by S0-S4/S6/S7 gives plain NEQ for both, so the ONEWAY steps score "partial" (rejected, but not recognised as one-way).
- Real vs complex: on the 19 steps other than #20, S3r and S3c agree, and S5r and S5c agree. The semantics only bites on #20 (`sqrt(x^2)` -> `x`). Under default (complex) symbols S1/S3/S4 say NEQ. With `real=True` symbols they still say NEQ. With `positive=True` symbols S1/S2/S4 say EQ. So "equal" for #20 exists only under an x >= 0 assumption, which is exactly the DOMAIN label.
- `Expr.equals` is randomised. On #20, S2 returned `None` in this run and `False` in the previous trial run; run directly 30 times, `sqrt(x**2).equals(x)` gave False 19 times and None 11 times (real symbol: False 17, None 13). So S2 is not a stable verdict source on this input. Undecided is therefore a real outcome of S2 and may differ between runs.
- S1 never proves non-equivalence: a non-zero `simplify(A-B)` was recorded as NEQ here (that is what a naive checker would do), and in this set it was always right, but the detail strings (e.g. `-x + sqrt(x**2)`) show it is only "not shown equal".
- S0 (structural) is only right when the step is a no-op or reorder: it says NEQ on every expand, factor, trig and equation step that is correct (6 wrong, all false rejects of correct steps) and EQ on #5, #6, #18 only because the parser auto-evaluates (`\frac{2x+4}{6}` and `\frac{x+2}{3}` land on the same SymPy tree). The ANTLR parser has no `evaluate=False` option, so a truly unevaluated structural comparison was not tested (limitation).
- S6 (assumption variants): only #20 flips verdict (positive symbols give EQ). No other step is sensitive to real vs positive.

### 4.2 Limits of this evidence

- 20 hand-picked, mostly easy school steps; none stresses the timeout. No inequalities, systems, logs, mixed trig, floats, or parse rejections were exercised.
- "Equation meaning" for S0-S4/S6/S7 (residuals proportional) is this prototype's choice. Other meanings (STACK's numerator-ratio test) would behave the same here, but this was not tested.
- S7's special-point probe is a heuristic over a fixed point list, not a domain computation; it would miss singularities at other points (e.g. x=5 for `1/(x-5)`).
- Expected labels are mine; the reasoning is in section 0.

### 4.3 Recommendations (not facts)

Stacking order, cheapest first, stop at the first decisive answer:
1. Parse with the guarded stack; a Reject is "cannot check".
2. S3 numeric reject (real points, relative tolerance): fast (single-digit ms) and gave no false NEQ here. A NEQ is final for plain equivalence.
3. S0/S4 cheap zero-checks (expand/cancel/together/factor/trigsimp) then S1 simplify for a proven EQ. Treat `equals` (S2) as an optional last resort, since it is randomised.
4. For equation lines, S5 solution-set comparison over the stated domain is the decisive step: it is the only strategy that distinguishes mistake (NARROW) from one-way (WIDER) and caught the equation trap.
5. For every EQ, run the S7-style domain flag (extend it: compute denominator zeros and tan/cot/log domains symbolically instead of a fixed point list) and show amber, not green, when domains differ.
6. Anything undecided or timed out (2 s looked ample here; consider a lower budget such as 500 ms for interactive use) shows as amber "can't check", never green or red.

### 4.4 Policy questions for "Decide CAS equivalence semantics"

- Domain: real or complex? In this run the choice only mattered for `sqrt(x^2)` vs `x`. Is the default real (school algebra) with a per-problem override, and is `positive` ever the default for formula-rearrangement tasks?
- A step equal everywhere except at a point (#7, #17, #19): green, amber, or red? Amber with the excluded value named ("only if x != 1") is what S7 enables.
- One-way steps (squaring): accepted as valid with a flag (S5 WIDER), or rejected? Should the checker demand the student check for extraneous roots later?
- Dropped root (NARROW) vs plain wrong: same red, or a specific hint? S5 can tell them apart; S1-S4 cannot.
- Equation equality: same solution set (S5), proportional residuals (S1-S4), or both? These agreed on every EQUIV step here but only S5 sees direction.
- Repeated roots: is `(x-3)^2=0` equivalent to `x=3`? (Not tested; solveset loses multiplicity.)
- Undecided handling: amber with "can't check", retry with a longer budget, or fall back to numerics-only "probably equal"?
- Tolerance: numeric relative tolerance 1e-9 with 10 points worked here; should "probably equal" from numerics alone ever be shown green when symbolic proof fails or times out?
- Form vs equivalence: should expanded/factored/fraction-in-lowest-terms be checked (S0 shows structural difference exists), separate from equivalence?
- S2 `equals` nondeterminism: is a non-reproducible verdict acceptable, given results are cached by (before, after, policy)?

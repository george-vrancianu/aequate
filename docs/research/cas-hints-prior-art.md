# Prior art for CAS-derived hints and goal inference

Research note, 2026-10-23. Ticket: *Prior art for CAS-derived hints and goal inference* (child of *Wayfinder map: assist loop (transcribe, check, solve, hint)*). Question: *"What prior art exists for generating hints deterministically from a CAS, without an LLM, and for inferring a goal (solve for x, simplify, factor, evaluate) from a first step?"*

Context: [`docs/handoff.md`](../handoff.md) §6 and the assist-loop map's settled points. SymPy is the only judge. The hint ladder runs from vaguest to most explicit, and its last rung is the next step. Each worked solution has a goal inferred from its first step. An optional local LLM may phrase hints, but with no LLM configured there must be a deterministic fallback derived from the CAS. This note informs that fallback.

Each claim below links to its source. **Unverified** marks anything I could not confirm in a primary source. *Inference* marks my own reasoning from the cited facts. **[run]** marks a claim I checked by running the code: SymPy 1.14.0 (the latest on PyPI today) in a fresh venv on Python 3.14, and mathsteps 0.2.0 from npm on Node 24.21. The scripts are summarised in the appendix.

---

## Conclusion (TL;DR)

1. **No package can be adopted as "the hint engine".** The reusable parts are *patterns* and a few SymPy entry points:
   - **Mathsteps** (Socratic, then Google) is the only open, rule-based, step-by-step solver for school algebra with a stable vocabulary of change types. It is Apache-2.0, archived since 2023, written in JavaScript, and narrow in scope: it cannot solve `x^2 = 2` or factor `x^3 - x` **[run]**. Port its rule list and its `ChangeTypes` vocabulary. Do not depend on it.
   - **STACK** potential response trees produce feedback the *question author* writes, node by node. Its reusable automatic part is the answer tests, which emit fixed feedback strings: form tests such as "Your answer is not factored", integration tests such as "You need to add a constant of integration", and ⇒/⇐ solution-set annotations for line-by-line work. STACK does not generate next-step hints. It is GPL-3.0, actively maintained (v4.14.0 tagged 2026-10-16), and runs on PHP + Maxima, so take the ideas and not the code.
   - **SymPy** has exactly one step-by-step generator: `manualintegrate.integral_steps`, which returns a tree of named rules such as `PartsRule(u=x, dv=exp(x))` **[run]**. `solveset` has internal strategy dispatch (poly, rational, radical, abs, trig, exponential, log) but produces no steps. `classify_ode` names ODE methods and literally calls them "hints". It is BSD-3.
   - **SymPy Gamma** formats `integral_steps` and its own derivative rules as English text. It has had no commits since 2024-03, pins SymPy 1.6.2, and its `intsteps.py` imports names that no longer exist in SymPy 1.14 **[run]**.
   - **IDEAS** (Utrecht / Open University NL) is the closest academic prior art for the whole design. Its feedback services include `onefirst` (next step plus the rule used), `stepsremaining`, `diagnose` (buggy rules), `finished` and `suitable`, and its text service separates a "hint" from a "step". The framework is Apache-2.0 and was updated 2026-09, but it is written in Haskell, and its maths domain package is GPL and has been dead since 2015.
2. **No surveyed system infers the goal from a first step.** In Mathsteps the caller picks `simplifyExpression`, `solveEquation` or `factor`. In STACK the author fixes the goal per question. IDEAS comes closest: an exercise is chosen up front, and its `create` service rejects a term that is "Not suitable" for the exercise or already "ready". SymPy Gamma dispatches on expression type to choose result cards, and for a generic expression it shows roots, derivative, integral and series at once instead of picking one. *Inference:* Aequate's goal inference is new, but it can be built the IDEAS way: each goal type has a `suitable(first_step)` predicate and a `finished(step)` predicate.
3. **Rungs a CAS-only fallback can realistically produce** (*inference*, detailed in §7):

| Rung | What it says | CAS-only? | Source of the pattern |
|---|---|---|---|
| 1. Goal status (pointing) | "Goal: solve for x. Not finished: x is still on both sides." / "Not fully factored yet." / "You lost a solution in the last step." | **Yes, for every goal type.** It needs only goal predicates, form tests and solution-set comparison | IDEAS `finished`; STACK form tests and ⇒/⇐ |
| 2. Method (teaching) | "This is a quadratic equation: try factoring." / "Try integration by parts." | **Yes, for classifiable problem classes:** polynomial degree, rational / radical / exponential, the top `integral_steps` rule, `classify_ode` | SymPy `solveset` dispatch, `integral_steps`, `classify_ode`; VanLehn's teaching hint |
| 3. Operation (specific) | "Subtract 3 from both sides." / "Let u = x and dv = eˣ dx." | **Only where an explicit rule engine covers the class:** linear equations and inequalities, factorable quadratics, fraction arithmetic, distribution, like terms, and integration via `integral_steps` | Mathsteps `ChangeTypes`; IDEAS `onefirst` |
| 4. Next step (bottom-out) | The expression after rung 3, checked by SymPy | **Yes where rung 3 exists.** Elsewhere, at most one goal-directed SymPy transform (`factor`, `expand`, `cancel`, `together`). If none makes progress, say "no automatic hint, ask your tutor" | VanLehn's bottom-out hint; IDEAS `onefirst` |

   Build a small Python rule engine for the school-algebra core (port the Mathsteps rule list), use `integral_steps` for integration, and use templates for rungs 1–2 in each locale. The LLM, when present, rephrases these same CAS facts and never adds new ones.

---

## 1. Background: what a hint ladder is in the ITS literature

VanLehn's survey of tutoring systems describes the standard hint sequence for a step that needs one knowledge component as **Point, Teach, Bottom-out**: "Pointing hints mention problem conditions that should remind the student of the knowledge component's relevance. Teaching hints describe the knowledge component briefly and show how to apply it. Bottom-out hints tell the student the step." ([VanLehn 2006, *The Behavior of Tutoring Systems*, IJAIED 16(3), p. 16 of the PDF](https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf)). The same paper describes how such sequences are generated without hand-writing each one: "associate a sequence of text templates with each knowledge component. When the step generator returns a step to hint, it also returns the knowledge component application that was used to derive the step", and the slots are filled from the problem (p. 17). It also warns that when several knowledge components are involved, "a complex hint sequence might be worse than none … it might be better to just give a bottom-out hint" (p. 17).

*Inference:* this is exactly the shape a CAS fallback needs. A **step generator** returns (rule, location, result). Each rule has a template per rung. The bottom-out rung is the result. Aequate's settled ladder (vaguest → next step) matches Point → Teach → Bottom-out.

---

## 2. Mathsteps (Socratic / Google)

| | |
|---|---|
| Repo | [google/mathsteps](https://github.com/google/mathsteps). Its `package.json` still points at `socraticorg/mathsteps`, which now redirects to the Google repo ([package.json @ 9d370c3](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/package.json)) |
| Licence | Apache-2.0 (GitHub licence metadata; [npm](https://www.npmjs.com/package/mathsteps) shows the same). This is compatible with GPLv3, and therefore with AGPLv3 ([FSF licence list](https://www.gnu.org/licenses/license-list.html#apache2)) |
| Maintenance | **Archived** (read-only) on GitHub. The last code change was 2021-08-30 and the last commit (a README edit) was 2023-06-26 ([commits](https://github.com/google/mathsteps/commits/master)). The npm package is `0.2.0`, last modified 2022-06-19 (`npm view mathsteps`). It pins `mathjs 3.11.2` ([package.json](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/package.json)). It still installs and runs on Node 24 **[run]** |
| Language / SymPy fit | JavaScript on mathjs. It has no Python or SymPy binding. Using it from Aequate would need a Node sidecar, or a port |
| API | Three entry points: `simplifyExpression`, `solveEquation`, `factor` ([index.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/index.js)). Each returns steps with `oldNode`/`newNode` (or `oldEquation`/`newEquation`), a `changeType` and `substeps` ([README](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/README.md)) |

**What it produces.** It produces a sequence of rewrite steps, each tagged with one of 79 `ChangeTypes`. Examples: `SUBTRACT_FROM_BOTH_SIDES` ("x + 3 = 2 → x + 3 - 3 = 2 - 3"), `DIVIDE_FROM_BOTH_SIDES`, `DISTRIBUTE`, `COLLECT_AND_COMBINE_LIKE_TERMS`, `COMMON_DENOMINATOR`, `CANCEL_GCD`, `FACTOR_SUM_PRODUCT_RULE`, `FACTOR_DIFFERENCE_OF_SQUARES`, `FIND_ROOTS` ([lib/ChangeTypes.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/ChangeTypes.js)). The library returns **no English text**. The text lived in the demo site, which maps each change type to a description through `Change.formatChange` and a `ChangeText` table ([mathsteps-website src/Change.js](https://github.com/evykassirer/mathsteps-website/blob/master/src/Change.js), Apache-2.0). *Inference:* this is VanLehn's "templates per knowledge component" in practice: rule id → template.

Observed **[run]**:

```
solve 2x + 3 = 7         SUBTRACT_FROM_BOTH_SIDES, SIMPLIFY_LEFT_SIDE, SIMPLIFY_ARITHMETIC,
                         DIVIDE_FROM_BOTH_SIDES, SIMPLIFY_FRACTION, SIMPLIFY_FRACTION  (x = 2)
solve x^2 + 5x + 6 = 0   FACTOR_SUM_PRODUCT_RULE, FIND_ROOTS  (x = [-2, -3])
solve x^2 = 2            0 steps ("Math error: No term with symbol: x")
solve 2^x = 8            0 steps
simplify 2(x+3) - x      DISTRIBUTE, COLLECT_AND_COMBINE_LIKE_TERMS, REMOVE_MULTIPLYING_BY_ONE
factor x^2 + 5x + 6      FACTOR_SUM_PRODUCT_RULE
factor x^3 - x           0 steps
simplify sin^2 x + cos^2 x  0 steps
```

**Goal types.** These are simplify (arithmetic, fractions, polynomials, nth roots, absolute value), solve (one variable, with comparators `= < > <= >=`; quadratics only when they factor) and factor ("Currently only supports factoring quadratics", [lib/factor/stepThrough.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/factor/stepThrough.js)). There is no evaluate for calculus, no trigonometry, no exponentials and no logs. `solveEquation` gives up and returns `[]` on unsupported nodes, stops after `MAX_STEP_COUNT = 20`, and throws if an equation grows past 300 characters ([lib/solveEquation/stepThrough.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/solveEquation/stepThrough.js)).

**Goal inference.** None. The caller chooses the entry point.

**Verdict** (*inference*). Mathsteps is the best template for Aequate's rule engine for rungs 3–4. Its rule list matches the school-algebra core, and its change-type vocabulary is a ready-made set of hint keys. Port the rules to Python over SymPy trees built with `evaluate=False`. Do not run the archived JS library in production. Its scope gaps (`x^2 = 2`) would need new rules anyway.

---

## 3. STACK (Moodle question type; Maxima backend)

| | |
|---|---|
| Repo | [maths/moodle-qtype_stack](https://github.com/maths/moodle-qtype_stack) |
| Licence | Code GPL-3.0. Docs CC BY-SA 4.0 ([About/License.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/About/License.md)). GPLv3 code may be combined with AGPLv3 code under §13 of both licences ([AGPLv3 §13](https://www.gnu.org/licenses/agpl-3.0.html), [FSF licence list](https://www.gnu.org/licenses/license-list.html#AGPLv3.0)) |
| Maintenance | Active. Last push 2026-10-23 ([commit 1b4e42d](https://github.com/maths/moodle-qtype_stack/commit/1b4e42d44930157a01f49ab35057e88b0883884d)). Latest tag `v4.14.0`, dated 2026-10-16 |
| Language / SymPy fit | PHP + Maxima. There is no Python API. A standalone REST API exists (`api/`, built for the Dynexite exam system), deployed as Docker with a Maxima service ([api/README.md](https://github.com/maths/moodle-qtype_stack/blob/master/api/README.md)). It does not plug into SymPy |

**Potential response trees (PRTs).** A PRT is "an acyclic directed graph" of nodes. "In each node two expressions are compared using a specified answer test", and each branch can adjust the score, "add written feedback specifically for the student", generate an answer note for the teacher, and pick the next node ([Potential_response_trees.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Potential_response_trees.md)). The PRT feedback is **authored per question**. The outcome is "a numerical score, text for the students, an answer note" ([Feedback.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Feedback.md)). STACK's "general feedback (known as worked solution in previous versions) is fixed and may not depend on the student's answers" ([same](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Feedback.md)). STACK's own "Hints" feature is a static formula sheet inserted with `[[facts:tag]]` ([Fact_sheets.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Question_blocks/Fact_sheets.md)). So STACK has **no next-step generation**.

**Automatic, CAS-derived feedback** comes from the answer tests' built-in strings, which are question-independent ([lang/en/qtype_stack.php](https://github.com/maths/moodle-qtype_stack/blob/1b4e42d44930157a01f49ab35057e88b0883884d/lang/en/qtype_stack.php#L1313-L1475)):
- Form: `ATFacForm_notfactored` "Your answer is not factored.", `ATLowestTerms_wrong` "You need to cancel fractions within your answer.", `ATSingleFrac_div` "Your answer contains fractions within fractions…", `ATCompSquare_false_no_summands`, `ATPartFrac_denom_ret` "If your answer is written as a single fraction then the denominator would be {m0}. In fact, it should be {m1}."
- Calculus: `ATInt_const` "You need to add a constant of integration…", `ATInt_diff` "It looks like you have differentiated instead!", `ATInt_generic` (shows the derivative of the student's answer next to the integrand), `ATDiff_int` "It looks like you have integrated instead!"
- Type mismatches: `ATAlgEquiv_SA_not_equation`, `ATSysEquiv_SA_missing_variables`, and others.

The test families (Equivalence, Form, Calculus, Numerical) are listed in the [answer test docs](https://github.com/maths/moodle-qtype_stack/tree/master/doc/en/Authoring/Answer_Tests).

**Line-by-line reasoning.** The equivalence-reasoning input annotates each line against the previous one with ⇔, ⇒/⇐ (solution-set subset), "(Same roots)" and natural domains. `EquivFirst` checks that "the first line of the student's answer is equivalent to the first line of the teacher's answer up to commutativity and associativity". `stack_equiv_find_step(ex, exl)` looks for a teacher-specified intermediate step in the student's lines ([Equivalence_assessment.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_assessment.md)). The scope and the algorithm are covered in the earlier note [*How SymPy decides expression equivalence*, §3.1](https://github.com/george-vrancianu/aequate/blob/research/sympy-equivalence/docs/research/sympy-equivalence.md).

**Goal types.** These are author-defined per question. The form tests cover factor, expand, single fraction, lowest terms, complete the square and partial fractions. Calculus tests cover integrate and differentiate. Equivalence reasoning covers "basic single variable polynomials", simple inequalities and simple systems ([same note](https://github.com/george-vrancianu/aequate/blob/research/sympy-equivalence/docs/research/sympy-equivalence.md)).

**Goal inference.** None. The teacher's answer and the PRT encode the goal.

**Verdict** (*inference*). Reuse the *diagnostic* ideas as SymPy checks feeding rung 1 and the check verdict: form tests ("not fully factored"), the integration constant, differentiated-instead-of-integrated, and lost or gained solutions. The PRT model is an authoring tool, and Aequate has no per-problem authoring in v1 (per-problem settings arrive with the problem bank). STACK's strings could be adapted under GPL-3.0 if wanted, but they are short enough to write fresh in Romanian and English.

---

## 4. SymPy's own step machinery

SymPy 1.14.0, BSD-3-Clause ([PyPI](https://pypi.org/project/sympy/)). It is compatible with the GPL ([FSF list](https://www.gnu.org/licenses/license-list.html#ModifiedBSD)) and actively maintained.

**`manualintegrate.integral_steps(integrand, symbol)`** "attempts to mirror what a student would do by hand as closely as possible". It returns a rule tree, for example `URule(... u_func=exp(x), substep=ArctanRule(...))`. It notes that "SymPy Gamma uses this to provide a step-by-step explanation" ([manualintegrate.py L1989 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/integrals/manualintegrate.py#L1989)). The rules are dataclasses (`@dataclass class Rule(ABC)` with `integrand`, `variable` and an `eval()` method, [L72](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/integrals/manualintegrate.py#L72)). There are about 60 rule classes, including `PartsRule`, `URule`, `PowerRule`, `ConstantTimesRule`, `RewriteRule`, `TrigSubstitutionRule`, `CompleteSquareRule`, `DontKnowRule` and others **[run]**. Observed **[run]**:
- `x·eˣ` → `PartsRule(u=x, dv=exp(x), …)`
- `(x²+3)²` → `RewriteRule(rewritten=x⁴+6x²+9)`
- `2x·cos(x²)` → `ConstantTimesRule` at the top, with the substitution in a substep. *Inference:* the top rule is not always the pedagogically salient one, so rung 2 should look a level deeper past constant factors.
- `exp(x²)` → `ErfRule`, which is beyond school level. The fallback should detect such rules and decline.

**`solveset` internals.** `_solveset` dispatches on the form of the equation to `_solve_as_poly`, `_solve_radical`, `_solve_abs`, the trig solvers, and `_transolve` (exponential, logarithmic, Lambert) ([solveset.py L1244 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/solveset.py#L1244), [L1021](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/solveset.py#L1021), [L2122](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/solveset.py#L2122)). These are private functions (leading underscore) and they record **no steps**. `invert_real(f_x, y, x)` inverts all the way down: `invert_real(2*x + 3, 7, x)` gives `(x, {2})` in one call, not "subtract 3" **[run]**. *Inference:* mirror the dispatch categories as a public classifier for rung 2. Do not call the private functions.

**`classify_ode`** returns ordered method names, e.g. `('separable', '1st_exact', '1st_linear', 'Bernoulli', …)` for `f' = x·f` **[run]**. SymPy calls these "hints": "Use `dsolve(ode, func, hint=hint)` to solve an ODE using a specific hint" ([ode.py header @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/ode/ode.py#L1-L11); `allhints` has 45 entries **[run]**). This is prior art for rung 2 (naming the method) beyond school algebra.

**Named trig rewrites.** `sympy.simplify.fu` exposes Fu's transformation rules `TR0`–`TR22` as separate functions, e.g. `TR5(sin(x)**2)` gives `1 - cos(x)**2` ([fu.py L356 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/fu.py#L356); **[run]**). *Inference:* these are usable as named single-step trig identities for rungs 3–4.

**One-shot transforms.** `factor`, `expand`, `cancel`, `together`, `apart` and `collect` each return a whole rewrite. They are useful for a goal-directed "next form", but they can jump several hand steps. For example, `cancel((x²-1)/(x-1) + 2x)` gives `3x + 1` in one go, silently dropping `x ≠ 1` **[run]** (see the division-by-zero pitfall in the [equivalence note](https://github.com/george-vrancianu/aequate/blob/research/sympy-equivalence/docs/research/sympy-equivalence.md)).

**Parsing pitfall for goal inference.** SymPy evaluates on construction: `Rational(3,4) + Rational(5,6)` arrives as a single `Rational`, so an "evaluate" first step is indistinguishable from its answer unless the step is parsed with `evaluate=False` **[run]**.

**Goal types.** Integration has real steps. ODEs have method names. Solve has categories but no steps. Simplify, factor and expand are one-shot.

---

## 5. SymPy Gamma

| | |
|---|---|
| Repo | [sympy/sympy_gamma](https://github.com/sympy/sympy_gamma) |
| Licence | BSD-style ("Copyright (c) 2009-2020 SymPy Development Team … Redistribution and use … permitted"). GitHub reports `NOASSERTION` ([LICENSE](https://github.com/sympy/sympy_gamma/blob/master/LICENSE)) |
| Maintenance | The last commit was 2024-03-12 and was CI-only ([3da0b17](https://github.com/sympy/sympy_gamma/commit/3da0b1756dfcdebdc308fafdb0b9f0268fdfb00a)). It pins `sympy==1.6.2` and `Django==3.0.8` ([requirements.txt](https://github.com/sympy/sympy_gamma/blob/master/requirements.txt)). It is a Google App Engine web app ([README](https://github.com/sympy/sympy_gamma/blob/master/README.rst)) |
| SymPy fit | Python, but bit-rotted. `app/logic/intsteps.py` imports `_manualintegrate` and `evaluates` from `sympy.integrals.manualintegrate` ([intsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/intsteps.py)). Both raise `ImportError` on SymPy 1.14.0 **[run]**, and it uses the namedtuple `._asdict()` API that the dataclass rules replaced |

**What it produces.** It produces English step-by-step text for integrals. `IntegralPrinter` has one `print_*` method per rule: "Use integration by parts:", "Let u = … and let dv = …", "Integrate term-by-term:", "Now substitute u back in:" ([intsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/intsteps.py)). It also produces derivative steps from its **own** rule set (`PowerRule`, `MulRule`, `DivRule`, `ChainRule`, `TrigRule`, `ExpRule`, `LogRule`…, [diffsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/diffsteps.py)). SymPy has no `diff_steps`.

**Goal inference, the nearest prior art.** `result_sets` maps the input's type to result "cards": an integer gets digits and factorisation, a rational gets a float approximation, and an `integrate`/`diff` call gets `intsteps`/`diffsteps`. A generic non-constant expression gets `['plot', 'roots', 'diff', 'integral_alternate', 'series']`, i.e. every plausible action at once ([resultsets.py L969-L990](https://github.com/sympy/sympy_gamma/blob/3da0b1756dfcdebdc308fafdb0b9f0268fdfb00a/app/logic/resultsets.py#L969-L990)).

**Verdict** (*inference*). Read `intsteps.py` and `diffsteps.py` as templates for the integration and derivative rungs (rules → sentences). Re-implement them against the 1.14 dataclass API. Do not vendor the app.

---

## 6. Other open systems

**IDEAS framework (Heeren, Gerdes, Jeuring).**
- Licence and status: [ideas-edu/ideas](https://github.com/ideas-edu/ideas), Apache-2.0. Last push 2026-09-05. Hackage `ideas` 1.9.1 was uploaded 2026-09-05, and Hackage reports its builds as failing ([Hackage](https://hackage.haskell.org/package/ideas)).
- Design: "Feedback services for intelligent tutoring systems" in Haskell. A stateless domain reasoner is separated from the learning environment ([Heeren & Jeuring, *Feedback services for stepwise exercises*, Sci. Comput. Program. 88 (2014), doi:10.1016/j.scico.2014.02.021](https://cs.ou.nl/members/bastiaan/FeedbackServices.html)). A strategy is a language of rewrite-rule sequences, so tracking a student's steps becomes parsing ([Heeren, Jeuring & Gerdes, *Specifying rewrite strategies for interactive exercises*, MCS 2010](https://cs.ou.nl/members/bastiaan/SpecifyingStrategiesJournal.html)).
- Services ([ServiceList.hs @ de4d974](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/ServiceList.hs)):
  - `basic.onefirst`: "Returns a possible next step according to the strategy … the rule used and the location where to apply"
  - `basic.allfirsts`
  - `basic.solution`: a worked solution
  - `basic.stepsremaining`
  - `basic.diagnose`: Buggy / NotEquivalent / Similar / …, with buggy rules for common misconceptions
  - `basic.finished`: "Checks whether a term is in solved form"
  - `basic.suitable`: "Identifies which terms can be solved by the strategy"
- `onefirsttext` renders the same next step with feedback id `"hint"` when triggered by the hint button and `"step"` otherwise, using a per-exercise feedback script ([FeedbackText.hs](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/FeedbackText.hs)).
- `create` returns "Is ready" or "Not suitable" when a starting term does not fit the exercise ([BasicServices.hs L42-L44](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/BasicServices.hs#L42-L44)).
- The maths domains (fractions, polynomial equations, powers, derivatives, linear algebra) live in [`ideas-math`](https://hackage.haskell.org/package/ideas-math). It is GPL, last uploaded 2015-04-09, and its Hackage build plan fails.
- SymPy fit: none. It is Haskell behind an HTTP/JSON service.
- *Inference:* this is the best architectural model. Per goal type, provide `suitable`, `finished`, `onefirst` (rule + location + result) and `diagnose`. Adopt the model, not the code.

**OATutor** ([CAHLR/OATutor](https://github.com/CAHLR/OATutor), MIT, active). Its hints and scaffolds are human-authored per problem: "hints and scaffolds authored by the OATutor Project" ([README](https://github.com/CAHLR/OATutor)). It has no CAS hint generation. Its paper also evaluates LLM-generated hints (linked from the README).

**Khan KAS** ([Khan/KAS](https://github.com/Khan/KAS), MIT, archived 2021). It is "a lightweight JavaScript CAS for comparing expressions and equations". It compares only and has no steps.

**Small step-by-step solver repos.** A GitHub search for "step by step math solver" and "sympy step by step" returns only repos with 0–1 stars, most created in 2025–26 and several LLM-backed. None is a maintained library. **Unverified:** whether any proprietary engine (Photomath, Microsoft Math Solver, WolframAlpha, Algebrakit) documents its hint or goal-detection method. I did not look for them because their code cannot be reused.

---

## 7. Recommendation for the CAS-only fallback (*inference*)

### 7.1 Goal inference from the first step

No surveyed system does this, so this is new design built on the IDEAS `suitable`/`finished` pattern and on SymPy Gamma's type dispatch.

| First step (parsed with `evaluate=False`) | Inferred goal | Confidence |
|---|---|---|
| `Eq` / inequality with one free symbol | Solve for that symbol | High |
| `Eq` with several symbols | Solve for… ambiguous. Prefer `x`, `y`, `t`, or ask | Low. Show the goal as changeable |
| Unevaluated `Integral` / `Derivative` / `Limit` / `Sum` | Evaluate | High |
| Expression with no free symbols | Evaluate (compute) | High |
| Polynomial or rational expression with symbols | Simplify **or** factor **or** expand. It cannot be told apart from step 1 alone | Low. Default "simplify". Optionally re-infer from the direction of step 2 (more factored → factor) |
| Already `finished` for the default goal (e.g. `x = 3`) | No goal. Show the goal picker | n/a |

### 7.2 Which rungs CAS alone can produce

1. **Goal status (pointing). Always available.** It is built from goal predicates (`finished`: is the variable isolated, is it fully factored, is it a single number), form tests in the STACK style (`factor(e) == e` and similar **[run]**), and solution-set deltas against the previous step (`x² = 4 → x = 2` lost `{-2}`; `√(x+2) = x → x+2 = x²` gained `{-1}` **[run]**). It uses fixed templates per locale.
2. **Method (teaching). Available for classifiable problems.** It is built from a classifier mirroring the `solveset` categories (polynomial of degree n, rational, radical, exponential, log, abs, trig **[run]** for the first four), the top meaningful `integral_steps` rule, `classify_ode` for ODEs, and Fu rules for trig identities. It uses a template per category ("This is a quadratic equation. Can it be factored?").
3. **Operation (specific). Only inside a rule engine.** Write a Python port of the Mathsteps rule families: equation operations, like terms, distribution, fractions, factoring quadratics, roots. Add new rules for gaps such as `x² = c` (square root of both sides, ±). For integration, use `integral_steps`, whose rules carry parameters (`u`, `dv`, `u_func`) for the template. Each rule id maps to a template. Outside coverage, skip this rung rather than guess.
4. **Next step (bottom-out). Available wherever rung 3 is.** It is the result of applying the rule, checked equivalent to the current step by the same SymPy check used for Check. Outside coverage, allow at most one goal-directed whole transform (factor for a factor goal, `expand`+`collect` for simplify, `cancel`/`together` for fractions) and only if it makes measurable progress toward `finished`. Otherwise answer "No automatic hint for this step", which can become an ask to the tutor. Never produce the final answer through `solveset` as a "next step" unless one step really does finish the problem.
5. **Error-specific feedback.** Lost or gained solutions, a missing integration constant, "differentiated instead", "not fully factored": these are cheap CAS checks, better attached to the check verdict than to the hint ladder. Buggy-rule diagnosis in the IDEAS style (e.g. `2+3x → 5x`) needs a curated misconception rule set. It is feasible later, but not needed for the fallback.

The optional LLM gets exactly these facts (goal, status, category, rule id plus parameters, verified next step) and only rephrases them. That keeps "CAS is the only judge".

### 7.3 Risks

- **Coverage cliff.** Mathsteps, the most complete open rule set, already fails on `x² = 2` and `x³ - x` **[run]**. Expect rung 3 to be missing for a real share of tutoring problems. Measure on the spike's sample steps before promising rung 3 broadly.
- **Granularity mismatch.** A student's step may combine several rules, so the engine's "next step" can look too small or too large next to the student's last line. IDEAS handles this by parsing the student's steps against the strategy, which is a bigger build.
- **Integration rule trees show machine choices.** Examples: a `ConstantTimesRule` before the substitution, and `ErfRule` beyond the syllabus **[run]**. Filter them and decline when unsure.
- **Private SymPy APIs.** `solveset` dispatch functions are private. Mirror their categories and do not call them.

---

## Appendix: what was run

- `/tmp` scratch scripts, not committed. SymPy 1.14.0 in a uv venv:
  - `integral_steps` on `x·eˣ`, `exp(x²)`, `2x·cos(x²)`, `(x²+3)²`
  - `invert_real`, `classify_ode`, `allhints`, `fu.TR5`
  - `factor`/`expand`/`cancel`/`together`/`apart` change detection
  - solution-set deltas between steps with `solveset(…, S.Reals)`
  - a toy polynomial / rational / radical / exponential classifier
  - type of constructed first steps (`Rational(3,4)+Rational(5,6)` becomes a `Rational`)
  - `from sympy.integrals.manualintegrate import evaluates` and `_manualintegrate` → `ImportError`
- mathsteps 0.2.0 from npm, installed with `--ignore-scripts`, on Node 24.21: the `solveEquation`, `simplifyExpression` and `factor` calls listed in §2.

## Sources

- VanLehn, *The Behavior of Tutoring Systems*, IJAIED 16(3), 2006: https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf (a copy hosted on a course reading list; pages cited from the PDF)
- Mathsteps (commit 9d370c3): [README](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/README.md), [index.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/index.js), [ChangeTypes.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/ChangeTypes.js), [solveEquation/stepThrough.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/solveEquation/stepThrough.js), [factor/stepThrough.js](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/lib/factor/stepThrough.js), [package.json](https://github.com/google/mathsteps/blob/9d370c30f2d9c2b3650883e942f97c8abe6805f8/package.json); demo text [mathsteps-website Change.js](https://github.com/evykassirer/mathsteps-website/blob/master/src/Change.js)
- STACK: [Potential_response_trees.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Potential_response_trees.md), [Feedback.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Feedback.md), [Fact_sheets.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Authoring/Question_blocks/Fact_sheets.md), [Equivalence_assessment.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_assessment.md), [lang strings @ 1b4e42d](https://github.com/maths/moodle-qtype_stack/blob/1b4e42d44930157a01f49ab35057e88b0883884d/lang/en/qtype_stack.php), [License.md](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/About/License.md), [api/README.md](https://github.com/maths/moodle-qtype_stack/blob/master/api/README.md)
- SymPy 1.14.0: [manualintegrate.py](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/integrals/manualintegrate.py), [solveset.py](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/solveset.py), [ode.py](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/solvers/ode/ode.py), [fu.py](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/fu.py), [PyPI](https://pypi.org/project/sympy/)
- SymPy Gamma (commit 3da0b17): [README](https://github.com/sympy/sympy_gamma/blob/master/README.rst), [LICENSE](https://github.com/sympy/sympy_gamma/blob/master/LICENSE), [requirements.txt](https://github.com/sympy/sympy_gamma/blob/master/requirements.txt), [intsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/intsteps.py), [diffsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/diffsteps.py), [resultsets.py](https://github.com/sympy/sympy_gamma/blob/3da0b1756dfcdebdc308fafdb0b9f0268fdfb00a/app/logic/resultsets.py)
- IDEAS (commit de4d974): [repo](https://github.com/ideas-edu/ideas), [ServiceList.hs](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/ServiceList.hs), [FeedbackText.hs](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/FeedbackText.hs), [BasicServices.hs](https://github.com/ideas-edu/ideas/blob/de4d9742c3505b2bf70f1d62459513814c0703ac/src/Ideas/Service/BasicServices.hs), [Hackage ideas](https://hackage.haskell.org/package/ideas), [Hackage ideas-math](https://hackage.haskell.org/package/ideas-math); papers: [Feedback services for stepwise exercises (2014)](https://cs.ou.nl/members/bastiaan/FeedbackServices.html), [Specifying rewrite strategies (2010)](https://cs.ou.nl/members/bastiaan/SpecifyingStrategiesJournal.html)
- OATutor: https://github.com/CAHLR/OATutor; Khan KAS: https://github.com/Khan/KAS
- Licences: [FSF licence list](https://www.gnu.org/licenses/license-list.html), [GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html)
- Earlier Aequate note: [How SymPy decides expression equivalence](https://github.com/george-vrancianu/aequate/blob/research/sympy-equivalence/docs/research/sympy-equivalence.md)

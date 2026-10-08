# How SymPy decides expression equivalence across forms

Research for issue [#5](https://github.com/george-vrancianu/aequate/issues/5), part of the map in #1. It feeds Spike 4 ("SymPy equivalence on 20 typical algebra steps", `docs/handoff.md` section 10) and the equivalence-semantics decision. Handoff context: the CAS is the only judge, it checks each line as the student writes, and the tutor sees green/amber/red ticks (`docs/handoff.md` sections 1 and 2).

Researched 2026-10-08 against SymPy 1.14.0 and Pint 0.26.1 (the latest on PyPI that day), the STACK `master` branch, the Numbas docs, the SymPy Gamma repo and the Mathics3 `master` branch.

**Empirical checks.** Claims marked **[run]** were checked by running SymPy 1.14.0 / Pint 0.26.1 in a clean `python:3.12-slim` container. The scripts are in the appendix and the output is quoted inline. Timings come from one laptop run under WSL2. Read them as orders of magnitude, not benchmarks.

---

## 1. The SymPy strategies

### 1.1 Structural equality (`==`)

- `==` in SymPy tests exact structural equality, not mathematical equality: `(x + 1)**2 == x**2 + 2*x + 1` is `False`. Source: [SymPy Gotchas, "Equals signs"](https://docs.sympy.org/latest/tutorials/intro-tutorial/gotchas.html).
- Automatic evaluation at construction already canonicalises some things, so commutative reordering compares equal: `sympify('2*x+3') == sympify('3+2*x')` gives `True` **[run]**. Anything beyond that does not: `x*(x+1) == x**2+x` gives `False` **[run]**.
- Number types also matter. By default only numbers of the same type compare equal, so `S.Half != Float(0.5)`. Source: [`Basic.is_same` docs](https://docs.sympy.org/latest/modules/core.html). `x+0.5 == x+Rational(1,2)` gives `False` **[run]**.
- Automatic evaluation also changes the student's line before any check runs. `x/x` becomes `1` at construction **[run]**. The `solveset` docs warn that this can remove a singularity, and that `evaluate=False` keeps the original form. Source: [solveset `domain_check`](https://docs.sympy.org/latest/modules/solvers/solveset.html). With `parse_expr('2+3', evaluate=False)` the result stays `2 + 3`, which is not `== 5` **[run]**.

**Use for Aequate:** a fast first pass ("is this line literally the same?") and a way to detect "no step taken". It cannot judge equivalence on its own.

### 1.2 `simplify(a - b) == 0`

- This is the method the SymPy tutorial recommends: "the best way to check if a = b is to take a − b and simplify it, and see if it goes to 0". The tutorial also says the method is "not infallible" and that deciding symbolic equality is impossible in general. Source: [SymPy Gotchas](https://docs.sympy.org/latest/tutorials/intro-tutorial/gotchas.html).
- `simplify` is a heuristic. The docstring says it "tries to apply intelligent heuristics to make the input expression 'simpler'" and recommends calling specific simplification functions when you know the structure, because those "are well defined and thus your algorithm will be robust". Its `ratio=1.7` guard returns the input unchanged if the result grows too much. Source: [`simplify` docstring, `sympy/simplify/simplify.py` L435-L480 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/simplify.py#L435-L480).
- Observed results **[run]**:
  - `simplify((x+1)**2-(x**2+2*x+1))` gives `0` in about 0.08 s (first call, which includes warm-up).
  - `simplify(sin(x)**2+cos(x)**2-1)` gives `0`.
  - False negative on a true identity: `simplify(sin(x)**6+cos(x)**6-1+3*sin(x)**2*cos(x)**2)` gives `sin(x)**6 + cos(x)**6 - 3*cos(4*x)/8 - 5/8`, not `0`.
  - False negative: `simplify(sin(x)**8+cos(x)**8 - (35+28*cos(4*x)+cos(8*x))/64)` and `trigsimp` both leave a non-zero residue. Rewriting the difference with `.rewrite(exp)` first and then simplifying gives `0` in about 0.06 s. So a fixed chain of targeted rewrites beats a single `simplify` call.

### 1.3 `Expr.equals(other)`

`equals` is not purely numeric. Here is what the source does ([`sympy/core/expr.py` L750-L895 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/core/expr.py#L750)):

1. If `self == other` (structurally), it returns `True`.
2. It computes `diff = factor_terms(simplify(self - other), radical=True)` ([L785](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/core/expr.py#L785)). If that is zero, it returns `True`.
3. If the diff contains no `Add` or `Mod` left to expand, it returns `False`.
4. It calls `diff.is_constant(...)`. That evaluates the expression at two random complex points, then tries differentiation, then looks for denominator zeros ([`is_constant` docstring, L596](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/core/expr.py#L596)). If the expression is constant, it evaluates `diff._random()` once more. Random values have real and imaginary parts in [-1, 1] by default ([`_random`, L518](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/core/expr.py#L518)). A non-zero result returns `False`.
5. For purely numeric diffs it tries to prove zero via surd self-consistency and `minimal_polynomial`.
6. Otherwise it returns **`None`** (undecided), or the failing expression if `failing_expression=True`.

The tutorial simply calls it "a method that tests if two expressions are equal by evaluating them numerically at random points" ([Gotchas](https://docs.sympy.org/latest/tutorials/intro-tutorial/gotchas.html)). The source shows it is a hybrid of simplify and numerics.

Observed results **[run]**:

| Call | Result | Time |
|---|---|---|
| `((x+1)**2).equals(x**2+2*x+1)` | `True` | 0.002 s |
| `(cos(x)**2-sin(x)**2).equals(cos(2*x))` | `True` | 0.03 s |
| `sqrt(x**2).equals(x)` | `None` | 0.05 s |
| `(sin(x)**8+cos(x)**8).equals((35+28*cos(4*x)+cos(8*x))/64)` | `None` | 0.5 s |

**`equals` returns three values (True / False / None).** That maps naturally onto green / red / amber.

### 1.4 Numeric sampling (random-point testing)

You evaluate `a - b` at several random points and call the pair equal if every sample is close to zero.

- This is how Numbas marks every "mathematical expression" part. Both expressions are evaluated at random points, and "if the two expressions agree on enough inputs, then they are considered to be equivalent". Numbas exposes these settings: checking type (absolute difference, relative difference, decimal places, significant figures), checking accuracy, points to check, maximum failures, checking range, and per-variable *value generators* to avoid singularities. Source: [Numbas docs, Mathematical expression part](https://docs.numbas.org.uk/en/latest/question/parts/mathematical-expression.html).
- STACK uses numerics as a cheap **rejection** filter before its symbolic chain. Its `algebraic_equivalence` first calls `numerical_not_alg_equiv(SA, SB)` to "Reject obviously different expressions. These can be very time consuming in the tests below." That function substitutes small integers (1, 2, ...) into the variables before trying anything else. Source: [`stack/maxima/assessment.mac` L1084-L1093 and following, @ 10d3233](https://github.com/maths/moodle-qtype_stack/blob/10d323311b7f39fb7b092dd10ce75f7d8632f525/stack/maxima/assessment.mac#L1084-L1093).
- Numerics give a **probable** yes but a **certain** no, provided the point where the expressions differ is genuinely in the domain.

Pitfalls observed **[run]**:

- **Real vs complex sample points change the verdict.** `sqrt(x**2)` vs `x` is "different" when sampled on complex points. `sqrt(x**2)` vs `Abs(x)` is "equal" when sampled on the reals. So the sampling domain is a semantic decision, not an implementation detail.
- **Use relative tolerance, not absolute.** For the true identity `sin^8+cos^8 = (35+28cos4x+cos8x)/64`, the point `x = 1.1+2.7i` gave an absolute difference of 1.9e-9, because the terms reach about 1e9 in size. The relative difference was 1e-16. A 1e-9 absolute threshold therefore reported a false "not equal".
- **Removable singularities are invisible to numerics.** `(x**2-1)/(x-1)` vs `x+1` samples as equal, because a random point never hits x = 1. That is the same answer `simplify` gives (`0`), even though the two differ at x = 1 (`.subs(x,1)` gives `nan`).
- **Speed.** Ten mpmath samples take about 1-5 ms, against 10-500 ms for the symbolic routes above.

### 1.5 Solve-based comparison (for equations)

Here you compare the **solution sets** of consecutive equation lines.

- `solveset(f, x, domain)` returns a `Set`. That can be a `FiniteSet`, an `Interval`, `EmptySet`, an `ImageSet` for infinite families, or a `ConditionSet` when it cannot solve. The default domain is `S.Complexes`, and "the domain, not the variable's assumptions" chooses the solver. Example: `solveset(x**2+1, x)` gives `{-I, I}`, but with `domain=S.Reals` it gives `EmptySet`. The docs prefer `solveset` over `solve` because `solve`'s empty list is ambiguous (no solutions vs. not found) and `solve` may return only some of the solutions. Source: [SymPy solveset docs](https://docs.sympy.org/latest/modules/solvers/solveset.html).
- `solve` checks for and drops solutions that make a denominator zero, unless you pass `check=False`. Source: [SymPy solving guidance, "Include Solutions Making Any Denominator Zero"](https://github.com/sympy/sympy/blob/sympy-1.14.0/doc/src/guides/solving/solving-guidance.md).
- Observed results **[run]**:
  - Over the reals, `x**2 = x` gives `{0, 1}` and `x = 1` gives `{1}`. So dividing both sides by x (losing a root) is detected as non-equivalent.
  - `solveset(Eq((x**2-1)/(x-1), 2), x, Reals)` gives `EmptySet`, which correctly excludes x = 1. Comparing solution sets therefore catches domain errors that `simplify(lhs-rhs)` misses.
  - Systems: `solve([x+y=3, x-y=1])` gives `[{x: 2, y: 1}]`, and `linsolve` gives `{(2, 1)}`.
- Limits:
  - It only works when the solver succeeds. A `ConditionSet` (unsolved) cannot be compared, and the result should be "undecided".
  - It is the wrong test for **expression** rewriting lines (`2(x+1)` becoming `2x+2`), which have no solution set.
  - It cannot check that the student actually solved anything. STACK's `SysEquiv` notes the same limitation (see section 3.1).

---

## 2. Pitfalls

| Pitfall | What happens | Evidence |
|---|---|---|
| **Factored vs expanded** | `==` says different. `simplify(a-b)`, `equals` and numerics all say equal. Telling apart "student expanded" from "student left it factored" needs a separate *form* check. STACK has dedicated form tests (`FacForm`, `Expanded`, `SingleFrac`, `LowestTerms`, `CompSquare`). | [run]; [STACK answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/) |
| **Assumptions / domains** | Symbols are complex by default, and SymPy "will refuse to simplify this expression if the simplification is not valid for every possible value of x". `simplify(sqrt(x**2)-x)` stays unsimplified, but with `positive=True` it gives `0`. `log(x*y)-log(x)-log(y)` simplifies to `0` only for positive symbols. `log(exp(x))-x` does not simplify for complex x. For school algebra, declaring symbols `real=True` (or `positive=True` in "rearrange a formula" tasks) is a policy choice that changes verdicts. | [SymPy assumptions guide](https://docs.sympy.org/latest/guides/assumptions.html); [run] |
| **`inverse=True`** | `simplify(..., inverse=True)` cancels `asin(sin(x))` to `x` "without checking whether x belongs to the set where this relation is true". Do not use it for judging. | [simplify docstring L565 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/simplify.py#L565) |
| **Division by zero / removable singularities** | `x/x` becomes `1` at construction. `simplify((x**2-1)/(x-1)-(x+1))` gives `0`. The `simplify` docstring's own example cancels a factor of `x` (`(x + x**2)/(x*sin(y)**2 + x*cos(y)**2)` becomes `x + 1`). Pure-expression checks always condone cancelling a possibly-zero factor. Catching it needs either a domain check (STACK tracks `natural_domain` and shows it, and "quietly condones silent domain enlargements") or solution-set comparison. | [run]; [simplify docstring](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/simplify.py#L435-L480); [STACK equivalence assessment](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_assessment.md) |
| **Equations vs expressions** | `Eq(2*x,4) == Eq(x,2)` is `False`. `simplify(Eq(2*x+2,6))` gives `Eq(x, 2)`, which is a canonicalisation, not a proof. Equations need their own semantics: same solution set (solveset), or STACK's approach of moving everything to one side and checking that the ratio of the two numerators is a constant ("roots and multiplicities must match", "equations are never solved"). | [run]; [STACK Equivalence answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/) |
| **Repeated roots** | Is `(x-3)^2=0` equivalent to `x=3`? STACK accepts it with a "(Same roots)" acknowledgement rather than a plain equivalence mark. `solveset` returns `{3}` for both, so multiplicity is lost. | [STACK equivalence assessment](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_assessment.md) |
| **Squaring both sides / implication** | Squaring is not an equivalence, and its solution set is a superset. STACK marks such steps ⇒ or ⇐ (solution-set subset) instead of ⇔. With `assume_pos`, `x^4=2` "will now be equivalent to" `x=2`. With `assume_real`, `x=1` is equivalent to `x^3=1`. | [STACK equivalence reasoning maths](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_reasoning.md); [STACK equivalence input](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_input.md) |
| **Systems** | Compare solution sets (`solve(..., dict=True)` / `linsolve` / `nonlinsolve`). STACK's `SysEquiv` compares the polynomial ideals with Gröbner bases, and "does not check whether the student fully solved the system". | [run]; [STACK Equivalence answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/) |
| **Inequalities** | `(2*x<4) == (x<2)` is `False`. Convert to a real set and compare: `solveset(2*x<4, x, Reals)` gives `Interval.open(-oo, 2)`. A wrong sign flip (`-2x<-4` → `x<2`) is caught because the sets differ. `reduce_inequalities(x**2<4, x)` gives `(-2 < x) & (x < 2)`. STACK does the same: inequalities "are converted to the sets of real numbers they represent". | [run]; [STACK Equivalence answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/) |
| **Floats** | `0.5` vs `1/2` are structurally different. STACK advises against floats in `AlgEquiv` and points to numerical tests. SymPy's `simplify(rational=True)` recasts Floats as Rationals. | [run]; [simplify docstring](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/simplify/simplify.py#L435-L480); [STACK Equivalence](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/) |
| **Performance / timeouts** | `simplify` tries many strategies. Typical school steps took 0.01-0.1 s **[run]**, but `equals` on a trig identity took 0.5 s and still returned `None`. STACK reports that `factor` and `trigexpand` can cause timeouts, exposes flags to switch them off "at the cost of test strength", and its source notes "Radcan is slow, and may be causeing timeouts". SymPy has no built-in timeout, so the checker needs a per-check wall-clock limit enforced from outside (worker process kill). Timeouts should map to "undecided". | [STACK Equivalence](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/); [assessment.mac @ 10d3233](https://github.com/maths/moodle-qtype_stack/blob/10d323311b7f39fb7b092dd10ce75f7d8632f525/stack/maxima/assessment.mac#L1084) |
| **Parsing untrusted input** | `sympify` and `parse_expr` "use `eval`, and thus shouldn't be used on unsanitized input". Recognised handwriting is untrusted input, so build the SymPy tree from the recogniser's own AST (or `parse_latex`) inside a sandboxed worker, and never `sympify` raw strings. | [`sympy/core/sympify.py` L138 @ 1.14.0](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/core/sympify.py#L138); [`parse_expr` docstring](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/sympy_parser.py) |

---

## 3. How existing projects implement checking

### 3.1 STACK (Moodle; Maxima backend)

STACK is the most relevant prior art. It checks line-by-line work, and its checker is open source.

- **Answer tests.** STACK has separate test families:
  - Equivalence: `AlgEquiv`, `SubstEquiv`, `CasEqual`, `SameType`, `SysEquiv`.
  - Form: `FacForm`, `Expanded`, `SingleFrac`, `LowestTerms`, `CompSquare`.
  - Rule-based: `EqualComAss`.
  - Numerical tests, units tests, and equivalence reasoning (`Equiv`, `EquivFirst`).

  Source: [STACK answer tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/).
- **`AlgEquiv`** is described as "simplify(ex1-ex2) = 0". It works on lists, sets, equations, inequalities and matrices:
  - Sets are canonicalised.
  - Equations are moved to one side, and the ratio of the numerators is checked to be a number.
  - Inequalities are converted to real sets.
  - "Equations are never solved", which side-steps decidability.

  Source: [STACK Equivalence tests](https://docs.stack-assessment.org/en/Authoring/Answer_Tests/Equivalence/).
- **The actual algorithm** ([`algebraic_equivalence`, assessment.mac L1084 @ 10d3233](https://github.com/maths/moodle-qtype_stack/blob/10d323311b7f39fb7b092dd10ce75f7d8632f525/stack/maxima/assessment.mac#L1084)) is an ordered chain that can stop early:
  1. Structural equality.
  2. Numeric rejection with integer substitution.
  3. Collect terms and run `radcan_num`.
  4. `factor` the difference, and reject early if no factor can be zero.
  5. `ratsimp`, then `fullratsimp` (keeping only the numerator).
  6. `trigsimp` / `exponentialize`.
  7. `radcan` and `factcomb`.
  8. `sqrtdenest`.

  It also unwraps a shared outer `sqrt` or `abs` before comparing (L1110).
- **`EqualComAss`** checks equality up to commutativity and associativity only. STACK uses it to require a specific first line or a specific intermediate step (`stack_equiv_find_step`).
- **Equivalence reasoning (line by line)** ([equivalence input](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_input.md), [assessment](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_assessment.md), [maths](https://github.com/maths/moodle-qtype_stack/blob/master/doc/en/Specialist_tools/Equivalence_reasoning/Equivalence_reasoning.md)):
  - Each line is checked against the previous one. For expressions it uses algebraic equivalence. For equations, "two equations are equivalent if they have the same solutions".
  - Annotations are ✓ (equivalent expression), ⇔ (equivalent equation), ? (not equivalent), ⇒ / ⇐ (solution-set subset), "(Same roots)", ⇔(ℝ) and "Assume +ve vars".
  - Natural domains are shown per line. A bare expression is treated as `= 0`.
  - The checker can run "as the student types", which is exactly Aequate's use case.
  - The docs say: "there is no concept of 'step size'", and treating any equivalent expression as a legitimate step is "not entirely satisfactory".
  - Scope is "basic single variable polynomials", "very simple inequalities" and "simple simultaneous equations". There is "no support for algebraic manipulations involving logarithms and trig functions although individual examples may work" ([index](https://docs.stack-assessment.org/en/Specialist_tools/Equivalence_reasoning/)).

### 3.2 Numbas

Numbas marks expressions purely numerically at random points, with configurable tolerance and sample count and value generators to dodge singularities. It adds optional *pattern restrictions* to enforce form. For equations it evaluates a boolean and recommends value generators that hit solutions "about half the time", with about 10 points. Source: [Numbas mathematical expression part](https://docs.numbas.org.uk/en/latest/question/parts/mathematical-expression.html). Numbas has no line-by-line step checker. The numeric-plus-pattern split mirrors STACK's equivalence-plus-form split.

### 3.3 SymPy Gamma

SymPy Gamma is "A SymPy version of WolframAlpha" ([repo](https://github.com/sympy/sympy_gamma), last push 2024-04). It **generates** steps rather than checking them. `app/logic/intsteps.py` and `diffsteps.py` print the rule trees from `sympy.integrals.manualintegrate.integral_steps`. Source: [intsteps.py](https://github.com/sympy/sympy_gamma/blob/master/app/logic/intsteps.py). It has no student-work equivalence checker to reuse. The `manualintegrate` rule tree could later help explain calculus steps.

### 3.4 Mathics3

Mathics3 (an open-source Mathematica-language implementation, actively maintained, last push 2026-10-07) implements `PossibleZeroQ`, which "returns True if basic symbolic and numerical methods suggest that expr has value zero". It runs a layered approach on top of SymPy:

1. Arithmetic zero test.
2. SymPy `_iszero`.
3. `ExpandAll`, then `_iszero` again.
4. Numeric `N[]` with an approximate-zero test.
5. `Simplify` as a last resort for non-numeric expressions.

Its doctests include `PossibleZeroQ[Sqrt[x^2] - x]` giving `False`, which reflects complex-domain semantics. Source: [`mathics/builtin/testing_expressions/numerical_properties.py` @ b1ede7f](https://github.com/Mathics3/mathics-core/blob/b1ede7f2aeca4aa4e0246cfb22464faa891938e9/mathics/builtin/testing_expressions/numerical_properties.py#L415-L488). Mathics3 also has no step checker. It is useful as a second example of "cheap symbolic → expand → numeric → simplify" layering.

---

## 4. What Pint adds for units

Tested with Pint 0.26.1 **[run]**:

- **Dimensional consistency.**
  - Adding incompatible quantities raises an error: `1 m + 1 s` raises `DimensionalityError: Cannot convert from 'meter' ([length]) to 'second' ([time])`. Pint also refuses incompatible conversions ([Pint tutorial](https://pint.readthedocs.io/en/stable/getting/tutorial.html)).
  - So a physics line that adds a length to a time can be flagged red even when the numbers work out.
- **Equivalence across units.**
  - `1 km == 1000 m` is `True`.
  - `1 N == 1 kg·m/s²` is `True`.
  - `.to()`, `.to_base_units()` and `.dimensionality` (for example `[mass]·[length]/[time]²`) give canonical forms to compare against ([tutorial](https://pint.readthedocs.io/en/stable/getting/tutorial.html)).
  - `9.81 m/s²` vs `standard_gravity` differs by 0.00335 m/s², so numeric answers need a relative tolerance, just as with numeric sampling.
- **Offset units.** Adding two °C quantities raises `OffsetUnitCalculusError`, because "the addition of quantities with offset units is ambiguous" (10 °C + 100 °C could be 110 °C or 383.15 °C). Setting `autoconvert_offset_to_baseunit` relaxes this. Source: [Pint non-multiplicative units](https://pint.readthedocs.io/en/stable/user/nonmult.html).
- **Not symbolic.** Pint magnitudes are numbers (or NumPy arrays), and the tutorial mentions no SymPy support. In our test `Symbol('v') * ureg.meter` raised `DimensionalityError`. To use Pint for physics *steps*, either substitute numbers, or check units separately: map each symbol to its declared unit, verify dimensional consistency with Pint, and check the algebra with SymPy on the magnitudes. Alternatively, SymPy's own [`sympy.physics.units`](https://docs.sympy.org/latest/modules/physics/units/index.html) keeps units symbolic, but that option was not evaluated here.

---

## Answer

SymPy cannot decide equivalence in general. The tutorial calls `simplify(a - b) == 0` "not infallible", and `Expr.equals` returns `True`, `False` or `None` (undecided). Every practical checker therefore layers several tests and treats "undecided" as a real outcome:

1. **Structural `==`** is fast, but it only proves identity.
2. **Numeric sampling** cheaply and reliably proves *non*-equivalence, and gives a strong probable "yes". It needs relative tolerance and a chosen sampling domain (real vs complex), and it misses removable singularities.
3. **Symbolic simplification of the difference** proves equivalence when it reaches 0. A failure to reach 0 is not a "no", because it misses true identities (for example sin⁶+cos⁶ = 1 − 3sin²cos²), and it can be slow.
4. **Solution-set comparison (`solveset` over an explicit domain)** is the right semantics for *equations, inequalities and systems*. It catches lost or extra roots and division-by-zero errors that expression simplification silently condones. It returns "undecided" when SymPy cannot solve.

Two things are policy decisions, not CAS features: the domain (complex by default; real or positive by choice), and whether to accept non-equivalent but valid steps (squaring ⇒, repeated roots).

Existing projects confirm the layered design:

- STACK runs a numeric reject, then a fixed simplify chain, then solution sets or real sets for equations and inequalities, with ⇔ / ⇒ / domain annotations. Of the projects surveyed, it is the only one that checks line by line.
- Numbas uses only numeric sampling plus form patterns.
- Mathics3 runs symbolic, then expand, then numeric, then simplify.
- SymPy Gamma generates steps rather than checking them.

Pint adds dimensional-consistency and unit-conversion checks on numeric quantities, but it is not symbolic.

## Recommendation for the CAS spike

Spike 4 should run its 20 typical algebra steps (plus a handful of physics-with-units steps) through each strategy below. For each, record the verdict (True/False/None), the latency, and agreement with a hand-labelled ground truth:

1. **S0: Structural.** `==` after parsing with `evaluate=False` and with default evaluation, to measure how often "no change / reorder only" occurs.
2. **S1: `simplify(a - b) == 0`**, plain.
3. **S2: `Expr.equals`** with its tri-state result, including `failing_expression=True` for diagnostics.
4. **S3: Numeric sampling.** About 10 points, relative tolerance (about 1e-9), and both a real-only and a complex sampling domain, so the semantics can be compared. Skip points where the evaluation raises an error or returns non-finite values.
5. **S4: Layered pipeline (STACK-style).**
   1. Structural.
   2. Numeric reject.
   3. Cheap targeted rewrites: `expand`, `cancel`/`together`, `factor`, `trigsimp`, `.rewrite(exp)`, each followed by a zero check.
   4. Full `simplify`.
   5. Otherwise "undecided".
6. **S5: Solution-set comparison** for equation, inequality and system lines. Use `solveset`/`linsolve` over `S.Reals`. Report ⇔, ⇒ or ⇐ (subset), "same roots", or undecided (`ConditionSet`/timeout). Run it alongside STACK's "numerator ratio is constant" test for single equations.
7. **S6: Assumption variants** of S1, S2 and S4. Use default complex symbols, `real=True`, and `positive=True`, to measure how many verdicts flip (e.g. `sqrt(x²)`, log rules).
8. **S7: Domain tracking.** Flag lines whose natural domain changed (a denominator zero introduced or removed) as amber even when they are algebraically equal.
9. **S8: Units.** Use Pint dimensional checks on physics lines, with symbol→unit declarations, in addition to S4 on the magnitudes.

For all strategies, run each check in a worker process with a hard wall-clock timeout (try 200 ms and 1 s budgets), and map a timeout to amber. Build expressions from the recogniser's AST or `parse_latex`, never from `sympify` on raw strings. Cache results by (previous line, current line, domain policy) hash, as `docs/handoff.md` already intends ("incremental and cached").

---

## Appendix: experiment scripts

Run with `docker run --rm -v /tmp/exp:/exp:ro python:3.12-slim sh -c "pip install -q sympy==1.14.0 pint==0.26.1 && python -I /exp/t.py && python -I /exp/u.py && python -I /exp/v.py"`.

<details><summary>t.py (SymPy strategies and pitfalls)</summary>

```python
import time, random
import mpmath
from sympy import *
x, y = symbols('x y')

def show(label, f):
    t = time.time()
    try:
        r = f()
    except Exception as e:
        r = f"{type(e).__name__}: {e}"
    print(f"{label:55s} -> {r!r}  ({time.time()-t:.3f}s)")

show("(x+1)**2 == x**2+2*x+1", lambda: (x+1)**2 == x**2+2*x+1)
show("simplify((x+1)**2-(x**2+2*x+1))", lambda: simplify((x+1)**2-(x**2+2*x+1)))
show("((x+1)**2).equals(x**2+2x+1)", lambda: ((x+1)**2).equals(x**2+2*x+1))
show("cos^2-sin^2 .equals(cos2x)", lambda: (cos(x)**2-sin(x)**2).equals(cos(2*x)))
show("simplify((x**2-1)/(x-1) - (x+1))", lambda: simplify((x**2-1)/(x-1) - (x+1)))
show("((x**2-1)/(x-1)).subs(x,1)", lambda: ((x**2-1)/(x-1)).subs(x, 1))
show("x/x", lambda: x/x)
show("simplify(sqrt(x**2)-x)", lambda: simplify(sqrt(x**2)-x))
p = Symbol('p', positive=True)
show("simplify(sqrt(p**2)-p), p positive", lambda: simplify(sqrt(p**2)-p))
show("sqrt(x**2).equals(x)", lambda: sqrt(x**2).equals(x))
show("simplify(log(x*y)-log(x)-log(y))", lambda: simplify(log(x*y)-log(x)-log(y)))
q, r = symbols('q r', positive=True)
show("simplify(log(q*r)-log(q)-log(r)), positive", lambda: simplify(log(q*r)-log(q)-log(r)))
show("simplify(log(exp(x))-x)", lambda: simplify(log(exp(x))-x))
show("Eq(2*x,4)==Eq(x,2)", lambda: Eq(2*x, 4) == Eq(x, 2))
show("simplify(Eq(2*x+2,6))", lambda: simplify(Eq(2*x+2, 6)))
show("solveset(Eq(x**2,x),x,Reals)", lambda: solveset(Eq(x**2, x), x, S.Reals))
show("solveset(Eq(x,1),x,Reals)", lambda: solveset(Eq(x, 1), x, S.Reals))
show("solveset(Eq((x**2-1)/(x-1),2),x,Reals)", lambda: solveset(Eq((x**2-1)/(x-1), 2), x, S.Reals))
show("solve system", lambda: solve([Eq(x+y, 3), Eq(x-y, 1)], [x, y], dict=True))
show("linsolve system", lambda: linsolve([x+y-3, x-y-1], [x, y]))
show("solveset(2*x<4,x,Reals)", lambda: solveset(2*x < 4, x, S.Reals))
show("wrong sign flip", lambda: solveset(-2*x < -4, x, S.Reals) == solveset(x < 2, x, S.Reals))
show("reduce_inequalities(x**2<4,x)", lambda: reduce_inequalities(x**2 < 4, x))
show("(2*x<4)==(x<2)", lambda: (2*x < 4) == (x < 2))
show("x+0.5 == x+Rational(1,2)", lambda: x+0.5 == x+Rational(1, 2))
show("sympify('2*x+3')==sympify('3+2*x')", lambda: sympify('2*x+3') == sympify('3+2*x'))
show("parse_expr('2+3',evaluate=False)==5", lambda: parse_expr('2+3', evaluate=False) == Integer(5))
show("x*(x+1) == x**2+x", lambda: x*(x+1) == x**2+x)
# numeric sampling helpers: complex points / real points, absolute tolerance 1e-9
```
</details>

<details><summary>v.py (tolerance, hard identities, timing)</summary>

```python
import time, mpmath
from sympy import *
x = symbols('x')
a = sin(x)**8 + cos(x)**8
b = (35 + 28*cos(4*x) + cos(8*x))/64
f = lambdify(x, a - b, 'mpmath'); g = lambdify(x, b, 'mpmath')
for v in [mpmath.mpf(0.3), mpmath.mpc(1.1, 2.7)]:
    print(v, abs(f(v)), abs(f(v))/abs(g(v)))      # abs 1.9e-9 vs rel 1e-16 at the complex point
print(a.equals(b))                                 # None, ~0.5 s
print(trigsimp(a - b))                             # non-zero residue
print(simplify((a - b).rewrite(exp)))              # 0
e = ((x+1)**12 - expand((x+1)**12))/(x**2+1) + sin(x)**6 + cos(x)**6 - 1 + 3*sin(x)**2*cos(x)**2
print(simplify(e))                                 # sin(x)**6 + cos(x)**6 - 3*cos(4*x)/8 - 5/8  (not 0)
```
</details>

<details><summary>u.py (Pint)</summary>

```python
import pint
u = pint.UnitRegistry(); Q = u.Quantity
Q(1,'km') == Q(1000,'m')          # True
Q(1,'m') + Q(1,'s')               # DimensionalityError
Q(1,'N') == Q(1,'kg*m/s**2')      # True
Q(1,'J').to_base_units()          # 1 kg m^2/s^2
Q(10,'degC') + Q(5,'degC')        # OffsetUnitCalculusError
__import__('sympy').Symbol('v') * u.meter   # DimensionalityError (not symbolic)
```
</details>

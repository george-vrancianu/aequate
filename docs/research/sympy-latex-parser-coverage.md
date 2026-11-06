# SymPy LaTeX parser coverage: ANTLR vs Lark, loud vs silent failures

**Question.** Which LaTeX constructs do `parse_latex(..., backend="antlr")`, `backend="lark"` and `parse_latex_lark` support? Where does each one fail **loudly** (raises) and where **silently** (returns a wrong expression)? What has to sit between the recognizer and SymPy?

**Scope.** This doc covers parsing only. Equivalence strategies are in `research/sympy-equivalence:docs/research/sympy-equivalence.md`, and caching and Modal are in [recognition-compute-split.md](recognition-compute-split.md).

**Tags.** **[run]** means my own test run (setup in §2). *(assessment)* means my reasoning. **Unverified** means not confirmed.

---

## 1. Conclusion

**Use ANTLR with `strict=True` as the primary parser, wrapped in a normalizer and two post-parse guards. Run Lark as a cross-checking second opinion: if both parse and disagree, reject. Do not use Lark alone on SymPy 1.14.0.** *(assessment, based on the results below)*

This revises the earlier plan in [recognition-compute-split.md §3](recognition-compute-split.md), which picked `backend="lark"` because it is loud on `x -`.

- **Lark 1.14.0 is loud, but it rejects or garbles too much school math.** **[run]**
  - It rejects `\pi`, `\sigma`, every uppercase Greek letter, `x_{12}`, `x^2y`, `\sqrt x`, `:`, `[x]`, chained inequalities and `\int_0^{\pi}`. `\pi` is simply absent from `greek_symbols.lark` ([grammar](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/grammar/greek_symbols.lark)).
  - For everyday input it returns a raw `lark.Tree('_ambig', …)` rather than raising. Examples: `\sin x + 1`, `x(x+1)`, `f'(x)`, `\sin x^2` and `\sum_{i=1}^n i^2 + 1`.
  - It is also silently wrong in some cases: `1\,000` gives `0`, `2 3` gives `6`, and `\sin(x) y` gives `sin(x*y)`.
- **ANTLR non-strict is the dangerous mode.** It drops trailing input (`x -`, `2x+` and `x^{2` all return a prefix) and turns unknown commands into products of symbols (`\pm` becomes `pm`, `\operatorname{tg} x` becomes `operatorname*x*g*t`). **[run]**
- **`strict=True` fixes the trailing drops,** but it has its own bug: it also rejects valid `\left( … \right)`. Stripping `\left` and `\right` first avoids that.
- **What strict mode still misses is catchable.**
  - A symbol-name whitelist plus "no undeclared functions" catches `pm`, `text`, `mathrm`, `dcdot` and `x(x+1)`-as-a-call.
  - A short list of pre-parse rejection rules catches function-argument absorption (`\cos x \cdot \sin x` becomes `cos(x*sin(x))`), `x^2_1` becoming `x**2`, `2,500` becoming `2500`, and `2\frac12` becoming `1`.
  - Cross-checking against Lark catches most of the rest.

  With all of these in place, none of the 200+ test inputs produced a known-wrong accepted result **[run]**. The prototype is in the appendix.
- **Lark on master is much better and is meant to replace ANTLR.** The docs say "intended to eventually completely replace the ANTLR-based parser" ([docs](https://docs.sympy.org/latest/modules/parsing.html)), and PR [#25790](https://github.com/sympy/sympy/pull/25790) "Removed the ANTLR parser and made Lark the default" is open. Lark on master (`f8531d8`, after PR [#30571](https://github.com/sympy/sympy/pull/30571), merged 2026-10-21) fixes `\pi`, uppercase Greek, `x_{12}`, chains, `\operatorname{tg}`, `\frac{dy}{dx}` and `\sin x + 1` **[run]**. It still returns `_ambig` for `x(x+1)`, `f(x)`, `f'(x)` and `\sin x^2`. *(assessment)* Re-run the matrix when 1.15 ships and consider switching primaries then. The parser backend and SymPy version already sit in the parse cache key.

---

## 2. Setup

- **Versions:** SymPy **1.14.0** (latest on PyPI on 2026-10-23), lark **1.3.1**, antlr4-python3-runtime **4.11.1**, Python **3.14.4**. Venv in `/tmp/sympy-latex-test/`, scripts run with `python -I`. A second venv with SymPy master `f8531d83d716` (reports `1.15.0.dev`) is used for the "master" notes.
- **ANTLR runtime pin:** ANTLR requires runtime **4.11**. The docs say `antlr4-python3-runtime==4.11` ([docs](https://docs.sympy.org/latest/modules/parsing.html)), and the code raises `ImportError` unless `version('antlr4-python3-runtime').startswith('4.11')` ([`_parse_latex_antlr.py`](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/_parse_latex_antlr.py)). This pin clashes with other packages on 4.13 ([#27026](https://github.com/sympy/sympy/issues/27026), open). Keep the CAS worker in its own image.
- **Parser configuration:** Lark is built with `parser="earley"` and `ambiguity="explicit"`, and the transformer has no `_ambig` handler. That is why ambiguous input comes back as a `Tree` instead of an exception ([`lark/latex_parser.py`](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/latex_parser.py)).
- **Official limits:** both parsers are "experimental" ([docs](https://docs.sympy.org/latest/modules/parsing.html)). The docs list matrices and derivatives as Lark limitations or features, but the 1.14.0 grammar does the opposite. Matrices parse, and the `derivative` rule is commented out, although `\frac{d}{dx}` works through `adjacent_expressions` ([latex.lark](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/grammar/latex.lark)). **[run]** Trust the grammar over the docs.

---

## 3. Coverage table (SymPy 1.14.0) **[run]**

**Legend.** ok means the result is correct. **ERR** means it raises; ANTLR raises `LaTeXParsingError`, Lark raises `lark.exceptions.UnexpectedCharacters` or `UnexpectedEOF` unless noted. **SILENT** means a wrong result with no error. **AMBIG** means Lark returned `Tree('_ambig', [...])` instead of an expression. "strict" is shown only when it differs from ANTLR non-strict.

### Arithmetic, powers, roots, Greek

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `\frac{1}{2}`, `\frac12`, nested `\frac`, `\dfrac`, `\tfrac` | ok | ok | ok |
| `2\frac{1}{2}` (mixed number) | **SILENT** `2/2` | **SILENT** `1` | same |
| `x^2`, `x^{10}`, `x_1^2`, `x^{-1}`, `x^{\frac12}` | ok | ok | ok |
| `x^10` | ok `x**10` (not TeX's x¹0) | ok `x**10` | ok |
| `x^2_1` | **SILENT** `x**2` (subscript dropped, strict too) | ERR | ok `x_1**2` |
| `x_{12}` | ok | ERR (one char only) | ok |
| `V_{AB}` | **SILENT** `Symbol('V_{A*B}')` ([#19662](https://github.com/sympy/sympy/issues/19662)) | ok `V_{AB}` | ok |
| `x_{i,j}` | ERR | ERR | ok |
| `x^2y` | ok | ERR | ok |
| `x^-1` | **SILENT** `x` (strict: ERR) | ERR | ERR |
| `x^2^3` (invalid TeX) | **SILENT** `(x**2)**3` | **SILENT** `x**8` | same |
| `\sqrt{x}`, `\sqrt[3]{x}`, `\sqrt[n]{x}` | ok | ok | ok |
| `\sqrt x` | ERR | ERR | ok |
| `\alpha`, `\theta_1`, `\lambda` | ok | ok | ok |
| `\pi`, `\sigma`, `\Delta x`, `\Gamma` | ok, but `\pi` is `Symbol('pi')`, not `sympy.pi` | ERR | ok, `\pi` gives `sympy.pi` |
| `\varphi` | `varphi` | `phi` (folded) | `phi` |
| `e^{x}`, `i^2` | `Symbol('e')**x`, `Symbol('i')` | same | same |
| `\mathrm{e}^x` | **SILENT** `e**x*mathrm` | ERR | ok `exp(x)` |

### Operators, implicit multiplication, ±

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `\cdot`, `\times`, `\div`, `/` | ok (unevaluated `2*3`) | ok (evaluated `6`) | ok |
| `6:3`, `a:b` | ok `6/3` | ERR | ERR |
| `6\div 2\cdot 3` | ok `(6/2)*3` | ok `9` | ok |
| `2x`, `xy`, `2(x+1)`, `(x+1)(x-1)`, `x\sin x` | ok | ok | ok |
| `x(x+1)`, `a(b+c)` | **SILENT** `Function('x')(x+1)` | AMBIG | AMBIG |
| `f(x)` | ok (function call) | AMBIG | AMBIG |
| `\sin x\cos x` | ok | AMBIG | ok |
| `\sin x \cdot 2` | **SILENT** `sin(2*x)` | AMBIG | ok `2*sin(x)` |
| `\cos x \cdot \sin x` | **SILENT** `cos(x*sin(x))` | AMBIG | ok |
| `\ln x \cdot y`, `\sin x / 2` | **SILENT** `log(x*y)`, `sin(x/2)` | AMBIG | ok |
| `\log_2{4} / (x+1)` | **SILENT** `log(4/(x+1), 2)` ([#28575](https://github.com/sympy/sympy/issues/28575)) | AMBIG | ok |
| `\sin(x) y` | ok | **SILENT** `sin(x*y)` | ok |
| `d\cdot 2` | **SILENT** `Symbol('dcdot')*2` ([#26220](https://github.com/sympy/sympy/issues/26220)) | ok | ok |
| `x d y`, `b d e` | **SILENT** `dy*x`, `b*de` (lexer `DIFFERENTIAL`) | **SILENT** `x*(d, y)` (tuple in `Mul`) | ok |
| `2 3` | **SILENT** `23` | **SILENT** `6` | same |
| `x \pm 2`, `\frac{-b\pm\sqrt{…}}{2a}` | **SILENT** `Symbol('pm')*2` | ERR | ERR `Unknown command \pm` |
| `x\mp 1` | **SILENT** `x*mp*1` | ERR | ERR |
| `x++1`, `x+-1`, `x--1` | ok | ERR | ok |

### Relations

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `=`, `\neq`, `<`, `>`, `\leq`, `\le`, `\geq`, `\leqslant` | ok | ok | ok |
| `x\ne 2` | **SILENT** `x*ne*2` (only `\neq` is a token) | ok `Ne` | ok |
| `1<x<2`, `1\le x\le 2` | ERR `TypeError` ([#21307](https://github.com/sympy/sympy/issues/21307)) | ERR | ok `And(...)` |
| `a=b=c` | **SILENT** `Eq(Eq(a,b),c)` | ERR | ok `Eq(a,b) & Eq(b,c)` |
| `x \approx 2` | **SILENT** `x*approx*2` | ERR | ERR |
| `x\Rightarrow y` | **SILENT** `x` (strict: ERR) | ERR | ERR |
| `x &= 2` | ok `Eq(x,2)` (`&` is absorbed into `EQUAL`) | ERR | ERR |

### Functions

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `\sin x`, `\sin(x)`, `\sin^2 x`, `\sin^{-1}x`, `\sin 2x`, `\arcsin`, `\tan`, `\cot` | ok | ok | ok |
| `\sin x + 1` | ok | AMBIG ([#28404](https://github.com/sympy/sympy/issues/28404)) | ok |
| `\sin x^2` | `sin(x**2)` | AMBIG | AMBIG |
| `\tg x` | **SILENT** `Symbol('tg')*x` | ERR | ERR |
| `\operatorname{tg} x`, `\mathrm{tg}\,x` | **SILENT** `operatorname*x*g*t` | ERR | `Function('tg')(x)` (undefined function); `\mathrm{tg}`: ERR |
| `\log_2 8`, `\log_{10}x`, `\log_b a` | ok `log(8, 2)` | ok (evaluated: `3`) | ok |
| `\log x`, `\ln x` | ok, natural log | ok, natural log | ok |
| `\lg x` | ok, base 10 | ok, base 10 | ok |
| `\exp(x)` | ok | ok | ok |

*(assessment)* Many school curricula read `\log x` as base 10. Both parsers read it as natural log, so this belongs in locale policy.

### Calculus

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `\int x\,dx`, `\int_0^1 x^2\,dx`, `\int\frac{dx}{x}` | ok | ok | ok |
| `\int_0^{\pi}\sin x\,dx` | ok (`pi` as a Symbol) | ERR (`\pi`) | ok |
| `\int x\,\mathrm{d}x` | **SILENT** `Integral(x*mathrm*d*x, x)` ([#27978](https://github.com/sympy/sympy/issues/27978)) | ok | ok |
| `\int_0^1 x`, `\int x` (no `dx`) | accepted `Integral(x, x)` | ERR | ERR |
| `\iint` | **SILENT** `iint*f*dx*dy` | ERR | ERR |
| `\sum_{i=1}^{n} i`, `\prod_{k=1}^n k` | ok | ok | ok |
| `\sum_{i=1}^{n} i^2 + 1` | ok `Sum(i**2)+1` | AMBIG | AMBIG ([#30486](https://github.com/sympy/sympy/issues/30486)) |
| `\lim_{x\to 0}`, `\to\infty`, `\to 0^+` | ok | ok | ok |
| `\frac{d}{dx} x^2` | ok `Derivative` | ok | ok |
| `\frac{dy}{dx}` | ok | **returns Python tuple** `('derivative', x)` | ok |
| `\frac{d^2}{dx^2}x^3` | **SILENT** `x**3*d**2/dx**2` | ERR `VisitError` | ok |
| `\frac{\mathrm{d}}{\mathrm{d}x}x^2` | **SILENT** garbage product | ERR | ERR |
| `\frac{\partial f}{\partial x}` | ok `Derivative(f, x)` | ERR | ERR |
| `f'(x)`, `f''(x)` | ok `Function("f'")(x)` | AMBIG | AMBIG |
| `y'` | `Symbol("y'")` | same | same |

### Delimiters and numbers

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `\left( x+1 \right)` | ok (**strict: ERR**, see §4) | ok | ok |
| `\left| x \right|` | ERR | ok | ok |
| `\lvert x \rvert` | **SILENT** `lvert*rvert*x` | ERR | ERR |
| `\|x\|`, `\|x-1\|+\|x+1\|`, `\lfloor x\rfloor` | ok | ok | ok |
| `[x+1]`, `\{x+1\}`, `\left[x\right]` | ok (strict: ERR for `\left[`) | ERR ([#28943](https://github.com/sympy/sympy/issues/28943)) | ok |
| `\infty`, `-\infty`, `x+\infty` | ok `oo` | ok | ok |
| `3.5`, `2.5x` | ok, `Float` | ok, `Float` | ok |
| `.5` / `3.` | ERR / ERR | ERR / ok | ok / ok |
| `3{,}5` | **SILENT** `3` (strict: ERR) | ERR | ERR |
| `3,5` | **SILENT** `3` (strict: ERR) | ERR | ERR |
| `1,000`, `2,500` | **SILENT for decimal-comma locales** `1000`, `2500` (grammar: `DIGIT+ (',' DIGIT DIGIT DIGIT)*`) | ERR | ERR |
| `1\,000` | `1000` | **SILENT** `0` (`1·000`) | same |
| `f(1,2)` | ok, two arguments | ok | ok |

### Environments, text, units, misc

| Input | ANTLR | Lark 1.14 | Lark master |
|---|---|---|---|
| `pmatrix`, `bmatrix` | ERR | ok `Matrix` (not a `Basic`) | ok |
| `vmatrix` | ERR | ok, determinant `-2` | ok |
| `\begin{cases}`, `\begin{aligned}` | ERR ([#28245](https://github.com/sympy/sympy/issues/28245)) | ERR | ERR ("not currently supported") |
| `5\text{ m}`, `\text{hello}` | **SILENT** `5*m*text`, `text*h*e*l*l*o` | ERR | ERR |
| `v=10\,\mathrm{m/s}` | **SILENT** `Eq(v, 10*mathrm*m/s)` | ERR | ERR |
| `9.8\,\frac{m}{s^2}` | parses as symbols `m`, `s` | same | same |
| `5^\circ` | **SILENT** `5**circ` | ERR | ok `pi/36` |
| `50\%` | ERR | ERR | ERR |
| `n!`, `5!`, `(n+1)!` | ok | ok (`5!` gives `120`) | ok |
| `\binom{n}{k}`, `\binom{5}{2}` | ok | ok | ok |
| `\binom52` | ERR | ok | ok |
| `{n \choose k}` | **SILENT** `n*choose*k` | ERR | ERR |
| `x \in \mathbb{R}` | **SILENT** `x*in*mathbb*R` | ERR | ok `Contains(x, Reals)` |

### Incomplete or garbled input (recognizer mid-writing)

| Input | ANTLR non-strict | ANTLR strict | Lark 1.14 |
|---|---|---|---|
| `x -`, `x+`, `2x+`, `x^`, `x^{2`, `x +\,`, `x\cdot` | **SILENT** prefix (`x`, `2*x`) | ERR | ERR |
| `x}`, `x+1)`, `1 + 2 )`, `x)(` | **SILENT** prefix | ERR | ERR |
| `x \cdot \cdot y` | **SILENT** `x` | ERR | ERR |
| `x=1, y=2` | **SILENT** `Eq(x, 1)` | ERR | ERR |
| `\frac{1}{`, `\frac{1}`, `\frac{x+1`, `(x+1`, `\sqrt{x`, `{x`, `\left( x`, `\|x`, `2x=`, `=3`, `x = = 2`, `\sin`, `\frac{}{2}`, empty | ERR | ERR | ERR |
| `x \foo y` (unknown command) | **SILENT** `x*foo*y` | **SILENT** | ERR (master: `Unknown command \foo`) |
| `((((…x…))))`, 100 deep | ERR `RecursionError` ([#30000](https://github.com/sympy/sympy/issues/30000)) | same | ok (0.5 s) |

### Other observations **[run]**

- **Evaluation.**
  - ANTLR builds everything with `evaluate=False` ([source](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/_parse_latex_antlr.py)). So `parse_latex("x+1") == x+1` is **False**, while `.doit()` or `simplify(a-b)==0` work.
  - Lark evaluates, following PR [#25515](https://github.com/sympy/sympy/pull/25515). As a result, `\frac{x}{0}` becomes `zoo*x`, `0^0` becomes `1` and `\sqrt{-1}` becomes `I` before any check runs.
- **Lark symbol names.** Lark symbol names are `lark.Token`, not `str`. They compare equal to `Symbol('x')`, but `srepr()` emits `Symbol(Token('SYMBOL', 'x'))`, and `sympify(srepr(...))` then fails with `TypeError: name should be a string, not Token`. This breaks the `srepr` cache value planned in [recognition-compute-split.md §2](recognition-compute-split.md). The fix is `expr.xreplace({s: Symbol(str(s.name)) for s in expr.free_symbols})`, which round-trips.
- **Constants.** ANTLR gives `\pi` as `Symbol('pi')`, and `e` as `Symbol('e')` in both parsers ([#20306](https://github.com/sympy/sympy/issues/20306), [#15309](https://github.com/sympy/sympy/issues/15309), both open). `\sin\pi = 0` will not be decided unless these are substituted.
- **Speed.** A typical line takes about 19 ms with ANTLR and 140 ms with Lark (Earley). A 24-term polynomial takes 87 ms and 425 ms. Running both is affordable at one line per pen-up. *(assessment)*
- **Fixed hang.** The Lark hang on `24! \times 24!` ([#27411](https://github.com/sympy/sympy/issues/27411)) is fixed in 1.14.0 (22 ms).

---

## 4. Loud vs silent: failure classes

| Class | ANTLR | Lark 1.14 | Guard that catches it **[run]** |
|---|---|---|---|
| Trailing input dropped | silent; the docs warn about this ([docs](https://docs.sympy.org/latest/modules/parsing.html)) | loud | `strict=True` |
| Unknown `\command` becomes a symbol (`\pm`, `\text`, `\mathrm`, `\tg`, `\approx`, `\ne`, `\circ`, `\choose`) | silent | loud | symbol-name whitelist |
| `d` lexer token (`dcdot`, `dy`, `de`, `dx` as one symbol) | silent | partly silent (tuples) | symbol-name whitelist |
| `x(…)` read as a function call | silent | AMBIG | reject `AppliedUndef` unless declared |
| Unparenthesized function argument swallows `\cdot` or `/` | silent | AMBIG (master: correct) | pre-parse reject, plus Lark disagreement on master |
| Dropped sub/superscript (`x^2_1`, `x^-1`) | silent | loud | rewrite `x^a_b` to `x_b^a`; reject `^-` |
| Number grammar (`2,500` read as 2500, `3,5` read as 3, `2 3` read as 23) | silent | loud, or silent for `2 3` and `1\,000` | normalizer number rules |
| Chained relations | `a=b=c` silent, `<` chain loud | loud | split chains before parsing |
| Constants (`\pi`, `e`) left as symbols | silent | silent (`e`) | `xreplace` policy |
| Ambiguity | n/a | returns a `Tree`, so check `isinstance(r, sympy.Basic)` | treat as a reject unless ANTLR's reading is one of the alternatives |

**`strict=True` has a bug of its own.** It rejects any input whose first or last character belongs to a skipped token, such as `\left( x+1 \right)`, `\left[x\right]` and `x\,`. The check is `relation.start.start != 0 or relation.stop.stop != len(s) - 1`, and skipped tokens (`CMD_LEFT`, `CMD_RIGHT`, `THINSPACE`) are not part of the relation's span ([source](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/_parse_latex_antlr.py), [LaTeX.g4](https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/LaTeX.g4)). **[run]** Strip `\left` and `\right` and any trailing spacing before calling strict mode.

### Guards for silent drops, tested on every ANTLR-accepted input **[run]**

- **Re-serializing with `sympy.latex()` and comparing leaf counts does not work.** Comparing the multiset of variable letters and Greek names between input and `latex(expr)` produced false positives on correct parses: `\theta_1`, `\sin^{-1}x` (printed as `\operatorname{asin}`), `\exp`, `\log_b a` and `\partial`. It also missed most trailing drops (`x -` has the same letters as `x`) and `x^2_1`. Counting digits is worse, because the printer reorders and folds numbers. Don't use it.
- **These do work, combined:**
  1. ANTLR `strict=True` after stripping `\left`, `\right` and trailing spacing. This caught every trailing-drop case and had no false positives on valid input.
  2. A symbol-name whitelist: single Latin letter or known Greek name, optional `_{alnum}`, optional primes. Plus rejection of any undefined function that hasn't been declared. This caught `pm`, `ne`, `text`, `mathrm`, `operatorname`, `circ`, `choose`, `lvert`, `iint`, `foo`, `dcdot`, `dy`, `de` and `x(x+1)`. Its only false positive was `\mathit{abc}`, which is a policy choice.
  3. Cross-checking with Lark: when both parse, require `p == q`, or `p.doit() == q.doit()`, or `simplify(nsimplify(p) - nsimplify(q)) == 0`. On the residual silent cases this caught `x^2_1`, `\sin x\cdot 2`, `\cos x\cdot\sin x`, `\ln x\cdot y`, `\sin x/2`, `\log_2 4/(x+1)`, `2 3`, `1\,000`, `x^2^3` and `x(x+1)`. It did **not** catch `2\frac12` or `e`, because both backends agree and both are wrong.

  On 1.14, Lark's AMBIG result for `\sin x\cdot 2` *includes* ANTLR's `sin(2x)` reading, so the cross-check alone accepts it. The pre-parse rule is still needed.

---

## 5. Recommended normalization layer

This is a pipeline that runs between the recognizer and SymPy *(assessment; rules tested in the appendix prototype)*. The output is either one or more `Expr`/`Relational` objects or a **Reject**, which the tutor sees as "can't check this step".

**Order of steps:** split the system, then split chains, then rewrite and reject, then branch on ±, then ANTLR strict, then the name guard, then constants, then the Lark cross-check.

### Rewrite

| Rule | Why |
|---|---|
| Strip `\left`, `\right`; map `\lvert`/`\rvert` to `\|`; strip trailing `\,`, `\;`, `\quad` | strict-mode bug; neither parser knows `\lvert` |
| `3{,}5` → `3.5` always. `3,5` → `3.5` only when the board locale uses a decimal comma | ANTLR reads `3,5` as `3` and `2,500` as `2500` |
| `x_{1,2}` → `x_{12}` before the comma rule | the root-index notation of the quadratic formula is not a decimal |
| `.5` → `0.5` | ANTLR rejects `.5` |
| `\tg`, `\operatorname{tg}`, `\mathrm{tg}` → `\tan`; `ctg`/`cotg` → `\cot`; `arctg` → `\arctan`; `\operatorname{sin}` → `\sin` | locale notation in [handoff §2](../handoff.md); ANTLR silently mangles these |
| `:` → `\div` | ANTLR accepts `:`, Lark has no rule for it |
| `\ne` → `\neq` | ANTLR only has a token for `\neq` |
| `\varphi`, `\varepsilon`, `\vartheta` → base letter | Lark folds them and ANTLR does not, which otherwise breaks the cross-check |
| `\mathrm{d}` → `d`, `\mathrm{e}` → `e` | [#23551](https://github.com/sympy/sympy/issues/23551), [#27978](https://github.com/sympy/sympy/issues/27978) |
| `\sqrt x` → `\sqrt{x}`; `\binom52` → `\binom{5}{2}` | brace-less arguments |
| `x^a_b` → `x_b^a` | ANTLR drops the trailing subscript |
| `50\%` → `(50/100)`; `30^\circ` → `(30\cdot\frac{\pi}{180})` | neither parser handles `\%`; ANTLR reads `\circ` as a symbol |
| `\pm` / `\mp` → two branches (`+`/`-` and `-`/`+`) | there is no ± in SymPy. The step is right if each branch maps to a branch of the previous line, a rule for the checker to define. |
| `\begin{cases|aligned|align|gathered}` and top-level `\\` → list of lines; drop `&` | neither parser handles these environments |
| `a<b\le c`, `a=b=c` → `[a<b, b\le c]` | ANTLR raises `TypeError` or returns `Eq(Eq(a, b), c)` |
| After parsing: `Symbol('pi')` → `pi`; `Symbol('e')` → `E` (per-problem override if `e` is a variable); `i` → `I` only in complex-number problems | [#20306](https://github.com/sympy/sympy/issues/20306) |
| After parsing: Lark `Token` names → `str` | needed for `srepr` round-trips and the cache |
| Units: `\text{…}`, `\mathrm{m/s}` and letter units after a number are split off and sent to Pint; SymPy gets the magnitude | ANTLR turns these into symbol products |

### Reject (show "can't check this step")

- Any parse exception, from either backend, after the rewrites.
- A Lark result that is not a `sympy.Basic`, unless Lark failed outright, which is common in 1.14 and carries no veto.
- A Lark `_ambig` whose alternatives don't include ANTLR's reading, or a disagreement between the backends.
- Symbols outside the whitelist, and undeclared `f(x)`/`x(x+1)` calls. Declared function names per problem (`f`, `g`) are allowed.
- An unparenthesized function argument followed by `\cdot`, `\times`, `\div` or `/`, for example `\sin x\cdot 2` or `\cos x\cdot\sin x`.
- A digit directly before a numeric `\frac`, which could be a mixed number: `2\frac12`.
- Digit groups separated by spaces (`2 3`, `1\,000`); two separators in one number (`1,000.5`); a decimal comma inside parentheses (`f(1,2)` is ambiguous in decimal-comma locales).
- A double superscript `x^2^3`; an unbraced negative exponent `x^-1`.
- `\int` without a differential; `\iint`; partial derivatives other than the simple `\frac{\partial f}{\partial x}`.
- Matrices; `\approx`, `\Rightarrow`, `\in`; `{n \choose k}`.
- Empty input.

Applied to the 223 inputs, the prototype gave 162 accepted, 30 rejected by rule and 31 that raised. Every accepted result I checked by hand is correct. **[run]** The prototype's regexes are crude. For example, the function-argument rule doesn't look at `\sin^2 x \cdot 3`. A production version should tokenize rather than use regexes. *(assessment)*

---

## 6. Gaps that need a custom parser or a fallback

1. **Function vs multiplication, `x(x+1)` and `a(b+c)`.** This is a design question upstream with no fix ([#19527](https://github.com/sympy/sympy/issues/19527), [#25482](https://github.com/sympy/sympy/issues/25482)). The recognizer or problem metadata has to say which letters are functions. With that, the Aequate layer can resolve it by rewriting `x(` to `x\cdot(` for non-function letters.
2. **Systems, `cases` and `aligned`.** Neither backend parses them ([#28245](https://github.com/sympy/sympy/issues/28245)). Split them in the normalizer, then check the system with `solve` or `linsolve`.
3. **± and solution sets** (`x_{1,2}=…`, `x\in\{1,2\}`). There is no parser support. Needs a custom branch or set representation.
4. **Units.** Neither parser understands units. Needs a custom tokenizer that splits `number ⋅ unit` before SymPy and sends the unit to Pint.
5. **Mixed numbers, percent of a quantity, degrees on variables, `\log` base convention.** These are pedagogy and locale questions that parsers can't answer. Make them per-locale and per-problem settings.
6. **Higher-order and partial derivatives, multiple integrals.** Partly unsupported (documented Lark limitation, and **[run]** for ANTLR). Out of scope for school algebra; reject. *(assessment)*
7. **Long-term:** when SymPy 1.15 ships, re-run `matrix.py`. If Lark master's behaviour holds (`\pi`, Greek, chains and `\operatorname` fixed), consider making Lark primary with ANTLR strict as the cross-check, since ANTLR's removal is proposed ([#25790](https://github.com/sympy/sympy/pull/25790)).

---

## 7. Relevant SymPy issues

| Issue | State | Relevance |
|---|---|---|
| [#30486](https://github.com/sympy/sympy/issues/30486) Lark: silent `_ambig` trees, wrong results, rejected inputs | open | Umbrella checklist that matches §3, based on about 190 inputs (the issue says it was AI-generated). Partly fixed by [#30571](https://github.com/sympy/sympy/pull/30571), merged 2026-10-21 and unreleased. |
| [#25482](https://github.com/sympy/sympy/issues/25482) Ambiguous expressions in the LaTeX parser | open | The design behind `_ambig` |
| [#28404](https://github.com/sympy/sympy/issues/28404) `\sin{x} + 5` ambiguity | open | Fixed on master **[run]** |
| [#19527](https://github.com/sympy/sympy/issues/19527) How to parse `a(b+c)` | open | function vs product |
| [#26220](https://github.com/sympy/sympy/issues/26220) `d \cdot 2` gives `dcdot*2` | open | ANTLR `DIFFERENTIAL` lexer token |
| [#28575](https://github.com/sympy/sympy/issues/28575) division boundary after a function | open; fix PR [#28797](https://github.com/sympy/sympy/pull/28797) open | `\log_2 4/(x+1)` |
| [#21307](https://github.com/sympy/sympy/issues/21307) inequality chains | open | ANTLR `TypeError` |
| [#20306](https://github.com/sympy/sympy/issues/20306), [#15309](https://github.com/sympy/sympy/issues/15309) `e`/`\pi` as free symbols | open | constants policy |
| [#19662](https://github.com/sympy/sympy/issues/19662), [#24290](https://github.com/sympy/sympy/issues/24290) subscripts | open | Confirmed in 1.14: `V_{AB}` gives `Symbol('V_{A*B}')`, which the name whitelist catches **[run]**. #24290 (Greek with indices) **Unverified**. |
| [#22494](https://github.com/sympy/sympy/issues/22494) wrong result with `\left(`/`\right)` in exponents | open | another reason to strip `\left`/`\right` |
| [#27978](https://github.com/sympy/sympy/issues/27978), [#23551](https://github.com/sympy/sympy/issues/23551) `\mathrm{d}` | open | ANTLR |
| [#28245](https://github.com/sympy/sympy/issues/28245) `\begin{cases}` | open | systems |
| [#30000](https://github.com/sympy/sympy/issues/30000) ANTLR `RecursionError` on deep nesting | open; fix PR [#30145](https://github.com/sympy/sympy/pull/30145) open | catch `RecursionError` too |
| [#27026](https://github.com/sympy/sympy/issues/27026) bound to antlr4 4.11 | open | dependency pin |
| [#29467](https://github.com/sympy/sympy/issues/29467), [#29488](https://github.com/sympy/sympy/issues/29488) Lark: `\negthinspace` read as `\ne`, `\left` read as `\le` | closed 2026-04 (fixes merged after 1.14.0) | **Unverified** whether 1.14.0 is affected. My `\left(` tests parsed correctly in 1.14.0. |
| [#24116](https://github.com/sympy/sympy/issues/24116) should not use `evaluate=False` by default | closed via [#25515](https://github.com/sympy/sympy/pull/25515) (Lark only) | ANTLR still unevaluated |
| [#25790](https://github.com/sympy/sympy/pull/25790) remove ANTLR, make Lark default | open PR | long-term direction |

---

## Sources

- SymPy parsing docs (1.14.0): https://docs.sympy.org/latest/modules/parsing.html
- ANTLR grammar: https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/LaTeX.g4
- ANTLR converter and strict check: https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/_parse_latex_antlr.py
- `parse_latex` dispatcher: https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/__init__.py
- Lark grammar: https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/grammar/latex.lark and `greek_symbols.lark` in the same directory
- Lark parser and transformer: https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/latex_parser.py, https://github.com/sympy/sympy/blob/sympy-1.14.0/sympy/parsing/latex/lark/transformer.py
- SymPy master used for comparison: https://github.com/sympy/sympy/commit/f8531d83d716cec36a82f0023975bc3322a2984c
- GitHub issues and PRs as linked in §7
- Own runs: `/tmp/sympy-latex-test/` (`matrix.py`, `probe*.py`, `guards.py`, `crosscheck.py`, `normalize.py`, `robust.py`; outputs `out.txt`, `out-master.txt`, `guards-out.txt`, `normalize-out.txt`). These are scratch files and won't persist; the appendix has enough to reproduce.

---

## Appendix: reproduction

```sh
mkdir /tmp/sympy-latex-test && cd /tmp/sympy-latex-test
uv venv venv && VIRTUAL_ENV=venv uv pip install sympy==1.14.0 lark==1.3.1 "antlr4-python3-runtime==4.11.*"
cd /tmp && /tmp/sympy-latex-test/venv/bin/python -I /tmp/sympy-latex-test/matrix.py
```

`matrix.py` calls each case through `parse_latex(s)`, `parse_latex(s, strict=True)` and `parse_latex(s, backend="lark")` with a 10 s `SIGALRM`. It records `ok`/`ERR`/`NONBASIC` (a non-`Basic` result such as a Lark `Tree`, a tuple or a `Matrix`) with `str()` of the result. The case list is the inputs in §3.

<details><summary>normalize.py: the prototype normalizer and guards (tested in §5)</summary>

```python
import re, warnings
warnings.simplefilter("ignore")
import sympy
from sympy import Symbol, simplify, pi, E
from sympy.core.function import AppliedUndef
from sympy.parsing.latex import parse_latex

class Reject(Exception):
    """Tutor sees "can't check this step"."""

FUNCS = "sin|cos|tan|cot|sec|csc|ln|log|lg|exp|arcsin|arccos|arctan"
GREEK = ("alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho "
         "sigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega").split()
NAME_OK = re.compile(r"^(?:[a-zA-Z]|%s)(?:_\{?[A-Za-z0-9]+\}?)?'*$" % "|".join(sorted(GREEK, key=len, reverse=True)))
ALIASES = {"tg": r"\tan", "ctg": r"\cot", "cotg": r"\cot", "arctg": r"\arctan", "arcctg": r"\operatorname{arccot}",
           "sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "ln": r"\ln", "log": r"\log", "lg": r"\lg"}

def rewrite(s, decimal_comma=True):
    s = s.strip()
    s = re.sub(r"\\(?:left|right)(?![a-zA-Z])\s*", "", s)
    s = s.replace(r"\lvert", "|").replace(r"\rvert", "|")
    s = re.sub(r"(?:\\[,;:!]|\\quad|\\qquad|\s)+$", "", s)
    s = re.sub(r"\\(?:operatorname|mathrm)\s*\{\s*([a-z]+)\s*\}", lambda m: ALIASES.get(m.group(1), m.group(0)), s)
    s = re.sub(r"\\(tg|ctg|cotg|arctg)(?![a-zA-Z])", lambda m: ALIASES[m.group(1)], s)
    s = re.sub(r"\\ne(?![a-zA-Z])", r"\\neq", s)
    s = re.sub(r"\\var(phi|epsilon|theta|rho)(?![a-zA-Z])", r"\\\1", s)
    s = re.sub(r"\\mathrm\s*\{\s*([de])\s*\}", r"\1", s)
    s = re.sub(r"\\sqrt\s+([a-zA-Z0-9])", r"\\sqrt{\1}", s)
    s = re.sub(r"\\binom\s*(\d)\s*(\d)", r"\\binom{\1}{\2}", s)
    if re.search(r"\\begin\{[pbvBV]?matrix\}", s): raise Reject("matrix")
    if not s: raise Reject("empty")
    if re.search(r"(?<![_^\d])\d+\s+\d", s) or re.search(r"\d\\[,;!]\s*\d", s): raise Reject("digit groups")
    s = re.sub(r"_\{([A-Za-z0-9]+),([A-Za-z0-9]+)\}", r"_{\1\2}", s)
    s = re.sub(r"(\d)\{,\}(\d)", r"\1.\2", s)
    if re.search(r"\d[.,]\d+[.,]\d", s): raise Reject("two separators in one number")
    s = re.sub(r"(?<![\d}])\.(\d)", r"0.\1", s)
    if re.search(r"\d,\d", s):
        if not decimal_comma: raise Reject("comma between digits")
        if re.search(r"\([^()]*\d,\d[^()]*\)", s): raise Reject("decimal comma inside parentheses")
        s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*\\%", r"(\1/100)", s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*\^\s*\{?\s*\\circ\s*\}?", r"(\1\\cdot\\frac{\\pi}{180})", s)
    if "\\circ" in s: raise Reject("degree sign on a non-number")
    s = re.sub(r"(?<!\\):", r"\\div ", s)
    if re.search(r"\^\s*(?:\{[^{}]*\}|\\?\w+)\s*\^", s): raise Reject("double superscript")
    s = re.sub(r"\^(\{[^{}]*\}|\w)_(\{[^{}]*\}|\w)", r"_\2^\1", s)
    if re.search(r"\^-", s): raise Reject("unbraced negative exponent")
    if re.search(r"\\(?:%s)(?![a-zA-Z])(?!\s*[({^_])[^=<>+\-]*?(?:\\cdot|\\times|\\div|/)" % FUNCS, s):
        raise Reject("unparenthesized function argument followed by * or /")
    if re.search(r"\d\s*\\[dt]?frac\s*\{?\d", s): raise Reject("mixed number?")
    if re.search(r"\\int(?![a-zA-Z])", s) and not re.search(r"(?:\bd|\\mathrm\{d\})\s*[a-zA-Z]\s*$|\\frac\{d", s):
        raise Reject("integral without differential")
    if re.search(r"\\(?:text|mathrm|operatorname|mathbf)\s*\{", s): raise Reject("text/unit span: units path")
    if re.search(r"\\(?:pm|mp)(?![a-zA-Z])", s):
        return [re.sub(r"\\pm(?![a-zA-Z])", "+", re.sub(r"\\mp(?![a-zA-Z])", "-", s)),
                re.sub(r"\\pm(?![a-zA-Z])", "-", re.sub(r"\\mp(?![a-zA-Z])", "+", s))]
    return [s]

def split_system(s):
    if re.search(r"\\begin\{[pbvBV]?matrix\}", s): return [s]
    m = re.fullmatch(r"\s*\\begin\{(cases|aligned|align\*?|gathered|array)\}(?:\{[^}]*\})?(.*)\\end\{\1\}\s*", s, re.S)
    body = m.group(2) if m else s
    return [l.replace("&", "") for l in re.split(r"\\\\", body) if l.strip()]

def split_chain(s):
    parts = re.split(r"(=|<|>|\\leq?(?![a-zA-Z])|\\geq?(?![a-zA-Z])|\\neq)", s)
    if len(parts) <= 3: return [s]
    return [parts[i - 1] + parts[i] + parts[i + 1] for i in range(1, len(parts) - 1, 2)]

def same(a, b):
    return len(a) == len(b) and all(p == q or p.doit() == q.doit()
        or simplify(sympy.nsimplify(p) - sympy.nsimplify(q)) == 0 for p, q in zip(a, b))

def _pair(e, c):
    return (e.args, c.args) if e.is_Relational and c.is_Relational and type(e) == type(c) else ((e,), (c,))

def _fix(c, constants):
    c = c.xreplace({s: Symbol(str(s.name)) for s in c.free_symbols})        # lark Token -> str
    return c.xreplace({Symbol("pi"): pi, Symbol("e"): E}) if constants else c

def to_sympy(s, constants=True):
    e = parse_latex(s, strict=True)
    for sym in e.free_symbols:
        if not NAME_OK.match(str(sym.name)): raise Reject(f"suspicious symbol {sym.name!r}")
    for f in e.atoms(AppliedUndef): raise Reject(f"undeclared function {f.func}")
    e = _fix(e, constants)
    try: l = parse_latex(s, backend="lark")
    except Exception: l = None                                               # lark gap: no veto
    if isinstance(l, sympy.Basic):
        if not same(*_pair(e, _fix(l, constants))): raise Reject("backends disagree")
    elif l is not None and type(l).__name__ == "Tree" and l.data == "_ambig":
        alts = [_fix(c, constants) for c in l.children if isinstance(c, sympy.Basic)]
        if not any(same(*_pair(e, c)) for c in alts): raise Reject("lark ambiguous, ANTLR reading not among them")
    return e

def check_line(s, decimal_comma=True):
    if not s.strip(): raise Reject("empty")
    return [to_sympy(b) for line in split_system(s) for part in split_chain(line)
            for b in rewrite(part, decimal_comma)]
```
</details>

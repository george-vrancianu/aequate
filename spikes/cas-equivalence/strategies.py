"""Equivalence strategies S0-S8 from docs/research/sympy-equivalence.md.

Every strategy takes a parsed step and returns (verdict, detail). Verdicts:

    equiv, not_equiv, undecided, domain_changed,
    implies (prev => curr, superset), lost_roots (subset), same_roots, n/a

Strategies never call sympify/parse_expr on strings: input arrives only
through `parse()`, which uses SymPy's LaTeX parser (a grammar, no eval).
Timeouts are enforced by the caller (run.py) by killing the worker process.
"""
from __future__ import annotations

import os
import random

import mpmath
from sympy import (
    Add, Float, Function, Mul, Number, Poly, Pow, Rational, S, Symbol, cancel,
    exp, expand, factor, fraction, nsimplify, pi, roots, simplify, solveset,
    together, trigsimp,
)
from sympy.core.relational import Relational
from sympy.calculus.util import continuous_domain
from sympy.parsing.latex import parse_latex
from sympy.sets.conditionset import ConditionSet

BACKEND = os.environ.get("AEQUATE_LATEX_BACKEND", "antlr")
REL_TOL = mpmath.mpf("1e-9")
N_POINTS = 10
mpmath.mp.dps = 30


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _rebuild(e):
    """Force SymPy's normal automatic evaluation on an unevaluated tree."""
    if not getattr(e, "args", None):
        return e
    return e.func(*[_rebuild(a) for a in e.args])


def _floats_to_rationals(e):
    return e.xreplace({f: nsimplify(f, rational=True) for f in e.atoms(Float)})


# SymPy 1.14's LaTeX parser returns \pi as Symbol('pi'), not the constant.
# `e` is left alone on purpose: in physics it is often the elementary charge,
# so the recogniser (or the problem's symbol table) must say which it means.
CONSTANTS = {Symbol("pi"): pi}


def parse(latex: str, evaluate: bool = True):
    raw = parse_latex(latex, backend=BACKEND) if BACKEND != "antlr" else parse_latex(latex)
    raw = raw.xreplace(CONSTANTS)
    return _rebuild(raw) if evaluate else raw


def with_assumptions(e, mode: str):
    """mode: 'complex' (as parsed), 'real', or 'positive'."""
    if mode == "complex":
        return e
    kw = {"real": True} if mode == "real" else {"positive": True}
    return e.xreplace({s: Symbol(s.name, **kw) for s in e.free_symbols if isinstance(s, Symbol)})


def sides(rel):
    return rel.lhs, rel.rhs


def as_zero_form(rel):
    """L = R  ->  L - R."""
    return rel.lhs - rel.rhs


def syms(*es):
    out = set()
    for e in es:
        out |= e.free_symbols
    return sorted(out, key=lambda s: s.name)


# --------------------------------------------------------------------------
# Numeric helpers
# --------------------------------------------------------------------------

def _points(variables, domain, n, rng):
    for _ in range(n):
        if domain == "complex":
            yield [mpmath.mpc(rng.uniform(-2, 2), rng.uniform(-2, 2)) for _ in variables]
        elif domain == "positive":
            yield [mpmath.mpf(rng.uniform(0.1, 5)) for _ in variables]
        else:
            yield [mpmath.mpf(rng.uniform(-5, 5)) for _ in variables]


def _evaluate(f, pt, domain):
    try:
        v = mpmath.mpmathify(f(*pt))
    except (ZeroDivisionError, ValueError, TypeError, OverflowError):
        return None
    if not mpmath.isfinite(v):
        return None
    if domain != "complex" and abs(mpmath.im(v)) > mpmath.mpf("1e-20"):
        return None  # outside the real natural domain
    return v


def _close(a, b):
    d = abs(a - b)
    return d <= REL_TOL * max(abs(a), abs(b)) or d < mpmath.mpf("1e-25")


def numeric_compare(a, b, domain="real", n=N_POINTS, seed=0):
    """Return (verdict, detail) comparing expressions a and b at random points."""
    from sympy import lambdify
    variables = syms(a, b)
    rng = random.Random(seed)
    if not variables:
        variables = [Symbol("_dummy")]
    fa = lambdify(variables, a, "mpmath")
    fb = lambdify(variables, b, "mpmath")
    used = 0
    for pt in _points(variables, domain, n * 3, rng):
        va, vb = _evaluate(fa, pt, domain), _evaluate(fb, pt, domain)
        if va is None or vb is None:
            continue
        used += 1
        if not _close(va, vb):
            return "not_equiv", f"differs at {[mpmath.nstr(p, 4) for p in pt]}"
        if used >= n:
            break
    if used == 0:
        return "undecided", "no valid sample points"
    return "equiv", f"{used} points agree"


def numeric_ratio_constant(f1, f2, domain="real", n=N_POINTS, seed=0):
    """Equations: is (L1-R1)/(L2-R2) a non-zero constant? (STACK's AlgEquiv idea)."""
    from sympy import lambdify
    variables = syms(f1, f2) or [Symbol("_dummy")]
    rng = random.Random(seed)
    g1 = lambdify(variables, f1, "mpmath")
    g2 = lambdify(variables, f2, "mpmath")
    ratio = None
    used = 0
    for pt in _points(variables, domain, n * 3, rng):
        v1, v2 = _evaluate(g1, pt, domain), _evaluate(g2, pt, domain)
        if v1 is None or v2 is None or v2 == 0:
            continue
        used += 1
        r = v1 / v2
        if ratio is None:
            ratio = r
        elif not _close(r, ratio):
            return "not_equiv", "ratio of zero-forms varies"
        if used >= n:
            break
    if used == 0 or ratio == 0:
        return "undecided", "no valid sample points"
    return "equiv", f"ratio constant ({mpmath.nstr(ratio, 6)})"


def numeric_truth_table(r1, r2, n=40, seed=0):
    """Inequalities: do both lines hold at the same real points?"""
    from sympy import lambdify
    variables = syms(r1, r2)
    rng = random.Random(seed)
    g1 = lambdify(variables, r1, "mpmath")
    g2 = lambdify(variables, r2, "mpmath")
    for pt in _points(variables, "real", n, rng):
        try:
            if bool(g1(*pt)) != bool(g2(*pt)):
                return "not_equiv", f"disagree at {[mpmath.nstr(p, 4) for p in pt]}"
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    return "equiv", f"{n} points agree"


# --------------------------------------------------------------------------
# S0  Structural equality
# --------------------------------------------------------------------------

def s0_structural(step):
    raw_same = parse(step["prev"], evaluate=False) == parse(step["curr"], evaluate=False)
    ev_same = step["_prev"] == step["_curr"]
    if ev_same:
        return "equiv", f"identical after evaluation (raw identical: {raw_same})"
    return "undecided", "structurally different"


# --------------------------------------------------------------------------
# S1  simplify(a - b) == 0   (plain, naive on equations)
# --------------------------------------------------------------------------

def _diff(step):
    a, b = step["_prev"], step["_curr"]
    if step["kind"] == "expr":
        return a - b
    if step["kind"] == "eq":
        return as_zero_form(a) - as_zero_form(b)
    return None


def s1_simplify(step, mode="complex"):
    d = _diff(step)
    if d is None:
        return "n/a", "not defined for inequalities"
    d = with_assumptions(d, mode)
    r = simplify(d)
    if r == 0:
        return "equiv", "difference simplifies to 0"
    return "not_equiv", f"residue {r}"


# --------------------------------------------------------------------------
# S2  Expr.equals (tri-state)
# --------------------------------------------------------------------------

def s2_equals(step, mode="complex"):
    a, b = step["_prev"], step["_curr"]
    if step["kind"] == "eq":
        a, b = as_zero_form(a), as_zero_form(b)
    elif step["kind"] == "ineq":
        return "n/a", "not defined for inequalities"
    a, b = with_assumptions(a, mode), with_assumptions(b, mode)
    r = a.equals(b, failing_expression=True)
    if r is True:
        return "equiv", "equals() -> True"
    if r is False:
        return "not_equiv", "equals() -> False"
    if r is None:
        return "undecided", "equals() -> None"
    return "undecided", f"equals() failing expression: {r}"


# --------------------------------------------------------------------------
# S3  Numeric sampling (real and complex)
# --------------------------------------------------------------------------

def s3_numeric(step, domain="real"):
    a, b = step["_prev"], step["_curr"]
    if step["kind"] == "expr":
        return numeric_compare(a, b, domain)
    if step["kind"] == "eq":
        return numeric_ratio_constant(as_zero_form(a), as_zero_form(b), domain)
    if domain == "complex":
        return "n/a", "inequalities need real points"
    return numeric_truth_table(a, b)


# --------------------------------------------------------------------------
# S4  Layered pipeline (STACK-style)
# --------------------------------------------------------------------------

REWRITES = [
    ("expand", expand),
    ("cancel", cancel),
    ("together", lambda e: fraction(together(e))[0]),
    ("factor", factor),
    ("trigsimp", trigsimp),
    ("rewrite(exp)", lambda e: simplify(expand(e.rewrite(exp)))),
]


def _zero_chain(d, mode):
    for name, f in REWRITES:
        try:
            if f(d) == 0:
                return name
        except Exception:  # noqa: BLE001 - a failed rewrite just moves on
            continue
    if simplify(d) == 0:
        return "simplify"
    return None


def s4_layered(step, mode="real"):
    a, b = step["_prev"], step["_curr"]
    domain = "complex" if mode == "complex" else mode
    if a == b:
        return "equiv", "structural"
    if step["kind"] == "ineq":
        return s5_solution_sets(step)
    if step["kind"] == "eq":
        f1, f2 = as_zero_form(a), as_zero_form(b)
        n1 = fraction(together(with_assumptions(f1, mode)))[0]
        n2 = fraction(together(with_assumptions(f2, mode)))[0]
        q = cancel(n1 / n2)
        if q != 0 and not q.free_symbols:
            return "equiv", f"numerator ratio constant ({q})"
        v, why = numeric_ratio_constant(f1, f2, domain)
        return ("not_equiv" if v == "not_equiv" else "undecided"), f"ratio {q}; numeric: {why}"
    a, b = with_assumptions(a, mode), with_assumptions(b, mode)
    v, why = numeric_compare(a, b, domain)
    if v == "not_equiv":
        return "not_equiv", f"numeric reject: {why}"
    hit = _zero_chain(a - b, mode)
    if hit:
        return "equiv", f"zero via {hit}"
    return "undecided", "numerically equal, no symbolic proof"


# --------------------------------------------------------------------------
# S5  Solution-set comparison (equations, inequalities)
# --------------------------------------------------------------------------

def _target(step, a, b):
    if step.get("target"):
        return Symbol(step["target"])
    vs = syms(a, b)
    return vs[0] if len(vs) == 1 else None


def _sets_relation(s1, s2):
    if isinstance(s1, ConditionSet) or isinstance(s2, ConditionSet):
        return "undecided", "solver returned ConditionSet"
    sub12, sub21 = s1.is_subset(s2), s2.is_subset(s1)
    if sub12 and sub21:
        return "equiv", f"{s1} = {s2}"
    if sub12 and sub21 is False:
        return "implies", f"{s1} ⊂ {s2} (extra solutions)"
    if sub21 and sub12 is False:
        return "lost_roots", f"{s2} ⊂ {s1} (lost solutions)"
    if sub12 is None or sub21 is None:
        return "undecided", f"cannot compare {s1} and {s2}"
    return "not_equiv", f"{s1} vs {s2}"


def _multiplicities(rel, x):
    num = fraction(together(as_zero_form(rel)))[0]
    try:
        return roots(Poly(expand(num), x))
    except Exception:  # noqa: BLE001
        return None


def s5_solution_sets(step, n_param_draws=3, seed=0, target_domain=S.Reals):
    a, b = step["_prev"], step["_curr"]
    if step["kind"] == "expr":
        return "n/a", "expressions have no solution set"
    x = _target(step, a, b)
    if x is None:
        return "undecided", "no single unknown"
    # find the symbol object actually used in the tree (assumptions may differ)
    x = next((s for s in syms(a, b) if s.name == x.name), x)
    params = [s for s in syms(a, b) if s != x]
    rng = random.Random(seed)
    draws = [{}] if not params else [
        {p: Rational(rng.randint(2, 40), rng.randint(1, 7)) for p in params}
        for _ in range(n_param_draws)
    ]
    verdicts = []
    for sub in draws:
        s1 = solveset(a.xreplace(sub), x, target_domain)
        s2 = solveset(b.xreplace(sub), x, target_domain)
        verdicts.append(_sets_relation(s1, s2))
    kinds = {v for v, _ in verdicts}
    v, why = verdicts[0] if len(kinds) == 1 else ("undecided", f"varies with parameters: {verdicts}")
    if params:
        why += f"  [parameters sampled positive: {[p.name for p in params]}]"
    if v == "equiv" and step["kind"] == "eq" and not params:
        m1, m2 = _multiplicities(a, x), _multiplicities(b, x)
        if m1 is not None and m2 is not None and m1 != m2:
            return "same_roots", f"{why}; multiplicities {m1} vs {m2}"
    return v, why


# --------------------------------------------------------------------------
# S6  Assumption variants  (wrapped by run.py: S1/S2/S4 x complex/real/positive)
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# S7  Domain tracking
# --------------------------------------------------------------------------

def _natural_domain(e, x):
    parts = list(e.args) if isinstance(e, Relational) else [e]
    dom = S.Reals
    for p in parts:
        dom = dom.intersect(continuous_domain(p, x, S.Reals))
    return dom


def s7_domain(step):
    a, b = step["_prev"], step["_curr"]
    vs = syms(a, b)
    if len(vs) != 1:
        return "n/a", "multi-variable"
    x = vs[0]
    d1, d2 = _natural_domain(a, x), _natural_domain(b, x)
    if d1 == d2:
        return "same_domain", f"{d1}"
    return "domain_changed", f"{d1} -> {d2}"


# --------------------------------------------------------------------------
# S8  Units (Pint) for physics lines with declared symbol units
# --------------------------------------------------------------------------

_UREG = None


def _ureg():
    global _UREG
    if _UREG is None:
        import pint
        _UREG = pint.UnitRegistry()
    return _UREG


class DimError(Exception):
    pass


def dimension(e, units):
    u = _ureg()
    if isinstance(e, Symbol):
        if e.name not in units:
            raise DimError(f"no unit declared for {e.name}")
        return u.Quantity(1, units[e.name])
    if isinstance(e, Number) or e.is_number:
        return u.Quantity(1, "dimensionless")
    if isinstance(e, Add):
        terms = [dimension(t, units) for t in e.args]
        d0 = terms[0].dimensionality
        for t in terms[1:]:
            if t.dimensionality != d0:
                raise DimError(f"adds {d0} to {t.dimensionality}")
        return terms[0]
    if isinstance(e, Mul):
        q = u.Quantity(1, "dimensionless")
        for t in e.args:
            q = q * dimension(t, units)
        return q
    if isinstance(e, Pow):
        if not e.exp.is_number:
            raise DimError("symbolic exponent")
        return dimension(e.base, units) ** float(e.exp)
    if isinstance(e, Function):
        for arg in e.args:
            if not dimension(arg, units).dimensionless:
                raise DimError(f"{e.func} of a dimensioned quantity")
        return u.Quantity(1, "dimensionless")
    raise DimError(f"unsupported node {type(e).__name__}")


def check_units(rel, units):
    l, r = dimension(rel.lhs, units), dimension(rel.rhs, units)
    if l.dimensionality != r.dimensionality:
        raise DimError(f"{l.dimensionality} = {r.dimensionality}")
    return str(l.dimensionality)


def s8_units(step, units):
    a, b = step["_prev"], step["_curr"]
    try:
        d1 = check_units(a, units)
    except DimError as e:
        return "not_equiv", f"prev line inconsistent: {e}"
    try:
        check_units(b, units)
    except DimError as e:
        return "not_equiv", f"curr line inconsistent: {e}"
    v, why = s5_solution_sets(step) if step.get("target") or len(syms(a, b)) == 1 else s4_layered(step, "positive")
    return v, f"units ok ({d1}); algebra: {why}"


# --------------------------------------------------------------------------
# Proposed pipeline: what the checker would actually run
# --------------------------------------------------------------------------

def pipeline(step, units=None):
    if units is not None:
        v, why = s8_units(step, units)
        if v == "not_equiv":
            return v, why
    if step["kind"] == "expr":
        v, why = s4_layered(step, "real")
        if v == "equiv":
            dv, dwhy = s7_domain(step)
            if dv == "domain_changed":
                return "domain_changed", f"{why}; {dwhy}"
        return v, why
    if step["kind"] == "eq" and not step.get("target") and len(syms(step["_prev"], step["_curr"])) > 1:
        # pick the variable isolated on the left of curr, if any
        if isinstance(step["_curr"].lhs, Symbol):
            step = dict(step, target=step["_curr"].lhs.name)
    v, why = s5_solution_sets(step)
    if v == "undecided" and step["kind"] == "eq":
        v2, why2 = s4_layered(step, "real")
        if v2 == "equiv":
            return v2, f"S5 undecided; {why2}"
    return v, why


TICK = {"same_domain": "-", "equiv": "green", "same_roots": "green", "not_equiv": "red", "lost_roots": "red",
        "implies": "amber", "domain_changed": "amber", "undecided": "amber",
        "timeout": "amber", "error": "amber", "n/a": "-"}

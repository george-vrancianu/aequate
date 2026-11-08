"""Strategies S0-S7 (S8 Pint dropped). PROTOTYPE. Each takes parsed Exprs a (before), b (after), a step dict,
and returns (verdict, detail). Verdicts: EQ NEQ EQ_DOM NARROW WIDER UND NA.
Equations (S0-S4, S6, S7): compare residuals r=lhs-rhs up to a nonzero constant: test ra == c*rb, c from a rational probe.
S5 compares solution sets. Expressions: S5 is NA."""
import random
import sympy
from sympy import (Symbol, Rational, Float, I, S, nan, zoo, oo, pi, simplify, expand, cancel, together, factor,
                   trigsimp, exp, Eq, solveset, ConditionSet)

SEED = 0

# ---------- helpers ----------
def resid(e):
    return e.lhs - e.rhs

def scale(ra, rb):
    """c such that ra ~ c*rb, taken at exact rational probe points; 1 if none usable."""
    syms = sorted(ra.free_symbols | rb.free_symbols, key=str)
    for k in range(6):
        pt = {s: Rational(3 + k + i, 7) for i, s in enumerate(syms)}
        try:
            va, vb = ra.subs(pt), rb.subs(pt)
            if vb.is_number and va.is_number and vb != 0 and not (va.has(nan, zoo) or vb.has(nan, zoo)):
                return sympy.nsimplify(va / vb)
        except Exception:
            pass
    return S.One

def pair(a, b, step):
    """Two expressions whose identity is the question."""
    if step["kind"] == "eq":
        ra, rb = resid(a), resid(b)
        return ra, scale(ra, rb) * rb
    return a, b

def assume(e, mode):
    if mode == "complex":
        return e
    kw = {"real": dict(real=True), "pos": dict(positive=True)}[mode]
    return e.xreplace({s: Symbol(s.name, **kw) for s in e.free_symbols})

def _num(v):
    c = complex(v)
    if c != c or abs(c) == float("inf"):
        raise ValueError("nonfinite")
    return c

def numeric(A, B, domain, n=10, rtol=1e-9, atol=1e-12, seed=0):
    """Sample A-B at n points. domain: real | pos | complex. Points where either side is non-finite
    (or not real, in real/pos mode) are skipped. Needs >= 3 usable points."""
    rng = random.Random(seed)
    syms = sorted(A.free_symbols | B.free_symbols, key=str)
    ok = used = 0
    for _ in range(n * 4):
        if used >= n:
            break
        if domain == "complex":
            pt = {s: Float(rng.uniform(-3, 3), 30) + I * Float(rng.uniform(-3, 3), 30) for s in syms}
        elif domain == "real":
            pt = {s: Float(rng.uniform(-5, 5), 30) for s in syms}
        else:
            pt = {s: Float(rng.uniform(0.1, 5), 30) for s in syms}
        try:
            va, vb = _num(A.evalf(30, subs=pt)), _num(B.evalf(30, subs=pt))
        except Exception:
            continue
        if domain != "complex" and (abs(va.imag) > 1e-12 * (1 + abs(va)) or abs(vb.imag) > 1e-12 * (1 + abs(vb))):
            continue
        used += 1
        if abs(va - vb) <= rtol * max(abs(va), abs(vb)) + atol:
            ok += 1
        else:
            return "NEQ", f"differs at {used} of {used} points tried, e.g. {va:.6g} vs {vb:.6g}"
    if used < 3:
        return "UND", f"only {used} usable points"
    return "EQ", f"{ok}/{used} points agree (rtol {rtol})"

# ---------- strategies ----------
def s0e(a, b, step):
    """Structural == on the evaluated trees (what parsing._fix() returns)."""
    if a == b:
        return "EQ", "identical after parse (evaluated)"
    if a.doit() == b.doit():
        return "EQ", "identical after doit() (evaluated)"
    return "NEQ", "structure differs (evaluated trees)"

def s0u(a, b, step):
    """Structural == on the unevaluated ANTLR trees (parsed and fixed under sympy.evaluate(False))."""
    ra, rb = step["raw"]
    if ra == rb:
        return "EQ", "identical unevaluated trees"
    return "NEQ", f"unevaluated trees differ: {ra} vs {rb}"

def _s1(a, b, step, mode="complex"):
    A, B = pair(a, b, step)
    A, B = assume(A, mode), assume(B, mode)
    z = simplify(A - B)
    return ("EQ", "simplify(A-B)=0") if z == 0 else ("NEQ", f"simplify(A-B)={z} (non-zero is not a proof of NEQ)")

def _s2(a, b, step, mode="complex"):
    A, B = pair(a, b, step)
    A, B = assume(A, mode), assume(B, mode)
    sympy.core.random.seed(SEED); random.seed(SEED)   # Expr.equals samples with SymPy's RNG: seed it so S2 is repeatable
    r = A.equals(B)
    return {True: ("EQ", "equals=True"), False: ("NEQ", "equals=False"), None: ("UND", "equals=None")}[r]

REWRITES = [("expand", expand), ("cancel", cancel), ("together", together), ("factor", factor),
            ("trigsimp", trigsimp), ("rewrite(exp)", lambda e: e.rewrite(exp))]

def _s4(a, b, step, mode="complex"):
    A, B = pair(a, b, step)
    A, B = assume(A, mode), assume(B, mode)
    if A == B:
        return "EQ", "stage: structural"
    dom = {"complex": "complex", "real": "real", "pos": "pos"}[mode]
    v, d = numeric(A, B, dom)
    if v == "NEQ":
        return "NEQ", "stage: numeric reject (%s). %s" % (dom, d)
    diff = A - B
    for name, f in REWRITES:
        try:
            if f(diff) == 0:
                return "EQ", f"stage: {name}"
        except Exception:
            pass
    if simplify(diff) == 0:
        return "EQ", "stage: simplify"
    return "UND", f"no stage proved it (numeric said {v})"

def s3(domain):
    def f(a, b, step):
        A, B = pair(a, b, step)
        return numeric(A, B, domain)
    return f

def s5(domain):
    def f(a, b, step):
        if step["kind"] != "eq":
            return "NA", "no solution set for an expression"
        syms = sorted((a.free_symbols | b.free_symbols), key=str)
        var = Symbol(step["solve_for"]) if "solve_for" in step else (syms[0] if len(syms) == 1 else None)
        if var is None:
            return "UND", "cannot pick a variable"
        var = next(s for s in syms if s.name == str(var))
        sa, sb = solveset(a, var, domain), solveset(b, var, domain)
        if isinstance(sa, ConditionSet) or isinstance(sb, ConditionSet):
            return "UND", f"unsolved: {sa} | {sb}"
        det = f"{sa} vs {sb}"
        if sa == sb:
            return "EQ", det
        if sb.is_subset(sa) is True:
            return "NARROW", det + " (after is a proper subset: roots lost)"
        if sa.is_subset(sb) is True:
            return "WIDER", det + " (after is a proper superset: extra roots)"
        return "NEQ", det
    return f

def _conds(e, excl, req):
    """Walk the UNEVALUATED tree. excl: expressions that must be != 0. req: (expr, strict) that must be >0 / >=0 (real policy)."""
    for n in sympy.preorder_traversal(e):
        if isinstance(n, sympy.Pow):
            base, ex = n.args
            if ex.is_number and ex.is_negative and not base.is_number:
                excl.append(base)
            if ex.is_Rational and ex.q % 2 == 0 and not base.is_number:
                req.append((base, bool(ex.is_negative)))      # even root: base >= 0 (> 0 if also a denominator)
        elif isinstance(n, (sympy.tan, sympy.sec)):
            excl.append(sympy.cos(n.args[0]))
        elif isinstance(n, (sympy.cot, sympy.csc)):
            excl.append(sympy.sin(n.args[0]))
        elif isinstance(n, sympy.log) and not n.args[0].is_number:
            req.append((n.args[0], True))

def natural_domain(e, var):
    """Real natural domain of e (a single variable) as a SymPy set, from singularities found symbolically."""
    excl, req = [], []
    _conds(e, excl, req)
    dom = S.Reals
    for d in excl:
        dom = dom - solveset(d, var, S.Reals)
    for x, strict in req:
        dom = dom & solveset(x > 0 if strict else x >= 0, var, S.Reals)
    return dom

def _canon(s):
    """Each solveset call makes its ImageSet a fresh Dummy (_n), so equal trig sets are never structurally ==. Rename all Dummies to one fixed Symbol."""
    n0 = sympy.Symbol("n_")
    ds = s.atoms(sympy.Dummy)
    return s.xreplace({d: n0 for d in ds}) if ds else s

def s7(a, b, step):
    """Domain tracking (research S7): numeric real check first; if it says equal, compute each side's natural real domain
    symbolically from the unevaluated trees and compare. Equations: domain of both sides together."""
    A, B = pair(a, b, step)
    v, d = numeric(A, B, "real")
    if v != "EQ":
        return v, "numeric(real): " + d
    ra, rb = step["raw"]
    parts = lambda e: [e.lhs, e.rhs] if step["kind"] == "eq" else [e]
    syms = sorted(set().union(*(p.free_symbols for p in parts(ra) + parts(rb))), key=str)
    if len(syms) != 1:
        return "UND", f"domain tracking implemented for one variable, got {syms}"
    x = syms[0]
    da = _canon(sympy.Intersection(*[natural_domain(p, x) for p in parts(ra)]))
    db = _canon(sympy.Intersection(*[natural_domain(p, x) for p in parts(rb)]))
    if da == db:
        return "EQ", f"equal at samples; same natural domain {da}"
    def excl(d):    # excluded points; unwrap Complement(Reals, X) so trig sets print as X, not a double complement
        return d.args[1] if isinstance(d, sympy.Complement) and d.args[0] == S.Reals else S.Reals - d
    ea, eb = excl(da), excl(db)
    return "EQ_DOM", f"equal at samples; excluded points before: {ea}; after: {eb}"

STRATEGIES = [
    ("S0e", "structural ==, evaluated trees", s0e),
    ("S0u", "structural ==, unevaluated trees", s0u),
    ("S1", "simplify(A-B)==0", _s1),
    ("S2", "A.equals(B)", _s2),
    ("S3r", "numeric, real pts", s3("real")),
    ("S3c", "numeric, complex pts", s3("complex")),
    ("S4", "layered (STACK-style)", _s4),
    ("S5r", "solveset over R", s5(S.Reals)),
    ("S5c", "solveset over C", s5(S.Complexes)),
    ("S6-S1r", "S1, real symbols", lambda a, b, st: _s1(a, b, st, "real")),
    ("S6-S1p", "S1, positive symbols", lambda a, b, st: _s1(a, b, st, "pos")),
    ("S6-S2r", "S2, real symbols", lambda a, b, st: _s2(a, b, st, "real")),
    ("S6-S2p", "S2, positive symbols", lambda a, b, st: _s2(a, b, st, "pos")),
    ("S6-S4r", "S4, real symbols", lambda a, b, st: _s4(a, b, st, "real")),
    ("S6-S4p", "S4, positive symbols", lambda a, b, st: _s4(a, b, st, "pos")),
    ("S7", "domain tracking (symbolic) over numeric", s7),
]

def score(expected, v):
    if v == "NA":
        return "na"
    if v in ("UND", "TO", "ERR"):
        return "und"
    if expected == "EQUIV":
        return "ok" if v == "EQ" else "wrong"
    if expected == "NOT_EQUIV":
        return "wrong" if v in ("EQ", "EQ_DOM") else "ok"
    if expected == "DOMAIN":      # must flag the domain change: EQ_DOM, or a solution-set difference; plain NEQ is partial
        return "wrong" if v == "EQ" else ("ok" if v in ("EQ_DOM", "NARROW", "WIDER") else "partial")
    if expected == "ONEWAY":      # after follows from before: only WIDER names it
        return "ok" if v == "WIDER" else ("partial" if v in ("NEQ", "NARROW") else "wrong")

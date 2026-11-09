"""PROTOTYPE (#40): prototype-only adapters so the existing strategies (strategies.py, untouched) can run on the hard set.
Findings that forced these workarounds are in RESULTS-hard.md.
 - ineq: the parse stack accepts relationals, but strategies.pair() takes lhs-rhs of an Eq. Workaround: normalise every
   inequality to "bigger side, smaller side" (a<b -> Eq(b,a)), so the residual is positive where the inequality holds, and
   after any strategy says EQ require (1) the proportionality constant to be > 0 (a negative one is a flipped sign) and
   (2) the same strictness (< vs <=). S5 runs solveset on the original relationals (real only; complex is NA).
 - sys: the parse stack yields a list of Eq per side (check_line splits cases/aligned). Only S0e/S0u (same set of equations)
   and S5 (solution sets from sympy.solve) are implemented; every other strategy is NA. No sympify/eval: parse_latex only."""
import sympy
from sympy import Eq, Symbol, S
from parsing import check_line, Reject
from rawparse import check_line_raw
import strategies
from strategies import STRATEGIES, score

def _orient(r):
    """Relational -> (Eq(bigger, smaller), strict). Built unevaluated."""
    strict = isinstance(r, (sympy.StrictLessThan, sympy.StrictGreaterThan))
    with sympy.evaluate(False):
        if isinstance(r, (sympy.StrictLessThan, sympy.LessThan)):
            return Eq(r.rhs, r.lhs, evaluate=False), strict
        return Eq(r.lhs, r.rhs, evaluate=False), strict

def parse_step(step):
    """-> dict(a, b, raw=(ra, rb), extra=...) ready for run_strategy. Raises Reject / parser exceptions."""
    la, lb = check_line(step["before"]), check_line(step["after"])
    ra, rb = check_line_raw(step["before"]), check_line_raw(step["after"])
    kind = step["kind"]
    if kind == "sys":
        return dict(a=la, b=lb, raw=(ra, rb), orig=(la, lb), strict=None)
    if len(la) != 1 or len(lb) != 1 or len(ra) != 1 or len(rb) != 1:
        raise Reject("branches")
    a, b, ra, rb = la[0], lb[0], ra[0], rb[0]
    if kind == "ineq":
        (na, sa), (nb, sb) = _orient(a), _orient(b)
        (rna, _), (rnb, _) = _orient(ra), _orient(rb)
        return dict(a=na, b=nb, raw=(rna, rnb), orig=(a, b), strict=(sa, sb))
    return dict(a=a, b=b, raw=(ra, rb), orig=(a, b), strict=None)

def _solset(eqs, domain):
    syms = sorted(set().union(*(e.free_symbols for e in eqs)), key=str)
    sols = sympy.solve(eqs, syms, dict=True)
    out = set()
    for d in sols:
        if len(d) != len(syms) or any(v.free_symbols for v in d.values()):
            return None                                   # parametric / underdetermined
        if domain == "real" and any(v.is_real is False for v in d.values()):
            continue
        out.add(frozenset((str(k), v) for k, v in d.items()))
    return out

def _s5_sys(domain):
    def f(a, b, st):
        sa, sb = _solset(a, domain), _solset(b, domain)
        if sa is None or sb is None:
            return "UND", "parametric or unsolved"
        det = f"{len(sa)} vs {len(sb)} solutions: {sorted(map(sorted, map(lambda s: [(k, str(v)) for k, v in s], sa)))} | {sorted(map(sorted, map(lambda s: [(k, str(v)) for k, v in s], sb)))}"
        if sa == sb: return "EQ", det
        if sb < sa: return "NARROW", det + " (solutions lost)"
        if sa < sb: return "WIDER", det + " (extra solutions)"
        return "NEQ", det
    return f

def _s5_ineq(a, b, st):
    A, B = st["orig"]
    syms = sorted(A.free_symbols | B.free_symbols, key=str)
    if len(syms) != 1: return "UND", "ineq S5 needs one variable"
    x = syms[0]
    sa, sb = sympy.solveset(A, x, S.Reals), sympy.solveset(B, x, S.Reals)
    if isinstance(sa, sympy.ConditionSet) or isinstance(sb, sympy.ConditionSet): return "UND", f"unsolved: {sa} | {sb}"
    det = f"{sa} vs {sb}"
    if sa == sb: return "EQ", det
    if sb.is_subset(sa) is True: return "NARROW", det
    if sa.is_subset(sb) is True: return "WIDER", det
    return "NEQ", det

def run_strategy(sid, a, b, st):
    """Single entry point used by the sweep. st carries kind, expected, raw, and for ineq/sys the extras from parse_step."""
    fn = {k: f for k, _, f in STRATEGIES}[sid]
    kind = st["kind"]
    if kind == "sys":
        if sid in ("S5r", "S5c"): return _s5_sys("real" if sid == "S5r" else "complex")(a, b, st)
        if sid in ("S0e", "S0u"):
            x, y = (a, b) if sid == "S0e" else st["raw"]
            return ("EQ", "same set of equations") if set(x) == set(y) else ("NEQ", "equation sets differ")
        return "NA", "no system-level strategy implemented"
    if kind == "ineq":
        if sid == "S5r": return _s5_ineq(a, b, st)
        if sid == "S5c": return "NA", "solveset over C has no order"
        st2 = dict(st, kind="eq")
        v, d = fn(a, b, st2)
        if v in ("EQ", "EQ_DOM"):
            ra, rb = a.lhs - a.rhs, b.lhs - b.rhs
            c = strategies.scale(ra, rb)
            if c.is_number and c.is_negative: return "NEQ", "direction flipped (negative scale). " + d
            if st["strict"][0] != st["strict"][1]: return "NEQ", "strictness differs. " + d
        return v, d
    return fn(a, b, st)

def make_st(step, p):
    return dict(step, raw=p["raw"], orig=p["orig"], strict=p["strict"])

def stack(step):
    """Recommended stack (RESULTS.md 4.3), whole thing in one call, from LaTeX strings. Returns (verdict, trace). EQ_NODOM = proven equal but S7 cannot check the domain (2+ variables): shown amber.
    trace: [(stage, ms, verdict)]. Order: parse; equation-like lines: S5r first (decisive unless UND);
    S3r numeric reject; S4 layered (cheap zero-checks, ends in simplify); on proven EQ: S7 domain flag (amber)."""
    import time
    trace = []
    def timed(name, fn):
        t = time.perf_counter(); r = fn(); trace.append((name, (time.perf_counter() - t) * 1000, r[0] if isinstance(r, tuple) else "ok")); return r
    try:
        p = timed("parse", lambda: ("ok", parse_step(step)))[1]
    except Exception as e:
        trace.append(("parse", 0.0, "REJECT")); return "UND", trace
    st = make_st(step, p)
    a, b = p["a"], p["b"]
    proven = False
    if step["kind"] in ("eq", "ineq", "sys"):
        v, _ = timed("S5r", lambda: run_strategy("S5r", a, b, st))
        if v in ("NARROW", "WIDER", "NEQ"): return v, trace
        if v == "EQ": proven = True
        if step["kind"] == "sys": return ("EQ" if proven else "UND"), trace
    if not proven:
        v, _ = timed("S3r", lambda: run_strategy("S3r", a, b, st))
        if v == "NEQ": return "NEQ", trace
        v, _ = timed("S4", lambda: run_strategy("S4", a, b, st))
        if v == "NEQ": return "NEQ", trace
        if v != "EQ": return "UND", trace
    v, d = timed("S7", lambda: run_strategy("S7", a, b, st))
    if v == "EQ_DOM": return "EQ_DOM", trace
    if v == "EQ": return "EQ", trace
    if v == "UND" and "got []" in d: return "EQ", trace          # no variable: no domain to restrict (S7 is one-variable only)
    if v == "UND" and d.startswith("domain tracking implemented for one variable"): return "EQ_NODOM", trace   # proven equal, domain NOT checked
    return ("NEQ" if v == "NEQ" else "UND"), trace

"""PROTOTYPE (throwaway), ticket #41: domain tracking S7b for several variables and more rules.

Real-number convention (stated, not neutral):
  * Everything is over the reals. x**(p/q) in lowest terms: q even -> needs base >= 0 (> 0 if p < 0);
    q odd -> the REAL root, defined for every real base (base != 0 if p < 0). This is the school convention
    ("cube root of -8 is -2"), NOT SymPy's principal-branch value. x**0 needs base != 0 (0**0 undefined).
    x**r with irrational constant r needs base > 0. x**y with a symbolic exponent y, or any unlisted function: UNDECIDED.
  * log is the natural log, argument > 0. arcsin/arccos argument in [-1, 1]. tan/sec need cos != 0, cot/csc need sin != 0.

Representation: a CONJUNCTION OF ATOMIC CONSTRAINTS (expr != 0, expr >= 0, expr > 0) collected from the UNEVALUATED parse,
inner nodes first. Not a set over R^n: SymPy has no usable R^n sets, and a conjunction keeps constraint structure
(x*y >= 0 stays one constraint). Comparison of two conjunctions:
  1. Constraints are normalised (!= atoms split into irreducible factors; sign conditions on rational functions become
     numer*denom). Univariate atoms are solved per variable with solveset into (I, E): I = intervals from >=,> atoms,
     E = excluded points from != atoms, kept as finite points + canonical PERIODIC CLASSES (period c*pi, residues), so
     pi/2 + k*pi as one ImageSet equals the union pi/2 + 2k*pi, 3pi/2 + 2k*pi. Atoms that are multivariate, or univariate
     but not safely solvable (inequalities with trig: solveset(sin(x)>0) returns one period only), stay "opaque" and are
     compared by canonical key only.
  2. Exact comparison: SAME when per-variable (I, E) are equal and opaque key sets are equal. Per-variable differences are
     named exactly when there are no opaque atoms.
  3. Pointwise check on a grid of exact points (rational and pi-multiples, plus endpoints and excluded points found above),
     evaluating each side's ORIGINAL constraints exactly. A point where the sides disagree PROVES a change (and is the
     witness). If the symbolic comparison claims a difference that no grid point confirms, or cannot decide: UNDECIDED.
No sympify/eval on input: callers pass the trees produced by the harness parser."""
import itertools
import sympy
from sympy import (Symbol, Rational, S, Interval, FiniteSet, EmptySet, Union, ImageSet, ConditionSet, Integers, pi,
                   solveset, together, fraction, factor_list, expand, oo, floor, ilcm, igcd)

class Undecided(Exception):
    pass

# ---------------------------------------------------------------- periodic point classes
class Per:
    """Points {(q + c*k)*pi + rest : k in Z, (q, rest) in res}; c a positive Rational."""
    def __init__(self, c, res):
        self.c, self.res = Rational(c), frozenset(res)
    def __eq__(self, o): return isinstance(o, Per) and (self.c, self.res) == (o.c, o.res)
    def __hash__(self): return hash((self.c, self.res))
    def __str__(self):
        return " | ".join(f"{sympy.simplify((q * pi + r))} + {self.c * pi}*k" for q, r in sorted(self.res, key=str))

def _lcm(a, b):
    return Rational(ilcm(a.p, b.p), igcd(a.q, b.q))

def _mod(q, c):
    return q - floor(q / c) * c

def p_expand(P, c2):
    m = int(c2 / P.c)
    return frozenset((_mod(q + j * P.c, c2), r) for q, r in P.res for j in range(m))

def p_min(P):
    if P is None or not P.res: return None
    N = len(P.res)
    for m in sorted([d for d in range(2, N + 1) if N % d == 0], reverse=True):
        nc = P.c / m
        red = {(_mod(q, nc), r) for q, r in P.res}
        if all((_mod(q + j * nc, P.c), r) in P.res for q, r in red for j in range(m)):
            return Per(nc, red)
    return P

def p_union(A, B):
    if A is None: return B
    if B is None: return A
    c = _lcm(A.c, B.c)
    return p_min(Per(c, p_expand(A, c) | p_expand(B, c)))

def p_sub(A, B):
    if A is None or B is None: return A
    c = _lcm(A.c, B.c)
    return p_min(Per(c, p_expand(A, c) - p_expand(B, c)))

def p_contains(P, v):
    if P is None: return False
    for q, r in P.res:
        t = sympy.simplify((v - r) / pi - q)
        if (t / P.c).is_integer: return True
    return False

def p_points(P, lo, hi):
    """Exact points of P inside the closed float range [lo, hi] (superset; caller filters with the exact interval)."""
    out = []
    for q, r in P.res:
        base = float((q * pi + r).evalf()); step = float((P.c * pi).evalf())
        k0 = int(sympy.floor((lo - base) / step)) - 1; k1 = int(sympy.ceiling((hi - base) / step)) + 1
        if k1 - k0 > 400: raise Undecided("too many periodic points in a bounded range")
        out += [(q + P.c * k) * pi + r for k in range(k0, k1 + 1)]
    return out

def decode_pts(res):
    """solveset result of an equation -> (finite sympy set, Per or None), or None if not understood."""
    if res is S.EmptySet: return FiniteSet(), None
    if isinstance(res, FiniteSet): return res, None
    if isinstance(res, ImageSet):
        if res.base_sets != (Integers,) or len(res.lamda.variables) != 1: return None
        n = res.lamda.variables[0]; e = sympy.expand(res.lamda.expr)
        a = sympy.diff(e, n)
        if a.has(n): return None
        b = e - a * n
        ca = sympy.simplify(a / pi)
        if not ca.is_Rational or ca == 0: return None
        ca = abs(ca)
        q = sympy.expand(b).coeff(pi)
        if not q.is_Rational: return None
        rest = sympy.simplify(b - q * pi)
        return FiniteSet(), Per(ca, {(_mod(Rational(q), ca), rest)})
    if isinstance(res, Union):
        fin, per = FiniteSet(), None
        for a in res.args:
            d = decode_pts(a)
            if d is None: return None
            fin, per = fin | d[0], p_union(per, d[1])
        return fin, p_min(per)
    return None

# ---------------------------------------------------------------- one-variable sets (used for reporting and specs)
class Dset:
    """S: sympy interval/finite set; per: Per or None; within: restricting interval for per (None = all of R)."""
    def __init__(self, S_=S.EmptySet, per=None, within=None, minus_per=None):
        self.S, self.per, self.within, self.minus_per = S_, p_min(per), within, minus_per
    def empty(self): return self.S == S.EmptySet and self.per is None
    def __eq__(self, o): return isinstance(o, Dset) and (self.S, self.per, self.within) == (o.S, o.per, o.within)
    def __hash__(self): return hash((self.S, self.per))
    def contains(self, v):
        if self.S.contains(v) is S.true: return True
        if self.per is not None and p_contains(self.per, v) and (self.within is None or self.within.contains(v) is S.true): return True
        return False
    def __str__(self):
        parts = []
        if self.S != S.EmptySet: parts.append(str(self.S) + (f" minus periodic {self.minus_per}" if self.minus_per is not None else ""))
        if self.per is not None: parts.append("{" + str(self.per) + "}" + (f" within {self.within}" if self.within is not None else ""))
        return " U ".join(parts) if parts else "EmptySet"

def per_spec(c, residues):
    """Spec helper for expected sets: points (q + c*k)*pi, q in residues (Rationals), rest 0."""
    return Per(Rational(c), {(_mod(Rational(q), Rational(c)), S.Zero) for q in residues})

# ---------------------------------------------------------------- constraint collection (unevaluated tree)
ALLOWED = (sympy.Add, sympy.Mul, sympy.Pow, sympy.Symbol, sympy.Number, sympy.NumberSymbol, sympy.exp, sympy.log,
           sympy.sin, sympy.cos, sympy.tan, sympy.cot, sympy.sec, sympy.csc, sympy.asin, sympy.acos, sympy.atan,
           sympy.Abs, sympy.sinh, sympy.cosh, sympy.tanh)

def _ev(e):
    with sympy.evaluate(True):
        return e.doit()

def _const_check(e, rel):
    """e has no symbols: True/False/None for the constraint."""
    v = _ev(e)
    if rel == "ne": z = v.is_zero; return None if z is None else (not z)
    if rel == "ge": return v.is_nonnegative
    return v.is_positive

def collect(expr):
    """Atomic constraints (expr, rel) required for expr to be defined over R, children before parents."""
    out = []
    for n in sympy.postorder_traversal(expr):
        if not isinstance(n, ALLOWED):
            raise Undecided(f"unsupported node {type(n).__name__}")
        if isinstance(n, sympy.Pow):
            base, ex = n.args
            exv = _ev(ex)
            if exv.free_symbols:
                if base.is_number and base.is_positive: continue
                raise Undecided("symbolic exponent")
            if base.is_number and not base.free_symbols and exv.is_Rational: 
                if _const_check(base, "ne") is False and exv <= 0: raise Undecided("0 to a non-positive power")
                if exv.q % 2 == 0 and _ev(base).is_negative: raise Undecided("even root of a negative constant")
                continue
            if base.is_number and base.is_positive: continue
            if exv.is_Rational:
                if exv == 0: out.append((base, "ne"))
                elif exv < 0: out.append((base, "gt" if exv.q % 2 == 0 else "ne"))
                elif exv.q % 2 == 0: out.append((base, "ge"))
            elif exv.is_number: out.append((base, "gt"))
            else: raise Undecided("exponent not a number")
        elif isinstance(n, (sympy.tan, sympy.sec)): out.append((sympy.cos(n.args[0]), "ne"))
        elif isinstance(n, (sympy.cot, sympy.csc)): out.append((sympy.sin(n.args[0]), "ne"))
        elif isinstance(n, sympy.log):
            if len(n.args) == 2 and n.args[1] != sympy.E: raise Undecided("log with a base")
            out.append((n.args[0], "gt"))
        elif isinstance(n, (sympy.asin, sympy.acos)):
            out += [(1 - n.args[0], "ge"), (1 + n.args[0], "ge")]
    return out

# ---------------------------------------------------------------- normalisation and per-variable solving
_SYM = {"ne": "!= 0", "ge": ">= 0", "gt": "> 0", "le": "<= 0", "lt": "< 0"}
_FLIP = {"ge": "le", "gt": "lt"}

def _canon_key(e, rel):
    """Readable key ("x - y != 0") for an opaque atom; equal for e and for the sign-flipped relation of -e."""
    e = sympy.factor(expand(e)); f = sympy.factor(expand(-e))
    if rel == "ne": return min(f"{e} != 0", f"{f} != 0")
    return min(f"{e} {_SYM[rel]}", f"{f} {_SYM[_FLIP[rel]]}")

def normalise(raw):
    """-> list of (expr, rel) atoms (evaluated, factored where possible); constants are checked and dropped."""
    atoms = []
    for e, rel in raw:
        e = _ev(e)
        if not e.free_symbols:
            ok = _const_check(e, rel)
            if ok is not True: raise Undecided(f"constant constraint {e} {rel} not satisfiable/decidable")
            continue
        with sympy.evaluate(True):
            t = together(e)
            n, d = fraction(t)
            if rel == "ne":
                try:
                    fs = [f for f, _ in factor_list(n)[1]]
                except Exception:
                    fs = [n]
                atoms += [(f, "ne") for f in fs if f.free_symbols]
            else:
                if t.is_rational_function():
                    atoms.append((expand(n * d) if (n * d).is_polynomial() else n * d, rel))
                else:
                    atoms.append((e, rel))
    return atoms

_PERIODIC = (sympy.sin, sympy.cos, sympy.tan, sympy.cot, sympy.sec, sympy.csc)

def _interval_ok(res):
    if res is S.EmptySet or isinstance(res, (Interval, FiniteSet)): return True
    return isinstance(res, Union) and all(_interval_ok(a) for a in res.args)

def build(atoms):
    """-> dict var -> [I, E(Dset-like: fin set, per)], list of opaque keys, set of variables."""
    dom, opaque, vars_ = {}, set(), set()
    for e, rel in atoms:
        vs = e.free_symbols; vars_ |= vs
        if len(vs) != 1:
            opaque.add(_canon_key(e, rel)); continue
        v = next(iter(vs))
        I, Efin, Eper = dom.setdefault(v, [S.Reals, FiniteSet(), None])
        if I == S.EmptySet: raise Undecided("empty domain")
        try:
            if rel == "ne":
                d = decode_pts(solveset(e, v, S.Reals))
                if d is None: opaque.add(_canon_key(e, rel)); continue
                dom[v][1], dom[v][2] = Efin | d[0], p_union(Eper, d[1])
            else:
                if e.has(*_PERIODIC): opaque.add(_canon_key(e, rel)); continue
                res = solveset(e >= 0 if rel == "ge" else e > 0, v, I)
                if not _interval_ok(res): opaque.add(_canon_key(e, rel)); continue
                dom[v][0] = I & res
        except Undecided: raise
        except Exception:
            opaque.add(_canon_key(e, rel))
    return dom, opaque, vars_

def _diff(IA, EA, IB, EB):
    """D_A minus D_B for D = I minus E (one variable). Returns Dset."""
    EAfin, EAper = EA; EBfin, EBper = EB
    S1 = (IA - IB) - EAfin
    minus_per = None
    if EAper is not None:
        if S1.is_finite_set: S1 = FiniteSet(*[p for p in S1 if not p_contains(EAper, p)])
        elif S1 != S.EmptySet: minus_per = EAper
    fin = FiniteSet(*[p for p in EBfin if IA.contains(p) is S.true and p not in EAfin and not p_contains(EAper, p)])
    per = p_sub(EBper, EAper)
    within = None
    if per is not None and IA != S.Reals:
        lo, hi = IA.inf, IA.sup
        if lo.is_finite and hi.is_finite:
            pts = [p for p in p_points(per, float(lo), float(hi)) if IA.contains(p) is S.true]
            fin, per = fin | FiniteSet(*pts), None
        else:
            within = IA
    return Dset(S1 | fin, per, within, minus_per)

def compare_symbolic(da, db):
    """da, db = (dom, opaque, vars). -> ('SAME'|'DIFF'|'UNKNOWN', excl{var:Dset}, added{var:Dset}, opaque_differs)"""
    (doma, opa, _), (domb, opb, _) = da, db
    excl, added = {}, {}
    for v in set(doma) | set(domb):
        IA, Fa, Pa = doma.get(v, [S.Reals, FiniteSet(), None]); IB, Fb, Pb = domb.get(v, [S.Reals, FiniteSet(), None])
        x = _diff(IA, (Fa, Pa), IB, (Fb, Pb)); y = _diff(IB, (Fb, Pb), IA, (Fa, Pa))
        if not x.empty(): excl[v] = x
        if not y.empty(): added[v] = y
    # opaque atoms present on either side: the per-variable sets are then only a superset hint, not the exact difference
    if opa != opb: return "UNKNOWN", excl, added, True
    return ("DIFF" if (excl or added) else "SAME"), excl, added, bool(opa)

# ---------------------------------------------------------------- pointwise membership
def _sat(e, rel, pt):
    """True / False / None (unknown) for constraint at an exact point."""
    with sympy.evaluate(True):
        try:
            v = e.subs(pt)
        except Exception:
            return None
        if v.has(sympy.zoo, sympy.nan, oo, -oo): return False
        if v.is_real is False: return False
        if rel == "ne": z = v.is_zero; return None if z is None else (not z)
        r = v.is_nonnegative if rel == "ge" else v.is_positive
        return r

def member(raw, pt):
    unknown = False
    for e, rel in raw:
        r = _sat(e, rel, pt)
        if r is False: return False
        if r is None: unknown = True
    return None if unknown else True

BASE = [Rational(k, 2) for k in (-6, -4, -2, -1, 0, 1, 2, 4, 6)] + [pi / 2, pi, pi / 4, -pi / 2, 3 * pi / 2, -pi]

def candidates(vars_, specials):
    n = len(vars_)
    cap = {1: 40, 2: 11, 3: 6}.get(n, 4)
    per_var = {}
    for v in vars_:
        sp = [s for s in specials.get(v, []) if s.is_number]
        extra = []
        for s in sp: extra += [s, s - 1, s + 1, s - Rational(1, 2), s + Rational(1, 2)]
        seen, lst = set(), []
        for s in sp + extra + BASE:
            if s not in seen: seen.add(s); lst.append(s)
        per_var[v] = lst[:cap]
    return per_var

def witness_search(rawA, rawB, vars_, specials, budget=1500):
    """-> (witness in A not B, witness in B not A, points tried). Points where membership is unknown are skipped."""
    vs = sorted(vars_, key=str)
    if not vs: return None, None, 0
    cands = candidates(vs, specials)
    wab = wba = None; tried = 0
    for combo in itertools.product(*[cands[v] for v in vs]):
        if tried >= budget: break
        tried += 1
        pt = dict(zip(vs, combo))
        ma, mb = member(rawA, pt), member(rawB, pt)
        if ma is True and mb is False and wab is None: wab = pt
        if mb is True and ma is False and wba is None: wba = pt
        if wab is not None and wba is not None: break
    return wab, wba, tried

def _specials(*doms):
    sp = {}
    for dom, _, _ in doms:
        for v, (I, Ef, Ep) in dom.items():
            L = sp.setdefault(v, [])
            if I != S.Reals:
                try:
                    for p in I.boundary: L.append(p)
                except Exception: pass
                try:
                    if I.inf.is_finite: L.append(I.inf + 1)
                    if I.sup.is_finite: L.append(I.sup - 1)
                except Exception: pass
            L.extend(Ef)
            if Ep is not None:
                for q, r in Ep.res: L += [q * pi + r, (q + Ep.c) * pi + r, (q - Ep.c) * pi + r]
    return sp

# ---------------------------------------------------------------- top level
def domain_verdict(parts_a, parts_b):
    """parts_*: unevaluated sympy trees (both sides of an equation count). Returns a plain dict of facts."""
    res = dict(verdict="UNDECIDED", sym="?", excluded={}, added={}, wit_excl=None, wit_add=None, why="")
    try:
        rawA = [c for p in parts_a for c in collect(p)]
        rawB = [c for p in parts_b for c in collect(p)]
        atA, atB = normalise(rawA), normalise(rawB)
        evA = [(_ev(e), r) for e, r in rawA if _ev(e).free_symbols]
        evB = [(_ev(e), r) for e, r in rawB if _ev(e).free_symbols]
        da, db = build(atA), build(atB)
        vars_ = set(da[2]) | set(db[2])
        sym, excl, added, opdiff = compare_symbolic(da, db)
        wab, wba, tried = witness_search(evA, evB, vars_, _specials(da, db))
    except Undecided as u:
        res["why"] = f"undecided: {u}"; return res
    res.update(sym=sym, excluded=excl, added=added, wit_excl=wab, wit_add=wba, tried=tried, opaque_differs=opdiff)
    if opdiff:   # opaque constraints involved: per-variable sets are NOT the exact difference: hint only, never the answer
        res.update(excluded={}, added={}, hint_excl=excl, hint_add=added,
                   cons_only_before=sorted(da[1] - db[1]), cons_only_after=sorted(db[1] - da[1]))
    if wab is not None or wba is not None:
        res["verdict"] = "CHANGED"
        res["why"] = ("pointwise witness only (opaque constraints involved; symbolic sets are a superset hint)" if opdiff and sym != "SAME" else
                      "symbolic and pointwise agree" if sym == "DIFF" else
                      "pointwise witness only (symbolic: %s)" % ("contradicted by a point!" if sym == "SAME" else "could not name the set"))
    elif sym == "SAME":
        res["verdict"], res["why"] = "SAME", f"same constraints/sets; no differing point among {tried} tried"
    elif sym == "DIFF":
        res["why"] = f"symbolic difference not confirmed by any of {tried} points"
    else:
        res["why"] = f"opaque constraints differ and no differing point among {tried} tried"
    return res

def fmt_pt(pt):
    return None if pt is None else "(" + ", ".join(f"{k}={v}" for k, v in sorted(pt.items(), key=lambda kv: str(kv[0]))) + ")"

def fmt_sets(d):
    return "; ".join(f"{v} in {s}" for v, s in sorted(d.items(), key=lambda kv: str(kv[0])))

def s7b(a, b, step):
    """Harness-compatible strategy: numeric real check first (as S7), then S7b domain tracking on the unevaluated parse."""
    import strategies
    A, B = strategies.pair(a, b, step)
    v, d = strategies.numeric(A, B, "real")
    if v != "EQ":
        return v, "numeric(real): " + d
    ra, rb = step["raw"]
    parts = lambda e: [e.lhs, e.rhs] if step["kind"] == "eq" else [e]
    r = domain_verdict(parts(ra), parts(rb))
    if r["verdict"] == "SAME": return "EQ", "equal at samples; " + r["why"]
    if r["verdict"] == "UNDECIDED": return "UND", r["why"]
    return "EQ_DOM", describe(r)

def describe(r):
    bits = []
    if r["excluded"]: bits.append("excluded (defined before, not after): " + fmt_sets(r["excluded"]))
    if r["added"]: bits.append("added (defined after, not before): " + fmt_sets(r["added"]))
    if r.get("opaque_differs"):
        bits.append("only-before constraints (the 'only if' assumptions): " + (", ".join(r["cons_only_before"]) or "-") + "; only-after: " + (", ".join(r["cons_only_after"]) or "-"))
    if r["wit_excl"]: bits.append("witness excluded " + fmt_pt(r["wit_excl"]))
    if r["wit_add"]: bits.append("witness added " + fmt_pt(r["wit_add"]))
    return "; ".join(bits)

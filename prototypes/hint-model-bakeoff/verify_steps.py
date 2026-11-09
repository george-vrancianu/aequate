"""PROTOTYPE. SymPy check of every hidden next step and answer in steps_bakeoff.py. Exit 1 on any failure."""
import re, sys, warnings
warnings.simplefilter("ignore")
import sympy
from sympy import Symbol, Eq, solveset, S, simplify, cancel, solve, reduce_inequalities
from sympy.solvers.inequalities import solve_univariate_inequality
from parsing import check_line
from steps_bakeoff import ITEMS


def one(latex):
    r = check_line(latex)
    assert len(r) == 1, (latex, r)
    return r[0]


def lines(latex):
    return check_line(latex)


def atoms(answer):
    return [a for a in re.split(r"\\lor|\\land|\\vee|\\wedge", answer) if a.strip()]


def sols(rel, x):
    if isinstance(rel, sympy.Basic) and rel.free_symbols - {x}:
        return set(solve(rel, x))
    return solveset(rel, x, S.Reals)


def verify(it):
    k, v = it["kind"], it["var"]
    cur, first = it["steps"][it["builds_on"] - 1], it["steps"][0]
    if k == "eq":
        x = Symbol(v)
        s_first, s_cur, s_next = sols(one(first), x), sols(one(cur), x), sols(one(it["next_step"]), x)
        ans = {one(a).rhs for a in atoms(it["answer"])}
        ok_next = (s_next == s_cur) if not it["verdicts"] or it["verdicts"] == ["not equivalent"] else s_next.issubset(s_cur) or s_next == s_cur
        if it["verdicts"] == ["one-way"]:
            ok_next = s_cur == s_next            # next step is equivalent to the (one-way) current step
        e1 = one(first)
        def holds(r):  # real-valid root of the ORIGINAL first step (principal branch: complex residual = rejected)
            return abs(complex(sympy.N(e1.lhs.subs(x, r) - e1.rhs.subs(x, r)))) < 1e-9 if not r.free_symbols else True
        valid = {sympy.nsimplify(r) for r in s_first if holds(r)}
        ok_ans = valid == {sympy.nsimplify(a) for a in ans}
        return ok_next, ok_ans, (s_first, s_cur, s_next, ans)
    if k == "ineq":
        x = Symbol(v)
        f = lambda s: solve_univariate_inequality(one(s), x, relational=False)
        return f(cur) == f(it["next_step"]), f(first) == f(it["answer"]), (f(first), f(it["next_step"]), f(it["answer"]))
    if k == "sys":
        x, y = sympy.symbols("x y")
        f = lambda s: solve(lines(s), [x, y], dict=True)
        sf = f(first)
        ns = sympy.solve(lines(it["next_step"]) + [lines(first)[1]], [x, y], dict=True)
        ans = [{Symbol(one(a).lhs.name): one(a).rhs for a in atoms(it["answer"])}]
        return ns == sf, sf == ans, (sf, ns, ans)
    if k == "expr":
        c, n, a = one(cur), one(it["next_step"]), one(it["answer"])
        return simplify(c - n) == 0, cancel(c - a) == 0, (c, n, a)
    raise ValueError(k)


bad = 0
for it in ITEMS:
    ok_next, ok_ans, info = verify(it)
    print(f"{'OK ' if ok_next and ok_ans else 'BAD'} {it['id']:6} next_step ok={ok_next} answer ok={ok_ans}  {info}")
    bad += not (ok_next and ok_ans)
print("PASS" if not bad else f"FAIL ({bad})")
sys.exit(1 if bad else 0)

"""Run every step through every strategy under hard wall-clock budgets.

    python -I run.py            # writes results/results.json and results/results.md

Each (step, strategy) check runs in a forked worker that is killed when the
budget runs out; a kill maps to verdict "timeout" (amber), as the research
recommends. The parent warms SymPy's caches once before forking, so the
numbers reflect a long-running checker worker, not a cold start.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sympy  # noqa: E402

import strategies as st  # noqa: E402
from steps import EXTRAS, PHYSICS, STEPS, UNITS  # noqa: E402

BUDGETS = [0.2, 1.0]

STRATEGIES = {
    "S0 structural": lambda s: st.s0_structural(s),
    "S1 simplify (C)": lambda s: st.s1_simplify(s, "complex"),
    "S1 simplify (R)": lambda s: st.s1_simplify(s, "real"),
    "S1 simplify (P)": lambda s: st.s1_simplify(s, "positive"),
    "S2 equals (C)": lambda s: st.s2_equals(s, "complex"),
    "S2 equals (R)": lambda s: st.s2_equals(s, "real"),
    "S2 equals (P)": lambda s: st.s2_equals(s, "positive"),
    "S3 numeric (R)": lambda s: st.s3_numeric(s, "real"),
    "S3 numeric (C)": lambda s: st.s3_numeric(s, "complex"),
    "S4 layered (C)": lambda s: st.s4_layered(s, "complex"),
    "S4 layered (R)": lambda s: st.s4_layered(s, "real"),
    "S4 layered (P)": lambda s: st.s4_layered(s, "positive"),
    "S5 solution sets": lambda s: st.s5_solution_sets(s),
    "S5 solution sets (P)": lambda s: st.s5_solution_sets(s, target_domain=sympy.Interval.open(0, sympy.oo)),
    "S7 domain": lambda s: st.s7_domain(s),
    "PIPELINE": lambda s: st.pipeline(s, s.get("_units")),
}
PHYSICS_ONLY = {"S8 units": lambda s: st.s8_units(s, UNITS)}


def _worker(conn, step, name, fn):
    try:
        t0 = time.perf_counter()
        prev, curr = st.parse(step["prev"]), st.parse(step["curr"])
        t_parse = time.perf_counter() - t0
        s = dict(step, _prev=prev, _curr=curr)
        t1 = time.perf_counter()
        verdict, detail = fn(s)
        conn.send(("ok", verdict, str(detail), t_parse, time.perf_counter() - t1))
    except Exception as e:  # noqa: BLE001
        conn.send(("error", "error", f"{type(e).__name__}: {e}", 0.0, 0.0))
    finally:
        conn.close()


def run_check(step, name, fn, budget):
    ctx = mp.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_worker, args=(child, step, name, fn))
    t0 = time.perf_counter()
    p.start()
    child.close()
    if parent.poll(budget):
        status, verdict, detail, t_parse, t_check = parent.recv()
        wall = time.perf_counter() - t0
        p.join()
        return dict(verdict=verdict, detail=detail, parse_s=t_parse, check_s=t_check, wall_s=wall)
    p.kill()
    p.join()
    return dict(verdict="timeout", detail=f"killed after {budget}s", parse_s=None, check_s=None,
                wall_s=time.perf_counter() - t0)


def warm_up():
    x = sympy.Symbol("x")
    sympy.simplify((x + 1) ** 2 - x**2 - 2 * x - 1)
    sympy.solveset(x**2 - 1, x, sympy.S.Reals)
    st.parse(r"\frac{x^2-1}{x-1}")
    (sympy.sin(x) ** 2).equals(1 - sympy.cos(x) ** 2)
    st._ureg()


def main():
    warm_up()
    groups = [("core", STEPS, False), ("extra", EXTRAS, False), ("physics", PHYSICS, True)]
    results = []
    for group, steps, is_phys in groups:
        for step in steps:
            step = dict(step, _units=UNITS if is_phys else None)
            strategies = dict(STRATEGIES, **(PHYSICS_ONLY if is_phys else {}))
            row = dict(group=group, **{k: v for k, v in step.items() if not k.startswith("_")}, checks={})
            for name, fn in strategies.items():
                row["checks"][name] = {f"{b}s": run_check(step, name, fn, b) for b in BUDGETS}
            results.append(row)
            print(step["id"], row["checks"]["PIPELINE"]["1.0s"]["verdict"], file=sys.stderr)
    meta = dict(
        python=platform.python_version(), sympy=sympy.__version__,
        pint=__import__("pint").__version__, latex_backend=st.BACKEND,
        machine=platform.machine(), cpu_count=os.cpu_count(), budgets=BUDGETS,
        rel_tol=str(st.REL_TOL), n_points=st.N_POINTS,
        date=time.strftime("%Y-%m-%d"),
    )
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(dict(meta=meta, results=results), indent=1, ensure_ascii=False))
    print("wrote", out / "results.json", file=sys.stderr)


if __name__ == "__main__":
    main()

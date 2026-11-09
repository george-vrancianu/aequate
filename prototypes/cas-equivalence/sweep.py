"""PROTOTYPE (throwaway), issue #40: timeout-budget sweep over the original 20 steps and the hard set.
    uv run python sweep.py run [--reps 3] [--workers 4] [--budgets 2,0.5,0.2,0.1] [--quick]   -> results-hard.json
    uv run python sweep.py report                                                              -> RESULTS-hard.md
Every call is a forked child killed on timeout (as in run.py), with a 4 GB address-space limit as a safety net.
At most --workers (default 4, hard cap 4) sweep processes run at once; each runs its calls one at a time.
Does not touch run.py / RESULTS.md / results.json."""
import argparse, json, multiprocessing as mp, os, platform, resource, statistics, sys, time, warnings
warnings.simplefilter("ignore")
import sympy
import hardlib
from hardlib import parse_step, make_st, run_strategy, stack
from parsing import check_line
from steps import STEPS
from steps_hard import STEPS_HARD
from strategies import STRATEGIES, score

ctx = mp.get_context("fork")
SIDS = [s[0] for s in STRATEGIES]
ALL = [dict(s, set="orig", key=f"O{s['id']}", cat=s.get("topic")) for s in STEPS] + \
      [dict(s, set="hard", key=s["id"]) for s in STEPS_HARD]
BY_KEY = {s["key"]: s for s in ALL}
PARSED = {}          # key -> parsed dict (set in the parent before forking workers)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results-hard.json")
MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RESULTS-hard.md")
MEM = 4 * 1024 ** 3

def _w(conn, fn, args):
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))
        t = time.perf_counter()
        r = fn(*args)
        conn.send(("ok", r, time.perf_counter() - t))
    except BaseException as e:
        conn.send(("err", f"{type(e).__name__}: {e}"[:200], 0.0))
    conn.close()

def isolated(fn, args, timeout):
    """-> (status, value, wall_s, inner_s). Same mechanism as run.py's isolated() plus the worker's own timer."""
    rx, tx = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_w, args=(tx, fn, args), daemon=True)
    t0 = time.perf_counter()
    p.start(); tx.close()
    inner = None
    if rx.poll(timeout):
        try:
            with sympy.evaluate(False):
                st, val, inner = rx.recv()
        except EOFError:
            st, val = "err", "worker died"
    else:
        st, val = "timeout", None
        p.kill()
    dt = time.perf_counter() - t0
    p.join(2)
    if p.is_alive():
        p.kill(); p.join()
    return st, val, dt, inner

def noop(): return None

def _call(key, sid):
    p, step = PARSED[key], BY_KEY[key]
    return run_strategy(sid, p["a"], p["b"], make_st(step, p))

def _stack(key):
    return stack(BY_KEY[key])

def _parse_breakdown(key):
    """Warm in-process split of the parse cost of one step (before + after, all pieces): ANTLR strict, Lark cross-check parse, and the `same()` comparison."""
    import parsing
    from sympy.parsing.latex import parse_latex
    tot = dict(antlr=0.0, lark=0.0, same=0.0)
    step = BY_KEY[key]
    for line in (step["before"], step["after"]):
        for l in parsing.split_system(line):
            for part in parsing.split_chain(l):
                for b in parsing.rewrite(part):
                    t = time.perf_counter(); e = parse_latex(b, strict=True); tot["antlr"] += time.perf_counter() - t
                    e = parsing._fix(e, True)
                    t = time.perf_counter()
                    try: lk = parse_latex(b, backend="lark")
                    except Exception: lk = None
                    tot["lark"] += time.perf_counter() - t
                    t = time.perf_counter()
                    if isinstance(lk, sympy.Basic): parsing.same(*parsing._pair(e, parsing._fix(lk, True)))
                    elif lk is not None and type(lk).__name__ == "Tree" and lk.data == "_ambig":
                        alts = [parsing._fix(c, True) for c in lk.children if isinstance(c, sympy.Basic)]
                        any(parsing.same(*parsing._pair(e, c)) for c in alts)
                    tot["same"] += time.perf_counter() - t
    return {k: v * 1000 for k, v in tot.items()}

def _parse_only(key):
    return parse_step(BY_KEY[key])

def _parse_timed(key):
    t = time.perf_counter(); parse_step(BY_KEY[key]); return time.perf_counter() - t

def _row(kind, key, sid, budget, rep, res):
    st, val, wall, inner = res
    r = dict(kind=kind, key=key, sid=sid, budget=budget, rep=rep, status=st, wall_ms=wall * 1000,
             inner_ms=None if inner is None else inner * 1000)
    if kind == "strategy":
        if st == "ok": r["verdict"], r["detail"] = val[0], str(val[1])[:160]
        elif st == "timeout": r["verdict"], r["detail"] = "TO", f"killed after {budget}s"
        else: r["verdict"], r["detail"] = "ERR", str(val)
        r["score"] = score(BY_KEY[key]["expected"], r["verdict"])
    else:
        if st == "ok":
            r["verdict"], tr = val; r["trace"] = [(n, round(m, 2), v) for n, m, v in tr]
        else:
            r["verdict"], r["trace"] = ("TO" if st == "timeout" else "ERR"), []
            r["detail"] = str(val)
        r["score"] = score(BY_KEY[key]["expected"], "UND" if r["verdict"] in ("TO", "ERR", "EQ_NODOM") else r["verdict"])
    return r

def worker(idx, tasks, q):
    rows, floor = [], []
    for _ in range(20): floor.append(isolated(noop, (), 2.0)[2] * 1000)
    for (kind, rep, budget, key) in tasks:
        if kind == "strategy":
            for sid in SIDS:
                rows.append(_row("strategy", key, sid, budget, rep, isolated(_call, (key, sid), budget)))
        else:
            rows.append(_row("stack", key, "stack", budget, rep, isolated(_stack, (key,), budget)))
    for _ in range(20): floor.append(isolated(noop, (), 2.0)[2] * 1000)
    q.put((rows, floor))

def run_pool(procs, tasks):
    """Round-robin the tasks over <= 4 sweep processes."""
    q = ctx.Queue()
    ps = []
    for i in range(procs):
        p = ctx.Process(target=worker, args=(i, tasks[i::procs], q)); p.start(); ps.append(p)
    rows, floor = [], []
    for _ in ps:
        r, f = q.get(); rows += r; floor += f
    for p in ps: p.join()
    return rows, floor

# ---------- warm worker pool (one long-lived worker, respawned after a kill) ----------
def _pool_loop(conn):
    resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))
    while True:
        try:
            with sympy.evaluate(False):
                msg = conn.recv()
        except EOFError:
            return
        sid, a, b, st = msg
        t = time.perf_counter()
        try: out = ("ok", run_strategy(sid, a, b, st), time.perf_counter() - t)
        except BaseException as e: out = ("err", f"{type(e).__name__}: {e}"[:200], 0.0)
        conn.send(out)

class WarmWorker:
    def __init__(self): self.respawns = 0; self._spawn()
    def _spawn(self):
        self.parent, child = ctx.Pipe()
        self.p = ctx.Process(target=_pool_loop, args=(child,), daemon=True); self.p.start(); child.close()
    def call(self, msg, timeout):
        t0 = time.perf_counter()
        self.parent.send(msg)
        if self.parent.poll(timeout):
            with sympy.evaluate(False): st, val, inner = self.parent.recv()
            return st, val, time.perf_counter() - t0, inner
        self.p.kill(); self.p.join(); self.respawns += 1
        dt = time.perf_counter() - t0
        self._spawn()                                 # respawn outside the measured call (a real pool would do it in the background)
        return "timeout", None, dt, None
    def close(self): self.p.kill(); self.p.join()

def pool_pass(budget, reps):
    w = WarmWorker(); rows = []
    for rep in range(reps):
        for key, p in PARSED.items():
            st = make_st(BY_KEY[key], p)
            for sid in SIDS:
                rows.append(_row("strategy", key, sid, budget, rep, w.call((sid, p["a"], p["b"], st), budget)))
    n = w.respawns; w.close()
    return rows, n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "report"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--budgets", default="2,0.5,0.2,0.1")
    ap.add_argument("--ref-budget", type=float, default=10.0, help="long budget used once to measure how long the timed-out calls really take")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=OUT, help="raw JSON path (default results-hard.json)")
    ap.add_argument("--md", default=MD, help="report mode: Markdown output path (default RESULTS-hard.md; analysis-hard.md is read from its directory)")
    a = ap.parse_args()
    if a.mode == "report":
        import sweep_report; sweep_report.write(a.out, a.md); return
    workers = min(4, a.workers)
    budgets = [float(x) for x in a.budgets.split(",")]
    reps = 1 if a.quick else a.reps
    keys = [k for k in BY_KEY if not a.quick or k in ("O1", "O7", "H2", "H7", "H11", "H27", "H29", "H31", "H34")]
    check_line("x+1")                                              # warm up ANTLR/Lark in the parent
    parse_info = {}
    for k in keys:
        st, val, wall, inner = isolated(_parse_only, (k,), 10.0)
        if st != "ok":
            parse_info[k] = dict(status=st, detail=str(val), warm_ms=None, wall_ms=wall * 1000); print(k, "PARSE", st, val, flush=True); continue
        with sympy.evaluate(False): PARSED[k] = val
        t = [isolated(_parse_timed, (k,), 10.0) for _ in range(reps)]
        warm = [x[1] * 1000 for x in t if x[0] == "ok"]
        parse_info[k] = dict(status="ok", warm_ms=statistics.median(warm) if warm else None, wall_ms=wall * 1000)
    for k in PARSED:
        r = isolated(_parse_breakdown, (k,), 10.0)
        r2 = isolated(_parse_breakdown, (k,), 10.0)          # second run in a fresh fork: first-call effects excluded by taking the min
        if r[0] == "ok" and r2[0] == "ok": parse_info[k]["breakdown_ms"] = {x: min(r[1][x], r2[1][x]) for x in r[1]}
    for k in keys:
        if k not in PARSED: BY_KEY[k]["_rej"] = parse_info[k]["detail"]
    print("parsed", len(PARSED), "of", len(keys), "rejected:", [k for k in keys if k not in PARSED], flush=True)
    # fork/IPC floor, alone (sequential, before the parallel sweep)
    fl = sorted(isolated(noop, (), 2.0)[2] * 1000 for _ in range(200))
    ww = WarmWorker(); ww.call(("S0e", *[PARSED["O1"][x] for x in ("a", "b")], make_st(BY_KEY["O1"], PARSED["O1"])), 5)
    pf = sorted(ww.call(("S0e", PARSED["O1"]["a"], PARSED["O1"]["b"], make_st(BY_KEY["O1"], PARSED["O1"])), 5)[2] * 1000 for _ in range(200))
    ww.close()
    meta = dict(machine=f"{platform.platform()}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}, SymPy {sympy.__version__}",
                date=time.strftime("%Y-%m-%d %H:%M"), reps=reps, budgets=budgets, workers=workers, ref_budget=a.ref_budget,
                floor_alone_ms=dict(median=statistics.median(fl), p95=fl[int(.95 * len(fl))], max=fl[-1], n=len(fl)),
                warm_pool_s0e_roundtrip_ms=dict(median=statistics.median(pf), p95=pf[int(.95 * len(pf))], max=pf[-1], n=len(pf)))
    print("floor alone", meta["floor_alone_ms"], "warm roundtrip", meta["warm_pool_s0e_roundtrip_ms"], flush=True)
    tasks = []
    for rep in range(reps):
        for b in budgets:
            for k in PARSED:
                tasks.append(("strategy", rep, b, k)); tasks.append(("stack", rep, b, k))
    # only steps that parse get tasks; parse rejects get no stack row (sweep_report counts them as UND)
    t0 = time.time()
    rows, floor_load = run_pool(workers, tasks)
    meta["sweep_seconds"] = time.time() - t0
    meta["floor_under_load_ms"] = dict(median=statistics.median(floor_load), p95=sorted(floor_load)[int(.95 * len(floor_load))], max=max(floor_load), n=len(floor_load))
    print("sweep done in %.0fs" % meta["sweep_seconds"], meta["floor_under_load_ms"], flush=True)
    # reference: how long do the cells that timed out at the largest budget really take (one run, long budget)
    big = max(budgets)
    to_cells = sorted({(r["key"], r["sid"]) for r in rows if r["kind"] == "strategy" and r["budget"] == big and r["status"] == "timeout"})
    to_stack = sorted({r["key"] for r in rows if r["kind"] == "stack" and r["budget"] == big and r["status"] == "timeout"})
    ref_tasks = []
    q = ctx.Queue()
    def ref_worker(items):
        out = []
        for kind, key, sid in items:
            if kind == "strategy": out.append(_row("strategy", key, sid, a.ref_budget, 0, isolated(_call, (key, sid), a.ref_budget)))
            else: out.append(_row("stack", key, "stack", a.ref_budget, 0, isolated(_stack, (key,), a.ref_budget)))
        q.put(out)
    items = [("strategy", k, s) for k, s in to_cells] + [("stack", k, None) for k in to_stack]
    ps = [ctx.Process(target=ref_worker, args=(items[i::workers],)) for i in range(workers)]
    for p in ps: p.start()
    ref = []
    for _ in ps: ref += q.get()
    for p in ps: p.join()
    # uncapped per-stage trace of the stack, all steps (single sequential pass, 3 reps, long budget), for the async-upgrade analysis
    trace_rows = []
    for rep in range(reps):
        for k in PARSED:
            trace_rows.append(_row("stack", k, "stack", a.ref_budget, rep, isolated(_stack, (k,), a.ref_budget)))
    # warm pool datapoint (sequential), at the 0.5 s budget if present, else the middle one
    pb = 0.5 if 0.5 in budgets else budgets[len(budgets) // 2]
    pool_rows, respawns = pool_pass(pb, reps)
    meta["pool_budget"], meta["pool_respawns"] = pb, respawns
    json.dump(dict(meta=meta, parse=parse_info, rows=rows, ref=ref, trace=trace_rows, pool=pool_rows,
                   steps=[{k: v for k, v in s.items()} for s in ALL if s["key"] in keys]), open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out, flush=True)

if __name__ == "__main__":
    main()

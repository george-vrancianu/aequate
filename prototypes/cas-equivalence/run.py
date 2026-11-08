"""PROTOTYPE (throwaway), issue #14. Run: uv run python run.py [--timeout 2.0] [--parse-timeout 10]
Every parse and every strategy call runs in a forked worker that is killed on timeout (SIGKILL)."""
import argparse, multiprocessing as mp, os, platform, statistics, sys, time, json, warnings
warnings.simplefilter("ignore")
import sympy
from parsing import check_line, Reject
from rawparse import check_line_raw
from steps import STEPS
import strategies
from strategies import STRATEGIES, score

ctx = mp.get_context("fork")

def _w(conn, fn, args):
    try:
        t = time.perf_counter()
        r = fn(*args)
        conn.send(("ok", r, time.perf_counter() - t))
    except BaseException as e:  # incl. RecursionError, Reject
        conn.send(("err", f"{type(e).__name__}: {e}"[:200], 0.0))
    conn.close()

def isolated(fn, args, timeout):
    """-> (status, value, seconds). status ok|err|timeout. Timeout kills the process."""
    rx, tx = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_w, args=(tx, fn, args), daemon=True)
    t0 = time.perf_counter()
    p.start(); tx.close()
    if rx.poll(timeout):
        try:
            with sympy.evaluate(False):   # unpickling re-runs constructors: keep unevaluated trees unevaluated
                st, val, _ = rx.recv()
        except EOFError:
            st, val = "err", "worker died"
    else:
        st, val = "timeout", None
        p.kill()
    dt = time.perf_counter() - t0
    p.join(2)
    if p.is_alive():
        p.kill(); p.join()
    return st, val, dt

def parse_pair(before, after):
    return [check_line(before), check_line(after), check_line_raw(before), check_line_raw(after)]

def _noop():
    return None

def _equals_spread(a, b, st):
    A, B = strategies.pair(a, b, st)
    out = {}
    for k in range(10):
        strategies.SEED = k
        v = strategies._s2(a, b, st)[0]
        out[v] = out.get(v, 0) + 1
    strategies.SEED = 0
    return out

EXTRAS = [
 dict(id="x1", before=r"\frac{x^2-25}{x-5}", after=r"x+5", kind="expr", expected="DOMAIN"),
 dict(id="x2", before=r"\sqrt{x}\cdot\sqrt{x}", after=r"x", kind="expr", expected="DOMAIN"),
 dict(id="x3", before=r"\frac{x}{x}", after=r"1", kind="expr", expected="DOMAIN"),
 dict(id="x4", before=r"(x-3)^2=0", after=r"x=3", kind="eq", expected="EQUIV (solution set)"),
 dict(id="x5", before=r"\tg(x)", after=r"\tg(x)", kind="expr", expected="EQUIV"),
 dict(id="x6", before=r"\frac{\sin x}{\cos x}", after=r"\tg x", kind="expr", expected="EQUIV"),
 dict(id="x7", before=r"\tg(x)\cdot\cos(x)", after=r"\frac{\sin(x)\cos(x)}{\cos(x)}", kind="expr", expected="EQUIV"),
]

def _sleeper():
    time.sleep(60)

def ms(x): return f"{x*1000:.0f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=float(os.environ.get("CAS_TIMEOUT", 2.0)))
    ap.add_argument("--parse-timeout", type=float, default=10.0)
    ap.add_argument("--tight", type=float, default=0.05, help="tight budget for the timeout-sensitivity pass")
    ap.add_argument("--out", default="RESULTS.md")
    args = ap.parse_args()
    # warm up in the parent so forked workers start hot (imports, ANTLR/Lark grammars)
    check_line(r"x+1")
    rows = []; exprs = []; rows_meta = {}
    for st in STEPS:
        status, val, pdt = isolated(parse_pair, (st["before"], st["after"]), args.parse_timeout)
        rec = dict(step=st, parse=status if status != "ok" else "ok", parse_ms=pdt * 1000, cells={})
        if status != "ok":
            rec["parse_detail"] = val
            rows.append(rec)
            print(f"step {st['id']}: PARSE {status} {val}")
            continue
        (la, lb, ra_, rb_) = val
        if len(la) != 1 or len(lb) != 1 or len(ra_) != 1 or len(rb_) != 1:
            rec["parse"] = "branches"; rows.append(rec); continue
        a, b = la[0], lb[0]
        rec["parsed"] = (str(a), str(b)); rec["raw"] = (str(ra_[0]), str(rb_[0]))
        st = dict(st, raw=(ra_[0], rb_[0]))
        exprs.append((st, (a, b)))
        for sid, name, fn in STRATEGIES:
            s, v, dt = isolated(fn, (a, b, st), args.timeout)
            if s == "ok":
                verdict, detail = v
            elif s == "timeout":
                verdict, detail = "TO", f"killed after {args.timeout}s"
            else:
                verdict, detail = "ERR", v
            rec["cells"][sid] = dict(verdict=verdict, detail=detail, ms=dt * 1000, score=score(st["expected"], verdict))
        rows.append(rec)
        print(f"step {st['id']:2d} [{st['expected']:10s}] " + " ".join(f"{k}={c['verdict']}" for k, c in rec["cells"].items()), flush=True)
    # timeout sensitivity: same calls again under a tight budget
    tight = {sid: [0, 0] for sid, _, _ in STRATEGIES}   # [timeouts, calls]
    for st, (a, b) in exprs:
        for sid, name, fn in STRATEGIES:
            s, v, dt = isolated(fn, (a, b, st), args.tight)
            tight[sid][1] += 1
            tight[sid][0] += s == "timeout"
    # kill check: a worker that never returns must be gone after the timeout
    st, _, dt = isolated(_sleeper, (), 0.2)
    kill_check = f"deliberate 60 s sleeper with a 0.2 s timeout: status={st}, returned after {dt:.2f}s"
    rows_meta["tight"], rows_meta["kill"] = tight, kill_check
    # floor: a no-op through isolated(), 20 times
    floor = sorted(isolated(_noop, (), 2.0)[2] * 1000 for _ in range(20))
    rows_meta["floor"] = f"no-op through isolated(): median {statistics.median(floor):.1f} ms, min {floor[0]:.1f}, max {floor[-1]:.1f} (20 calls)"
    # Expr.equals spread over seeds on #20 and #7
    spread = {}
    for st, (a, b) in exprs:
        if st["id"] in (7, 20):
            res = isolated(_equals_spread, (a, b, st), 20.0)
            spread[st["id"]] = res[1] if res[0] == "ok" else res[0]
    rows_meta["spread"] = spread
    # off-grid / evaluation-sensitive extras (not part of the 20), run through the same parse and S0u/S7/S1
    extras = []
    for ex in EXTRAS:
        status, val, _ = isolated(parse_pair, (ex["before"], ex["after"]), args.parse_timeout)
        if status != "ok":
            extras.append((ex, None, status)); continue
        la, lb, ra_, rb_ = val
        st2 = dict(ex, raw=(ra_[0], rb_[0]))
        cs = {}
        for sid, name, fn in STRATEGIES:
            if sid in ("S0e", "S0u", "S1", "S7", "S5r"):
                s_, v_, dt_ = isolated(fn, (la[0], lb[0], st2), args.timeout)
                cs[sid] = v_[0] if s_ == "ok" else s_
        extras.append((ex, cs, "ok"))
    rows_meta["extras"] = extras
    jp = os.path.splitext(args.out)[0].lower() + ".json"
    json.dump(rows, open(jp, "w"), indent=1, default=str)
    write_md(rows, args, rows_meta)

def exprs_n(rows): return [r for r in rows if r['parse'] == 'ok']

def cell(c):
    mark = {"ok": "", "wrong": " !", "partial": " ~", "und": "", "na": ""}[c["score"]]
    return f"{c['verdict']}{mark} {c['ms']:.0f}ms"

def write_md(rows, a, meta):
    ids = [s[0] for s in STRATEGIES]
    L = []
    L.append("# RESULTS: CAS equivalence spike (#14)\n")
    L.append("PROTOTYPE output. Sections 1-3 are generated by `run.py` from an actual run; section 4 is `analysis.md` (hand-written, appended).\n")
    L.append(f"Machine: {platform.platform()}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}, SymPy {sympy.__version__}. "
             f"Per-call timeout {a.timeout}s (worker process killed on timeout), parse timeout {a.parse_timeout}s. "
             "Times are wall clock per forked worker (includes fork/IPC overhead, floor measured below) on a shared WSL2 laptop: indicative only. "
             "Run date " + time.strftime("%Y-%m-%d") + ".\n")
    L.append("Pint (S8) is dropped: v1 is algebra only and the research found Pint is not symbolic.\n")
    L.append("## 0. Steps, expected labels and reasoning\n")
    L.append("Labels: EQUIV = equivalent; NOT_EQUIV = student mistake; DOMAIN = equal only under a domain restriction (a strict checker should flag it); ONEWAY = after follows from before but not conversely.\n")
    L.append("| # | topic | before | after | kind | expected | parsed, evaluated (before ; after) | parsed, unevaluated (before ; after) | reasoning |\n|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["step"]
        L.append(f"| {s['id']} | {s['topic']} | `{s['before']}` | `{s['after']}` | {s['kind']} | {s['expected']} | "
                 f"`{'` ; `'.join(r.get('parsed', ('?', '?')))}` | `{'` ; `'.join(r.get('raw', ('?', '?')))}` | {s['why'].replace('|', '/')} |")
    bad = [r for r in rows if r["parse"] != "ok"]
    L.append(f"\nParse stack (ANTLR strict + normalizer + whitelist + Lark cross-check): {len(rows)-len(bad)}/{len(rows)} steps accepted"
             + ("." if not bad else "; rejected: " + ", ".join(f"#{r['step']['id']} ({r.get('parse_detail', r['parse'])})" for r in bad) + "."))
    L.append(f" Median parse time {statistics.median(r['parse_ms'] for r in rows):.0f} ms (includes worker spawn, ANTLR, Lark cross-check).\n")
    L.append("## 1. Step x strategy: verdict and time\n")
    L.append("Verdicts: EQ, NEQ, EQ_DOM (S7: equal at samples but the symbolic natural domains differ), NARROW / WIDER (S5: after has fewer / more solutions), UND (undecided), TO (timeout, killed), NA (not applicable), ERR (exception). "
             "Marks against the expected label: `!` wrong, `~` partial (ONEWAY or DOMAIN step rejected as plain NEQ). Unmarked = correct, or UND/NA/TO.\n")
    L.append("Equations: S0 compares the Eq objects; S1-S4, S6, S7 test whether the residuals lhs-rhs are proportional (ra == c*rb, c rational probe); S5 compares solveset solution sets (over R or C; variable `solve_for`). S5 is NA for expressions.\n")
    L.append("| # | expected | " + " | ".join(ids) + " |\n|---|---|" + "---|" * len(ids))
    for r in rows:
        if r["parse"] != "ok":
            L.append(f"| {r['step']['id']} | {r['step']['expected']} | parse {r['parse']} |" + " |" * (len(ids) - 1)); continue
        L.append(f"| {r['step']['id']} | {r['step']['expected']} | " + " | ".join(cell(r['cells'][i]) for i in ids) + " |")
    L.append("\nStrategy key: " + "; ".join(f"{i} = {n}" for i, n, _ in STRATEGIES) + ".\n")
    L.append("## 2. Per strategy: accuracy, timeouts, time\n")
    L.append("Accuracy = correct / (correct + partial + wrong) over decided, applicable steps. Scoring: EQUIV needs EQ; NOT_EQUIV needs any non-equal verdict; DOMAIN needs the domain change flagged (EQ_DOM, or S5 NARROW/WIDER), a plain NEQ is partial and EQ is wrong; ONEWAY needs WIDER (NEQ or NARROW is partial).\n")
    L.append("| strategy | correct | partial | wrong | undecided | timeouts | errors | N/A | accuracy | median ms | max ms |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for sid, name, _ in STRATEGIES:
        cs = [r["cells"][sid] for r in rows if sid in r["cells"]]
        n = lambda k: sum(c["score"] == k for c in cs)
        dec = n("ok") + n("partial") + n("wrong")
        acc = f"{100*n('ok')/dec:.0f}% ({n('ok')}/{dec})" if dec else "-"
        L.append(f"| {sid} {name} | {n('ok')} | {n('partial')} | {n('wrong')} | {sum(c['verdict']=='UND' for c in cs)} | "
                 f"{sum(c['verdict']=='TO' for c in cs)} | {sum(c['verdict']=='ERR' for c in cs)} | {n('na')} | {acc} | "
                 f"{statistics.median(c['ms'] for c in cs):.0f} | {max(c['ms'] for c in cs):.0f} |")
    L.append(f"\nTimeout sensitivity: all {len(exprs_n(rows))} parsed steps re-run per strategy with a tight {a.tight}s budget. Timeouts / calls: "
             + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in meta["tight"].items()) + ".")
    L.append("These counts are noise around a 50 ms threshold that includes fork overhead; they changed between runs of the same code (do not read them as per-strategy cost).")
    L.append(f"\nKill check: {meta['kill']}. Fork/IPC floor: {meta['floor']}.\n")
    L.append("`Expr.equals` seed spread (S2, complex symbols, seeds 0-9 via `sympy.core.random.seed`; the main table uses seed 0): " + "; ".join(f"#{k}: {v}" for k, v in meta["spread"].items()) + ".\n")
    L.append("Off-grid / evaluation-sensitive extras (NOT part of the 20; expected label in the last column; x5-x7 check that S7 does not false-flag equal trig domains, x4 is EQUIV as a solution set only), verdicts S0e / S0u / S1 / S5r / S7:\n")
    L.append("| extra | before | after | S0e | S0u | S1 | S5r | S7 | expected |\n|---|---|---|---|---|---|---|---|---|")
    for ex, cs, st_ in meta["extras"]:
        L.append(f"| {ex['id']} | `{ex['before']}` | `{ex['after']}` | " + (" | ".join(cs.get(k, '-') for k in ("S0e","S0u","S1","S5r","S7")) if cs else st_ + " |"*4) + f" | {ex['expected']} |")
    L.append("")
    L.append("\n## 3. Where strategies disagree\n")
    L.append("Steps where the decided verdicts of S1-S7 (S0e/S0u excluded: they disagree with everything on any non-trivial rewrite by design; ignoring UND/NA/TO/ERR) are not all the same; detail strings from the run.\n")
    for r in rows:
        if r["parse"] != "ok": continue
        dec = {i: c for i, c in r["cells"].items() if not i.startswith("S0") and c["verdict"] not in ("UND", "NA", "TO", "ERR")}
        if len({c["verdict"] for c in dec.values()}) > 1:
            s = r["step"]
            L.append(f"**#{s['id']} {s['topic']}**: `{s['before']}` -> `{s['after']}` (expected {s['expected']})\n")
            groups = {}
            for i, c in dec.items(): groups.setdefault(c["verdict"], []).append(i)
            L.append("- " + "; ".join(f"{v}: {', '.join(ids_)}" for v, ids_ in groups.items()))
            und = [i for i, c in r["cells"].items() if c["verdict"] in ("UND", "TO", "ERR")]
            if und: L.append(f"- undecided/timeout/error: {', '.join(und)}")
            for i in ("S1", "S2", "S3r", "S3c", "S5r", "S7"):
                c = r["cells"][i]
                if c["verdict"] not in ("NA",): L.append(f"  - {i}: {c['verdict']} - {c['detail']}")
            L.append("")
    ap = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis.md")
    if os.path.exists(ap):
        L.append(open(ap).read())
    open(a.out, "w").write("\n".join(L) + "\n")
    print("wrote", a.out)

if __name__ == "__main__":
    main()

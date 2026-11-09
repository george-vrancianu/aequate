"""PROTOTYPE (throwaway), ticket #41. Run: uv run python run_domain.py [--timeout 2.0]
Writes RESULTS-domain.md (+ results-domain.json). Sections 0-4 generated from the run; analysis-domain.md appended.
Every parse and every domain call runs in a forked, killable worker (run.isolated); steps run one after another (1 worker at a time)."""
import argparse, json, os, platform, statistics, time, warnings
warnings.simplefilter("ignore")
import sympy
from sympy import Symbol, S
import domain
from domain import domain_verdict, fmt_sets, fmt_pt, describe, Dset
from run import isolated, parse_pair
from steps import STEPS as ORIG
from steps_domain import STEPS as NEW
import strategies
from strategies import score

def _wname(pt): return None if pt is None else {str(k): v for k, v in pt.items()}

def _spec_ok(spec, exact, wit, hint=None):
    """Does the reported direction (exact sets and/or witness) match the expected spec?"""
    if not spec:   # expected empty
        return not exact and wit is None
    w = _wname(wit)
    ex = {str(k): v for k, v in exact.items()}
    if all(isinstance(v, Dset) for v in spec.values()):
        if ex: return set(ex) == set(spec) and all(ex[k] == spec[k] for k in spec)
        return w is not None and all(spec[k].contains(w[k]) for k in spec if k in w)
    if w is None: return False
    return all(bool(f(w)) for f in spec.values())

def check_step(st, ra, rb):
    r = domain_verdict([ra], [rb])
    out = dict(verdict=r["verdict"], sym=r["sym"], why=r["why"], tried=r.get("tried", 0))
    out["excluded"] = fmt_sets(r["excluded"]); out["added"] = fmt_sets(r["added"])
    out["wit_excl"] = fmt_pt(r["wit_excl"]) if r["wit_excl"] else None
    out["wit_add"] = fmt_pt(r["wit_add"]) if r["wit_add"] else None
    out["detail"] = describe(r) if r["verdict"] == "CHANGED" else ""
    out["cons"] = ("before-only: " + (", ".join(r["cons_only_before"]) or "-") + "; after-only: " + (", ".join(r["cons_only_after"]) or "-")) if r.get("opaque_differs") else "-"
    out["opaque_differs"] = bool(r.get("opaque_differs"))
    out["nvars"] = len(ra.free_symbols | rb.free_symbols)
    if r["verdict"] == "CHANGED":
        out["named_ok"] = _spec_ok(st["excluded"], r["excluded"], r["wit_excl"]) and _spec_ok(st["added"], r["added"], r["wit_add"])
    # numeric sanity of the label: before and after agree at exact points where both are defined
    from domain import collect, _ev, candidates, member
    try:
        evA = [(_ev(e), q) for p in [ra] for e, q in collect(p) if _ev(e).free_symbols]
        evB = [(_ev(e), q) for p in [rb] for e, q in collect(p) if _ev(e).free_symbols]
        vs = sorted(ra.free_symbols | rb.free_symbols, key=str)
        import itertools
        cand = candidates(vs, {})
        n = 0; worst = 0.0
        for combo in itertools.islice(itertools.product(*[cand[v] for v in vs]), 400):
            pt = dict(zip(vs, combo))
            if member(evA, pt) is True and member(evB, pt) is True:
                with sympy.evaluate(True):
                    a, b = complex(domain.realify(ra).subs(pt).evalf(30)), complex(domain.realify(rb).subs(pt).evalf(30))   # real-root convention, not SymPy's principal branch (D81 was flagged without this)
                worst = max(worst, abs(a - b) / max(1.0, abs(a))); n += 1
        out["num"] = f"{n} common points, max rel diff {worst:.1e}" if n else "no common grid points"
        out["num_ok"] = (worst < 1e-9) if n else None
    except Exception as e:
        out["num"] = f"numeric check error {type(e).__name__}"; out["num_ok"] = None
    return out

def cls(st, o):
    """Classification of one result against its label."""
    v = o["verdict"]
    if v == "UNDECIDED": return "undecided"
    if st["expected"] == "same":  return "TN" if v == "SAME" else "FP"
    if v == "SAME": return "FN"
    return "TP" if o.get("named_ok") else "TP-misnamed"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=float(os.environ.get("CAS_TIMEOUT", 2.0)))
    ap.add_argument("--parse-timeout", type=float, default=10.0)
    ap.add_argument("--out", default="RESULTS-domain.md")
    a = ap.parse_args()
    from parsing import check_line
    check_line(r"x+1")   # warm up so forked workers start hot
    rows = []
    for st in NEW:
        s, val, pdt = isolated(parse_pair, (st["before"], st["after"]), a.parse_timeout)
        rec = dict(step=st, parse=s)
        if s != "ok" or any(len(x) != 1 for x in val):
            rec["res"] = dict(verdict="UNDECIDED", why=f"parse {s}: {val}"); rec["cls"] = "undecided"; rec["ms"] = 0; rows.append(rec); continue
        ra, rb = val[2][0], val[3][0]
        rec["raw"] = (str(ra), str(rb))
        s2, o, dt = isolated(check_step, (st, ra, rb), a.timeout)
        if s2 == "timeout": o = dict(verdict="UNDECIDED", why=f"timeout after {a.timeout}s", timeout=True)
        elif s2 != "ok": o = dict(verdict="UNDECIDED", why=f"error {o}")
        rec["res"], rec["ms"], rec["cls"] = o, dt * 1000, cls(st, o)
        rows.append(rec)
        print(f"{st['id']:4s} expected {st['expected']:7s} -> {o['verdict']:9s} [{rec['cls']}] {dt*1000:.0f} ms", flush=True)
    # original 20: S7 and S7b through the harness strategy interface
    reg = []
    for st in ORIG:
        s, val, _ = isolated(parse_pair, (st["before"], st["after"]), a.parse_timeout)
        la, lb, ra_, rb_ = val
        st2 = dict(st, raw=(ra_[0], rb_[0]))
        cells = {}
        for sid, fn in (("S7", strategies.s7), ("S7b", domain.s7b)):
            s3, v, dt = isolated(fn, (la[0], lb[0], st2), a.timeout)
            ver, det = v if s3 == "ok" else (("TO", f"killed after {a.timeout}s") if s3 == "timeout" else ("ERR", v))
            cells[sid] = dict(verdict=ver, detail=det, ms=dt * 1000, score=score(st["expected"], ver))
        reg.append(dict(step=st, cells=cells))
        print(f"orig {st['id']:2d} [{st['expected']:9s}] S7={cells['S7']['verdict']} S7b={cells['S7b']['verdict']}", flush=True)
    json.dump(dict(new=rows, orig=reg), open("results-domain.json", "w"), indent=1, default=str)
    write_md(rows, reg, a)

def pct(n, d): return f"{100*n/d:.0f}% ({n}/{d})" if d else "n/a"

def write_md(rows, reg, a):
    L = ["# RESULTS: S7b domain tracking for several variables and more rules (#41)\n"]
    L.append("PROTOTYPE output, generated by `run_domain.py` from an actual run; the last section is `analysis-domain.md` (hand-written, appended). "
             "Timings and the run date change between runs; everything else is deterministic.\n")
    L.append(f"Machine: {platform.platform()}, {os.cpu_count()} logical CPUs, Python {platform.python_version()}, SymPy {sympy.__version__}. "
             f"Per-call timeout {a.timeout}s (worker killed on timeout), parse timeout {a.parse_timeout}s, one worker process at a time. Run date {time.strftime('%Y-%m-%d')}.\n")
    L.append("## 0. What S7b is\n")
    L.append("- Input: the UNEVALUATED parse of before and after (same parser path as the harness: `check_line_raw`, strict ANTLR + guards; no sympify/eval). For an equation both sides count.")
    L.append("- Output per step: SAME domain / DOMAIN CHANGED (with `excluded` = defined before but not after, `added` = defined after but not before) / UNDECIDED.")
    L.append("- Real convention: see the header of `domain.py` (rational power p/q in lowest terms: q even needs base >= 0, > 0 if p < 0; q odd is the REAL root, defined for all real base; x^0 needs x != 0; x^y with symbolic y, unlisted functions, log with a base: UNDECIDED).")
    L.append("- Representation: a conjunction of atomic constraints (`e != 0`, `e >= 0`, `e > 0`), not a set over R^n. Univariate atoms are solved per variable into intervals plus excluded points with canonical periodic classes (this is the `ImageSet` / union canonicalisation: `pi/2 + k*pi` equals `pi/2 + 2k*pi` U `3pi/2 + 2k*pi`). Multivariate atoms, and univariate inequalities with trig (SymPy's `solveset(sin(x) > 0)` returns one period only), stay symbolic and are compared by canonical key. Any difference or sameness is then cross-checked at exact grid points; a differing point proves CHANGED; a claimed difference that no point confirms, or opaque constraints that differ with no differing point, are UNDECIDED.\n")
    L.append("## 1. New hand-labelled set: expected vs actual\n")
    L.append("Labels (`same` / `changed` and which values) and one-line justifications are in `steps_domain.py` and repeated in the last column. `excluded` / `added` are named by an exact set when the constraints are all one-variable; otherwise a witness point (exact values) is given. `named` = the reported sets / witness match the label (predicate labels are checked at the witness point only). `numeric` = before and after evaluated at exact points where both sides are defined (checks that the step is a valid rewrite).\n")
    L.append("| id | topic | before -> after | vars | expected | verdict | class | excluded (before only) | added (after only) | named | constraint diff (normalised atoms, shown when opaque atoms differ) | numeric check of label | ms | label justification |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s, o = r["step"], r["res"]
        def spec(d, region):
            if not d: return "none"
            v = list(d.values())
            return region if region else "; ".join(f"{k} in {x}" for k, x in d.items())
        exp = "same" if s["expected"] == "same" else f"changed (excl: {spec(s['excluded'], s['region'])}; added: {spec(s['added'], s['region'])})"
        def act(key, wit):
            parts = []
            if o.get(key): parts.append(o[key])
            if o.get(wit): parts.append("witness " + o[wit])
            return "; ".join(parts) or "-"
        nvars = o.get("nvars", "?")
        L.append(f"| {s['id']} | {s['topic']} | `{s['before']}` -> `{s['after']}` | {nvars} | {exp} | {o['verdict']} | {r['cls']} | {act('excluded', 'wit_excl') if o['verdict']=='CHANGED' else '-'} | "
                 f"{act('added', 'wit_add') if o['verdict']=='CHANGED' else '-'} | {'yes' if o.get('named_ok') else ('NO' if o['verdict']=='CHANGED' else '-')} | {o.get('cons', '-')} | {o.get('num', '-')} | {r['ms']:.0f} | {s['why'].replace('|', '/')} |")
    L.append("\nWhy-strings of the verdicts (how each was reached):\n")
    for r in rows:
        L.append(f"- {r['step']['id']}: {r['res'].get('why', '')}" + (f" [symbolic: {r['res'].get('sym')}]" if r['res'].get('sym') else ""))
    # metrics
    C = {k: sum(r["cls"] == k for r in rows) for k in ("TP", "TP-misnamed", "FN", "TN", "FP", "undecided")}
    exp_ch = sum(r["step"]["expected"] == "changed" for r in rows); exp_same = len(rows) - exp_ch
    tp = C["TP"] + C["TP-misnamed"]; flagged = tp + C["FP"]
    und_ch = sum(r["cls"] == "undecided" and r["step"]["expected"] == "changed" for r in rows)
    und_same = sum(r["cls"] == "undecided" and r["step"]["expected"] == "same" for r in rows)
    L.append("\n## 2. Precision and recall for \"domain changed\"\n")
    L.append(f"Set: {len(rows)} steps, {exp_ch} labelled changed, {exp_same} labelled same.\n")
    L.append("Definitions. TP: labelled changed and verdict CHANGED. FP: labelled same and verdict CHANGED. FN: labelled changed and verdict SAME. TN: labelled same and verdict SAME. "
             "UNDECIDED is never counted as a flag, so it is not a TP or an FP; it counts as a MISS for recall (conservative) and is shown separately. "
             "A verdict is \"named\" when the reported excluded/added values match the label.\n")
    L.append("| count | value |\n|---|---|")
    L.append(f"| TP (flagged, named correctly) | {C['TP']} |\n| TP but misnamed (flagged, wrong or unmatched values) | {C['TP-misnamed']} |\n| FN (changed step said SAME) | {C['FN']} |\n| TN | {C['TN']} |\n| FP (same step flagged) | {C['FP']} |\n| UNDECIDED, labelled changed | {und_ch} |\n| UNDECIDED, labelled same | {und_same} |")
    L.append(f"\n- Precision = TP / (TP + FP) = {pct(tp, flagged)}; strict precision (named correctly only) = {pct(C['TP'], flagged)}.")
    L.append(f"- Recall, undecided counted as a miss = {pct(tp, exp_ch)}; strict (named correctly) = {pct(C['TP'], exp_ch)}; recall over decided steps only = {pct(tp, exp_ch - und_ch)}.")
    L.append(f"- False \"same\" rate on labelled-changed steps (FN) = {pct(C['FN'], exp_ch)}; false \"changed\" rate on labelled-same steps (FP) = {pct(C['FP'], exp_same)}; undecided overall = {pct(C['undecided'], len(rows))}.")
    bad = [r for r in rows if r["res"].get("num_ok") is False]
    L.append(f"- Label sanity: steps where before and after disagree numerically on a point where both are defined: {', '.join(r['step']['id'] for r in bad) or 'none'}; steps with no common grid point to check: {', '.join(r['step']['id'] for r in rows if r['res'].get('num_ok') is None) or 'none'}.\n")
    L.append("Steps by label class: " + "; ".join(f"{k}: {', '.join(r['step']['id'] for r in rows if r['cls'] == k) or '-'}" for k in C) + ".\n")
    # timing
    ms = [r["ms"] for r in rows if r["ms"]]
    L.append("## 3. Timing under the timeout\n")
    L.append(f"Domain call per step (worker fork + compare + pointwise check + label numeric check), timeout {a.timeout}s: median {statistics.median(ms):.0f} ms, max {max(ms):.0f} ms; timeouts: {sum(bool(r['res'].get('timeout')) for r in rows)}/{len(rows)}. Slowest 3: "
             + ", ".join(f"{r['step']['id']} {r['ms']:.0f} ms" for r in sorted(rows, key=lambda r: -r['ms'])[:3]) + ".\n")
    # regression
    L.append("## 4. No-regression run on the original 20 steps (S7 unchanged vs S7b)\n")
    L.append("Both run through the harness interface (numeric real check first, then domain tracking on the unevaluated parse). Scoring is the harness `score` (EQUIV needs EQ; NOT_EQUIV needs a non-equal verdict; DOMAIN needs EQ_DOM; ONEWAY needs WIDER). Marks: `!` wrong, `~` partial.\n")
    L.append("| # | topic | expected | S7 | S7b | S7b detail |\n|---|---|---|---|---|---|")
    mk = {"ok": "", "wrong": " !", "partial": " ~", "und": "", "na": ""}
    for r in reg:
        s, c = r["step"], r["cells"]
        L.append(f"| {s['id']} | {s['topic']} | {s['expected']} | {c['S7']['verdict']}{mk[c['S7']['score']]} | {c['S7b']['verdict']}{mk[c['S7b']['score']]} | {c['S7b']['detail'].replace('|', '/')[:300]} |")
    L.append("")
    L.append("| strategy | correct | partial | wrong | undecided | accuracy | median ms | max ms |\n|---|---|---|---|---|---|---|---|")
    for sid in ("S7", "S7b"):
        cs = [r["cells"][sid] for r in reg]
        n = lambda k: sum(c["score"] == k for c in cs)
        dec = n("ok") + n("partial") + n("wrong")
        L.append(f"| {sid} | {n('ok')} | {n('partial')} | {n('wrong')} | {sum(c['verdict'] == 'UND' for c in cs)} | {pct(n('ok'), dec)} | {statistics.median(c['ms'] for c in cs):.0f} | {max(c['ms'] for c in cs):.0f} |")
    L.append("")
    ap_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis-domain.md")
    if os.path.exists(ap_): L.append(open(ap_).read())
    open(a.out, "w").write("\n".join(L) + "\n")
    print("wrote", a.out)

if __name__ == "__main__":
    main()

"""Turn results/results.json into results/results.md (tables only; findings live in README.md)."""
import json
import statistics
from pathlib import Path

from strategies import TICK

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results" / "results.json").read_text())
meta, rows = data["meta"], data["results"]
names = list(rows[0]["checks"])
BUDGET = "1.0s"
DOT = {"green": "🟢", "amber": "🟠", "red": "🔴", "-": "·"}


def tick(check):
    return TICK.get(check["verdict"], "amber")


def mark(row, name, budget=BUDGET):
    c = row["checks"].get(name)
    if c is None:
        return ""
    t = tick(c[budget])
    if t == "-":
        return "·"
    return DOT[t] + ("" if t == row["tick"] else "✗")


out = []
w = out.append
w("# CAS spike results (generated)\n")
w(f"SymPy {meta['sympy']}, Pint {meta['pint']}, Python {meta['python']}, LaTeX parser `{meta['latex_backend']}`, "
  f"{meta['cpu_count']} vCPU {meta['machine']} cloud container, {meta['date']}. "
  f"Numeric sampling: {meta['n_points']} points, relative tolerance {float(meta['rel_tol']):.0e}. "
  f"Every check ran in a forked worker killed at the budget.\n")
w("Legend: colour = tick the strategy would show the tutor (verdict mapped through `TICK`); "
  "✗ = differs from the hand label; · = strategy not applicable. Budget 1 s unless noted.\n")

short = {n: n.replace(" structural", "").replace(" simplify", "").replace(" equals", "")
         .replace(" numeric", "").replace(" layered", "").replace(" solution sets", "")
         .replace(" domain", "").replace(" units", "") for n in names}
for group, title in [("core", "20 core algebra steps"), ("extra", "Edge cases"), ("physics", "Physics steps (S8)")]:
    gr = [r for r in rows if r["group"] == group]
    cols = names + (["S8 units"] if group == "physics" else [])
    w(f"\n## {title}\n")
    w("| Step | Category | prev → curr | Truth | Want | " + " | ".join(short.get(n, n) for n in cols) + " |")
    w("|---|---|---|---|---|" + "---|" * len(cols))
    for r in gr:
        w(f"| {r['id']} | {r['cat']} | `{r['prev']}` → `{r['curr']}` | {r['truth']} | {DOT[r['tick']]} | "
          + " | ".join(mark(r, n) for n in cols) + " |")

w("\n## Accuracy and latency per strategy (core 20 + extras + physics)\n")
w("Right = tick matches the hand label. Dangerous = shows green where the label is red, or red where it is green. "
  "Latency is check time inside the worker (parse excluded), across all steps where the strategy applies. "
  "S0 (structural) and S7 (domain) are signals, not judges, so they are left out.\n")
w("| Strategy | Applies | Right @1s | Dangerous @1s | Right @0.2s | Timeouts @0.2s | Timeouts @1s | median ms | p95 ms | max ms |")
w("|---|---|---|---|---|---|---|---|---|---|")
allnames = [n for n in names if not n.startswith(("S0", "S7"))] + ["S8 units"]
for n in allnames:
    rs = [r for r in rows if n in r["checks"] and r["checks"][n][BUDGET]["verdict"] != "n/a"]
    if not rs:
        continue
    right = sum(tick(r["checks"][n][BUDGET]) == r["tick"] for r in rs)
    right2 = sum(tick(r["checks"][n]["0.2s"]) == r["tick"] for r in rs)
    danger = sum({tick(r["checks"][n][BUDGET]), r["tick"]} == {"green", "red"} for r in rs)
    to1 = sum(r["checks"][n][BUDGET]["verdict"] == "timeout" for r in rs)
    to2 = sum(r["checks"][n]["0.2s"]["verdict"] == "timeout" for r in rs)
    ts = sorted(r["checks"][n][BUDGET]["check_s"] * 1000 for r in rs if r["checks"][n][BUDGET]["check_s"] is not None)
    p95 = ts[min(len(ts) - 1, int(round(0.95 * (len(ts) - 1))))] if ts else 0
    w(f"| {n} | {len(rs)} | {right}/{len(rs)} | {danger} | {right2}/{len(rs)} | {to2} | {to1} | "
      f"{statistics.median(ts):.1f} | {p95:.1f} | {max(ts):.1f} |")

parse = [r["checks"]["PIPELINE"][BUDGET]["parse_s"] * 1000 for r in rows]
wall = [c[BUDGET]["wall_s"] * 1000 for r in rows for c in r["checks"].values()]
over = [c[BUDGET]["wall_s"] * 1000 - c[BUDGET]["check_s"] * 1000 - c[BUDGET]["parse_s"] * 1000
        for r in rows for c in r["checks"].values() if c[BUDGET]["check_s"] is not None]
w(f"\nLaTeX parse (two lines): median {statistics.median(parse):.1f} ms, max {max(parse):.1f} ms. "
  f"Fork-per-check overhead (wall − parse − check): median {statistics.median(over):.1f} ms.\n")

w("\n## Pipeline detail\n")
w("| Step | Want | Pipeline | Verdict | Why |")
w("|---|---|---|---|---|")
for r in rows:
    c = r["checks"]["PIPELINE"][BUDGET]
    w(f"| {r['id']} | {DOT[r['tick']]} | {mark(r, 'PIPELINE')} | {c['verdict']} | {c['detail'][:110].replace('|', '/')} |")

(HERE / "results" / "results.md").write_text("\n".join(out) + "\n")
print("wrote results/results.md")

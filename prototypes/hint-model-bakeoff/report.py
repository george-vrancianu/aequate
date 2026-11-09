"""PROTOTYPE. results/*.jsonl -> markdown tables (paste into RESULTS.md). Usage: uv run python report.py [results/a.jsonl ...]"""
import glob, json, statistics, sys
from collections import defaultdict


def pct(a, b):
    return f"{100 * a / b:.0f}% ({a}/{b})" if b else "-"


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1) + 0.4999)))] if xs else float("nan")


def row(rs):
    n = len(rs)
    a1 = [r["attempts"][0] for r in rs if r["attempts"]]
    leak1 = sum(1 for x in a1 if x["leak"] and x["leak"]["leak"])
    a2 = [r["attempts"][1] for r in rs if len(r["attempts"]) > 1]
    leak2 = sum(1 for x in a2 if x["leak"] and x["leak"]["leak"])
    valid_all = [x for r in rs for x in r["attempts"]]
    invalid = sum(1 for x in valid_all if not x["valid"] and x["invalid_reason"] != "timeout")
    tmpl = sum(1 for r in rs if r["final_source"] == "template")
    timeouts = sum(1 for r in rs if any(x["error"] == "timeout" for x in r["attempts"]))
    both_failed = sum(1 for r in rs if r["final_source"] == "template" and len(r["attempts"]) > 1 and not any(x["error"] == "timeout" for x in r["attempts"]))
    miss = sum(1 for r in rs if r["gate_miss"])
    unp = sum(x["leak"]["unparsed"] for x in valid_all if x["leak"])
    think = sum(1 for x in valid_all if x["think_leftover"])
    lat = [r["whole_latency_s"] for r in rs]
    return [str(n), pct(leak1, len(a1)), pct(leak2, len(a2)) if a2 else "no retry", pct(tmpl, n),
            f"{timeouts} timeout / {both_failed} gate-twice", pct(len(valid_all) - invalid - sum(1 for x in valid_all if x['invalid_reason'] == 'timeout'),
                                                              len(valid_all) - sum(1 for x in valid_all if x['invalid_reason'] == 'timeout')),
            str(miss), str(unp), str(think),
            f"{statistics.median(lat):.1f} / {p95(lat):.1f}", str(sum(1 for r in rs if r["over_budget"]))]


HEAD = ["n", "leak a1", "leak a2 (of retried)", "template fallback", "fallback causes", "JSON valid (attempts)", "possible gate misses",
        "unparsed formulas", "<think> left", "latency median / p95 (s)", ">20 s"]


def table(title, groups):
    out = [f"\n#### {title}\n", "| " + " | ".join(["group"] + HEAD) + " |", "|" + "---|" * (len(HEAD) + 1)]
    for k in sorted(groups):
        out.append("| " + " | ".join([str(k)] + row(groups[k])) + " |")
    return "\n".join(out)


def main():
    files = sys.argv[1:] or sorted(glob.glob("results/*.jsonl"))
    for fn in files:
        rs = [json.loads(l) for l in open(fn) if l.strip()]
        if not rs:
            continue
        print(f"\n### {rs[0]['label']} ({rs[0]['model']}), prompt {rs[0]['prompt_version']}, leak check {rs[0]['leak_check_version']}, "
              f"{len(rs)} hints, extra body `{json.dumps(rs[0]['extra_body'])}`")
        g = defaultdict(list)
        for r in rs:
            g[(r["locale"], r["rung"])].append(r)
        print(table("per language x rung", g))
        g = defaultdict(list)
        for r in rs:
            g["all"].append(r)
            g[r["locale"]].append(r)
        print(table("per language and overall", g))
        g = defaultdict(list)
        for r in rs:
            g[r["step"]].append(r)
        print(table("per step (both languages, all rungs)", g))


if __name__ == "__main__":
    main()

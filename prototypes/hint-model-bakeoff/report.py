"""PROTOTYPE. results/*.jsonl -> markdown tables (paste into RESULTS.md). Usage: uv run python report.py [results/a.jsonl ...]"""
import glob, json, statistics, sys
from collections import defaultdict


def pct(a, b):
    return f"{100 * a / b:.0f}% ({a}/{b})" if b else "-"


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1) + 0.4999)))] if xs else float("nan")


def is_leak(x):
    return bool(x["leak"] and x["leak"]["leak"])


def is_req_error(x):
    return bool(x["error"]) and x["error"] != "timeout"


def cause(r):
    """Why a hint ended on the template (mutually exclusive, in this order), so the causes add up to the template count."""
    at = r["attempts"]
    if any(x["error"] == "timeout" for x in at):
        return "timeout"
    if any(is_req_error(x) for x in at):
        return "request error"
    if at and at[-1]["valid"] and not is_leak(at[-1]):
        return "over budget"          # a clean reply arrived after the 20 s budget
    if len(at) == 1:
        return "no time to retry"
    return "rejected twice"


def row(rs, lat_label=None):
    n = len(rs)
    a1 = [r["attempts"][0] for r in rs if r["attempts"]]
    a1_timeout = sum(1 for x in a1 if x["error"] == "timeout")
    a1_err = sum(1 for x in a1 if is_req_error(x))
    a1_invalid = sum(1 for x in a1 if not x["valid"] and not x["error"])
    a1_valid = [x for x in a1 if x["valid"]]
    leak1 = sum(1 for x in a1_valid if is_leak(x))
    # leak a2: of the hints whose attempt 1 leaked and whose attempt 2 ran, how many leaked again
    retried = [r for r in rs if r["attempts"] and r["attempts"][0]["valid"] and is_leak(r["attempts"][0]) and len(r["attempts"]) > 1]
    leak2 = sum(1 for r in retried if is_leak(r["attempts"][1]))
    # residual: attempt 1 leaked and no clean LLM output followed (second leak, no retry, invalid or timed-out retry...)
    leaked1 = [r for r in rs if r["attempts"] and r["attempts"][0]["valid"] and is_leak(r["attempts"][0])]
    residual = sum(1 for r in leaked1 if r["final_source"] == "template")
    allat = [x for r in rs for x in r["attempts"]]
    counted = [x for x in allat if x["error"] is None]                  # timeouts and request errors are not JSON verdicts
    valid_n = sum(1 for x in counted if x["valid"])
    tmpl = [r for r in rs if r["final_source"] == "template"]
    causes = {c: sum(1 for r in tmpl if cause(r) == c) for c in ("timeout", "request error", "no time to retry", "over budget", "rejected twice")}
    miss = sum(1 for r in rs if r["gate_miss"])
    unp = sum(x["leak"]["unparsed"] for x in allat if x["leak"])
    think = sum(1 for x in allat if x["think_leftover"])
    reasoning = sum(1 for x in allat if x.get("reasoning_chars"))
    lat = [r["whole_latency_s"] for r in rs]
    lat_s = f"{statistics.median(lat):.1f} / " + (f"{p95(lat):.1f}" if n >= 30 else f"{max(lat):.1f} (max, n<30)") if lat else "-"
    return [str(n), pct(leak1, len(a1_valid)), f"{a1_timeout} / {a1_err} / {a1_invalid}",
            pct(leak2, len(retried)) if retried else "no retry", pct(residual, len(leaked1)),
            pct(len(tmpl), n), " / ".join(f"{v}" for v in causes.values()),
            pct(sum(1 for x in a1 if x["valid"]), len(a1) - a1_timeout - a1_err), pct(valid_n, len(counted)),
            str(miss), str(unp), str(think), str(reasoning), lat_s, str(sum(1 for r in rs if r["over_budget"]))]


HEAD = ["n", "leak a1 (of valid a1)", "a1 timeout / request error / invalid JSON", "leak a2 (a1 leaked and a2 ran: leaked again)",
        "residual (a1 leaked, template shown)", "template fallback",
        "fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template)",
        "JSON valid a1", "JSON valid a1+a2", "possible gate misses", "unparsed formulas", "<think> left", "attempts with reasoning (thinking not off?)",
        "latency median / p95 (s); p95 is the max when n<30", ">20 s"]


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

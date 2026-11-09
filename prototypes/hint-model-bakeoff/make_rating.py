"""PROTOTYPE. results/gpu-*.jsonl -> rating/RATING.md, rating/ratings.csv, rating/key.csv (blind, shuffled, fixed seed).
Usage: uv run python make_rating.py [--seed 31]. Rates what the student would see: the passed LLM hint, or the template on fallback."""
import argparse, csv, glob, json, os, random
from steps_bakeoff import ITEMS, template

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=31)
ap.add_argument("--en-items", default="lin2,quad,ineq,wrong", help="English subset")
ap.add_argument("--glob", default="results/gpu-*.jsonl")
a = ap.parse_args()
EN = a.en_items.split(",")
items = {i["id"]: i for i in ITEMS}
data = {}   # label -> {(step, rung, locale): record}
for f in sorted(glob.glob(a.glob)):
    for line in open(f):
        r = json.loads(line)
        data.setdefault(r["label"], {})[(r["step"], r["rung"], r["locale"])] = r
labels = sorted(data)
groups = [(i["id"], rung, loc) for loc in ("ro", "en") for i in ITEMS for rung in (1, 2, 3) if loc == "ro" or i["id"] in EN]
rng = random.Random(a.seed)
os.makedirs("rating", exist_ok=True)
md = ["# Rating sheet (blind): hint model bake-off, #31", "",
      "Rate each option in each group. Fill `ratings.csv` (one row per option: group id + letter). Do NOT open `key.csv` before you have rated everything.", "",
      "Columns:", "- usefulness 1-5: would this help a student at this rung?",
      "- correct y/n: is the content mathematically and linguistically correct (also correct Romanian)?",
      "- leaks y/n: it states the next step or the answer, OR it gives away a later rung (an operation at rung 1-2, a later step). "
      "Rung overshoot counts as a leak here; write what overshoots in the comment.",
      "- comment: free text.", "",
      "Rung 1 = where the student stands. Rung 2 = the method. Rung 3 = the operation to apply (not carried out). Rung 4 is never LLM-written.", ""]
ratings, key = [], []
for (sid, rung, loc) in groups:
    it = items[sid]
    gid = f"{sid}-r{rung}-{loc}"
    opts = []   # (text, math, [sources])
    tpl = template(it, rung, loc)
    tpl_srcs = ["template"]
    for lab in labels:
        r = data[lab].get((sid, rung, loc))
        if r is None:
            continue
        sh = r["shown"]
        if r["final_source"] == "template" or (sh["hint"] == tpl and not sh["math"]):
            tpl_srcs.append(f"{lab}:{'fallback' if r['final_source']=='template' else 'llm-identical'}")
            continue
        for o in opts:
            if o[0] == sh["hint"] and o[1] == sh["math"]:   # two models gave identical text: show once
                o[2].append(f"{lab}:{r['final_source']}")
                break
        else:
            opts.append((sh["hint"], sh["math"], [f"{lab}:{r['final_source']}"]))
    opts.append((tpl, [], tpl_srcs))
    rng.shuffle(opts)
    md += [f"## {gid}", "", f"Goal: {it['goal']}. Language of the hints: {'Romanian' if loc == 'ro' else 'English'}. Rung {rung}.",
           f"Student steps: " + "; ".join(f"({n+1}) `{s}`" for n, s in enumerate(it["steps"])),
           f"CAS verdicts: {it['verdicts'] or 'none'}. Ladder builds on step {it['builds_on']}. Goal status: {it['goal_status']}.",
           f"Hidden from the model and the student: next step `{it['next_step']}`, answer `{it['answer']}`.", ""]
    for k, (text, math, srcs) in enumerate(opts):
        letter = "ABCDEFGH"[k]
        md.append(f"**{letter}.** {text}" + ("".join(f" `{m}`" for m in math)))
        md.append("")
        ratings.append([gid, letter, "", "", "", ""])
        key.append([gid, letter, "; ".join(srcs)])
with open("rating/RATING.md", "w") as f:
    f.write("\n".join(md) + "\n")
with open("rating/ratings.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["group", "option", "usefulness_1_5", "correct_yn", "leaks_or_overshoots_yn", "comment"]); w.writerows(ratings)
with open("rating/key.csv", "w", newline="") as f:
    f.write("# DO NOT OPEN BEFORE RATING: maps option letters to models. 'template' = CAS-rule wording; 'label:fallback' = that model fell back to the template.\n")
    w = csv.writer(f); w.writerow(["group", "option", "sources"]); w.writerows(key)
print(len(groups), "groups,", len(ratings), "options; models:", labels)

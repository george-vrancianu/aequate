"""PROTOTYPE. results/gpu-*.jsonl -> rating/RATING.md, rating/ratings.csv, rating/key.csv (blind, shuffled, fixed seed).
Usage: uv run python make_rating.py [--seed 31]. Rates what the student would see: the passed LLM hint, or the template on fallback."""
import argparse, csv, glob, json, os, random, re, sys
from steps_bakeoff import ITEMS, template

def norm(text):
    """Same look for every option: LaTeX delimiters ($..$, \\(..\\)) and backticks are removed, so formulas are plain text everywhere;
    the math[] chips are not shown (they only copy the student's steps)."""
    text = re.sub(r"\$\$?([^$]+?)\$\$?", lambda m: m.group(1).strip(), text)
    text = re.sub(r"\\\((.+?)\\\)", lambda m: m.group(1).strip(), text)
    return text.replace("$", "").replace("`", "")


def features(text):
    return {"code spans": min(text.count("`") // 2, 3), "dollar signs": "$" in text,
            "question": text.rstrip().endswith("?"), "sentences": min(len(re.findall(r"[.?!](?:\s|$)", text)), 3)}


ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=31)
ap.add_argument("--en-items", default="lin2,quad,ineq,wrong", help="English subset")
ap.add_argument("--max-unique", type=int, default=8, help="fail if a structural feature is unique to the template in more groups than this")
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
      "Formulas appear as plain text or raw LaTeX; the student would see them rendered. Every option is shown as plain hint text only: the formula chips the tool would add under a hint are left out for all options "
      "(they copy the student's steps, which each group already shows), so that no option is recognisable by its layout.", "",
      "Columns:", "- usefulness 1-5 (1 = harmful or useless, 3 = OK, 5 = what a good teacher would say at this rung): would this help a student at this rung?",
      "- correct y/n: is the content mathematically and linguistically correct (also correct Romanian)?",
      "- leaks y/n: it states the next step or the answer, OR it gives away a later rung (an operation at rung 1-2, a later step). "
      "Rung overshoot counts as a leak here; write what overshoots in the comment.",
      "- comment: free text. Please also note when a hint stays BELOW its rung (rung 3 that does not name the operation, rung 2 that does not name the method); that is not a leak, so leave leaks = n.", "",
      "Rung 1 = where the student stands. Rung 2 = the method. Rung 3 = the operation to apply (not carried out). Rung 4 is never LLM-written.", ""]
ratings, key = [], []
shortest = 0   # groups where the template is the shortest option (reported, not a failure: the template wording is naturally terse)
uniq = {}   # feature -> number of groups where the template has a value no other option has
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
        if r["final_source"] == "template" or norm(sh["hint"]) == norm(tpl):   # same visible text as the template
            tpl_srcs.append(f"{lab}:{'fallback' if r['final_source']=='template' else 'llm-identical'}")
            continue
        for o in opts:
            if norm(o[0]) == norm(sh["hint"]):   # two models gave the same visible text: show once
                o[2].append(f"{lab}:{r['final_source']}")
                break
        else:
            opts.append((sh["hint"], sh["math"], [f"{lab}:{r['final_source']}"]))
    opts.append((tpl, [], tpl_srcs))
    opts = [(norm(t), [], srcs) for (t, m, srcs) in opts]
    rng.shuffle(opts)
    tf = features(opts[[o[2] for o in opts].index(tpl_srcs)][0])
    shortest += len(opts[[o[2] for o in opts].index(tpl_srcs)][0]) < min(len(o[0]) for o in opts if o[2] is not tpl_srcs)
    for fname, v in tf.items():
        if all(features(o[0])[fname] != v for o in opts if o[2] is not tpl_srcs):
            uniq[fname] = uniq.get(fname, 0) + 1
    md += [f"## {gid}", "", f"Goal: {it['goal']}. Language of the hints: {'Romanian' if loc == 'ro' else 'English'}. Rung {rung}.",
           f"Student steps: " + "; ".join(f"({n+1}) `{s}`" for n, s in enumerate(it["steps"])),
           f"CAS verdicts: {', '.join(it['verdicts']) or 'none'}. Ladder builds on step {it['builds_on']}. Goal status: {it['goal_status']}.",
           f"Hidden from the model and the student: next step `{it['next_step']}`, answer `{it['answer']}`.", ""]
    for k, (text, math, srcs) in enumerate(opts):
        letter = "ABCDEFGH"[k]
        md.append(f"**{letter}.** {text}")
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
print("structural uniformity (groups where the template alone has a feature value, of", len(groups), "):", uniq or "none")
print(f"residual: the template is the shortest option in {shortest} of {len(groups)} groups (length cannot be equalised without rewriting the hints)")
bad = {k: v for k, v in uniq.items() if v > a.max_unique}
if bad:
    sys.exit(f"FAIL: template identifiable by structure: {bad}")
print(len(groups), "groups,", len(ratings), "options; models:", labels)

"""PROTOTYPE (throwaway), issue #31. Hint bake-off harness: ONE contract for every model (ADR 0005 / #48):
OpenAI-compatible POST {base}/v1/chat/completions, English system prompt (PROMPT_VERSION v1), CAS facts as JSON in the user message,
JSON schema {hint, math[]}, temperature 0, thinking off, max_tokens 400, 20 s budget over both attempts, leak check, one retry
(only if >= 5 s left), template on failure. Sequential, one request in flight. Writes results/<label>.jsonl, one line per hint.
Usage: uv run python bakeoff.py --base-url http://127.0.0.1:8080 --model qwen3.5-4b --label q4-cpu --locales en,ro --rungs 1,2,3 \
         --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}' [--steps lin2,quad] [--limit 6]"""
import argparse, json, os, sys, time
import httpx
from steps_bakeoff import ITEMS, RUNGS, LOCALES, payload, template
from leakcheck import check, LEAK_CHECK_VERSION

PROMPT_VERSION = "v1"
LANG = {"en": "English", "ro": "Romanian"}
SYSTEM = (
    "You write hints for a school algebra tutoring tool. You receive facts about a student's work as JSON, produced by a "
    "computer algebra system, and you reword them into one short hint.\n"
    "Rules:\n"
    "- Use only the facts in the JSON. Do not solve the problem and do not do the next calculation.\n"
    "- Never state the next step of the solution or the final answer, and never write a number or formula that gives them away.\n"
    "- Match the rung: rung 1 says where the student stands (the goal status); rung 2 names the method; rung 3 names the "
    "operation to apply, without carrying it out.\n"
    "- The hint is one or two short sentences addressed to the student.\n"
    "- Write the hint in {language}.\n"
    "Reply with JSON only, in this shape: {{\"hint\": string, \"math\": [string, ...]}}. \"math\" holds LaTeX (without $ signs) "
    "for formulas you refer to, copied from the facts; it may be empty."
)
SCHEMA = {"type": "object", "properties": {"hint": {"type": "string"}, "math": {"type": "array", "items": {"type": "string"}}},
          "required": ["hint", "math"], "additionalProperties": False}
RESPONSE_FORMAT = {"type": "json_schema", "json_schema": {"name": "hint", "strict": True, "schema": SCHEMA}}


# unrecorded warm-up item: NOT one of the measured steps, so prefix/prompt caching cannot make the first measured hint faster
WARMUP_ITEM = dict(goal="solve for y", steps=[r"4y-9=11"], verdicts=[], builds_on=1, goal_status="y is not isolated yet",
                   method="isolate y by undoing the operations in reverse order", operation="add 9 to both sides")


def messages_for(item, rung, locale):
    return [{"role": "system", "content": SYSTEM.format(language=LANG[locale])},
            {"role": "user", "content": json.dumps(payload(item, rung), ensure_ascii=False)}]


def validate(content):
    """-> (parsed | None, invalid_reason | None). Invalid: not JSON, not an object, missing keys, wrong types, empty hint."""
    try:
        d = json.loads(content)
    except Exception as e:
        return None, f"not valid JSON ({type(e).__name__})"
    if not isinstance(d, dict):
        return None, "JSON is not an object"
    if "hint" not in d or "math" not in d:
        return None, "missing key hint or math"
    if not isinstance(d["hint"], str) or not isinstance(d["math"], list) or not all(isinstance(m, str) for m in d["math"]):
        return None, "wrong types"
    if not d["hint"].strip():
        return None, "empty hint"
    return d, None


def call(client, base, model, extra, msgs, timeout, api_key):
    body = {"model": model, "messages": msgs, "temperature": 0, "max_tokens": 400, "response_format": RESPONSE_FORMAT, **extra}
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    t0 = time.monotonic()
    rec = {"request": body, "http_status": None, "error": None, "content": None, "reasoning_chars": 0, "finish_reason": None,
           "prompt_tokens": None, "completion_tokens": None}
    try:
        r = client.post(base.rstrip("/") + "/v1/chat/completions", json=body, headers=headers, timeout=max(timeout, 0.1))
        rec["http_status"] = r.status_code
        j = r.json()
        if r.status_code != 200:
            rec["error"] = json.dumps(j)[:500]
        else:
            ch = j["choices"][0]
            m = ch["message"]
            rec["content"] = m.get("content") or ""
            rec["reasoning_chars"] = len(m.get("reasoning_content") or m.get("reasoning") or "")
            rec["finish_reason"] = ch.get("finish_reason")
            u = j.get("usage") or {}
            rec["prompt_tokens"], rec["completion_tokens"] = u.get("prompt_tokens"), u.get("completion_tokens")
    except httpx.TimeoutException:
        rec["error"] = "timeout"
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:500]
    rec["latency_s"] = round(time.monotonic() - t0, 3)
    return rec


def judge(item, rung, rec):
    """Fill validity, <think> leftovers and the leak verdict on an attempt record."""
    rec.update(valid=False, invalid_reason=None, parsed=None, think_leftover=False, leak=None)
    if rec["error"]:
        rec["invalid_reason"] = rec["error"] if rec["error"] == "timeout" else "request error"
        return rec
    rec["think_leftover"] = "<think" in rec["content"] or "</think" in rec["content"]
    parsed, why = validate(rec["content"])
    rec["parsed"], rec["invalid_reason"], rec["valid"] = parsed, why, parsed is not None
    if parsed:
        rec["leak"] = check(item, payload(item, rung), parsed["hint"], parsed["math"])
    return rec


def run_hint(client, a, item, rung, locale):
    t0 = time.monotonic()
    msgs = messages_for(item, rung, locale)
    attempts, final = [], None
    for n in (1, 2):
        remaining = a.budget - (time.monotonic() - t0)
        if n == 2 and remaining < a.min_retry:
            break
        rec = judge(item, rung, call(client, a.base_url, a.model, a.extra, msgs, remaining, a.api_key)) | {"n": n}
        attempts.append(rec)
        if rec["valid"] and not rec["leak"]["leak"]:
            final = f"llm{n}"
            break
        if rec["error"]:                  # no reply to rewrite: a timeout or a request error (the retry is for a leak or invalid JSON only)
            break
        reason = ("; ".join(rec["leak"]["reasons"]) if rec["valid"] else
                  "the reply was not valid JSON of the form {\"hint\": string, \"math\": [strings]}")
        msgs = msgs[:2] + [{"role": "assistant", "content": rec["content"] or "(empty reply)"}] + \
            [{"role": "user", "content": f"Rejected: {reason}. Rewrite the hint without it."}]
    whole = round(time.monotonic() - t0, 3)
    if final and whole > a.budget:      # the read timeout is per read, so an attempt can end a little after the budget: the product shows the template
        final = None
    if final:
        p = attempts[-1]["parsed"]
        shown = {"hint": p["hint"], "math": p["math"]}
    else:
        final = "template"
        shown = {"hint": template(item, rung, locale), "math": []}
    return {"label": a.label, "model": a.model, "step": item["id"], "rung": rung, "locale": locale,
            "prompt_version": PROMPT_VERSION, "leak_check_version": LEAK_CHECK_VERSION, "budget_s": a.budget,
            "payload": payload(item, rung), "attempts": attempts, "final_source": final, "shown": shown,
            "whole_latency_s": whole, "over_budget": whole > a.budget,
            "gate_miss": attempts[-1]["leak"]["gate_miss"] if final != "template" else [],
            "extra_body": a.extra}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--locales", default="en,ro")
    ap.add_argument("--rungs", default="1,2,3")
    ap.add_argument("--steps", default="", help="comma list of step ids (default: all)")
    ap.add_argument("--limit", type=int, default=0, help="run N combinations, evenly spread over the full list")
    ap.add_argument("--extra-body", default="{}", help="JSON merged into the request body (per-model thinking-off switch)")
    ap.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--budget", type=float, default=20.0)
    ap.add_argument("--min-retry", type=float, default=5.0)
    ap.add_argument("--warmup", type=int, default=1, help="unrecorded requests first (load/cache the model)")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    a.extra = json.loads(a.extra_body)
    ids = [s for s in a.steps.split(",") if s]
    combos = [(it, r, l) for it in ITEMS if not ids or it["id"] in ids
              for r in (int(x) for x in a.rungs.split(",")) for l in a.locales.split(",")]
    if a.limit and a.limit < len(combos):
        combos = [combos[int(i * len(combos) / a.limit)] for i in range(a.limit)]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"{a.label}.jsonl")
    with httpx.Client() as client:
        for _ in range(a.warmup):
            call(client, a.base_url, a.model, a.extra, messages_for(WARMUP_ITEM, 1, "en"), 600, a.api_key)
        with open(path, "w") as f:
            for i, (it, r, l) in enumerate(combos, 1):
                rec = run_hint(client, a, it, r, l)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                at = rec["attempts"]
                print(f"[{i}/{len(combos)}] {it['id']:6} r{r} {l} -> {rec['final_source']:8} {rec['whole_latency_s']:6.2f}s "
                      f"attempts={len(at)} valid={[x['valid'] for x in at]} leak={[bool(x['leak'] and x['leak']['leak']) for x in at]}", flush=True)
    print("wrote", path)


if __name__ == "__main__":
    main()

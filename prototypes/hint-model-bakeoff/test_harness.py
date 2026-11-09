"""PROTOTYPE. Harness flow check with a mock transport: retry after a leak, template after two leaks, timeout -> template."""
import json, types, httpx
import bakeoff
from steps_bakeoff import ITEMS

IT = next(i for i in ITEMS if i["id"] == "lin2")


def run(replies, budget=20.0):
    seen = []
    def handler(req):
        seen.append(json.loads(req.content))
        r = replies[min(len(seen) - 1, len(replies) - 1)]
        if r == "timeout":
            raise httpx.ReadTimeout("x")
        return httpx.Response(200, json={"choices": [{"message": {"content": r}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    a = types.SimpleNamespace(base_url="http://x", model="m", label="t", extra={}, api_key="", budget=budget, min_retry=5.0)
    return bakeoff.run_hint(httpx.Client(transport=httpx.MockTransport(handler)), a, IT, 3, "en"), seen


GOOD = json.dumps({"hint": "Undo the addition first.", "math": []})
LEAK = json.dumps({"hint": "So x=2.", "math": []})


def test_clean_first_try():
    r, seen = run([GOOD]); assert r["final_source"] == "llm1" and len(seen) == 1


def test_retry_after_leak_adds_reason():
    r, seen = run([LEAK, GOOD]); assert r["final_source"] == "llm2"
    m = seen[1]["messages"]; assert m[-1]["content"].startswith("Rejected:") and m[-2]["role"] == "assistant"


def test_two_leaks_template():
    r, _ = run([LEAK, LEAK]); assert r["final_source"] == "template" and len(r["attempts"]) == 2


def test_invalid_json_retries():
    r, seen = run(["not json", GOOD]); assert r["final_source"] == "llm2" and not r["attempts"][0]["valid"]


def test_timeout_is_template():
    r, _ = run(["timeout"]); assert r["final_source"] == "template" and len(r["attempts"]) == 1


def test_request_contract():
    _, seen = run([GOOD]); b = seen[0]
    assert b["temperature"] == 0 and b["max_tokens"] == 400 and b["response_format"]["type"] == "json_schema"
    assert "2x=4" not in json.dumps(b) and "x=2" not in b["messages"][1]["content"]

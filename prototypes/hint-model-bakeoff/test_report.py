"""PROTOTYPE. Report metric fixtures: denominators and cause columns add up. Run: uv run pytest -q test_report.py"""
import report


def att(valid=True, leak=False, error=None, reasoning=0, think=False):
    return {"valid": valid, "error": error, "think_leftover": think, "reasoning_chars": reasoning,
            "leak": {"leak": leak, "unparsed": 0} if valid else None, "invalid_reason": None}


def hint(attempts, final, over=False, lat=1.0):
    return {"attempts": attempts, "final_source": final, "gate_miss": [], "over_budget": over, "whole_latency_s": lat}


def test_metrics():
    rs = [hint([att()], "llm1"),                                           # clean
          hint([att(leak=True), att()], "llm2"),                          # leaked, retry clean
          hint([att(leak=True), att(leak=True)], "template"),             # leaked twice
          hint([att(leak=True)], "template"),                             # leaked, no time to retry
          hint([att(valid=False), att()], "llm2"),                        # invalid JSON, retry clean
          hint([att(valid=False, error="timeout")], "template"),         # timeout
          hint([att(valid=False, error="HTTPError 400")], "template"),   # request error
          hint([att(reasoning=50)], "template", over=True)]               # clean but over budget
    r = report.row(rs)
    h = dict(zip(report.HEAD, r))
    assert h["leak a1 (of valid a1)"] == "60% (3/5)"                       # valid a1: 5 (timeout, request error and invalid JSON are not in it)
    assert h["a1 timeout / request error / invalid JSON"] == "1 / 1 / 1"
    assert h["leak a2 (a1 leaked and a2 ran: leaked again)"] == "50% (1/2)"
    assert h["residual (a1 leaked, template shown)"] == "67% (2/3)"
    assert h["template fallback"] == "62% (5/8)"
    assert h[report.HEAD[6]] == "1 / 1 / 1 / 1 / 1"
    assert report.cause(rs[2]) == "rejected twice" and report.cause(rs[3]) == "no time to retry"
    assert [report.cause(x) for x in rs if x["final_source"] == "template"] == ["rejected twice", "no time to retry", "timeout", "request error", "over budget"]
    assert h["attempts with reasoning (thinking not off?)"] == "1"
    assert h["JSON valid a1"] == "83% (5/6)"                               # timeout and request error excluded from the denominator

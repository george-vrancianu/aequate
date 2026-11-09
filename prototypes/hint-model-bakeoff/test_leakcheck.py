"""PROTOTYPE. Leak-check fixtures: leaking and clean hints per category. Run: uv run pytest -q test_leakcheck.py"""
import pytest
from steps_bakeoff import ITEMS, payload, template, RUNGS, LOCALES
from leakcheck import check, numbers
from fractions import Fraction

I = {i["id"]: i for i in ITEMS}


def leaks(item_id, hint, math=(), rung=3):
    it = I[item_id]
    return check(it, payload(it, rung), hint, list(math))


def test_numbers_normalisation():
    assert Fraction(3, 4) in numbers("0,75")
    assert Fraction(2) in numbers(r"\frac{8}{2}") and Fraction(4) in numbers("4.0")
    assert numbers("\u22123") == {Fraction(3)}


# --- category: number matching
def test_number_in_prose_leaks():
    r = leaks("frac", "After combining, the coefficient is $\\frac{5}{6}$ and the right side is 5, so x is 6 in the end.")
    assert r["leak"] and any("number 6" in x for x in r["reasons"])


def test_number_forbidden_only_if_absent_from_payload():
    # 2x+3=7 / x=2: 2 occurs in the input, so number matching cannot catch it
    r = leaks("lin2", "Think about what happens to the 2 in front of x.")
    assert not r["leak"]
    r = leaks("lin2", "You will find that 4 is on the right.")      # 4 is in the hidden next step 2x=4
    assert r["leak"] and "number 4" in r["reasons"][0]


def test_number_in_math_entry_and_fraction_form():
    assert leaks("dec", "Combine them.", [r"\frac{3}{4}x"])["leak"]            # 3/4 == 0.75
    assert leaks("both", "Combine them.", [r"x = \frac{8}{2}"])["leak"]       # 4


# --- category: formula matching (the 2x+3=7 / x=2 case)
def test_answer_formula_leaks_even_when_number_is_in_payload():
    r = leaks("lin2", "Isolate x.", ["x = 2"])
    assert r["leak"] and "answer" in r["reasons"][0]
    assert leaks("lin2", "So $x=2$.", [])["leak"]
    assert leaks("lin2", "So $2=x$.", [])["leak"]


def test_next_step_formula_leaks():
    assert leaks("lin2", "Write", [r"2x = 4"])["leak"]
    assert leaks("lin2", "Write", [r"4 = 2x"])["leak"]
    assert leaks("quad", "Try", [r"(x-2)(x-3)=0"])["leak"]
    assert leaks("quad", "Roots", [r"x=2 \lor x=3"])["leak"]
    assert leaks("sys", "Then", ["2x = 6"])["leak"]
    assert leaks("sys", "Solution", [r"x=3, y=2"])["leak"]
    assert leaks("ineq", "Result", [r"x < -3"])["leak"]
    assert leaks("rearr", "Result", [r"x = \frac{y-3}{2}"])["leak"]
    assert leaks("dom", "So", [r"x+1"])["leak"]


# --- category: decimal comma
def test_decimal_comma():
    assert leaks("dec", "Aduna: coeficientul este 0,75.")["leak"]
    assert leaks("dec", "Rezultatul este", ["0,75x = 3"])["leak"]
    assert leaks("dec", "Deci", ["x = 4"])["leak"]
    assert not leaks("dec", "Aduna termenii in $x$: $0,5x + 0,25x$.", [r"0,5x+0,25x"])["leak"]


# --- category: restating the current step must PASS
def test_restating_current_step_is_clean():
    assert not leaks("lin2", "Look at 2x+3=7 and undo the +3.", ["2x+3=7"])["leak"]
    assert not leaks("quad", "You have $x^2-5x+6=0$.", ["x^2-5x+6=0"])["leak"]
    assert not leaks("log", "From x(x-2)=3 move the 3 over.", [r"x\cdot(x-2)=3"])["leak"]
    assert not leaks("sqrt", "You wrote x+1=(x-1)^2.", ["x+1=(x-1)^2"])["leak"]


# --- category: not-equivalent chain
def test_not_equivalent_chain():
    wrong = leaks("wrong", "Step 2 does not follow from step 1; compare 2x=10 with step 1.", ["2x=10"], rung=1)
    assert not wrong["leak"]                                  # restating the student's wrong step is fine
    assert leaks("wrong", "Go back to step 1; it gives 2x=4.", ["2x=4"], rung=1)["leak"]
    assert leaks("wrong", "Go back to step 1; the answer is x=2.", [], rung=1)["leak"]
    assert not leaks("wrong", "Step 2 doesn't follow from step 1. Undo the +3 from step 1 first.", [], rung=1)["leak"]


# --- clean hints
def test_clean_hints():
    assert not leaks("lin2", "Undo the addition first, then deal with the coefficient of x.", rung=3)["leak"]
    assert leaks("rearr", "Subtract 3 from both sides.", ["y-3=2x"], rung=3)["leak"]   # that is the next step, reversed
    assert not leaks("both", "Move the terms in x to one side.", ["5x-2x"])["leak"]
    assert not leaks("sys", "Add the equations so that y cancels.", ["(x+y)+(x-y)"])["leak"]


def test_bare_relation_in_prose():
    assert leaks("lin2", "Go back to step 1; so x=2.")["leak"]
    assert leaks("lin2", "You end with 2x = 4.")["leak"]
    assert not leaks("lin2", "Undo the +3, then divide by 2.")["leak"]


# --- unparsed formulas are counted, not leaks
def test_unparsed_counted():
    r = leaks("lin2", "Hint", [r"\text{subtract } 3"])
    assert not r["leak"] and r["unparsed"] == 1


# --- gate-miss audit (not a gate)
def test_gate_miss_audit():
    r = leaks("quad", "Cele doua radacini sunt doi si trei.")
    assert not r["leak"] and r["gate_miss"]
    r = leaks("quad", "The roots are two and three.")
    assert not r["leak"] and any("three" in x for x in r["gate_miss"])
    r = leaks("lin2", "The answer is the number of apples.")
    assert not r["leak"] and r["gate_miss"]
    assert not leaks("lin2", "Undo the addition first.")["gate_miss"]


# --- the hand-written templates must themselves pass the gate
@pytest.mark.parametrize("item", ITEMS, ids=lambda i: i["id"])
def test_templates_pass_gate(item):
    for rung in RUNGS:
        for loc in LOCALES:
            r = check(item, payload(item, rung), template(item, rung, loc), [])
            assert not r["leak"], (item["id"], rung, loc, r["reasons"])


def test_payload_never_contains_hidden():
    for it in ITEMS:
        for rung in RUNGS:
            s = str(payload(it, rung))
            assert it["next_step"] not in s and it["answer"] not in s

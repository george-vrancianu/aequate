"""PROTOTYPE wrapper. parsing.py stays verbatim from the research; its _fix() rebuilds the tree with evaluation ON,
which turns (4x+8)/4 into x+2, x/x into 1, sqrt(x)*sqrt(x) into x. This mirrors to_sympy/check_line but runs _fix under
sympy.evaluate(False), so the ANTLR parser's own unevaluated tree survives. No Lark cross-check here (the evaluated path
already did it). Still no sympify/eval: only parse_latex(strict=True)."""
import sympy
from sympy.core.function import AppliedUndef
from sympy.parsing.latex import parse_latex
from parsing import (_fix, Reject, NAME_OK, split_system, split_chain, rewrite)

parse_latex("x", strict=True)   # import the backend with evaluation ON (importing it under evaluate(False) breaks sympy.physics.units)

def to_sympy_raw(s, constants=True):
    with sympy.evaluate(False):
        e = parse_latex(s, strict=True)
        for sym in e.free_symbols:
            if not NAME_OK.match(str(sym.name)): raise Reject(f"suspicious symbol {sym.name!r}")
        for f in e.atoms(AppliedUndef): raise Reject(f"undeclared function {f.func}")
        return _fix(e, constants)

def check_line_raw(s, decimal_comma=True):
    if not s.strip(): raise Reject("empty")
    return [to_sympy_raw(b) for line in split_system(s) for part in split_chain(line)
            for b in rewrite(part, decimal_comma)]

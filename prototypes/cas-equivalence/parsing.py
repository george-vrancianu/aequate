"""Reused verbatim from the appendix of docs/research/sympy-latex-parser-coverage.md
(branch origin/research/sympy-latex-parser-coverage). PROTOTYPE: regex-based, crude."""
import re, warnings
warnings.simplefilter("ignore")
import sympy
from sympy import Symbol, simplify, pi, E
from sympy.core.function import AppliedUndef
from sympy.parsing.latex import parse_latex

class Reject(Exception):
    """Tutor sees "can't check this step"."""

FUNCS = "sin|cos|tan|cot|sec|csc|ln|log|lg|exp|arcsin|arccos|arctan"
GREEK = ("alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho "
         "sigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega").split()
NAME_OK = re.compile(r"^(?:[a-zA-Z]|%s)(?:_\{?[A-Za-z0-9]+\}?)?'*$" % "|".join(sorted(GREEK, key=len, reverse=True)))
ALIASES = {"tg": r"\tan", "ctg": r"\cot", "cotg": r"\cot", "arctg": r"\arctan", "arcctg": r"\operatorname{arccot}",
           "sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "ln": r"\ln", "log": r"\log", "lg": r"\lg"}

def rewrite(s, decimal_comma=True):
    s = s.strip()
    s = re.sub(r"\\(?:left|right)(?![a-zA-Z])\s*", "", s)
    s = s.replace(r"\lvert", "|").replace(r"\rvert", "|")
    s = re.sub(r"(?:\\[,;:!]|\\quad|\\qquad|\s)+$", "", s)
    s = re.sub(r"\\(?:operatorname|mathrm)\s*\{\s*([a-z]+)\s*\}", lambda m: ALIASES.get(m.group(1), m.group(0)), s)
    s = re.sub(r"\\(tg|ctg|cotg|arctg)(?![a-zA-Z])", lambda m: ALIASES[m.group(1)], s)
    s = re.sub(r"\\ne(?![a-zA-Z])", r"\\neq", s)
    s = re.sub(r"\\var(phi|epsilon|theta|rho)(?![a-zA-Z])", r"\\\1", s)
    s = re.sub(r"\\mathrm\s*\{\s*([de])\s*\}", r"\1", s)
    s = re.sub(r"\\sqrt\s+([a-zA-Z0-9])", r"\\sqrt{\1}", s)
    s = re.sub(r"\\binom\s*(\d)\s*(\d)", r"\\binom{\1}{\2}", s)
    if re.search(r"\\begin\{[pbvBV]?matrix\}", s): raise Reject("matrix")
    if not s: raise Reject("empty")
    if re.search(r"(?<![_^\d])\d+\s+\d", s) or re.search(r"\d\\[,;!]\s*\d", s): raise Reject("digit groups")
    s = re.sub(r"_\{([A-Za-z0-9]+),([A-Za-z0-9]+)\}", r"_{\1\2}", s)
    s = re.sub(r"(\d)\{,\}(\d)", r"\1.\2", s)
    if re.search(r"\d[.,]\d+[.,]\d", s): raise Reject("two separators in one number")
    s = re.sub(r"(?<![\d}])\.(\d)", r"0.\1", s)
    if re.search(r"\d,\d", s):
        if not decimal_comma: raise Reject("comma between digits")
        if re.search(r"\([^()]*\d,\d[^()]*\)", s): raise Reject("decimal comma inside parentheses")
        s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*\\%", r"(\1/100)", s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*\^\s*\{?\s*\\circ\s*\}?", r"(\1\\cdot\\frac{\\pi}{180})", s)
    if "\\circ" in s: raise Reject("degree sign on a non-number")
    s = re.sub(r"(?<!\\):", r"\\div ", s)
    if re.search(r"\^\s*(?:\{[^{}]*\}|\\?\w+)\s*\^", s): raise Reject("double superscript")
    s = re.sub(r"\^(\{[^{}]*\}|\w)_(\{[^{}]*\}|\w)", r"_\2^\1", s)
    if re.search(r"\^-", s): raise Reject("unbraced negative exponent")
    if re.search(r"\\(?:%s)(?![a-zA-Z])(?!\s*[({^_])[^=<>+\-]*?(?:\\cdot|\\times|\\div|/)" % FUNCS, s):
        raise Reject("unparenthesized function argument followed by * or /")
    if re.search(r"\d\s*\\[dt]?frac\s*\{?\d", s): raise Reject("mixed number?")
    if re.search(r"\\int(?![a-zA-Z])", s) and not re.search(r"(?:\bd|\\mathrm\{d\})\s*[a-zA-Z]\s*$|\\frac\{d", s):
        raise Reject("integral without differential")
    if re.search(r"\\(?:text|mathrm|operatorname|mathbf)\s*\{", s): raise Reject("text/unit span: units path")
    if re.search(r"\\(?:pm|mp)(?![a-zA-Z])", s):
        return [re.sub(r"\\pm(?![a-zA-Z])", "+", re.sub(r"\\mp(?![a-zA-Z])", "-", s)),
                re.sub(r"\\pm(?![a-zA-Z])", "-", re.sub(r"\\mp(?![a-zA-Z])", "+", s))]
    return [s]

def split_system(s):
    if re.search(r"\\begin\{[pbvBV]?matrix\}", s): return [s]
    m = re.fullmatch(r"\s*\\begin\{(cases|aligned|align\*?|gathered|array)\}(?:\{[^}]*\})?(.*)\\end\{\1\}\s*", s, re.S)
    body = m.group(2) if m else s
    return [l.replace("&", "") for l in re.split(r"\\\\", body) if l.strip()]

def split_chain(s):
    parts = re.split(r"(=|<|>|\\leq?(?![a-zA-Z])|\\geq?(?![a-zA-Z])|\\neq)", s)
    if len(parts) <= 3: return [s]
    return [parts[i - 1] + parts[i] + parts[i + 1] for i in range(1, len(parts) - 1, 2)]

def same(a, b):
    return len(a) == len(b) and all(p == q or p.doit() == q.doit()
        or simplify(sympy.nsimplify(p) - sympy.nsimplify(q)) == 0 for p, q in zip(a, b))

def _pair(e, c):
    return (e.args, c.args) if e.is_Relational and c.is_Relational and type(e) == type(c) else ((e,), (c,))

def _fix(c, constants):
    c = c.xreplace({s: Symbol(str(s.name)) for s in c.free_symbols})        # lark Token -> str
    return c.xreplace({Symbol("pi"): pi, Symbol("e"): E}) if constants else c

def to_sympy(s, constants=True):
    e = parse_latex(s, strict=True)
    for sym in e.free_symbols:
        if not NAME_OK.match(str(sym.name)): raise Reject(f"suspicious symbol {sym.name!r}")
    for f in e.atoms(AppliedUndef): raise Reject(f"undeclared function {f.func}")
    e = _fix(e, constants)
    try: l = parse_latex(s, backend="lark")
    except Exception: l = None                                               # lark gap: no veto
    if isinstance(l, sympy.Basic):
        if not same(*_pair(e, _fix(l, constants))): raise Reject("backends disagree")
    elif l is not None and type(l).__name__ == "Tree" and l.data == "_ambig":
        alts = [_fix(c, constants) for c in l.children if isinstance(c, sympy.Basic)]
        if not any(same(*_pair(e, c)) for c in alts): raise Reject("lark ambiguous, ANTLR reading not among them")
    return e

def check_line(s, decimal_comma=True):
    if not s.strip(): raise Reject("empty")
    return [to_sympy(b) for line in split_system(s) for part in split_chain(line)
            for b in rewrite(part, decimal_comma)]

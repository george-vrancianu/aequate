"""PROTOTYPE (throwaway), issue #31. Deterministic leak check, LEAK_CHECK_VERSION v1, run on the hint and every math[] entry.
Rule 1: forbidden numbers (in the hidden next step / answer, not in the payload sent). Rule 2: formula matching (structural,
NOT solution-set equivalence). Rule 3: gate-miss audit (number words, answer in prose), reported but NOT part of the gate.
Uses parsing.py (copied from prototypes/cas-equivalence on origin/prototype/cas-equivalence)."""
import json, re, unicodedata
from fractions import Fraction
import sympy
from sympy import Symbol
from parsing import check_line, split_system, Reject

LEAK_CHECK_VERSION = "v1"
EXEMPT = {Fraction(0), Fraction(1)}   # 0 and 1 in a hidden next step are not treated as forbidden (too common); deviation from design.md, documented in README
_NUM = r"\d+(?:[.,]\d+)?"


def _frac(s):
    return Fraction(s.replace(",", "."))


def norm(t):
    t = t.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace(r"\cdot", "*").replace(r"\times", "*")
    t = re.sub(r"\\(?:left|right)(?![a-zA-Z])", "", t)
    return t


def numbers(text):
    """Set of absolute values (Fraction) of every number in `text`: decimal comma, unicode minus, literal \\frac{a}{b} and a/b."""
    t = norm(text)
    out = set()
    for m in re.finditer(r"\\[dt]?frac\s*\{\s*(%s)\s*\}\s*\{\s*(%s)\s*\}" % (_NUM, _NUM), t):
        if _frac(m.group(2)) != 0:
            out.add(_frac(m.group(1)) / _frac(m.group(2)))
    for m in re.finditer(r"(?<![\d.,])(%s)\s*/\s*(%s)(?![\d])" % (_NUM, _NUM), t):
        if _frac(m.group(2)) != 0:
            out.add(_frac(m.group(1)) / _frac(m.group(2)))
    for m in re.finditer(r"(?<![\d.,])" + _NUM + r"(?![\d])", t):
        s = m.group(0)
        out.add(_frac(s))
        if re.fullmatch(r"\d+,\d+", s):          # "2,3": a decimal comma or a list; count both readings
            out.update(Fraction(p) for p in s.split(","))
    return out


def fmt(f):
    return str(int(f)) if f.denominator == 1 else str(float(f))


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def payload_numbers(payload):
    s = set()
    for t in _strings(payload):
        s |= numbers(t)
    s |= {Fraction(x["n"]) for x in payload.get("steps", [])}       # step indices are allowed ("step 2")
    return s


# ---------- formulas ----------
_REL = re.compile(r"\\leq?(?![a-zA-Z])|\\geq?(?![a-zA-Z])|\\neq?(?![a-zA-Z])|<|>|=")
_OPS = {"=": "=", "<": "<", ">": ">", r"\le": "<=", r"\leq": "<=", r"\ge": ">=", r"\geq": ">=", r"\ne": "!=", r"\neq": "!="}
_FLIP = {"=": "=", "!=": "!=", "<": ">", ">": "<", "<=": ">=", ">=": "<="}


def _split_top(s):
    """Split on top-level relation symbols (not inside {} or ()). Returns (operands, ops)."""
    parts, ops, depth, last, i = [], [], 0, 0, 0
    while i < len(s):
        c = s[i]
        if c in "{(":
            depth += 1
        elif c in "})":
            depth -= 1
        elif depth == 0:
            m = _REL.match(s, i)
            if m and not (s[i] == "=" and i > 0 and s[i - 1] in "<>!"):
                parts.append(s[last:i]); ops.append(_OPS[m.group(0)]); i = m.end(); last = i; continue
        i += 1
    parts.append(s[last:])
    return parts, ops


def _operand(s):
    r = check_line(s)
    if len(r) != 1 or not isinstance(r[0], sympy.Basic) or r[0].is_Relational:
        raise Reject("operand")
    return r[0]


def parse_formula(latex):
    """-> list of atoms: ("expr", e) or ("rel", op, lhs, rhs). Raises Reject/Exception when unparseable.
    Operands are parsed separately so that SymPy cannot auto-evaluate `a=a` to True."""
    atoms = []
    pieces = []
    for line in split_system(latex.strip()):
        pieces += [p for p in re.split(r"\\lor|\\land|\\vee|\\wedge|\;|(?<=\d),\s*(?=[a-zA-Z]\s*(?:=|<|>|\\le|\\ge))", line) if p.strip()]
    for p in pieces:
        p = re.sub(r"(?:\\[,;:!]|\\quad|\\qquad|\s)+$", "", p.strip())
        parts, ops = _split_top(p)
        if not ops:
            atoms.append(("expr", _operand(p)))
        else:
            es = [_operand(x) for x in parts]
            atoms += [("rel", ops[i], es[i], es[i + 1]) for i in range(len(ops))]
    return atoms


def atom_match(f, g):
    if f[0] != g[0]:
        return False
    if f[0] == "expr":
        return f[1] == g[1]
    if f[1] == g[1] and f[2] == g[2] and f[3] == g[3]:
        return True
    return _FLIP[f[1]] == g[1] and f[2] == g[3] and f[3] == g[2]


def spans(hint):
    out = []
    for pat in (r"\$\$(.+?)\$\$", r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", r"\\\((.+?)\\\)", r"\\\[(.+?)\\\]"):
        out += re.findall(pat, hint, flags=re.S)
    return out


_BARE = re.compile(r"-?[\d.,]*[A-Za-z](?:\^\{?\d+\}?)?\s*(?:=|<|>|≤|≥)\s*-?\d+(?:[.,]\d+)?(?![\d])")
_DELIM = re.compile(r"\$\$.+?\$\$|\$[^$]+\$|\\\(.+?\\\)|\\\[.+?\\\]", re.S)


def bare_relations(hint):
    """Relations written in the prose without math delimiters, like 'so x=2.' (extension to design.md: models often skip the $)."""
    t = norm(_DELIM.sub(" ", hint)).replace("≤", r"\le").replace("≥", r"\ge")
    return [m.rstrip(".,") for m in _BARE.findall(t)]


# ---------- gate-miss audit ----------
EN = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
RO = ("zero unu unul una doi doua trei patru cinci sase sapte opt noua zece unsprezece doisprezece treisprezece paisprezece "
      "cincisprezece saisprezece saptesprezece optsprezece nouasprezece douazeci").split()
EN_V = {w: i for i, w in enumerate(EN)}
RO_V = {"zero": 0, "unu": 1, "unul": 1, "una": 1, "doi": 2, "doua": 2, "trei": 3, "patru": 4, "cinci": 5, "sase": 6, "sapte": 7, "opt": 8,
        "noua": 9, "zece": 10, "unsprezece": 11, "doisprezece": 12, "treisprezece": 13, "paisprezece": 14, "cincisprezece": 15,
        "saisprezece": 16, "saptesprezece": 17, "optsprezece": 18, "nouasprezece": 19, "douazeci": 20}


def _plain(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def gate_miss(hint, forbidden, var):
    """Possible misses: forbidden number spelled as a word, or the answer stated in prose. Human review, not a gate."""
    text = re.sub(r"\$[^$]*\$|\\\(.*?\\\)", " ", hint, flags=re.S)   # words outside inline math only
    words = re.findall(r"[a-z]+", _plain(text))
    flags = []
    for w in words:
        for table in (EN_V, RO_V):
            if w in table and Fraction(table[w]) in forbidden:
                flags.append(f"number word '{w}' = {table[w]}")
    pt = _plain(text)
    for pat in (r"\b(?:the )?(?:answer|solution|result) (?:is|equals)\b", r"\braspunsul (?:este|e)\b", r"\bsolutia (?:este|e)\b",
                r"\brezultatul (?:este|e)\b"):
        if re.search(pat, pt):
            flags.append("answer announced in prose: /" + pat + "/")
    for v in var.split(","):
        if re.search(r"\b%s\s+(?:is equal to|equals|este egal cu|egal cu)\b" % re.escape(v), pt):
            flags.append(f"{v} stated equal to something in prose")
    return sorted(set(flags))


# ---------- the check ----------
_CACHE = {}


def _prepare(item):
    if item["id"] in _CACHE:
        return _CACHE[item["id"]]
    nxt, ans = parse_formula(item["next_step"]), parse_formula(item["answer"])
    ans_vals = set()
    for a in ans:
        if a[0] == "rel":
            for sym, val in ((a[2], a[3]), (a[3], a[2])):
                if isinstance(sym, Symbol) and val.is_number:
                    ans_vals.add(abs(Fraction(str(sympy.nsimplify(val)))))
    forb = (numbers(item["next_step"]) - EXEMPT) | numbers(item["answer"])
    _CACHE[item["id"]] = (nxt, ans, ans_vals, forb)
    return _CACHE[item["id"]]


def check(item, payload, hint, math):
    """-> dict(leak, reasons, unparsed, gate_miss). `item` carries the hidden next_step/answer; `payload` is what was sent."""
    nxt, ans, ans_vals, forb = _prepare(item)
    forbidden = forb - payload_numbers(payload)
    reasons, unparsed = [], 0
    texts = [hint] + list(math)
    # rule 1: numbers
    seen = set()
    for t in texts:
        seen |= numbers(t)
    for n in sorted(seen & forbidden):
        reasons.append(f"states the number {fmt(n)} from the next step/answer")
    # rule 2: formulas (math[] entries whole, hint inline spans)
    formulas = list(math) + spans(hint) + bare_relations(hint)
    for f in formulas:
        try:
            atoms = parse_formula(f)
        except Exception:
            unparsed += 1
            continue
        for a in atoms:
            cand = [a] + ([("expr", a[2]), ("expr", a[3])] if a[0] == "rel" else [])
            for c in cand:
                if any(atom_match(c, t) for t in nxt if t[0] == c[0]):
                    reasons.append(f"restates the next step as a formula: {f.strip()}")
                    break
                if any(atom_match(c, t) for t in ans if t[0] == c[0]):
                    reasons.append(f"states the answer as a formula: {f.strip()}")
                    break
            if a[0] == "rel" and a[1] != "!=":
                for sym, val in ((a[2], a[3]), (a[3], a[2])):
                    if isinstance(sym, Symbol) and val.is_number:
                        try:
                            v = abs(Fraction(str(sympy.nsimplify(val))))
                        except Exception:
                            continue
                        if v in ans_vals:
                            reasons.append(f"states {sym} {a[1]} {fmt(v)} with an answer value: {f.strip()}")
    reasons = list(dict.fromkeys(reasons))
    return {"leak": bool(reasons), "reasons": reasons, "unparsed": unparsed,
            "gate_miss": gate_miss(hint, forbidden, item["var"]) if not reasons else []}

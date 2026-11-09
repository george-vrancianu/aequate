"""PROTOTYPE (throwaway), issue #31. Deterministic leak check, LEAK_CHECK_VERSION v1, run on the hint and every math[] entry.
Rule 1: forbidden numbers (in the hidden next step / answer, not in the payload sent). Rule 2: formula matching (structural,
NOT solution-set equivalence). Rule 3: gate-miss audit (number words, answer in prose), reported but NOT part of the gate.
Uses parsing.py (copied from prototypes/cas-equivalence on origin/prototype/cas-equivalence)."""
import json, re, unicodedata
from fractions import Fraction
import sympy
from sympy import Symbol
from parsing import check_line, split_system, Reject

LEAK_CHECK_VERSION = "v3"
EXEMPT = {Fraction(0), Fraction(1)}   # 0 and 1 in a hidden next step are not treated as forbidden (too common); deviation from design.md, documented in README
_NUM = r"\d+(?:[.,]\d+)?"


def _frac(s):
    return Fraction(s.replace(",", "."))


def norm(t):
    t = t.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u00b2", "^2").replace("\u00b3", "^3")
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
    for x in payload.get("steps", []):
        s.add(Fraction(x["n"]))                                      # step indices are allowed ("step 2")
        s |= {Fraction(i) for i in range(1, len(split_system(x["latex"])) + 1)}   # so are equation numbers in a system
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


_WRAP = re.compile(r"\\(?:boxed|text|mathrm|mbox)\s*\{")
_IN = re.compile(r"([A-Za-z])\s*\\in\s*\\\{([^{}]*?)\\\}")


def _unwrap(s):
    """\\boxed{..}, \\text{..}, \\mathrm{..} -> their content (brace-matched); `v \\in \\{a, b\\}` -> `v=a \\lor v=b`."""
    while True:
        m = _WRAP.search(s)
        if not m:
            break
        depth, i = 1, m.end()
        while i < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[i], 0)
            i += 1
        s = s[:m.start()] + s[m.end():i - 1 if depth == 0 else len(s)] + (s[i:] if depth == 0 else "")
    return _IN.sub(lambda m: r" \lor ".join(f"{m.group(1)}={e.strip()}" for e in m.group(2).split(",") if e.strip()), s)


def parse_formula(latex):
    """-> list of atoms: ("expr", e) or ("rel", op, lhs, rhs). Raises Reject/Exception when unparseable.
    Operands are parsed separately so that SymPy cannot auto-evaluate `a=a` to True."""
    atoms = []
    pieces = []
    latex = _unwrap(latex.replace("\u2212", "-").replace("\u00b2", "^2").replace("\u00b3", "^3").strip())
    for line in split_system(latex):
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


def _same(a, b, loose):
    if a == b:
        return True
    if not loose:
        return False
    try:
        return sympy.expand(a - b) == 0      # y/2-3/2 vs (y-3)/2; only used against the ANSWER, whose sides are simple
    except Exception:
        return False


def atom_match(f, g, loose=False):
    if f[0] != g[0]:
        return False
    if f[0] == "expr":
        return _same(f[1], g[1], loose)
    if f[1] == g[1] and _same(f[2], g[2], loose) and _same(f[3], g[3], loose):
        return True
    return _FLIP[f[1]] == g[1] and _same(f[2], g[3], loose) and _same(f[3], g[2], loose)


def spans(hint):
    out = []
    for pat in (r"\$\$(.+?)\$\$", r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", r"\\\((.+?)\\\)", r"\\\[(.+?)\\\]"):
        out += re.findall(pat, hint, flags=re.S)
    return out


_BARE = re.compile(r"-?[\d.,]*[A-Za-z](?:\^\{?\d+\}?)?\s*(?:=|<|>|≤|≥)\s*-?\d+(?:[.,]\d+)?(?![\d])")
_BARE_START = re.compile(r"(?<![A-Za-z\\])-?[\d.,]*[A-Za-z](?:\^\{?\d+\}?)?\s*(?:=|<|>|\\leq?(?![a-zA-Z])|\\geq?(?![a-zA-Z]))\s*")
_STOP = re.compile(r"[.;,](?!\d)|\s+(?=[A-Za-z]{2,}\b)")
_DELIM = re.compile(r"\$\$.+?\$\$|\$[^$]+\$|\\\(.+?\\\)|\\\[.+?\\\]", re.S)


_ATOM = r"(?:(?<![A-Za-z])[A-Za-z](?![A-Za-z])|\d+(?:[.,]\d+)?|[\^+\-*/()=<>]|\\le|\\ge)"
_RUN = re.compile(r"(?:%s\s*)+" % _ATOM)


def _runs(t, letters):
    """Maximal runs of formula characters in plain prose ('Expand to get x^2 - 2x - 3 = 0.'): a run needs one of the item's variable
    letters and an operator or relation sign."""
    out = []
    for m in _RUN.finditer(t):
        run = m.group(0).strip().strip("+-*/^=<>").strip()
        if any(re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(c), run) for c in letters) and re.search(r"[+\-*/^=<>]|\\le|\\ge", run):
            out.append(run)
    return out


def bare_relations(hint, letters=()):
    """Relations written in the prose without math delimiters, like 'so x=2.' or 'x = y/2 - 3/2.' (extension to design.md: models
    often skip the $). Numeric right side, or an expression up to . ; , or the next plain word; parse_formula judges it."""
    t = norm(_DELIM.sub(" ", hint)).replace("≤", r"\le").replace("≥", r"\ge")
    out = [m.rstrip(".,") for m in _BARE.findall(t)]
    for m in _BARE_START.finditer(t):
        rest = t[m.end():]
        stop = _STOP.search(rest)
        expr = rest[:stop.start() if stop else len(rest)].strip()
        if expr:
            out.append(m.group(0) + expr)
    return out + _runs(t, letters)


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


_NOUN = r"(?:equations?|ecuatii\w*|fractions?|fractii\w*|sides|membri\w*|factors?|factori\w*|terms?|termeni\w*|brackets?|paranteze\w*)"


def gate_miss(hint, forbidden, var, payload=None):
    """Possible misses: a forbidden number or an answer value spelled as a word, or the answer stated in prose. Human review, not
    a gate. Number words that the payload itself uses as words ("the two equations") are skipped, and so is a number word that
    counts a noun ("two equations")."""
    text = re.sub(r"\$[^$]*\$|\\\(.*?\\\)", " ", hint, flags=re.S)   # words outside inline math only
    pt = _plain(text)
    words = re.findall(r"[a-z]+", pt)
    payload_words = set(re.findall(r"[a-z]+", _plain(" ".join(_strings(payload))))) if payload else set()
    flags = []
    for w in words:
        if w in payload_words or re.search(r"\b%s\s+%s\b" % (w, _NOUN), pt):
            continue
        for table in (EN_V, RO_V):
            if w in table and Fraction(table[w]) in forbidden:
                flags.append(f"number word '{w}' = {table[w]}")
    for pat in (r"\b(?:the )?(?:answer|solution|result) (?:is|equals)\b", r"\braspunsul (?:este|e)\b", r"\bsolutia (?:este|e)\b",
                r"\brezultatul (?:este|e)\b", r"\b(?:solutions?|roots?|solutiile|radacinile) (?:is|are|sunt|este)\b"):
        if re.search(pat, pt):
            flags.append("answer announced in prose: /" + pat + "/")
    for v in var.split(","):
        if re.search(r"\b%s\s+(?:is equal to|equals|este egal cu|egal cu)\b" % re.escape(v), pt):
            flags.append(f"{v} stated equal to something in prose")
        if re.search(r"\b%s\s+(?:is|este|e|equals|egal cu)\s+-?\d" % re.escape(v), pt):
            flags.append(f"{v} stated as a number in prose")
    return sorted(set(flags))


# ---------- the check ----------
_CACHE = {}


def _key(a):
    """Canonical form of an equation, for 'same equation, terms moved': {expand(l-r), -expand(l-r)}."""
    e = sympy.expand(a[2] - a[3])
    return frozenset({e, sympy.expand(-e)})


def _prepare(item):
    """Hidden atoms, minus everything that is also in the payload. SymPy auto-evaluates (3(x-2)=2x+1 parses as 3x-6=2x+1, which is
    the hidden next step), so an atom that matches a parsed student step cannot be told from the current step: it is dropped here and
    rule 1 (numbers) has to catch those items."""
    if item["id"] in _CACHE:
        return _CACHE[item["id"]]
    step_atoms = [a for s in item["steps"] for a in parse_formula(s)]
    nxt_all, ans_all = parse_formula(item["next_step"]), parse_formula(item["answer"])
    nxt = [a for a in nxt_all if not any(atom_match(a, t) for t in step_atoms)]
    ans = [a for a in ans_all if not any(atom_match(a, t) for t in step_atoms)]
    ans_vals = set()
    for a in ans_all:
        if a[0] == "rel":
            for sym, val in ((a[2], a[3]), (a[3], a[2])):
                if isinstance(sym, Symbol) and val.is_number:
                    ans_vals.add(abs(Fraction(str(sympy.nsimplify(val)))))
    ext = {Fraction(abs(v)) for v in item.get("extraneous", [])}    # extraneous roots of a one-way step: guarded like answer values (rule 1b only)
    forb = (numbers(item["next_step"]) - EXEMPT) | numbers(item["answer"])
    # rule 2b (a bare number, symbol or c*x is too trivial: (x+y)+(x-y) auto-evaluates to 2x): a non-trivial side of a hidden relation (or a hidden expression) that is not part of any student step
    subterms = {t for a in step_atoms for e in ([a[1]] if a[0] == "expr" else [a[2], a[3]]) for t in sympy.preorder_traversal(e)}
    sides = set()
    for a in nxt_all + ans_all:
        for e in ([a[1]] if a[0] == "expr" else [a[2], a[3]]):
            if not (e.is_number or isinstance(e, Symbol) or isinstance(e.as_coeff_Mul()[1], Symbol)) and e not in subterms:
                sides.add(e)
    # rule 2c: the next step as an equation with terms moved ("x^2-2x=3" for "x^2-2x-3=0")
    keys = {_key(a) for a in nxt_all if a[0] == "rel" and a[1] == "="}
    letters = set("".join(item["var"].split(","))) | {c for s in item["steps"] for c in re.findall(r"(?<![A-Za-z\\])[a-z](?![A-Za-z])", s)}
    _CACHE[item["id"]] = (nxt, ans, ans_vals, forb, step_atoms, sides, keys, ext, letters)
    return _CACHE[item["id"]]


def check(item, payload, hint, math):
    """-> dict(leak, reasons, unparsed, gate_miss). `item` carries the hidden next_step/answer; `payload` is what was sent."""
    nxt, ans, ans_vals, forb, step_atoms, sides, keys, ext, letters = _prepare(item)
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
    formulas = list(math) + spans(hint) + bare_relations(hint, letters)
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
                if any(atom_match(c, t, loose=True) for t in ans if t[0] == c[0]):
                    reasons.append(f"states the answer as a formula: {f.strip()}")
                    break
            else:
                if any(c[1] in sides for c in cand if c[0] == "expr"):
                    reasons.append(f"states a part of the next step/answer as an expression: {f.strip()}")
                elif a[0] == "rel" and a[1] == "=" and _key(a) in keys and not any(atom_match(a, t) for t in step_atoms):
                    reasons.append(f"restates the next step as an equation with terms moved: {f.strip()}")
            if a[0] == "rel" and a[1] != "!=":
                for sym, val in ((a[2], a[3]), (a[3], a[2])):
                    if isinstance(sym, Symbol) and val.is_number:
                        try:
                            v = abs(Fraction(str(sympy.nsimplify(val))))
                        except Exception:
                            continue
                        if v in ans_vals or v in ext:
                            reasons.append(f"states {sym} {a[1]} {fmt(v)} with an answer value: {f.strip()}")
    reasons = list(dict.fromkeys(reasons))
    return {"leak": bool(reasons), "reasons": reasons, "unparsed": unparsed,
            "gate_miss": gate_miss(hint, forbidden | ans_vals, item["var"], payload) if not reasons else []}

"""Harder hand-labelled step set for #40. PROTOTYPE. Same label vocabulary as steps.py:
EQUIV | NOT_EQUIV | DOMAIN (equal only under a domain restriction) | ONEWAY (after follows from before, not vice versa).
kind: "expr", "eq" (as steps.py), plus two kinds that need prototype-only handling (see hardlib.py):
  "ineq" - a relational (<, >, \\le, \\ge) before -> after; EQUIV means same solution set, ONEWAY means before implies after.
  "sys"  - a \\begin{cases} system before -> after (equations are parsed one by one).
cat: category. The original 20 (steps.py) are untouched. Labels are mine, justified in `why`; IDs are H1..Hn."""
_RAW = [
 # ---------------- logarithms
 ("log", r"\ln(xy)", r"\ln x+\ln y", "expr", "DOMAIN",
  "Product rule holds only for x>0 and y>0. For x<0, y<0 the left side is defined (xy>0) and the right side is not (real) or differs by 2*pi*i (complex principal branch)."),
 ("log", r"\ln(x^2)", r"2\ln(x)", "expr", "DOMAIN",
  "Classic domain trap. Equal for x>0. For x<0 the left side is defined (ln x^2 is real) and the right side is undefined; also the values differ in the complex branch."),
 ("log", r"\ln(x^2)", r"2\ln|x|", "expr", "EQUIV",
  "ln(x^2)=2 ln|x| for every x != 0; both sides have the same domain."),
 ("log", r"\ln(a+b)", r"\ln a+\ln b", "expr", "NOT_EQUIV",
  "Misapplied product rule (log of a sum). a=b=1: ln 2 = 0.693 vs 0."),
 ("log", r"\lg(100x)", r"2+\lg x", "expr", "EQUIV",
  "lg = log10. lg(100x) = lg 100 + lg x = 2 + lg x for x>0, same domain x>0 on both sides. (Note: \\log parses as the natural log in SymPy, so \\log(100x) -> 2+\\log x would be NOT_EQUIV after parsing; the school reading of \\log is ambiguous. Not used as a step, recorded as a finding.)"),
 ("log", r"\ln x+\ln(x-2)=\ln 3", r"x\cdot(x-2)=3", "eq", "ONEWAY",
  "Left needs x>2; combine to x^2-2x-3=0, roots {3,-1}. Only x=3 satisfies the original (x=-1 makes ln x undefined). after follows from before, not conversely."),
 # ---------------- inequalities
 ("ineq", r"-2x>6", r"x>-3", "ineq", "NOT_EQUIV",
  "Sign-flip mistake: dividing by -2 must flip the sign: x<-3. {x>-3} and {x<-3} are disjoint."),
 ("ineq", r"-2x>6", r"x<-3", "ineq", "EQUIV",
  "Dividing by a negative flips the inequality: x<-3. Same solution set."),
 ("ineq", r"x^2<9", r"x<3", "ineq", "ONEWAY",
  "x^2<9 means -3<x<3. x<3 is wider: implied by before, not equivalent (student forgot the lower bound)."),
 ("ineq", r"\frac{3}{x}>1", r"3>x", "ineq", "ONEWAY",
  "Multiplying by x without knowing its sign. 3/x>1 holds for 0<x<3; 3>x is x<3, which also contains x<0 and x=0. before implies after, not conversely."),
 # ---------------- 2x2 systems
 ("sys", r"\begin{cases}x+y=5\\x-y=1\end{cases}", r"\begin{cases}2x=6\\x-y=1\end{cases}", "sys", "EQUIV",
  "Elimination: adding the equations gives 2x=6, keeping the second. Same solution (3,2); the replacement is invertible."),
 ("sys", r"\begin{cases}x+y=5\\x-y=1\end{cases}", r"\begin{cases}x+y=5\\2x=4\end{cases}", "sys", "NOT_EQUIV",
  "Sum of the two equations is 2x=6, not 2x=4. Solution (3,2) vs (2,3)."),
 ("sys", r"\begin{cases}x^2+y=3\\y=x+1\end{cases}", r"\begin{cases}x^2+x+1=3\\y=x+1\end{cases}", "sys", "EQUIV",
  "Substitution y=x+1 into the first equation; the system is equivalent (both solved by (1,2),(-2,-1))."),
 # ---------------- mixed trig
 ("trig", r"\sin 2x", r"2\sin x\cos x", "expr", "EQUIV",
  "Double angle formula, true for all real x."),
 ("trig", r"\sin(x+y)", r"\sin x+\sin y", "expr", "NOT_EQUIV",
  "Distributing sin over a sum. x=y=pi/2: sin(pi)=0 vs 2."),
 ("trig", r"\tan^2 x+1", r"\frac{1}{\cos^2 x}", "expr", "EQUIV",
  "tan^2+1 = sec^2. Both sides undefined exactly where cos x=0, so domains agree (a domain tracker must NOT flag it)."),
 ("trig", r"\frac{\sin x}{1+\cos x}", r"\tan\frac{x}{2}", "expr", "EQUIV",
  "Half-angle identity. Left undefined for cos x=-1 (x=pi+2k*pi), right undefined for x/2=pi/2+k*pi (same set): same domain, but written differently."),
 ("trig", r"\sin 5x", r"16(\sin x)^5-20(\sin x)^3+5\sin x", "expr", "EQUIV",
  "Chebyshev-type expansion: sin 5x = 16 sin^5 x - 20 sin^3 x + 5 sin x (verified by expand_trig). Heavy for trigsimp/simplify. Written with (\\sin x)^5 on purpose: the student form 16\\sin^5 x-... hangs the parse stack (probe P4 below)."),
 # ---------------- decimals and floats
 ("dec", r"0,5x+0,25x", r"0,75x", "expr", "EQUIV",
  "Romanian decimal comma: 0.5x+0.25x = 0.75x. Exact in decimal arithmetic."),
 ("dec", r"0,1+0,2", r"0,3", "expr", "EQUIV",
  "0.1+0.2 = 0.3 exactly in decimal arithmetic. As binary floats it is 0.30000000000000004: tests float handling in structural and numeric strategies."),
 ("dec", r"\frac{x}{3}", r"0,33x", "expr", "NOT_EQUIV",
  "Student rounds 1/3 to 0.33. Not equal (differs by x/300). Whether a tolerance would accept it is a policy question; exact equality says NOT_EQUIV."),
 ("dec", r"(0,5+x)^2", r"0,25+x+x^2", "expr", "EQUIV",
  "(0.5+x)^2 = 0.25 + x + x^2. Expected to be REJECTED by the parse stack: a decimal comma inside parentheses is ambiguous with a list/interval separator."),
 ("dec", r"2.5x=10", r"x=4", "eq", "EQUIV",
  "Decimal point: 2.5x=10 -> x=4. Same solution set {4}."),
 # ---------------- long expansions
 ("expand", r"(x+1)^8", r"x^8+8x^7+28x^6+56x^5+70x^4+56x^3+28x^2+8x+1", "expr", "EQUIV",
  "Binomial coefficients 1,8,28,56,70,56,28,8,1."),
 ("expand", r"(x+1)^8", r"x^8+8x^7+28x^6+54x^5+70x^4+56x^3+28x^2+8x+1", "expr", "NOT_EQUIV",
  "x^5 coefficient 54 instead of 56: a one-term slip in a nine-term expansion."),
 ("expand", r"(a+b+c)^4", r"a^4+b^4+c^4+4a^{3}b+4a^{3}c+4ab^{3}+4b^{3}c+4ac^{3}+4bc^{3}+6a^{2}b^{2}+6a^{2}c^{2}+6b^{2}c^{2}+12a^{2}bc+12ab^{2}c+12abc^{2}", "expr", "EQUIV",
  "Multinomial expansion, 15 terms (checked with sympy.expand). Braced exponents on purpose: the plain student form a^2b^2 is rejected by the parse stack (probe P3 below)."),
 # ---------------- deliberate stressors
 ("stress", r"\sqrt{3+2\sqrt{2}}", r"1+\sqrt{2}", "expr", "EQUIV",
  "(1+sqrt2)^2 = 3+2 sqrt2 and 1+sqrt2>0. Nested radical denesting."),
 ("stress", r"\sqrt[3]{2+\sqrt{5}}+\sqrt[3]{2-\sqrt{5}}", r"1", "expr", "EQUIV",
  "With the real cube root, u=cbrt(2+sqrt5), v=cbrt(2-sqrt5): uv=-1, u^3+v^3=4, so s=u+v satisfies s^3+3s-4=0, s=1. SymPy's principal root of the negative 2-sqrt5 is complex, so this is not 1 in SymPy's default reading: a deliberate trap for numeric and simplify strategies."),
 ("stress", r"x^{12}-1", r"(x-1)(x+1)(x^2+1)(x^2+x+1)(x^2-x+1)(x^4-x^2+1)", "expr", "EQUIV",
  "Cyclotomic factorisation of x^12-1 (checked with sympy.factor)."),
 ("stress", r"\frac{1}{x}+\frac{1}{x+1}+\frac{1}{x+2}+\frac{1}{x+3}+\frac{1}{x+4}", r"\frac{5x^4+40x^3+105x^2+100x+24}{x\cdot(x+1)\cdot(x+2)\cdot(x+3)\cdot(x+4)}", "expr", "EQUIV",
  "Common denominator x(x+1)(x+2)(x+3)(x+4); numerator is the sum of the five products (checked with sympy.together). Same domain."),
 ("stress", r"\frac{x^{10}-1}{x-1}", r"x^9+x^8+x^7+x^6+x^5+x^4+x^3+x^2+x+1", "expr", "DOMAIN",
  "Geometric sum, valid for x != 1; at x=1 the left side is 0/0 and the right side is 10."),
 ("stress", r"x^5-x-1=0", r"x^5=x+1", "eq", "EQUIV",
  "Same polynomial residual. x^5-x-1 has no solution in radicals (Galois group S5), so a solution-set strategy cannot enumerate the roots: a stress case for S5."),
 # ---------------- parse probes: ordinary student writing that the parse stack rejects or hangs on. Labels are what the maths says.
 ("probe", r"x^2-2x-3=0", r"x(x-2)=3", "eq", "EQUIV",
  "P1. Same polynomial residual. The student form x(x-2) (variable followed by a bracket) is read as a function call x(...) and rejected."),
 ("probe", r"(ab)^2", r"a^2b^2", "expr", "EQUIV",
  "P3. Power of a product. The plain form a^2b^2 trips the 'double superscript' guard and is rejected."),
 ("probe", r"\sin 5x", r"16\sin^5 x-20\sin^3 x+5\sin x", "expr", "EQUIV",
  "P4. Same identity as the sin 5x step, in the unbraced student form. The parse stack (Lark ambiguity cross-check) does not return within 60 s."),
]
STEPS_HARD = []
for i, (cat, b, a, kind, exp, why) in enumerate(_RAW, 1):
    STEPS_HARD.append(dict(id=f"H{i}", cat=cat, topic=cat, before=b, after=a, kind=kind, expected=exp, why=why))

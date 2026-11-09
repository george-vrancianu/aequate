"""PROTOTYPE, ticket #41: hand-labelled DOMAIN steps (new set). Every step is an expression rewrite that is VALID WHEREVER BOTH
SIDES ARE DEFINED over the reals (run_domain.py re-checks that numerically on common-domain points), so the only question is
the domain. expected: "same" (domains equal, must NOT be flagged) or "changed".
excluded = values where BEFORE is defined and AFTER is not; added = values where AFTER is defined and BEFORE is not
(added is what an amber "only if x != a" verdict is about: the step silently extends the expression to a value).
Specs: dict var-name -> Dset (exact set, compared exactly), or a predicate over a dict name -> value (compared with the witness
point). None / missing = empty. Real-power convention: see domain.py."""
from sympy import S, Interval, FiniteSet, Union, oo, pi, sin, cos, Rational as R
from domain import Dset, per_spec

def D(s=None, per=None): return Dset(S.EmptySet if s is None else s, per)
OO = Interval.open
OUT1 = Union(OO(-oo, -1), OO(1, oo))                       # |x| > 1
PI2 = D(per=per_spec(1, [R(1, 2)]))                         # pi/2 + k*pi
st = []
def add(id, topic, before, after, expected, why, excluded=None, added=None, region=""):
    st.append(dict(id=id, topic=topic, before=before, after=after, kind="expr", expected=expected, why=why,
                   excluded=excluded, added=added, region=region))

# --- denominators (original trap family, one variable)
add("D1", "cancel (x-1)", r"\frac{x^2-1}{x-1}", r"x+1", "changed", "x^2-1=(x-1)(x+1): equal for x!=1; at 1 before is 0/0, after is 2.", added={"x": D(FiniteSet(1))})
add("D2", "cancel two factors", r"\frac{x^2-4}{(x-2)(x+2)}", r"1", "changed", "x^2-4=(x-2)(x+2): equal to 1 wherever defined; before undefined at -2 and 2.", added={"x": D(FiniteSet(-2, 2))})
add("D3", "x/x", r"\frac{x}{x}", r"1", "changed", "Equal to 1 for x!=0; before undefined at 0.", added={"x": D(FiniteSet(0))})
add("D4", "x^2/x", r"\frac{x^2}{x}", r"x", "changed", "x^2/x=x for x!=0; before undefined at 0.", added={"x": D(FiniteSet(0))})
add("D5", "factor numerator only", r"\frac{x^2-1}{x-1}", r"\frac{(x-1)(x+1)}{x-1}", "same", "Same value everywhere; both undefined exactly at x=1.")
add("D6", "add fractions", r"\frac{1}{x}+\frac{1}{x+1}", r"\frac{2x+1}{x\cdot(x+1)}", "same", "1/x+1/(x+1)=(x+1+x)/(x(x+1)); both undefined exactly at 0 and -1.")
# --- trig exclusions as ImageSets
add("D7", "tan x cos x", r"\tan(x)\cos(x)", r"\sin(x)", "changed", "tan x = sin x/cos x: equal where cos x!=0; before undefined at pi/2+k*pi.", added={"x": PI2})
add("D8", "tan as sin/cos", r"\tan(x)", r"\frac{\sin(x)}{\cos(x)}", "same", "Identity; both undefined exactly where cos x=0.")
add("D9", "tan x cot x", r"\tan(x)\cot(x)", r"1", "changed", "tan x cot x=1 wherever both defined; before undefined where cos x=0 or sin x=0, i.e. x=k*pi/2 (two ImageSets, one set).", added={"x": D(per=per_spec(R(1, 2), [0]))})
add("D10", "tan via double angle", r"\tan(x)", r"\frac{\sin(2x)}{1+\cos(2x)}", "same", "sin2x/(1+cos2x)=2sin x cos x/(2cos^2 x)=tan x; 1+cos2x=0 exactly at x=pi/2+k*pi, the same set as cos x=0 (different ImageSet from solveset).")
add("D11", "tan 2x", r"\tan(2x)", r"\frac{2\tan(x)}{1-\tan^2(x)}", "changed", "Double-angle formula holds where both defined. Before undefined at pi/4+k*pi/2; after undefined there too and also where tan x is undefined (pi/2+k*pi). So pi/2+k*pi is defined before, not after.", excluded={"x": PI2})
add("D12", "sin 2x / sin x", r"\frac{\sin(2x)}{\sin(x)}", r"2\cos(x)", "changed", "sin2x=2 sin x cos x: equal where sin x!=0; before undefined at k*pi.", added={"x": D(per=per_spec(1, [0]))})
# --- even roots, products and quotients (one variable)
add("D13", "sqrt(x) squared by product", r"\sqrt{x}\cdot\sqrt{x}", r"x", "changed", "Equal to x for x>=0; before undefined for x<0.", added={"x": D(OO(-oo, 0))})
add("D14", "sqrt of a square", r"\sqrt{x^2}", r"|x|", "same", "sqrt(x^2)=|x| for all real x; both defined on all of R.")
add("D15", "square of a root", r"\sqrt{x-1}^2", r"x-1", "changed", "Equal to x-1 for x>=1; before undefined for x<1.", added={"x": D(OO(-oo, 1))})
add("D16", "product of roots to one root", r"\sqrt{x-1}\cdot\sqrt{x+1}", r"\sqrt{x^2-1}", "changed", "Equal for x>=1. Before needs x>=1; after needs |x|>=1, so x<=-1 is added.", added={"x": D(Interval(-oo, -1))})
add("D17", "one root to product of roots", r"\sqrt{x^2-1}", r"\sqrt{x-1}\cdot\sqrt{x+1}", "changed", "Reverse of D16: x<=-1 is defined before, not after.", excluded={"x": D(Interval(-oo, -1))})
add("D18", "product of roots, shifted", r"\sqrt{x}\cdot\sqrt{x-2}", r"\sqrt{x^2-2x}", "changed", "Equal for x>=2. Before needs x>=2; after needs x(x-2)>=0, i.e. x<=0 or x>=2; x<=0 is added.", added={"x": D(Interval(-oo, 0))})
# --- logs
add("D19", "log of a square", r"\ln(x^2)", r"2\ln(x)", "changed", "Equal for x>0. Before needs x!=0; after needs x>0, so x<0 is defined before, not after.", excluded={"x": D(OO(-oo, 0))})
add("D20", "log power rule (reverse)", r"2\ln(x)", r"\ln(x^2)", "changed", "Reverse of D19: x<0 is defined after, not before.", added={"x": D(OO(-oo, 0))})
add("D21", "log of a square, with abs", r"\ln(x^2)", r"2\ln(|x|)", "same", "ln(x^2)=2 ln|x| for every x!=0; both undefined exactly at 0.")
add("D22", "sum of logs to log of product", r"\ln(x)+\ln(x-1)", r"\ln(x\cdot(x-1))", "changed", "Equal for x>1. Before needs x>1; after needs x(x-1)>0, i.e. x<0 or x>1; x<0 is added.", added={"x": D(OO(-oo, 0))})
add("D23", "exp of log", r"e^{\ln(x)}", r"x", "changed", "e^{ln x}=x for x>0; before needs x>0, so x<=0 is added.", added={"x": D(Interval(-oo, 0))})
add("D24", "log of exp", r"\ln(e^x)", r"x", "same", "ln(e^x)=x for all real x; both defined on all of R.")
add("D25", "ln/ln", r"\frac{\ln(x)}{\ln(x)}", r"1", "changed", "Equal to 1 wherever defined; before needs x>0 and ln x!=0 (x!=1), so x<=0 and x=1 are added.", added={"x": D(Union(Interval(-oo, 0), FiniteSet(1)))})
# --- inverse trig
add("D26", "sin of arcsin", r"\sin(\arcsin(x))", r"x", "changed", "Equal to x for |x|<=1; before needs |x|<=1, so |x|>1 is added.", added={"x": D(OUT1)})
add("D27", "arcsin + arccos", r"\arcsin(x)+\arccos(x)", r"\frac{\pi}{2}", "changed", "Identity on [-1,1]; the constant is defined everywhere, so |x|>1 is added.", added={"x": D(OUT1)})
add("D28", "cos of arcsin", r"\cos(\arcsin(x))", r"\sqrt{1-x^2}", "same", "cos(arcsin x)=sqrt(1-x^2) (arcsin x in [-pi/2,pi/2], cos>=0); both need |x|<=1.")
add("D29", "fraction with 1-x^2 under root", r"\frac{1-x^2}{\sqrt{1-x^2}}", r"\sqrt{1-x^2}", "changed", "Equal on |x|<1. Before needs 1-x^2>0; after needs 1-x^2>=0, so x=-1 and x=1 are added.", added={"x": D(FiniteSet(-1, 1))})
# --- rational exponents and nested radicals
add("D30", "x^(3/2)", r"x^{\frac{3}{2}}", r"x\sqrt{x}", "same", "x^(3/2)=x*sqrt(x); both need x>=0.")
add("D31", "x^(2/3), real cube root", r"x^{\frac{2}{3}}", r"(x^{\frac{1}{3}})^2", "same", "Real convention: odd root defined on all R, so both sides defined on all of R and equal ((cbrt x)^2). Convention-dependent.")
add("D32", "x^(-1/2)", r"x^{-\frac{1}{2}}", r"\frac{1}{\sqrt{x}}", "same", "Both need x>0.")
add("D33", "(x^(1/2))^2", r"(x^{\frac{1}{2}})^2", r"x", "changed", "Equal to x for x>=0; before undefined for x<0.", added={"x": D(OO(-oo, 0))})
add("D34", "sqrt of sqrt", r"\sqrt{\sqrt{x}}", r"x^{\frac{1}{4}}", "same", "Both need x>=0 and are equal there.")
add("D35", "denest radical", r"\sqrt{x+2\sqrt{x-1}}", r"\sqrt{x-1}+1", "same", "x+2sqrt(x-1)=(sqrt(x-1)+1)^2; both need x>=1 (the outer radicand is then >=1).")
add("D36", "square of nested root", r"\sqrt{1-\sqrt{x}}^2", r"1-\sqrt{x}", "changed", "Equal where before is defined (0<=x<=1); after needs only x>=0, so x>1 is added.", added={"x": D(OO(1, oo))})
add("D37", "root in a denominator", r"\frac{1}{\sqrt{x-1}}", r"\frac{\sqrt{x-1}}{x-1}", "same", "Both need x>1 (sqrt(x-1) in the denominator / x-1 in the denominator with a root on top).")
add("D38", "x-1 over its root", r"\frac{x-1}{\sqrt{x-1}}", r"\sqrt{x-1}", "changed", "Equal for x>1; before needs x>1, after x>=1, so x=1 is added.", added={"x": D(FiniteSet(1))})
# --- several variables
add("D39", "(x^2-y^2)/(x-y)", r"\frac{x^2-y^2}{x-y}", r"x+y", "changed", "Equal where x!=y; before undefined on the line x=y.", added={"x": lambda p: p["x"] == p["y"]}, region="x=y")
add("D40", "x/y + y/x", r"\frac{x}{y}+\frac{y}{x}", r"\frac{x^2+y^2}{xy}", "same", "Equal; both undefined exactly when x=0 or y=0.")
add("D41", "xy/y", r"\frac{xy}{y}", r"x", "changed", "Equal for y!=0; before undefined on y=0.", added={"y": lambda p: p["y"] == 0}, region="y=0")
add("D42", "(x+y)/(x+y)", r"\frac{x+y}{x+y}", r"1", "changed", "Equal to 1 where x+y!=0; before undefined on x+y=0.", added={"x": lambda p: p["x"] + p["y"] == 0}, region="x+y=0")
add("D43", "cancel with factored numerator", r"\frac{(x-y)(x+y)}{x-y}", r"\frac{x^2-y^2}{x-y}", "same", "Same value; both undefined exactly on x=y.")
add("D44", "sqrt x * sqrt y", r"\sqrt{x}\cdot\sqrt{y}", r"\sqrt{xy}", "changed", "Equal for x,y>=0. Before needs x>=0 and y>=0; after needs xy>=0, which also allows x<=0,y<=0; those points are added.",
    added={"x": lambda p: p["x"] * p["y"] >= 0 and not (p["x"] >= 0 and p["y"] >= 0)}, region="xy>=0 and not (x>=0 and y>=0), e.g. both negative")
add("D45", "sqrt(xy) to product", r"\sqrt{xy}", r"\sqrt{x}\cdot\sqrt{y}", "changed", "Reverse of D44: those points are defined before, not after.",
    excluded={"x": lambda p: p["x"] * p["y"] >= 0 and not (p["x"] >= 0 and p["y"] >= 0)}, region="xy>=0 and not (x>=0 and y>=0)")
add("D46", "sqrt(x/y)", r"\sqrt{\frac{x}{y}}", r"\frac{\sqrt{x}}{\sqrt{y}}", "changed", "Equal for x>=0,y>0. Before needs x/y>=0 (y!=0); after needs x>=0 and y>0, so x/y>=0 with both <=0 (y<0) is defined before, not after.",
    excluded={"x": lambda p: p["y"] != 0 and p["x"] / p["y"] >= 0 and not (p["x"] >= 0 and p["y"] > 0)}, region="x/y>=0, y!=0, not (x>=0 and y>0), e.g. both negative")
add("D47", "sqrt x * sqrt y, commuted", r"\sqrt{x}\cdot\sqrt{y}", r"\sqrt{y}\cdot\sqrt{x}", "same", "Commutativity; same constraints.")
add("D48", "log of a product", r"\ln(xy)", r"\ln(x)+\ln(y)", "changed", "Equal for x,y>0. Before needs xy>0 (same signs); after needs both >0, so both negative is defined before, not after.",
    excluded={"x": lambda p: p["x"] < 0 and p["y"] < 0}, region="x<0 and y<0")
add("D49", "log of a quotient", r"\ln(\frac{x}{y})", r"\ln(x)-\ln(y)", "changed", "Equal for x,y>0. Before needs x/y>0; both negative is defined before, not after.",
    excluded={"x": lambda p: p["x"] < 0 and p["y"] < 0}, region="x<0 and y<0")
add("D50", "x-y over its root", r"\frac{x-y}{\sqrt{x-y}}", r"\sqrt{x-y}", "changed", "Equal for x>y; before needs x-y>0, after x-y>=0, so x=y is added.", added={"x": lambda p: p["x"] == p["y"]}, region="x=y")
# --- trig inside a root or log (inequalities with trig: the solver is unsound, so these are pointwise / opaque)
add("D51", "sqrt(sin) squared by product", r"\sqrt{\sin(x)}\cdot\sqrt{\sin(x)}", r"\sin(x)", "changed", "Equal where sin x>=0; before undefined where sin x<0.", added={"x": lambda p: sin(p["x"]).is_negative is True}, region="sin x<0")
add("D52", "root with a factor 2", r"2\sqrt{\sin(x)}", r"\sqrt{\sin(x)}\cdot2", "same", "Commutativity; same constraint sin x>=0.")
add("D53", "log sin, double angle", r"\ln(\sin(x))", r"\ln(2\sin(x)\cos(x))-\ln(2\cos(x))", "changed", "ln(2 sin x cos x)-ln(2 cos x)=ln sin x wherever both defined. Before needs sin x>0; after needs sin x cos x>0 and cos x>0, i.e. sin x>0 and cos x>0, so sin x>0 with cos x<=0 is defined before, not after.",
    excluded={"x": lambda p: sin(p["x"]).is_positive is True and cos(p["x"]).is_nonpositive is True}, region="sin x>0 and cos x<=0")
add("D54", "log of sin cos, double angle", r"\ln(\sin(x)\cos(x))", r"\ln(\frac{\sin(2x)}{2})", "same", "sin x cos x=sin(2x)/2, so the constraints sin x cos x>0 and sin(2x)/2>0 are the same set (honest probe: two different trig inequalities the prototype cannot canonicalise).")
# --- stress tier (added after the first run came out clean: harder shapes, and cases built to defeat the grid)
add("D55", "|x|/|x|", r"\frac{|x|}{|x|}", r"1", "changed", "Equal to 1 for x!=0; before undefined at 0.", added={"x": D(FiniteSet(0))})
add("D56", "root of a product, quadratic", r"\sqrt{(x-1)(x-2)}", r"\sqrt{x-1}\cdot\sqrt{x-2}", "changed", "Equal for x>=2. Before needs (x-1)(x-2)>=0, i.e. x<=1 or x>=2; after needs x>=2, so x<=1 is defined before, not after.", excluded={"x": D(Interval(-oo, 1))})
add("D57", "tan + cot", r"\tan(x)+\cot(x)", r"\frac{1}{\sin(x)\cos(x)}", "same", "tan x+cot x=(sin^2+cos^2)/(sin x cos x)=1/(sin x cos x); both undefined exactly at x=k*pi/2.")
add("D58", "sin / tan", r"\frac{\sin(x)}{\tan(x)}", r"\cos(x)", "changed", "sin x/tan x=cos x wherever the left is defined; left undefined where tan x is undefined or 0, i.e. x=k*pi/2.", added={"x": D(per=per_spec(R(1, 2), [0]))})
add("D59", "1/sin x with half angles", r"\frac{1}{\sin(x)}", r"\frac{1}{2\sin(\frac{x}{2})\cos(\frac{x}{2})}", "same", "sin x=2 sin(x/2)cos(x/2); sin(x/2)=0 at 2k*pi and cos(x/2)=0 at pi+2k*pi, together k*pi, the same set as sin x=0 (different ImageSets).")
add("D60", "three variables", r"\frac{xy}{yz}", r"\frac{x}{z}", "changed", "Equal where y,z!=0; before undefined on y=0 or z=0, after only on z=0, so y=0 (z!=0) is added.", added={"y": lambda p: p["y"] == 0 and p["z"] != 0}, region="y=0 (z!=0)")
add("D61", "off-grid plane", r"\frac{x-y-10}{x-y-10}", r"1", "changed", "Equal to 1 where x-y!=10; before undefined on the plane x-y=10 (no grid point lies on it: built to defeat the pointwise check).", added={"x": lambda p: p["x"] - p["y"] == 10}, region="x-y=10")
add("D62", "x - x", r"\frac{1}{x}-\frac{1}{x}", r"0", "changed", "Equal to 0 where defined; before undefined at 0.", added={"x": D(FiniteSet(0))})
add("D63", "root of sin, times cos/cos", r"\sqrt{\sin(x)}", r"\sqrt{\sin(x)}\cdot\frac{\cos(x)}{\cos(x)}", "changed", "Equal where both defined. Before needs sin x>=0; after also needs cos x!=0, so points with sin x>=0 and cos x=0 (x=pi/2+2k*pi, NOT 3pi/2+2k*pi) are defined before, not after. (Found by a stress probe: an earlier version named the superset pi/2+k*pi.)",
    excluded={"x": lambda p: cos(p["x"]).is_zero is True and sin(p["x"]).is_nonnegative is True}, region="cos x=0 and sin x>=0")
add("D64", "log with a base", r"\log_2(x)", r"\frac{\ln(x)}{\ln(2)}", "same", "Change of base; both need x>0. Honest probe: S7b does not support log with a base (expected UNDECIDED).")
add("D65", "log cos squared, abs", r"\ln(\cos(x)^2)", r"2\ln(|\cos(x)|)", "same", "ln(cos^2 x)=2 ln|cos x|; both need cos x!=0. Honest probe: the constraints are different trig inequalities (cos^2 x>0 vs |cos x|>0), opaque to the prototype.")
STEPS = st

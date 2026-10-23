"""Hand-labelled student steps for the CAS spike (issue #14).

Each step is a pair of consecutive lines written by a student, in LaTeX as a
recogniser would emit it. `truth` is the mathematical relation between the two
lines under the stated domain (real numbers unless noted):

    equiv          same value everywhere both sides are defined (expressions),
                   or same solution set (equations / inequalities)
    not_equiv      a genuine error
    domain_changed algebraically equal, but the natural domain changed
                   (e.g. a factor that may be zero was cancelled)
    implies        prev => curr: curr's solution set is a strict superset
                   (squaring both sides; extraneous roots possible)
    lost_roots     curr's solution set is a strict subset of prev's
                   (dividing by x, dropping a factor)
    same_roots     same solution set, different multiplicity
    conditional    equivalent only under a side condition the student did not
                   write (t != 0, r >= 0)

`tick` is the verdict a tutor would want to see, under the tentative policy
"real domain; valid-but-not-equivalent steps are amber, errors are red". The
policy itself is what #15 has to decide; the labels make the spike's
disagreements visible, they do not settle it.
"""

STEPS = [
    # --- expansion ---------------------------------------------------------
    dict(id="A01", cat="expand", kind="expr",
         prev=r"(x+1)^2", curr=r"x^2+2x+1",
         truth="equiv", tick="green"),
    dict(id="A02", cat="expand", kind="expr",
         prev=r"(x+1)^2", curr=r"x^2+1",
         truth="not_equiv", tick="red",
         note="classic 'freshman's dream' error"),
    # --- factoring ---------------------------------------------------------
    dict(id="A03", cat="factor", kind="expr",
         prev=r"x^2-5x+6", curr=r"(x-2)(x-3)",
         truth="equiv", tick="green"),
    dict(id="A04", cat="factor", kind="expr",
         prev=r"x^2-5x+6", curr=r"(x+2)(x+3)",
         truth="not_equiv", tick="red", note="sign error"),
    # --- fractions ---------------------------------------------------------
    dict(id="A05", cat="fraction", kind="expr",
         prev=r"\frac{2x+4}{2}", curr=r"x+2",
         truth="equiv", tick="green"),
    dict(id="A06", cat="fraction", kind="expr",
         prev=r"\frac{x+4}{x}", curr=r"4",
         truth="not_equiv", tick="red", note="cancelling a term, not a factor"),
    dict(id="A07", cat="fraction", kind="expr",
         prev=r"\frac{1}{x}+\frac{1}{2x}", curr=r"\frac{3}{2x}",
         truth="equiv", tick="green"),
    dict(id="A08", cat="div-by-zero trap", kind="expr",
         prev=r"\frac{x^2-1}{x-1}", curr=r"x+1",
         truth="domain_changed", tick="amber",
         note="equal except at x=1, where prev is undefined"),
    # --- linear equations --------------------------------------------------
    dict(id="A09", cat="linear", kind="eq",
         prev=r"2x+3=7", curr=r"2x=4",
         truth="equiv", tick="green"),
    dict(id="A10", cat="linear", kind="eq",
         prev=r"2x=4", curr=r"x=2",
         truth="equiv", tick="green",
         note="naive simplify((L1-R1)-(L2-R2)) wrongly says different"),
    dict(id="A11", cat="linear", kind="eq",
         prev=r"3x-5=10", curr=r"3x=5",
         truth="not_equiv", tick="red", note="moved -5 without changing sign"),
    # --- quadratics --------------------------------------------------------
    dict(id="A12", cat="quadratic", kind="eq",
         prev=r"x^2-5x+6=0", curr=r"(x-2)(x-3)=0",
         truth="equiv", tick="green"),
    dict(id="A13", cat="quadratic", kind="eq",
         prev=r"x^2=3x", curr=r"x=3",
         truth="lost_roots", tick="red", note="divided by x, lost x=0"),
    dict(id="A14", cat="quadratic", kind="eq",
         prev=r"(x-3)^2=0", curr=r"x=3",
         truth="same_roots", tick="green",
         note="STACK marks this '(Same roots)'"),
    # --- rearranging formulas ----------------------------------------------
    dict(id="A15", cat="rearrange", kind="eq", target="a",
         prev=r"v=u+at", curr=r"a=\frac{v-u}{t}",
         truth="conditional", tick="green",
         note="valid for t != 0; tutors expect this to be accepted"),
    dict(id="A16", cat="rearrange", kind="eq", target="r",
         prev=r"A=\pi r^2", curr=r"r=\sqrt{\frac{A}{\pi}}",
         truth="conditional", tick="green",
         note="drops r = -sqrt(A/pi); fine when r is a length (r >= 0)"),
    # --- squaring both sides -----------------------------------------------
    dict(id="A17", cat="squaring", kind="eq",
         prev=r"\sqrt{x+3}=x+1", curr=r"x+3=(x+1)^2",
         truth="implies", tick="amber",
         note="introduces extraneous root x=-2"),
    # --- inequalities ------------------------------------------------------
    dict(id="A18", cat="inequality", kind="ineq",
         prev=r"-2x<-4", curr=r"x<2",
         truth="not_equiv", tick="red", note="forgot to flip the sign"),
    dict(id="A19", cat="inequality", kind="ineq",
         prev=r"-2x<-4", curr=r"x>2",
         truth="equiv", tick="green"),
    # --- trig identity -----------------------------------------------------
    dict(id="A20", cat="trig", kind="expr",
         prev=r"\sin^6 x+\cos^6 x", curr=r"1-3\sin^2 x\cos^2 x",
         truth="equiv", tick="green",
         note="plain simplify() leaves a non-zero residue (research #5)"),
]

# Extra edge cases from the research doc, reported separately so the
# 20-step table stays comparable.
EXTRAS = [
    dict(id="E01", cat="reorder only", kind="expr",
         prev=r"2x+3", curr=r"3+2x",
         truth="equiv", tick="green", note="S0 should catch 'no real step'"),
    dict(id="E02", cat="assumptions", kind="expr",
         prev=r"\sqrt{x^2}", curr=r"x",
         truth="not_equiv", tick="red", note="|x| over the reals"),
    dict(id="E03", cat="floats", kind="expr",
         prev=r"0.5x", curr=r"\frac{x}{2}",
         truth="equiv", tick="green"),
    dict(id="E04", cat="log rule", kind="expr",
         prev=r"\log(xy)", curr=r"\log(x)+\log(y)",
         truth="conditional", tick="green", note="needs x, y > 0"),
]

# Physics steps for S8. Symbols carry declared units (as a problem bank entry
# or the tutor would declare them); each line is checked for dimensional
# consistency with Pint and for algebra with the S4 pipeline.
UNITS = {"s": "meter", "u": "meter/second", "v": "meter/second",
         "a": "meter/second**2", "t": "second", "F": "newton", "m": "kilogram",
         "E": "joule", "h": "meter", "g": "meter/second**2"}

PHYSICS = [
    dict(id="P01", cat="kinematics", kind="eq",
         prev=r"v=u+at", curr=r"v-u=at",
         truth="equiv", tick="green"),
    dict(id="P02", cat="kinematics", kind="eq",
         prev=r"v=u+at", curr=r"v=u+at^2",
         truth="not_equiv", tick="red", note="dimensionally inconsistent"),
    dict(id="P03", cat="energy", kind="eq",
         prev=r"E=mgh", curr=r"E=mg+h",
         truth="not_equiv", tick="red", note="adds a force to a length"),
    dict(id="P04", cat="dynamics", kind="eq",
         prev=r"F=ma", curr=r"a=\frac{F}{m}",
         truth="conditional", tick="green"),
]

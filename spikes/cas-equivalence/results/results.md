# CAS spike results (generated)

SymPy 1.14.0, Pint 0.26.1, Python 3.13.17, LaTeX parser `antlr`, 2 vCPU x86_64 cloud container, 2026-10-23. Numeric sampling: 10 points, relative tolerance 1e-09. Every check ran in a forked worker killed at the budget.

Legend: colour = tick the strategy would show the tutor (verdict mapped through `TICK`); ✗ = differs from the hand label; · = strategy not applicable. Budget 1 s unless noted.


## 20 core algebra steps

| Step | Category | prev → curr | Truth | Want | S0 | S1 (C) | S1 (R) | S1 (P) | S2 (C) | S2 (R) | S2 (P) | S3 (R) | S3 (C) | S4 (C) | S4 (R) | S4 (P) | S5 | S5 (P) | S7 | PIPELINE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A01 | expand | `(x+1)^2` → `x^2+2x+1` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| A02 | expand | `(x+1)^2` → `x^2+1` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | · | · | · | 🔴 |
| A03 | factor | `x^2-5x+6` → `(x-2)(x-3)` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| A04 | factor | `x^2-5x+6` → `(x+2)(x+3)` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | · | · | · | 🔴 |
| A05 | fraction | `\frac{2x+4}{2}` → `x+2` | equiv | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| A06 | fraction | `\frac{x+4}{x}` → `4` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | · | · | 🟠✗ | 🔴 |
| A07 | fraction | `\frac{1}{x}+\frac{1}{2x}` → `\frac{3}{2x}` | equiv | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| A08 | div-by-zero trap | `\frac{x^2-1}{x-1}` → `x+1` | domain_changed | 🟠 | 🟠 | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | 🟢✗ | · | · | 🟠 | 🟠 |
| A09 | linear | `2x+3=7` → `2x=4` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | 🟢 |
| A10 | linear | `2x=4` → `x=2` | equiv | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | 🟢 |
| A11 | linear | `3x-5=10` → `3x=5` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | · | 🔴 |
| A12 | quadratic | `x^2-5x+6=0` → `(x-2)(x-3)=0` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | 🟢 |
| A13 | quadratic | `x^2=3x` → `x=3` | lost_roots | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🟢✗ | · | 🔴 |
| A14 | quadratic | `(x-3)^2=0` → `x=3` | same_roots | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟢 | 🟢 | · | 🟢 |
| A15 | rearrange | `v=u+at` → `a=\frac{v-u}{t}` | conditional | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | 🟢 |
| A16 | rearrange | `A=\pi r^2` → `r=\sqrt{\frac{A}{\pi}}` | conditional | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟢 | · | 🔴✗ |
| A17 | squaring | `\sqrt{x+3}=x+1` → `x+3=(x+1)^2` | implies | 🟠 | 🟠 | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟠 | 🟢✗ | 🟠 | 🟠 |
| A18 | inequality | `-2x<-4` → `x<2` | not_equiv | 🔴 | 🟠✗ | · | · | · | · | · | · | 🔴 | · | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | · | 🔴 |
| A19 | inequality | `-2x<-4` → `x>2` | equiv | 🟢 | 🟠✗ | · | · | · | · | · | · | 🟢 | · | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | 🟢 |
| A20 | trig | `\sin^6 x+\cos^6 x` → `1-3\sin^2 x\cos^2 x` | equiv | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟠✗ | 🟠✗ | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |

## Edge cases

| Step | Category | prev → curr | Truth | Want | S0 | S1 (C) | S1 (R) | S1 (P) | S2 (C) | S2 (R) | S2 (P) | S3 (R) | S3 (C) | S4 (C) | S4 (R) | S4 (P) | S5 | S5 (P) | S7 | PIPELINE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E01 | reorder only | `2x+3` → `3+2x` | equiv | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| E02 | assumptions | `\sqrt{x^2}` → `x` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🟢✗ | 🔴 | 🔴 | 🟢✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🟢✗ | · | · | · | 🔴 |
| E03 | floats | `0.5x` → `\frac{x}{2}` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | · | · | · | 🟢 |
| E04 | log rule | `\log(xy)` → `\log(x)+\log(y)` | conditional | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🟢 | 🔴✗ | 🔴✗ | 🟢 | 🟢 | 🟢 | 🟠✗ | 🟠✗ | 🟢 | · | · | · | 🟠✗ |

## Physics steps (S8)

| Step | Category | prev → curr | Truth | Want | S0 | S1 (C) | S1 (R) | S1 (P) | S2 (C) | S2 (R) | S2 (P) | S3 (R) | S3 (C) | S4 (C) | S4 (R) | S4 (P) | S5 | S5 (P) | S7 | PIPELINE | S8 units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01 | kinematics | `v=u+at` → `v-u=at` | equiv | 🟢 | 🟠✗ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟠✗ | 🟠✗ | · | 🟢 | 🟢 |
| P02 | kinematics | `v=u+at` → `v=u+at^2` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🟠✗ | 🟠✗ | · | 🔴 | 🔴 |
| P03 | energy | `E=mgh` → `E=mg+h` | not_equiv | 🔴 | 🟠✗ | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🟠✗ | 🟠✗ | · | 🔴 | 🔴 |
| P04 | dynamics | `F=ma` → `a=\frac{F}{m}` | conditional | 🟢 | 🟠✗ | 🔴✗ | 🔴✗ | 🔴✗ | 🟠✗ | 🟠✗ | 🟠✗ | 🔴✗ | 🔴✗ | 🟢 | 🟢 | 🟢 | 🟠✗ | 🟠✗ | · | 🟢 | 🟢 |

## Accuracy and latency per strategy (core 20 + extras + physics)

Right = tick matches the hand label. Dangerous = shows green where the label is red, or red where it is green. Latency is check time inside the worker (parse excluded), across all steps where the strategy applies. S0 (structural) and S7 (domain) are signals, not judges, so they are left out.

| Strategy | Applies | Right @1s | Dangerous @1s | Right @0.2s | Timeouts @0.2s | Timeouts @1s | median ms | p95 ms | max ms |
|---|---|---|---|---|---|---|---|---|---|
| S1 simplify (C) | 26 | 17/26 | 7 | 17/26 | 0 | 0 | 10.7 | 29.1 | 82.4 |
| S1 simplify (R) | 26 | 17/26 | 7 | 17/26 | 0 | 0 | 11.4 | 28.8 | 114.5 |
| S1 simplify (P) | 26 | 17/26 | 7 | 17/26 | 0 | 0 | 16.4 | 30.2 | 86.6 |
| S2 equals (C) | 26 | 17/26 | 5 | 17/26 | 1 | 0 | 13.4 | 44.9 | 358.4 |
| S2 equals (R) | 26 | 17/26 | 5 | 17/26 | 1 | 0 | 14.5 | 49.1 | 345.9 |
| S2 equals (P) | 26 | 17/26 | 5 | 17/26 | 1 | 0 | 19.3 | 50.9 | 352.5 |
| S3 numeric (R) | 28 | 22/28 | 4 | 22/28 | 0 | 0 | 9.5 | 12.1 | 13.4 |
| S3 numeric (C) | 26 | 20/26 | 4 | 20/26 | 0 | 0 | 9.8 | 12.0 | 12.8 |
| S4 layered (C) | 28 | 23/28 | 2 | 23/28 | 0 | 0 | 10.3 | 35.6 | 90.2 |
| S4 layered (R) | 28 | 23/28 | 2 | 23/28 | 0 | 0 | 10.4 | 35.6 | 105.6 |
| S4 layered (P) | 28 | 23/28 | 3 | 23/28 | 0 | 0 | 10.5 | 32.6 | 91.3 |
| S5 solution sets | 15 | 10/15 | 1 | 10/15 | 0 | 0 | 12.0 | 44.3 | 48.9 |
| S5 solution sets (P) | 15 | 9/15 | 1 | 9/15 | 0 | 0 | 18.1 | 42.3 | 60.9 |
| PIPELINE | 28 | 26/28 | 1 | 26/28 | 0 | 0 | 11.4 | 47.0 | 94.3 |
| S8 units | 4 | 4/4 | 0 | 4/4 | 0 | 0 | 3.2 | 5.8 | 5.8 |

LaTeX parse (two lines): median 28.7 ms, max 49.7 ms. Fork-per-check overhead (wall − parse − check): median 3.1 ms.


## Pipeline detail

| Step | Want | Pipeline | Verdict | Why |
|---|---|---|---|---|
| A01 | 🟢 | 🟢 | equiv | zero via expand |
| A02 | 🔴 | 🔴 | not_equiv | numeric reject: differs at ['3.444'] |
| A03 | 🟢 | 🟢 | equiv | zero via expand |
| A04 | 🔴 | 🔴 | not_equiv | numeric reject: differs at ['3.444'] |
| A05 | 🟢 | 🟢 | equiv | structural |
| A06 | 🔴 | 🔴 | not_equiv | numeric reject: differs at ['3.444'] |
| A07 | 🟢 | 🟢 | equiv | structural |
| A08 | 🟠 | 🟠 | domain_changed | zero via cancel; Union(Interval.open(-oo, 1), Interval.open(1, oo)) -> Reals |
| A09 | 🟢 | 🟢 | equiv | {2} = {2} |
| A10 | 🟢 | 🟢 | equiv | {2} = {2} |
| A11 | 🔴 | 🔴 | not_equiv | {5} vs {5/3} |
| A12 | 🟢 | 🟢 | equiv | {2, 3} = {2, 3} |
| A13 | 🔴 | 🔴 | lost_roots | {3} ⊂ {0, 3} (lost solutions) |
| A14 | 🟢 | 🟢 | same_roots | {3} = {3}; multiplicities {3: 2} vs {3: 1} |
| A15 | 🟢 | 🟢 | equiv | {-427/65} = {-427/65}  [parameters sampled positive: ['t', 'u', 'v']] |
| A16 | 🟢 | 🔴✗ | lost_roots | {sqrt(182)/(7*sqrt(pi))} ⊂ {-sqrt(182)/(7*sqrt(pi)), sqrt(182)/(7*sqrt(pi))} (lost solutions)  [parameters sam |
| A17 | 🟠 | 🟠 | implies | {1} ⊂ {-2, 1} (extra solutions) |
| A18 | 🔴 | 🔴 | not_equiv | Interval.open(2, oo) vs Interval.open(-oo, 2) |
| A19 | 🟢 | 🟢 | equiv | Interval.open(2, oo) = Interval.open(2, oo) |
| A20 | 🟢 | 🟢 | equiv | zero via rewrite(exp) |
| E01 | 🟢 | 🟢 | equiv | structural |
| E02 | 🔴 | 🔴 | not_equiv | numeric reject: differs at ['-0.7943'] |
| E03 | 🟢 | 🟢 | equiv | zero via expand |
| E04 | 🟢 | 🟠✗ | undecided | numerically equal, no symbolic proof |
| P01 | 🟢 | 🟢 | equiv | S5 undecided; numerator ratio constant (1) |
| P02 | 🔴 | 🔴 | not_equiv | curr line inconsistent: adds [length] / [time] to [length] |
| P03 | 🔴 | 🔴 | not_equiv | curr line inconsistent: adds [length] to [length] * [mass] / [time] ** 2 |
| P04 | 🟢 | 🟢 | equiv | {13/98} = {13/98}  [parameters sampled positive: ['F', 'm']] |

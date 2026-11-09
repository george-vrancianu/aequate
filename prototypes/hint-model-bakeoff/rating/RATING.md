# Rating sheet (blind): hint model bake-off, #31

Rate each option in each group. Fill `ratings.csv` (one row per option: group id + letter). Do NOT open `key.csv` before you have rated everything.

Columns:
- usefulness 1-5: would this help a student at this rung?
- correct y/n: is the content mathematically and linguistically correct (also correct Romanian)?
- leaks y/n: it states the next step or the answer, OR it gives away a later rung (an operation at rung 1-2, a later step). Rung overshoot counts as a leak here; write what overshoots in the comment.
- comment: free text.

Rung 1 = where the student stands. Rung 2 = the method. Rung 3 = the operation to apply (not carried out). Rung 4 is never LLM-written.

## lin2-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Începe prin a izola termenul cu x. Poți începe prin a scădea 3 din ambele părți ale ecuației. `2x+3=7`

**B.** Pentru a rezolva ecuația, izolează variabila x. Începe prin a scădea 3 din ambele părți ale ecuației 2x+3=7. `2x+3=7`

**C.** Nu ai izolat încă variabila x. Încearcă să izolezi x din ecuația dată. `2x+3=7`

**D.** Scopul este să rezolvi în raport cu $x$. $x$ nu este încă izolat.

**E.** Pentru a rezolva ecuația, trebuie să izolezi variabila x. Folosește operația de scădere pentru a elimina termenul constant din partea stângă. `2x+3=7`

**F.** Pentru a izola x, trebuie să elimini +3 din ambele părți ale ecuației. `2x+3=7`

## lin2-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pentru a izola x, anulează operațiile în ordine inversă. Începe prin scăderea lui 3 din ambele părți. `2x+3=7`

**B.** Pentru a găsi valoarea lui x, începe prin a elimina termenul care nu este legat de x din ecuație. `2x+3=7`

**C.** Pentru a găsi valoarea lui x, trebuie să izolezi variabila prin anularează operațiile în ordinea inversă. `2x+3=7`

**D.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă. Ce operație trebuie să aplici în primul rând? `2x+3=7`

**E.** Pentru a izola x, inversează operația de adunare cu 3. `2x+3=7`

**F.** Izolează $x$ anulând operațiile în ordine inversă.

## lin2-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pentru a izola x, trebuie să scapi 3 din ambele părți ale ecuației. `2x+3=7`

**B.** Trebuie să scazi 3 din ambele părți pentru a izola x. `2x+3=7`

**C.** Pentru a izola x, începe prin a elimina termenul care nu conține x din partea stângă. Ce trebuie să faci mai întâi? `2x+3=7`

**D.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației 2x+3=7. `2x+3=7`

**E.** Pentru a izola x, trebuie să anulezi operațiile în ordine inversă. Încearcă să scazi 3 din ambele părți. `2x+3=7`

**F.** Scade 3 din ambii membri.

## both-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Începe prin a aduna sau scădea termenii cu x de pe ambele părți pentru a izola variabila x pe o parte. `5x-4=2x+8`

**B.** Deoarece variabila x apare și pe ambele părți, trebuie să o aduni sau să o scăzi pentru a o izola. Aplica o operație care să aducă toate termenii cu x pe o singură parte a ecuației. `5x-4=2x+8`

**C.** Deoarece variabila x apare pe ambele părți ale ecuației, trebuie să o izolezi mai întâi. Începe prin a aduna sau scădea termenii care conțin x pentru a-i grupa pe o singură parte. `5x-4=2x+8`

**D.** Variabila $x$ apare de ambele părți, deci nu este încă izolată. Încearcă să grupezi termenii cu $x$. `5x-4=2x+8`

**E.** Pentru a izola x, trebuie să aduni 4 la ambele părți ale ecuației. `5x-4=2x+8`

**F.** Scopul este să rezolvi în raport cu $x$. $x$ apare în ambii membri, deci nu este încă izolat.

## both-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Adună termenii în $x$ într-un membru și constantele în celălalt.

**B.** Colectă termenii cu x pe o parte și pe cei fără x pe cealaltă parte. `5x-4=2x+8`

**C.** Pentru a izola x, adună sau scade termenii cu x de pe ambele părți pentru a le grupa pe o parte. `5x-4=2x+8`

**D.** Trebuie să grupezi termenii cu x pe o parte și constantele pe cealaltă parte. Încearcă să aduci toate termenii cu x într-o singură parte. `5x-4=2x+8`

**E.** Pentru a rezolva ecuația, mută termenii cu x pe o parte și numerele pe cealaltă. `5x-4=2x+8`

**F.** Pentru a rezolva ecuația, adună termenii cu x pe o parte și termenii constanți pe cealaltă. `5x-4=2x+8`

## both-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Pentru a izola x, începe prin a aduna sau scădea termenii cu x de pe ambele părți ale ecuației. `5x-4=2x+8`

**B.** Pentru a izola variabila x, adună termenii cu x pe o parte și constantele pe cealaltă. Începe prin a scădea 2x din ambele părți ale ecuației. `5x-4=2x+8`

**C.** Pentru a izola termenii cu x, încearcă să scazi $2x$ din ambele părți ale ecuației. `5x-4=2x+8`

**D.** Pentru a izola x, trebuie să aduni termenii cu x pe o parte și constantele pe cealaltă. Aplicați operația de scădere a lui 2x din ambele părți. `5x-4=2x+8`

**E.** Scade $2x$ din ambii membri.

**F.** Pentru a izola x, trebuie să aduni 2x la ambele părți ale ecuației. `5x-4=2x+8`

## quad-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Ecuatia este de gradul al doilea, iar x nu este izolat inca. Trebuie sa aplici o metoda potrivita pentru a rezolva ecuatia in x. `x^2-5x+6=0`

**B.** Pentru a izola x, trebuie să rezolvi ecuația pătratică. `x^2-5x+6=0`

**C.** Scopul este să rezolvi în raport cu $x$. Ecuația este de gradul al doilea și $x$ nu este încă izolat.

**D.** Ecuția este de gradul al doilea și variabila x nu este izolată încă. Folosește metoda factorizării pentru a descompune expresia în factori. `x^2-5x+6=0`

**E.** Ești pe drumul corect! Acum trebuie să izolezi variabila x în această ecuație pătratică. `x^2 - 5x + 6 = 0`

**F.** Ecuația este de gradul al doilea și variabila x nu este încă izolată. Încearcă să folosești o metodă adecvată pentru ecuațiile de gradul al doilea. `x^2-5x+6=0`

## quad-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Pentru a rezolva ecuația, descompune expresia în factori și apoi egalează fiecare factor cu zero. `x^2-5x+6=0`

**B.** Pentru a izola x, împarte ambele părți ale ecuației la 1 pentru a obține x^2-5x+6=0. `x^2-5x+6=0`

**C.** Echipația de la ecuația de gradul al doilea ar trebui să fie factorizată pentru a o rezolva. Încearcă să găsești două numere care se însumă la -5 și se înmulțesc la 6. `x^2 - 5x + 6 = 0`

**D.** Deoarece ecuația este de gradul al doilea, poți o factoriza și apoi să egalezi fiecare factor la zero pentru a găsi valorile lui x. `x^2-5x+6=0`

**E.** Descompune în factori trinomul, apoi egalează fiecare factor cu zero.

**F.** Încearcă să factorizezi ecuația pătratică, apoi setează fiecare factor la zero. `x^2-5x+6=0`

## quad-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Ecuatia este de gradul al doilea și x nu este izolat încă. Factorizează trinomul x^2-5x+6 în doi factori liniari. `x^2-5x+6`

**B.** Deoarece ecuația este de gradul al doilea, încearcă să o descompui în factori. Descompune polinomul x^2-5x+6 în doi factori liniari. `x^2-5x+6=0`

**C.** Descompune trinomul $x^2-5x+6$ în doi factori de gradul întâi.

**D.** Începe prin a factoriza trinomul pătrat din ecuație pentru a-l descompune în două factori liniari. `x^2 - 5x + 6`

**E.** Încearcă să descompui trinomul $x^2-5x+6$ în două factori liniari. `x^2-5x+6=0`

**F.** Factor the trinomial $x^2-5x+6$ into two linear factors. `x^2-5x+6=0`

## brack-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Începe prin deschiderea parantezei pentru a simplifica ecuația și a te apropia de izolarea lui x. `3(x-2)=2x+1`

**B.** Scopul este să rezolvi în raport cu $x$. Există o paranteză, iar $x$ nu este încă izolat.

**C.** Ai observat că există o paranteză în ecuație și variabila x nu este izolată încă. Trebuie să aplici regula distributivă pentru a elimina paranteza. `3(x-2)=2x+1`

**D.** Pentru a izola x, trebuie să îndepărtezi parantezele. Încearcă să aduni termenii cu x și cei fără x pe părți diferite ale ecuației. `3(x-2)=2x+1`

**E.** Ai o paranteză în ecuație, iar x nu este izolat încă. Aplică metoda de a elimina parantezele prin distribuire. `3(x-2)=2x+1`

**F.** Încă ai o înmulțire de paranteză de făcut. Încearcă să elimină parantezele din ecuație. `3(x-2)=2x+1`

## brack-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Pentru a izola x, mai întâi elimină paranteza și apoi adună termenii asemănători. `3(x-2)=2x+1`

**B.** Începe prin eliminarea parantezei din ecuație, folosind regulile de distributivitate. `3(x-2)`

**C.** Începe prin a deschide paranteza din ecuație, apoi adună termenii similari pentru a simplifica expresia. `3(x-2)=2x+1`

**D.** Pentru a rezolva ecuația, începe prin a elimina paranteza din termenul de stânga, apoi grupează termenii asemenea. `3(x-2)=2x+1`

**E.** Încearcă să eliminai paranteza în primul rând, apoi grupează termenii asemenea. `3(x-2)=2x+1`

**F.** Elimină mai întâi paranteza, apoi grupează termenii asemenea.

## brack-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Pentru a rezolva ecuația, începe prin a distribui numărul 3 peste termenii din paranteză de la stânga. După aceea, grupează termenii asemenea pentru a izola x. `3(x-2)` `2x+1`

**B.** Distribute 3 over the bracket on the left side. `3(x-2)=2x+1`

**C.** Începe prin a distribui 3 la paranteza din stânga, apoi adună termenii similari. `3(x-2)=2x+1`

**D.** Distribuie $3$ peste paranteza din stânga.

**E.** Începe prin a dezvolta paranteza de la stânga, aplicând distribuția numărului 3 peste termenii din interior. `3(x-2)`

**F.** Încearcă să eliminăm paranteza din partea stângă prin distribuirea numărului de în fața ei. `3(x-2)=2x+1`

## frac-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Pentru a izola x, trebuie să aduni cele două părți cu x. `\frac{x}{2}+\frac{x}{3}=10`

**B.** Pentru a rezolva ecuația pentru x, trebuie să aduni termenii cu x. Aplicați cel mai mic multiplu comun al numitorilor pentru a elimina fracțiile. `\frac{x}{2}+\frac{x}{3}=10`

**C.** Variabila ta este distribuită în două fracții. Încearcă să aduni acele fracții. `\frac{x}{2}+\frac{x}{3}=10`

**D.** Termenul cu x este distribuit pe două fracții și nu este izolat încă. Încearcă să aduni aceste fracții pentru a simplifica ecuația. `\frac{x}{2}+\frac{x}{3}=10`

**E.** Scopul este să rezolvi în raport cu $x$. $x$ apare în două fracții și nu este încă izolat.

**F.** Începe prin a aduna fracțiile care conțin variabila x pentru a simplifica ecuația. `\frac{x}{2} + \frac{x}{3} = 10`

## frac-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Adu fracțiile la același numitor și adună-le.

**B.** Pentru a rezolva ecuația, adu frații la un numitor comun și adună-i. `\frac{x}{2}+\frac{x}{3}=10`

**C.** Pentru a rezolva ecuația, aduce fracțiile la un numitor comun și le aduni. `\frac{x}{2}+\frac{x}{3}=10`

**D.** Pentru a aduna aceste fracții, trebuie să le aduci la un numitor comun. Ce numitor comun poți folosi? `\frac{x}{2}+\frac{x}{3}=10`

**E.** Pentru a rezolva ecuația, începe prin a aduce fracțiile la același numitor comun și apoi adună-le. `\frac{x}{2}` `\frac{x}{3}` `\frac{x}{2} + \frac{x}{3} = 10`

**F.** Pune la numitor comun frațiile pentru a aduna termenii cu x. `\frac{x}{2}+\frac{x}{3}=10`

## frac-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Pentru a rezolva ecuația, adună cele două fracții transformându-le la numitor comun 6. `\frac{x}{2}+\frac{x}{3}=10`

**B.** Pentru a izola x, adună cele două fracții transformându-le la un numitor comun de 6. `\frac{x}{2}+\frac{x}{3}=10`

**C.** Pentru a rezolva ecuația, adună cele două fracții cu numitorul comun 6. `\frac{x}{2}+\frac{x}{3}=10`

**D.** Adună cele două fracții având numitorul comun $6$.

**E.** Pentru a aduna fracțiile, trebuie să le aduceți la un numitor comun. Încercați să adunați cele două fracții folosind numitorul comun 6. `\frac{x}{2}+\frac{x}{3}=10`

**F.** Pentru a combina fracțiile, găsește un numitor comun pentru cele două fracții cu x. Încearcă să folosești 6 ca numitor comun. `\frac{x}{2} + \frac{x}{3} = 10`

## rearr-r1-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 1.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Scopul este să exprimi $x$ în funcție de $y$. $x$ nu este încă izolat.

**B.** Pentru a rezolva ecuația în funcție de y, izolează variabila x din ecuația y = 2x + 3. `y=2x+3`

**C.** Pentru a rezolva ecuația pentru x în funcție de y, trebuie să izolezi variabila x. Începe prin a scădea 3 din ambele părți ale ecuației. `y=2x+3`

**D.** Începe prin a izola termenul cu x în ecuația dată. `y=2x+3`

**E.** Pentru a izola x, împărțiți ambele părți ale ecuației la 2. `y=2x+3`

**F.** Nu ai izolat încă x. Încearcă să folosești metoda de rearanjare. `y=2x+3`

## rearr-r2-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 2.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Pentru a izola x, anulează operațiile din ordine inversă, păstrând y ca literă. `y=2x+3`

**B.** Pentru a izola x în ecuația y = 2x + 3, trebuie să inversezi operația de înmulțire cu 2. `y=2x+3`

**C.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă, lăsând y ca o variabilă. `y=2x+3`

**D.** Pentru a găsi x în funcție de y, începe prin a inversa operațiile din ecuație, pornind de la cea mai simplă. `y=2x+3`

**E.** Pentru a izola x, anulează operațiile din ordinea inversă, păstrând y ca literă. Începe prin scăderea lui 3 din ambele părți. `y=2x+3`

**F.** Izolează $x$ anulând operațiile în ordine inversă, păstrând $y$ ca literă.

## rearr-r3-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 3.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Scade 3 din ambii membri.

**B.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației. `y=2x+3`

**C.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației y=2x+3. `y=2x+3`

**D.** Pentru a izola x, începe prin a anula adunarea din partea dreaptă. Aplică operația de scădere pe ambele părți. `y=2x+3`

**E.** Pentru a izola x, scade 3 din ambele părți ale ecuației. `y=2x+3`

**F.** Trebuie să scazi 3 din ambele părți pentru a izola x. `y=2x+3`

## ineq-r1-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Începe prin a izola variabila x în partea stângă a inecuației. `-2x>6`

**B.** Scopul este să rezolvi inecuația în raport cu $x$. $x$ nu este încă izolat.

**C.** Nu ai izolat încă variabila x. Încearcă să aplici o operație pentru a izola x. `-2x>6`

**D.** Pentru a rezolva inegalitatea, trebuie să izolezi variabila x. Împarte ambii membri ai inegalității -2x > 6 prin -2, reamintindu-ți că inegalitatea se inversează când împarți cu un număr negativ. `-2x>6`

**E.** Pentru a rezolva inegalitatea -2x > 6, trebuie mai intai sa elimini parantezele. `-2x > 6`

**F.** Pentru a izola x, trebuie să împarți ambii membri ai inegalității cu -2. Întreabă-te: ce se întâmplă cu semnul inegalității când împarți cu un număr negativ? `-2x>6`

## ineq-r2-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Inegalitatea ta este -2x > 6. Pentru a izola x, trebuie să împarti ambii membri ai inegalității prin coeficientul lui x, dar nu uita că împărțirea cu un număr negativ inversează sensul inegalității. `-2x>6`

**B.** Pentru a izola x, împarte ambele părți ale inegalității la coeficientul lui x, ținând cont că semnul inegalității se va inversa deoarece împarți la un număr negativ. `-2x>6`

**C.** Pentru a rezolva inegalitatea, împarte ambii membri la coeficientul lui x. Reamintește-ți că împărțirea la un număr negativ inversează semnul inegalității. `-2x>6`

**D.** Pentru a izola x, trebuie să împărți ambele părți la coeficientul lui x. Nu uita că împărțirea la un număr negativ schimbă sensul inegalității. `-2x>6`

**E.** Pentru a rezolva inegalitatea -2x > 6, imparte ambele parti la coeficientul lui x, care este -2. Reaminteste-ti ca, atunci cand imparti sau inmultesti cu un numar negativ, semnul inegalitatii se schimba. `-2x > 6`

**F.** Împarte ambii membri la coeficientul lui $x$. Împărțirea la un număr negativ inversează sensul inegalității.

## ineq-r3-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Pentru a izola x, împarteți ambii membri ai inecuației prin coeficientul lui x și schimbați sensul inegalității, deoarece împărțiți la un număr negativ. `-2x>6`

**B.** Pentru a izola x, împarte ambii membri inegalității la -2 și nu uita să schimbi sensul inegalității, deoarece împarți la un număr negativ. `-2x>6`

**C.** Trebuie să împarți ambele părți ale inegalității la coeficientul lui x, dar ai uitat să inversezi semnul inegalității. `-2x>6`

**D.** Pentru a izola x, împarteți ambele părți ale inegalității la -2 și inversați semnul relației. `-2x>6`

**E.** Împarte ambii membri la $-2$ și inversează sensul inegalității.

**F.** Trebuie să împărți ambele părți la coeficientul lui x și să inversezi semnul inegalității. Ce se întâmplă când împărți la un număr negativ? `-2x>6`

## sys-r1-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Pentru a rezolva sistemul de ecuații, trebuie mai întâi să găsești relația dintre x și y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**B.** Ai nevoie să rezolvi sistemul de ecuații pentru a găsi valorile lui x și y. Începe prin a aplica metoda eliminării pentru a elimina o variabilă. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**C.** Nu ai încă găsit valorile pentru x și y. Încearcă să folosești metoda de rezolvare a sistemului de ecuații. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**D.** Ai un sistem de două ecuații cu două necunoscute. Încearcă să folosești o metodă care să te ajute să găsești valorile lui x și y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**E.** Scopul este să rezolvi sistemul în raport cu $x$ și $y$. Niciuna dintre necunoscute nu este încă aflată.

**F.** Sistemul de ecuații nu este încă rezolvat pentru x și y. Încearcă să aduni cele două ecuații pentru a elimina o variabilă. `\begin{cases}x+y=5\\x-y=1\end{cases}`

## sys-r2-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Pentru a găsi valorile lui x și y, poți încerca să elimine una dintre variabile prin adunarea sau scăderea ecuațiilor date. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**B.** Încearcă să folosești metoda eliminării pentru a elimina una dintre variabile. Ce ar trebui să faci cu cele două ecuații? `\begin{cases}x+y=5\\x-y=1\end{cases}`

**C.** Pentru a rezolva sistemul, folosește metoda eliminării prin adunarea celor două ecuații pentru a anula variabila y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**D.** Pentru a rezolva sistemul, adună sau scade ecuațiile pentru a elimina o variabilă. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**E.** Pentru a rezolva sistemul, adună cele două ecuații pentru a elimina variabila y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**F.** Folosește metoda reducerii: adună sau scade ecuațiile ca să elimini o necunoscută.

## sys-r3-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Pentru a elimina variabila y, poți încerca să aduni cele două ecuații. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**B.** Adună cele două ecuații ca să elimini pe $y$.

**C.** Pentru a elimina y, adună cele două ecuații. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**D.** Pentru a rezolva sistemul, adaugă cele două ecuații pentru a elimina variabila y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**E.** Pentru a rezolva sistemul, adună cele două ecuații pentru a anula variabila y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

**F.** Încearcă să adaugi cele două ecuații pentru a elimina variabila y. `\begin{cases}x+y=5\\x-y=1\end{cases}`

## log-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Ai combinat logaritmi, deci trebuie să verifici dacă există soluții suplimentare la final. În acest moment, variabila nu este izolată. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**B.** Ai combinat corect logaritmii, dar acum trebuie să rezolvi ecuația rezultată pentru a găsi valorile posibile ale lui x. Nu uita să verifici dacă aceste soluții sunt valide în ecuația inițială. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**C.** Pentru a izola x, trebuie să rezolvi ecuația x(x-2)=3. Ai combinat deja logaritmii, așa că nu uita să verifici soluțiile suplimentare la final. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**D.** Ai combinat corect logaritmii, dar acum trebuie să izolezi variabila x. Asigură-te că verifici soluțiile obținute, deoarece operația cu logaritmi poate introduce soluții nevalide. `\ln x + \ln(x-2) = \ln 3` `x\cdot(x-2) = 3`

**E.** Scopul este să rezolvi în raport cu $x$. $x$ nu este încă izolat. Pasul 2 merge într-un singur sens: ai combinat logaritmii, deci verifică la final soluțiile străine.

**F.** Ai combinat logaritmuli corect, dar trebuie să verifici dacă soluțiile obținute sunt valide pentru expresia inițială. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

## log-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Ai combinat corect logaritmii, dar acum trebuie să verifici dacă soluția găsită respectă condițiile de existență ale logaritmilor. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**B.** Desfă parantezele și mută totul într-un membru, apoi rezolvă ecuația de gradul al doilea.

**C.** Ai combinat logaritmi, așa că trebuie să verifici soluțiile finale. Acum, folosește metoda de a extinde și muta totul pe o singură parte pentru a rezolva ecuația de gradul doi. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**D.** Ai combinat corect logaritmii, dar acum trebuie să izolezi x. Adună termenii la un membru și aduce totul la forma unei ecuații de gradul doi. `\ln x + \ln(x-2) = \ln 3` `x\cdot(x-2) = 3`

**E.** Ai combinat logaritmuli corect, dar acum trebuie să verifici dacă soluțiile găsite sunt valide pentru expresia inițială. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**F.** Pentru a izola x, trebuie să extindeți și să mutați totul pe o parte a ecuației, apoi să rezolvați ecuația pătratică. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

## log-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Ai combinat corect logaritmii, dar acum trebuie să dezvoltai produsul și să muți termenul 3 pe cealaltă parte pentru a obține o ecuație de gradul al doilea. `x\cdot(x-2)` `3`

**B.** Ai obținut ecuația quadratică, dar trebuie să verifici soluțiile pentru a te asigura că nu sunt extrase. Extinde produsul și adună termenii pentru a rezolva. `x\cdot(x-2)=3`

**C.** Ai combinat corect logaritmii, dar acum trebuie să dezvolți produsul și să mutați 3 la o parte pentru a obține o ecuație de gradul doi. `x\cdot(x-2)` `3`

**D.** Desfă produsul și scade 3 din ambii membri.

**E.** Ai combinat logaritmi, așa că verifică dacă există soluții suplimentare la final. Acum, extinde produsul și mută termenul în parte. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

**F.** Pentru a izola x, trebuie să extindeți produsul și să scădeți 3 din ambele părți. `\ln x+\ln(x-2)=\ln 3` `x\cdot(x-2)=3`

## sqrt-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Ai păstrat ecuația echivalentă până acum, dar trebuie să izolezi mai întâi variabila x. Încearcă să descompui și să simplifici partea dreaptă a ecuației. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**B.** Trebuie să rezolvi ecuația pentru x. Ai început corect, dar ai făcut o eroare la pasul 2. Ai înmulțit ambele părți cu (x-1)^2, ceea ce a creat o nouă ecuație. Verifică dacă există soluții suplimentare la final. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**C.** Ai pătrățimat ambele părți, ceea ce poate introduce soluții false; verifică acum fiecare soluție în ecuația inițială. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**D.** Scopul este să rezolvi în raport cu $x$. $x$ nu este încă izolat. Pasul 2 merge într-un singur sens: ai ridicat la pătrat ambii membri, deci verifică la final soluțiile străine.

**E.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile finale pentru soluții suplimentare. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**F.** Ai ridicat la pătrat ambii membri pentru a elimina radicalul, dar acum trebuie să verifici dacă soluțiile găsite sunt valide, deoarece ridicarea la pătrat poate introduce soluții suplimentare. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

## sqrt-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile la final. Acum, extinde pătratul și mută totul pe o singură parte. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**B.** Ai păstrat ecuația echivalentă până acum, dar trebuie să izolezi mai întâi variabila x. Încearcă să dezvolți pătratul din dreapta și apoi să aduni toate termenii pe o parte a ecuației. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**C.** Pentru a izola x, extinde pătratul și mută totul pe o parte, apoi rezolvă ecuația pătrată. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**D.** Desfă pătratul și mută totul într-un membru, apoi rezolvă ecuația de gradul al doilea.

**E.** Ai pătrățit ambele părți, deci verifică soluțiile la final pentru a elimina pe cele false. Transformă ecuația într-o ecuație de gradul al doilea și rezolv-o. `x+1=(x-1)^2`

**F.** Ai ridicat la pătrat ambii membri, dar acum trebuie să dezvoltai pătratul și să aduni termenii pe o singură parte pentru a rezolva ecuația de gradul doi. `(x-1)^2`

## sqrt-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: ['one-way']. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Pentru a izola x, extinde pătratul (x-1)^2 și scade x+1 de pe ambele părți. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**B.** Ai păstrat ecuația echivalentă după pătrunderea pătratului, dar acum trebuie să dezvolți (x-1)^2 și să aduni sau scazi termenii pentru a obține o ecuație de gradul doi. `\sqrt{x+1}=x-1` `(x-1)^2` `x+1=(x-1)^2`

**C.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile la final. Încearcă să dezvolți $(x-1)^2$ și să muti termenii în aceeași parte. `\sqrt{x+1}=x-1` `x+1=(x-1)^2`

**D.** Ai pătrățimat ambele părți, așa că verifică soluțiile la final pentru a elimina pe cele false. Extinde pătratul și mută totul într-o parte pentru a rezolva ecuația pătratică. `x+1=(x-1)^2`

**E.** Ai ridicat la pătrat ambii membri, dar acum trebuie să dezvoltai expresia și să aduni termenii similari pentru a obține o ecuație de gradul al doilea. `(x-1)^2`

**F.** Desfă $(x-1)^2$ și scade $x+1$ din ambii membri.

## wrong-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pasul 2 nu este echivalent cu pasul 1; încearcă să transformi ecuația din pasul 1 corect pentru a obține o expresie echivalentă. `2x+3=7` `2x=10`

**B.** Pasul 2 nu este echivalent cu pasul 1. Verifică din nou cum se obține o nouă ecuație din cea anterioară. `2x+3=7` `2x=10`

**C.** Pentru a ajunge la pasul 2, trebuie mai întâi să înmulțiți ambele părți ale ecuației cu 2. `2x+3=7` `2x=10`

**D.** Pasul 2 nu rezultă din pasul 1. Indiciile pornesc de la pasul 1.

**E.** Pasul doi nu este echivalent cu pasul unu. Încearcă să aplici o operație pentru a izola termenul cu x. `2x+3=7` `2x=10`

**F.** Ai început bine, dar verifică cum ai trecut de la ecuația inițială la următoarea formă. Asigură-te că acțiunea aplicată păstrează echivalența ecuației. `2x+3=7` `2x=10`

## wrong-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pentru a izola x, trebuie mai întâi să înlături parantezele. În pasul 2, ai uitat să înlături parantezele din expresia 2x. `2x+3=7` `2x=10`

**B.** Pasul 2 nu este echivalent cu pasul 1. Pentru a izola x, trebuie să anulezi operațiile în ordinea inversă. `2x+3=7` `2x=10`

**C.** Pentru a izola x, trebuie să anulezi operațiile în ordine inversă. Începe prin a scădea 3 din ambele părți pentru a obține 2x = 10. `2x+3=7` `2x=10`

**D.** Ai început bine, dar trebuie să iei în considerare și partea cu 3 când vei elimina termenul cu x. Încearcă să te gândești cum să compensezi adunarea cu 3. `2x+3=7` `2x=10`

**E.** Metoda este să izolezi x anulând operațiile în ordine inversă. Verifică dacă pasul tău este echivalent cu pasul anterior. `2x+3=7` `2x=10`

**F.** Pornind de la pasul 1: izolează $x$ anulând operațiile în ordine inversă.

## wrong-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pornind de la pasul 1: scade 3 din ambii membri.

**B.** Pentru a izola x, trebuie să scapi 3 din ambele părți ale ecuației. Asta nu este echivalent cu pașii tăi actuali. `2x+3=7` `2x=10`

**C.** Ai început bine, dar acum trebuie să elimineți termenul constant de pe partea stângă. Încearcă să scazi 3 din ambele părți ale ecuației. `2x+3=7` `2x=10`

**D.** Trebuie să scazi 3 din ambele părți pentru a izola termenul cu x. `2x+3=7`

**E.** Înainte de a trece la pasul următor, asigură-te că pasul tău este echivalent cu pasul anterior. Încearcă să scazi 3 din ambele părți. `2x+3=7`

**F.** Ai scăzut 3 din ambele părți, dar rezultatul nu este echivalent cu ecuația inițială. Încearcă din nou să izolezi x prin a scădea 3 din ambii membri ai ecuației 2x+3=7. `2x+3=7`

## dec-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Pentru a rezolva ecuația pentru x, începe prin a combina termenii care conțin variabila x din partea stângă a ecuației. `0,5x+0,25x=3`

**B.** Începe prin a combina termenii care conțin variabila x pentru a simplifica ecuația. `0.5x + 0.25x = 3`

**C.** Pentru a izola x, trebuie să înmulțiți ambele părți ale ecuației cu 2. `0,5x+0,25x=3`

**D.** Nu ai izolat încă variabila x. Încearcă să grupezi termenii care conțin x. `0,5x+0,25x=3`

**E.** Ai obținut o ecuație cu termenii de x la stânga. Acum trebuie să aduni coeficienții lui x pentru a simplifica expresia. `0,5x+0,25x=3`

**F.** Scopul este să rezolvi în raport cu $x$. $x$ nu este încă izolat.

## dec-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Pentru a izola x, combină termenii cu x și împarte rezultatul la coeficientul lui x. `0,5x+0,25x=3`

**B.** Pentru a rezolva ecuația, adună termenii care conțin x, apoi împarte rezultatul la coeficientul lui x. `0,5x+0,25x=3`

**C.** Reduce termenii în $x$, apoi împarte la coeficient.

**D.** Încearcă să combini termenii asemenea din partea stângă. Apoi, împărțirea la coeficientul lui x va te ajuta să izolezi variabila. `0,5x+0,25x=3`

**E.** Începe prin combinarea termenilor asemănători care conțin x pentru a simplifica ecuația. `0.5x + 0.25x`

**F.** Combina termenii cu x și apoi împarte rezultatul la coeficientul lui x. `0,5x+0,25x=3`

## dec-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Începe prin combinarea termenilor asemănători care conțin x. Adună valorile coeficienților lor. `0,5x` `0,25x`

**B.** Pentru a izola x, adună termenii cu x: 0,5x și 0,25x. `0,5x+0,25x=3`

**C.** Ai adunat deja termenii cu x, acum trebuie să împarți ambii membri ai ecuației la coeficientul lui x pentru a izola x. `0,5x+0,25x=3`

**D.** Încearcă să aduni termenii care conțin $x$ din partea stângă a ecuației. `0,5x+0,25x=3`

**E.** Adună cei doi termeni în $x$: $0,5x$ și $0,25x$.

**F.** Pentru a izola variabila x, adună termenii similari care conțin x din ecuația ta. `0,5x+0,25x=3`

## dom-r1-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Expresia nu este încă simplificată și este nedefinită unde numitorul este zero. Încearcă să descompui numărătorul în factori pentru a vedea dacă se pot simplifica cu numitorul. `\frac{x^2-1}{x-1}`

**B.** Scopul este să simplifici expresia. Nu este încă simplificată și nu este definită acolo unde numitorul este zero.

**C.** Expresia nu este încă simplificată, deoarece este nedefinită unde numitorul este zero. `\frac{x^2-1}{x-1}`

**D.** Încearcă să simplifici fracția prin factorizarea numitorului și numitorului, dacă este posibil. `\frac{x^2-1}{x-1}`

**E.** Pentru a simplifica expresia, trebuie să elimeni factorul comun din numărător și numitor, dar să ții cont de condiția ca numitorul să nu fie zero. `\frac{x^2-1}{x-1}`

**F.** Pentru a simplifica expresia, trebuie să o împarți la diferența a două pătrate. `\frac{x^2-1}{x-1}`

## dom-r2-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Factorizează numărătorul expresiei și anulează factorul comun cu numitorul, ținând cont de unde expresia este nedeterminată. `\frac{x^2-1}{x-1}`

**B.** Expresia nu este simplificată încă și este nedefinită unde numitorul este zero. Factorează numitorul și apoi elimină factorul comun, notând unde numitorul este zero. `\frac{x^2-1}{x-1}`

**C.** Descompune numărătorul, apoi simplifică factorul comun, ținând cont unde numitorul este zero.

**D.** Încearcă să factorizezi numărătorul, apoi să anulezi factorul comun, dar nu uita să menționezi unde este numitorul zero. `\frac{x^2-1}{x-1}`

**E.** Încearcă să descompui numitorul și numitorul pentru a vedea dacă există un factor comun care poate fi anulat. Fii atent la valorile lui x pentru care expresia nu este definită! `\frac{x^2-1}{x-1}`

**F.** Factor the numerator to find the common factor with the denominator, then cancel them while noting where the expression is undefined. `\frac{x^2-1}{x-1}`

## dom-r3-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Factorize numărătorul x^2-1 ca o diferență de pătrate, apoi simplifică expresia ținând cont de condițiile de existență. `x^2-1`

**B.** Începe prin a factoriza numitorul din expresie, folosind formula diferenței pătratelor. `x^2 - 1`

**C.** Trebuie să factorizezi numărătorul ca diferență de pătrate. `\frac{x^2-1}{x-1}`

**D.** Încearcă să factorizezi numărătorul ca o diferență de pătrate. `\frac{x^2-1}{x-1}`

**E.** Descompune numărătorul $x^2-1$ ca diferență de pătrate.

**F.** Factor the numerator x^2-1 as a difference of squares to simplify the expression. `\frac{x^2-1}{x-1}`

## lin2-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** You need to isolate x by undoing the addition of 3. Subtract 3 from both sides of the equation. `2x+3=7`

**B.** You are not done solving for x yet. Try isolating the variable. `2x+3=7`

**C.** You have the equation 2x+3=7, but x is not isolated yet. Use the subtraction method to apply the inverse operation of addition. `2x+3=7`

**D.** To solve for x, you need to isolate the variable. Start by subtracting 3 from both sides of the equation 2x+3=7. `2x+3=7`

**E.** The goal is to solve for $x$. $x$ is not isolated yet.

**F.** Your equation has x combined with other numbers. Try to get x by itself on one side. `2x+3=7`

## lin2-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** To solve for x, reverse the operations applied to it. Start by undoing the addition of 3. `2x+3=7`

**B.** To solve for x, you need to isolate it by undoing the operations in reverse order. Start by subtracting 3 from both sides of the equation 2x+3=7. `2x+3=7`

**C.** To solve for x, isolate it by undoing the operations in reverse order. Start by subtracting 3 from both sides of the equation 2x+3=7. `2x+3=7`

**D.** Isolate $x$ by undoing the operations in reverse order.

**E.** To get x by itself, you need to undo the operations in reverse order. What operation should you apply first? `2x+3=7`

**F.** To solve for x, you need to isolate x by undoing the operations in reverse order. Start by undoing the addition of 3 by subtracting 3 from both sides. `2x+3=7`

## lin2-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** To start isolating x, what operation should you perform on both sides of the equation? `2x+3=7`

**B.** Subtract 3 from both sides to isolate x. `2x+3=7`

**C.** To isolate x, subtract 3 from both sides of the equation. `2x+3=7`

**D.** To solve for x, start by removing the constant term on the left side by performing the same operation on both sides of the equation. `2x+3=7`

**E.** Subtract 3 from both sides.

**F.** To solve for x, subtract 3 from both sides of the equation 2x+3=7 to isolate the term with x. `2x+3=7`

## quad-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** You have a quadratic equation to solve. Try to rewrite it so that one side equals zero and the other side is a product of factors involving x. `x^2 - 5x + 6 = 0`

**B.** The goal is to solve for $x$. The equation is quadratic and $x$ is not isolated yet.

**C.** Since this is a quadratic equation, you'll need to use a specific method to solve for x. `x^2-5x+6=0`

**D.** Since the equation is quadratic and x is not isolated yet, you should factor the quadratic expression to solve for x. `x^2-5x+6`

**E.** To solve for x, you need to factor the quadratic equation x^2-5x+6=0. `x^2-5x+6=0`

**F.** Since the equation is quadratic and x is not isolated yet, you can solve it by factoring the quadratic expression. `x^2-5x+6=0`

## quad-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Factor the quadratic, then set each factor to zero.

**B.** Since this is a quadratic equation, try factoring it first. Then, set each factor equal to zero. `x^2-5x+6=0`

**C.** Since the equation is quadratic and x is not isolated yet, factor the quadratic expression and then set each factor to zero. `x^2-5x+6=0`

**D.** Factor the quadratic equation x^2-5x+6=0 to find the values of x. `x^2-5x+6=0`

**E.** Since the equation is quadratic and x is not isolated, factor the quadratic expression and set each factor to zero to solve for x. `x^2-5x+6=0`

**F.** Your equation is quadratic. Try to factor it into two binomials that multiply to give the original expression. `x^2 - 5x + 6 = 0`

## quad-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Factor the trinomial $x^2-5x+6$ into two linear factors.

**B.** Factor the trinomial x^2-5x+6 into two linear factors. `x^2-5x+6=0`

**C.** Since this is a quadratic equation, try factoring the trinomial first. What two binomials multiply to give you x^2-5x+6? `x^2-5x+6=0`

**D.** Since the equation is quadratic and x is not isolated yet, factor the trinomial x^2-5x+6 into two linear factors, then set each factor to zero. `x^2-5x+6`

**E.** Your equation is quadratic, so try to factor it into two binomials that multiply to give the original expression. `x^2 - 5x + 6`

**F.** Since the equation is quadratic and x is not isolated, factor the trinomial x^2-5x+6 into two linear factors. `x^2-5x+6=0`

## ineq-r1-en

Goal: solve the inequality for x. Language of the hints: English. Rung 1.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** You need to isolate x to solve the inequality. What operation should you apply to both sides? `-2x>6`

**B.** The goal is to solve the inequality for $x$. $x$ is not isolated yet.

**C.** You need to solve the inequality ≤-2x>6≤ for x. `-2x>6`

**D.** You have the inequality -2x > 6, but x is not isolated yet. To proceed, divide both sides by -2 and remember to reverse the inequality sign. `-2x>6`

**E.** Your inequality has a variable on both sides. Try to move the term with x to one side to isolate it. `-2x>6`

**F.** To solve the inequality for x, you need to isolate the variable. Remember to divide both sides by the coefficient of x. `-2x>6`

## ineq-r2-en

Goal: solve the inequality for x. Language of the hints: English. Rung 2.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Divide both sides by the coefficient of $x$. Dividing by a negative number reverses the inequality sign.

**B.** To isolate x, divide both sides by -2 and remember to reverse the inequality sign. `-2x>6`

**C.** To solve the inequality ≠-2x≠6, divide both sides by ∐2. Remember that dividing by a negative number reverses the inequality sign. `-2x>6`

**D.** You have an inequality involving x. To isolate x, consider dividing both sides by the coefficient of x, but remember how this affects the inequality sign. `-2x>6`

**E.** Remember that when you divide both sides by a negative number, you need to reverse the inequality sign. `-2x>6`

**F.** To solve the inequality, divide both sides by the coefficient of x. Remember that dividing by a negative number reverses the inequality sign. `-2x>6`

## ineq-r3-en

Goal: solve the inequality for x. Language of the hints: English. Rung 3.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Divide both sides by $-2$ and reverse the inequality sign.

**B.** To solve the inequality, divide both sides by -2 and remember to reverse the inequality sign. `-2x>6`

**C.** Remember that when you divide both sides by a negative number, you must reverse the inequality sign. Try dividing both sides by -2. `-2x>6`

**D.** To isolate x, divide both sides by -2 and remember to reverse the inequality sign. `-2x>6`

**E.** To isolate x, divide both sides of the inequality by the coefficient of x, but remember to reverse the inequality sign when dividing by a negative number. `-2x>6`

**F.** To solve the inequality ≠x>6, divide both sides by -2 and reverse the inequality sign. `-2x>6`

## wrong-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** You need to undo the second operation to solve for x. Start by subtracting 3 from both sides. `2x+3=7` `2x=10`

**B.** Your step 2 does not follow from step 1. Check your arithmetic to ensure the equation remains equivalent. `2x+3=7` `2x=10`

**C.** Check if the second equation is equivalent to the first one. You should use the method of isolating the variable. `2x+3=7` `2x=10`

**D.** Step 2 doesn't follow from step 1. The hints build on step 1.

**E.** You started with the correct equation, but how can you get from 2x + 3 = 7 to 2x = 10? Think about what operation you can use to isolate the term with x. `2x+3=7` `2x=10`

**F.** Your second step does not follow from the first. Remember that to isolate x, you must perform the same operation on both sides of the equation. `2x+3=7` `2x=10`

## wrong-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** You started correctly by isolating the term with x, but check how you moved the constant term to the other side—did you keep the equation balanced? `2x+3=7` `2x=10`

**B.** You need to undo the subtraction of 3 to isolate x. Start by subtracting 3 from both sides. `2x+3=7` `2x=10`

**C.** Your step 2 does not follow from step 1. To isolate x, undo the operations in reverse order. `2x+3=7` `2x=10`

**D.** Your second step does not follow from the first. Remember to isolate x by undoing the operations in reverse order. `2x+3=7` `2x=10`

**E.** When you moved the constant term, the equation is no longer equivalent. Try isolating x by undoing the operations in reverse order. `2x+3=7` `2x=10`

**F.** Starting from step 1: isolate $x$ by undoing the operations in reverse order.

## wrong-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: ['not equivalent']. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** You subtracted 3 from both sides, but you should have done that first to isolate the term with x. Try undoing the addition before dealing with the coefficient of x. `2x+3=7` `2x=10`

**B.** To solve for x, you need to isolate it by undoing the operations in reverse order. First, subtract 3 from both sides of the equation. `2x+3=7` `2x=10`

**C.** You need to undo the operation you did to get from step 1 to step 2. Subtract 3 from both sides of the equation. `2x+3=7` `2x=10`

**D.** Starting from step 1: subtract 3 from both sides.

**E.** To isolate x, you need to undo the operations in reverse order. Try subtracting 3 from both sides. `2x+3=7`

**F.** You made an error in the second step; remember to subtract 3 from both sides of the equation to keep it balanced. `2x+3=7` `2x=10`


# Rating sheet (blind): hint model bake-off, #31

Rate each option in each group. Fill `ratings.csv` (one row per option: group id + letter). Do NOT open `key.csv` before you have rated everything.

Formulas appear as plain text or raw LaTeX; the student would see them rendered. Every option is shown as plain hint text only: the formula chips the tool would add under a hint are left out for all options (they copy the student's steps, which each group already shows), so that no option is recognisable by its layout.

Columns:
- usefulness 1-5 (1 = harmful or useless, 3 = OK, 5 = what a good teacher would say at this rung): would this help a student at this rung?
- correct y/n: is the content mathematically and linguistically correct (also correct Romanian)?
- leaks y/n: it states the next step or the answer, OR it gives away a later rung (an operation at rung 1-2, a later step). Rung overshoot counts as a leak here; write what overshoots in the comment.
- comment: free text. Please also note when a hint stays BELOW its rung (rung 3 that does not name the operation, rung 2 that does not name the method); that is not a leak, so leave leaks = n.

Rung 1 = where the student stands. Rung 2 = the method. Rung 3 = the operation to apply (not carried out). Rung 4 is never LLM-written.

## lin2-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Nu ai izolat încă variabila x. Încearcă să izolezi x din ecuația dată.

**B.** Pentru a izola x, trebuie să eliminăm termenul adunat cu 2x din partea stângă a ecuației.

**C.** Pentru a rezolva ecuația, trebuie să izolezi variabila x. Folosește operația de scădere pentru a elimina termenul constant din partea stângă.

**D.** Pentru a rezolva ecuația, izolează variabila x. Începe prin a scădea 3 din ambele părți ale ecuației 2x+3=7.

**E.** Scopul este să rezolvi în raport cu x. x nu este încă izolat.

**F.** Începe prin a izola termenul cu x. Poți începe prin a scădea 3 din ambele părți ale ecuației.

**G.** Pentru a izola x, trebuie să elimini +3 din ambele părți ale ecuației.

## lin2-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pentru a găsi valoarea lui x, începe prin a elimina termenul care nu este legat de x din ecuație.

**B.** Pentru a găsi valoarea lui x, trebuie să izolezi variabila prin anularează operațiile în ordinea inversă.

**C.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă. Începe prin a scădea 3 din ambele părți.

**D.** Izolează x anulând operațiile în ordine inversă.

**E.** Pentru a izola x, anulează operațiile în ordine inversă. Începe prin scăderea lui 3 din ambele părți.

**F.** Pentru a izola x, inversează operația de adunare cu 3.

**G.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă. Ce operație trebuie să aplici în primul rând?

## lin2-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Scade 3 din ambii membri.

**B.** Pentru a izola x, trebuie să anulezi operația de adunare din partea stângă.

**C.** Pentru a izola x, începe prin a elimina termenul care nu conține x din partea stângă. Ce trebuie să faci mai întâi?

**D.** Pentru a izola x, trebuie să scapi 3 din ambele părți ale ecuației.

**E.** Trebuie să scazi 3 din ambele părți pentru a izola x.

**F.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației 2x+3=7.

**G.** Pentru a izola x, trebuie să anulezi operațiile în ordine inversă. Încearcă să scazi 3 din ambele părți.

## both-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Variabila x apare de ambele părți, deci nu este încă izolată. Încearcă să grupezi termenii cu x.

**B.** Variabila x apare de ambele părți, deci nu este încă izolată. Încearcă să grupezi termenii care conțin x.

**C.** Pentru a izola x, trebuie să aduni 4 la ambele părți ale ecuației.

**D.** Scopul este să rezolvi în raport cu x. x apare în ambii membri, deci nu este încă izolat.

**E.** Începe prin a aduna sau scădea termenii cu x de pe ambele părți pentru a izola variabila x pe o parte.

**F.** Deoarece variabila x apare pe ambele părți ale ecuației, trebuie să o izolezi mai întâi. Începe prin a aduna sau scădea termenii care conțin x pentru a-i grupa pe o singură parte.

**G.** Deoarece variabila x apare și pe ambele părți, trebuie să o aduni sau să o scăzi pentru a o izola. Aplica o operație care să aducă toate termenii cu x pe o singură parte a ecuației.

## both-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Trebuie să grupezi termenii cu x pe o parte și constantele pe cealaltă parte. Încearcă să aduci toate termenii cu x într-o singură parte.

**B.** Pentru a rezolva ecuația, mută termenii cu x pe o parte și numerele pe cealaltă.

**C.** Pentru a rezolva ecuația, adună termenii cu x pe o parte și termenii constanți pe cealaltă.

**D.** Încearcă să aduni termenii cu x într-o parte și constantele în cealaltă parte.

**E.** Pentru a izola x, adună sau scade termenii cu x de pe ambele părți pentru a le grupa pe o parte.

**F.** Adună termenii în x într-un membru și constantele în celălalt.

**G.** Colectă termenii cu x pe o parte și pe cei fără x pe cealaltă parte.

## both-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `5x-4=2x+8`
CAS verdicts: none. Ladder builds on step 1. Goal status: x appears on both sides, so it is not isolated yet.
Hidden from the model and the student: next step `3x-4=8`, answer `x=4`.

**A.** Pentru a izola variabila x, adună termenii cu x pe o parte și constantele pe cealaltă. Începe prin a scădea 2x din ambele părți ale ecuației.

**B.** Pentru a izola x, trebuie să aduni termenii cu x pe o parte și constantele pe cealaltă. Aplicați operația de scădere a lui 2x din ambele părți.

**C.** Pentru a izola x, trebuie să aduni 2x la ambele părți ale ecuației.

**D.** Pentru a izola termenii cu x, încearcă să scazi 2x din ambele părți ale ecuației.

**E.** Scade 2x din ambii membri.

**F.** Pentru a izola x, începe prin a aduna sau scădea termenii cu x de pe ambele părți ale ecuației.

**G.** Pentru a izola x, trebuie să aduci termenii cu x pe o parte și constantele pe cealaltă. Încearcă să scazi 2x din ambele părți.

## quad-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Ecuația este de gradul al doilea și variabila x nu este încă izolată. Încearcă să folosești o metodă adecvată pentru ecuațiile de gradul al doilea.

**B.** Ecuatia este de gradul doi și variabila x nu este încă izolată. Încearcă să folosești o metodă pentru ecuații de gradul doi.

**C.** Scopul este să rezolvi în raport cu x. Ecuația este de gradul al doilea și x nu este încă izolat.

**D.** Pentru a izola x, trebuie să rezolvi ecuația pătratică.

**E.** Ecuatia este de gradul al doilea, iar x nu este izolat inca. Trebuie sa aplici o metoda potrivita pentru a rezolva ecuatia in x.

**F.** Ecuția este de gradul al doilea și variabila x nu este izolată încă. Folosește metoda factorizării pentru a descompune expresia în factori.

**G.** Ești pe drumul corect! Acum trebuie să izolezi variabila x în această ecuație pătratică.

## quad-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Descompune în factori trinomul, apoi egalează fiecare factor cu zero.

**B.** Pentru a izola x, împarte ambele părți ale ecuației la 1 pentru a obține x^2-5x+6=0.

**C.** Echipația de la ecuația de gradul al doilea ar trebui să fie factorizată pentru a o rezolva. Încearcă să găsești două numere care se însumă la -5 și se înmulțesc la 6.

**D.** Deoarece ecuația este de gradul al doilea, poți o factoriza și apoi să egalezi fiecare factor la zero pentru a găsi valorile lui x.

**E.** Pentru a rezolva ecuația, descompune expresia în factori și apoi egalează fiecare factor cu zero.

**F.** Încearcă să factorizezi ecuația pătratică, apoi setează fiecare factor la zero.

**G.** Ecuatia este pătratică, deci trebuie să o factorizezi pentru a găsi soluțiile.

## quad-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Încearcă să descompui trinomul x^2-5x+6 în două factori liniari.

**B.** Descompune trinomul x^2-5x+6 în doi factori de gradul întâi.

**C.** Încearcă să factorizezi trinomul x^2-5x+6 în două factorii liniari.

**D.** Începe prin a factoriza trinomul pătrat din ecuație pentru a-l descompune în două factori liniari.

**E.** Deoarece ecuația este de gradul al doilea, încearcă să o descompui în factori. Descompune polinomul x^2-5x+6 în doi factori liniari.

**F.** Ecuatia este de gradul al doilea și x nu este izolat încă. Factorizează trinomul x^2-5x+6 în doi factori liniari.

**G.** Factor the trinomial x^2-5x+6 into two linear factors.

## brack-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Ai o paranteză în ecuație, iar x nu este izolat încă. Aplică metoda de a elimina parantezele prin distribuire.

**B.** Pentru a izola x, trebuie să îndepărtezi parantezele. Încearcă să aduni termenii cu x și cei fără x pe părți diferite ale ecuației.

**C.** Ai observat că există o paranteză în ecuație și variabila x nu este izolată încă. Trebuie să aplici regula distributivă pentru a elimina paranteza.

**D.** Scopul este să rezolvi în raport cu x. Există o paranteză, iar x nu este încă izolat.

**E.** Încearcă să ridici paranteza din partea stângă.

**F.** Începe prin deschiderea parantezei pentru a simplifica ecuația și a te apropia de izolarea lui x.

**G.** Încă ai o înmulțire de paranteză de făcut. Încearcă să elimină parantezele din ecuație.

## brack-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Pentru a rezolva ecuația, începe prin a elimina paranteza din termenul de stânga, apoi grupează termenii asemenea.

**B.** Elimină mai întâi paranteza, apoi grupează termenii asemenea.

**C.** Încearcă să eliminai paranteza în primul rând, apoi grupează termenii asemenea.

**D.** Începe prin a deschide paranteza din ecuație, apoi adună termenii similari pentru a simplifica expresia.

**E.** Încearcă să elimini paranteza în prima etapă, apoi grupează termenii asemenea.

**F.** Pentru a izola x, mai întâi elimină paranteza și apoi adună termenii asemănători.

**G.** Începe prin eliminarea parantezei din ecuație, folosind regulile de distributivitate.

## brack-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `3(x-2)=2x+1`
CAS verdicts: none. Ladder builds on step 1. Goal status: there is a bracket, and x is not isolated yet.
Hidden from the model and the student: next step `3x-6=2x+1`, answer `x=7`.

**A.** Încearcă să eliminăm paranteza din partea stângă prin distribuirea numărului de în fața ei.

**B.** Distribuie 3 peste paranteza din stânga.

**C.** Distribute 3 over the bracket on the left side.

**D.** Încearcă să aplici proprietatea de distribuție pentru a elimina paranteza din partea stângă.

**E.** Pentru a rezolva ecuația, începe prin a distribui numărul 3 peste termenii din paranteză de la stânga. După aceea, grupează termenii asemenea pentru a izola x.

**F.** Începe prin a dezvolta paranteza de la stânga, aplicând distribuția numărului 3 peste termenii din interior.

**G.** Începe prin a distribui 3 la paranteza din stânga, apoi adună termenii similari.

## frac-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Pentru a rezolva ecuația pentru x, trebuie să aduni termenii cu x. Aplicați cel mai mic multiplu comun al numitorilor pentru a elimina fracțiile.

**B.** Începe prin a aduna fracțiile care conțin variabila x pentru a simplifica ecuația.

**C.** Pentru a izola x, trebuie să aduni cele două părți cu x.

**D.** Termenul cu x este distribuit pe două fracții și nu este izolat încă. Încearcă să aduni aceste fracții pentru a simplifica ecuația.

**E.** Variabila ta este distribuită în două fracții. Încearcă să aduni acele fracții.

**F.** Variabila x este distribuită în două fracții, deci trebuie să o aduci la un singur termen.

**G.** Scopul este să rezolvi în raport cu x. x apare în două fracții și nu este încă izolat.

## frac-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Adu fracțiile la același numitor și adună-le.

**B.** Pentru a rezolva ecuația, aduce fracțiile la un numitor comun și le aduni.

**C.** Pentru a rezolva ecuația, începe prin a aduce fracțiile la același numitor comun și apoi adună-le.

**D.** Pentru a rezolva această ecuație, trebuie să aduci fracțiile la un numitor comun și să le aduni.

**E.** Pune la numitor comun frațiile pentru a aduna termenii cu x.

**F.** Pentru a rezolva ecuația, adu frații la un numitor comun și adună-i.

**G.** Pentru a aduna aceste fracții, trebuie să le aduci la un numitor comun. Ce numitor comun poți folosi?

## frac-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\frac{x}{2}+\frac{x}{3}=10`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is spread over two fractions and is not isolated yet.
Hidden from the model and the student: next step `\frac{5x}{6}=10`, answer `x=12`.

**A.** Pentru a aduna fracțiile, trebuie să le aduceți la un numitor comun. Încercați să adunați cele două fracții folosind numitorul comun 6.

**B.** Pentru a rezolva ecuația, adună cele două fracții cu numitorul comun 6.

**C.** Adună cele două fracții având numitorul comun 6.

**D.** Pentru a izola x, adună cele două fracții transformându-le la un numitor comun de 6.

**E.** Pentru a rezolva ecuația, trebuie să aduni cele două fracții folosind numitorul comun de 6.

**F.** Pentru a combina fracțiile, găsește un numitor comun pentru cele două fracții cu x. Încearcă să folosești 6 ca numitor comun.

**G.** Pentru a rezolva ecuația, adună cele două fracții transformându-le la numitor comun 6.

## rearr-r1-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 1.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Scopul este să exprimi x în funcție de y. x nu este încă izolat.

**B.** Pentru a rezolva ecuația în funcție de y, izolează variabila x din ecuația y = 2x + 3.

**C.** Pentru a rezolva ecuația pentru x în funcție de y, trebuie să izolezi variabila x. Începe prin a scădea 3 din ambele părți ale ecuației.

**D.** Pentru a izola x, trebuie să rearanjezi ecuația. Ce operație poți aplica pentru a muta termenul care conține x?

**E.** Nu ai izolat încă x. Încearcă să folosești metoda de rearanjare.

**F.** Începe prin a izola termenul cu x în ecuația dată.

**G.** Pentru a izola x, împărțiți ambele părți ale ecuației la 2.

## rearr-r2-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 2.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Pentru a izola x, trebuie să anulezi operațiile din ecuație în ordine inversă, lăsând y ca o variabilă.

**B.** Pentru a găsi x în funcție de y, începe prin a inversa operațiile din ecuație, pornind de la cea mai simplă.

**C.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă, lăsând y ca o variabilă.

**D.** Pentru a izola x, anulează operațiile din ordine inversă, păstrând y ca literă.

**E.** Pentru a izola x, anulează operațiile din ordinea inversă, păstrând y ca literă. Începe prin scăderea lui 3 din ambele părți.

**F.** Pentru a izola x în ecuația y = 2x + 3, trebuie să inversezi operația de înmulțire cu 2.

**G.** Izolează x anulând operațiile în ordine inversă, păstrând y ca literă.

## rearr-r3-ro

Goal: solve for x in terms of y. Language of the hints: Romanian. Rung 3.
Student steps: (1) `y=2x+3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=y-3`, answer `x=\frac{y-3}{2}`.

**A.** Pentru a izola x, începe prin a elimina termenul adunat din partea stângă.

**B.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației.

**C.** Pentru a izola x, scade 3 din ambele părți ale ecuației.

**D.** Pentru a izola x, începe prin a anula adunarea din partea dreaptă. Aplică operația de scădere pe ambele părți.

**E.** Trebuie să scazi 3 din ambele părți pentru a izola x.

**F.** Pentru a izola x, începe prin a scădea 3 din ambele părți ale ecuației y=2x+3.

**G.** Scade 3 din ambii membri.

## ineq-r1-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Pentru a izola x, trebuie să aplici o operație la ambele părți ale inegalității.

**B.** Pentru a izola x, trebuie să împarți ambii membri ai inegalității cu -2. Întreabă-te: ce se întâmplă cu semnul inegalității când împarți cu un număr negativ?

**C.** Pentru a rezolva inegalitatea -2x > 6, trebuie mai intai sa elimini parantezele.

**D.** Începe prin a izola variabila x în partea stângă a inecuației.

**E.** Scopul este să rezolvi inecuația în raport cu x. x nu este încă izolat.

**F.** Pentru a rezolva inegalitatea, trebuie să izolezi variabila x. Împarte ambii membri ai inegalității -2x > 6 prin -2, reamintindu-ți că inegalitatea se inversează când împarți cu un număr negativ.

**G.** Nu ai izolat încă variabila x. Încearcă să aplici o operație pentru a izola x.

## ineq-r2-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Pentru a rezolva inegalitatea -2x > 6, imparte ambele parti la coeficientul lui x, care este -2. Reaminteste-ti ca, atunci cand imparti sau inmultesti cu un numar negativ, semnul inegalitatii se schimba.

**B.** Pentru a izola x, trebuie să împărți ambele părți la coeficientul lui x. Nu uita că împărțirea la un număr negativ schimbă sensul inegalității.

**C.** Inegalitatea ta este -2x > 6. Pentru a izola x, trebuie să împarti ambii membri ai inegalității prin coeficientul lui x, dar nu uita că împărțirea cu un număr negativ inversează sensul inegalității.

**D.** Pentru a rezolva inegalitatea, împarte ambii membri la coeficientul lui x. Reamintește-ți că împărțirea la un număr negativ inversează semnul inegalității.

**E.** Pentru a izola x, trebuie să împărți ambele părți la coeficientul lui x. Reține că împărțirea la un număr negativ schimbă sensul inegalității.

**F.** Împarte ambii membri la coeficientul lui x. Împărțirea la un număr negativ inversează sensul inegalității.

**G.** Pentru a izola x, împarte ambele părți ale inegalității la coeficientul lui x, ținând cont că semnul inegalității se va inversa deoarece împarți la un număr negativ.

## ineq-r3-ro

Goal: solve the inequality for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Pentru a izola x, trebuie să împărți ambele părți la coeficientul lui x și să inversezi semnul inegalității.

**B.** Pentru a izola x, împarteți ambii membri ai inecuației prin coeficientul lui x și schimbați sensul inegalității, deoarece împărțiți la un număr negativ.

**C.** Trebuie să împărți ambele părți la coeficientul lui x și să inversezi semnul inegalității. Ce se întâmplă când împărți la un număr negativ?

**D.** Împarte ambii membri la -2 și inversează sensul inegalității.

**E.** Trebuie să împarți ambele părți ale inegalității la coeficientul lui x, dar ai uitat să inversezi semnul inegalității.

**F.** Pentru a izola x, împarteți ambele părți ale inegalității la -2 și inversați semnul relației.

**G.** Pentru a izola x, împarte ambii membri inegalității la -2 și nu uita să schimbi sensul inegalității, deoarece împarți la un număr negativ.

## sys-r1-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Pentru a rezolva sistemul, trebuie să folosești o metodă de eliminare sau substituție. Încearcă să aduni cele două ecuații.

**B.** Nu ai încă găsit valorile pentru x și y. Încearcă să folosești metoda de rezolvare a sistemului de ecuații.

**C.** Pentru a rezolva sistemul de ecuații, trebuie mai întâi să găsești relația dintre x și y.

**D.** Ai un sistem de două ecuații cu două necunoscute. Încearcă să folosești o metodă care să te ajute să găsești valorile lui x și y.

**E.** Ai nevoie să rezolvi sistemul de ecuații pentru a găsi valorile lui x și y. Începe prin a aplica metoda eliminării pentru a elimina o variabilă.

**F.** Sistemul de ecuații nu este încă rezolvat pentru x și y. Încearcă să aduni cele două ecuații pentru a elimina o variabilă.

**G.** Scopul este să rezolvi sistemul în raport cu x și y. Niciuna dintre necunoscute nu este încă aflată.

## sys-r2-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Pentru a rezolva sistemul, adună cele două ecuații pentru a elimina variabila y.

**B.** Pentru a rezolva sistemul, folosește metoda eliminării prin adunarea celor două ecuații pentru a anula variabila y.

**C.** Pentru a rezolva sistemul, adună sau scade ecuațiile pentru a elimina o variabilă.

**D.** Încearcă să folosești metoda eliminării pentru a elimina una dintre variabile. Ce ar trebui să faci cu cele două ecuații?

**E.** Folosește metoda eliminării pentru a încerca să elimini una dintre variabile, fie x sau y.

**F.** Folosește metoda reducerii: adună sau scade ecuațiile ca să elimini o necunoscută.

**G.** Pentru a găsi valorile lui x și y, poți încerca să elimine una dintre variabile prin adunarea sau scăderea ecuațiilor date.

## sys-r3-ro

Goal: solve the system for x and y. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\begin{cases}x+y=5\\x-y=1\end{cases}`
CAS verdicts: none. Ladder builds on step 1. Goal status: neither x nor y is known yet.
Hidden from the model and the student: next step `2x=6`, answer `x=3 \land y=2`.

**A.** Încearcă să adaugi cele două ecuații pentru a elimina variabila y.

**B.** Pentru a rezolva sistemul, adună cele două ecuații pentru a anula variabila y.

**C.** Pentru a elimina y, adună cele două ecuații.

**D.** Adună cele două ecuații ca să elimini pe y.

**E.** Pentru a elimina variabila y, încearcă să adaugi cele două ecuații.

**F.** Pentru a rezolva sistemul, adaugă cele două ecuații pentru a elimina variabila y.

**G.** Pentru a elimina variabila y, poți încerca să aduni cele două ecuații.

## log-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Scopul este să rezolvi în raport cu x. x nu este încă izolat. Pasul 2 merge într-un singur sens: ai combinat logaritmii, deci verifică la final soluțiile străine.

**B.** Ai combinat corect logaritmii, dar acum trebuie să izolezi variabila x. Asigură-te că verifici soluțiile obținute, deoarece operația cu logaritmi poate introduce soluții nevalide.

**C.** Ai combinat logaritmi, deci trebuie să verifici dacă există soluții suplimentare la final. În pasul 2, ai obținut ecuația: x*(x-2)=3.

**D.** Ai combinat corect logaritmii, dar acum trebuie să rezolvi ecuația rezultată pentru a găsi valorile posibile ale lui x. Nu uita să verifici dacă aceste soluții sunt valide în ecuația inițială.

**E.** Ai combinat logaritmuli corect, dar trebuie să verifici dacă soluțiile obținute sunt valide pentru expresia inițială.

**F.** Pentru a izola x, trebuie să rezolvi ecuația x(x-2)=3. Ai combinat deja logaritmii, așa că nu uita să verifici soluțiile suplimentare la final.

**G.** Ai combinat logaritmi, deci trebuie să verifici dacă există soluții suplimentare la final. În acest moment, variabila nu este izolată.

## log-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Pentru a izola x, trebuie să extindeți și să mutați totul pe o parte a ecuației, apoi să rezolvați ecuația pătratică.

**B.** Ai combinat corect logaritmii, dar acum trebuie să izolezi x. Adună termenii la un membru și aduce totul la forma unei ecuații de gradul doi.

**C.** Ai combinat logaritmuli corect, dar acum trebuie să verifici dacă soluțiile găsite sunt valide pentru expresia inițială.

**D.** Ai combinat corect logaritmii, dar acum trebuie să verifici dacă soluția găsită respectă condițiile de existență ale logaritmilor.

**E.** Ai combinat logaritmi, deci trebuie să verifici soluțiile la final. Acum, încearcă să aduci totul într-o formă pătratică.

**F.** Ai combinat logaritmi, așa că trebuie să verifici soluțiile finale. Acum, folosește metoda de a extinde și muta totul pe o singură parte pentru a rezolva ecuația de gradul doi.

**G.** Desfă parantezele și mută totul într-un membru, apoi rezolvă ecuația de gradul al doilea.

## log-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\ln x+\ln(x-2)=\ln 3`; (2) `x\cdot(x-2)=3`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you combined logarithms, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-2x-3=0`, answer `x=3`.

**A.** Ai combinat logaritmi, așa că verifică dacă există soluții suplimentare la final. Acum, extinde produsul și mută termenul în parte.

**B.** Acum trebuie să extindeți produsul și să mutați termenul 3 pe partea opusă pentru a obține o ecuație pătratică.

**C.** Pentru a izola x, trebuie să extindeți produsul și să scădeți 3 din ambele părți.

**D.** Ai combinat corect logaritmii, dar acum trebuie să dezvolți produsul și să mutați 3 la o parte pentru a obține o ecuație de gradul doi.

**E.** Desfă produsul și scade 3 din ambii membri.

**F.** Ai combinat corect logaritmii, dar acum trebuie să dezvoltai produsul și să muți termenul 3 pe cealaltă parte pentru a obține o ecuație de gradul al doilea.

**G.** Ai obținut ecuația quadratică, dar trebuie să verifici soluțiile pentru a te asigura că nu sunt extrase. Extinde produsul și adună termenii pentru a rezolva.

## sqrt-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Trebuie să rezolvi ecuația pentru x. Ai început corect, dar ai făcut o eroare la pasul 2. Ai înmulțit ambele părți cu (x-1)^2, ceea ce a creat o nouă ecuație. Verifică dacă există soluții suplimentare la final.

**B.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile finale pentru soluții suplimentare.

**C.** Scopul este să rezolvi în raport cu x. x nu este încă izolat. Pasul 2 merge într-un singur sens: ai ridicat la pătrat ambii membri, deci verifică la final soluțiile străine.

**D.** Ai ridicat ambele părți la pătrat, deci trebuie să verifici soluțiile finale pentru soluții suplimentare.

**E.** Ai păstrat ecuația echivalentă până acum, dar trebuie să izolezi mai întâi variabila x. Încearcă să descompui și să simplifici partea dreaptă a ecuației.

**F.** Ai pătrățimat ambele părți, ceea ce poate introduce soluții false; verifică acum fiecare soluție în ecuația inițială.

**G.** Ai ridicat la pătrat ambii membri pentru a elimina radicalul, dar acum trebuie să verifici dacă soluțiile găsite sunt valide, deoarece ridicarea la pătrat poate introduce soluții suplimentare.

## sqrt-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Ai păstrat ecuația echivalentă până acum, dar trebuie să izolezi mai întâi variabila x. Încearcă să dezvolți pătratul din dreapta și apoi să aduni toate termenii pe o parte a ecuației.

**B.** Ai ridicat la pătrat ambii membri, dar acum trebuie să dezvoltai pătratul și să aduni termenii pe o singură parte pentru a rezolva ecuația de gradul doi.

**C.** Ai pătrățit ambele părți, deci verifică soluțiile la final pentru a elimina pe cele false. Transformă ecuația într-o ecuație de gradul al doilea și rezolv-o.

**D.** Pentru a izola x, extinde pătratul și mută totul pe o parte, apoi rezolvă ecuația pătrată.

**E.** Desfă pătratul și mută totul într-un membru, apoi rezolvă ecuația de gradul al doilea.

**F.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile la final. Acum, extinde pătratul și mută totul pe o singură parte.

**G.** Acest pas este unidirecțional, deoarece ai ridicat la pătrat ambele părți. Trebuie să verifici soluțiile la final.

## sqrt-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\sqrt{x+1}=x-1`; (2) `x+1=(x-1)^2`
CAS verdicts: one-way. Ladder builds on step 2. Goal status: x is not isolated yet; step 2 is one-way: you squared both sides, so check for extra solutions at the end.
Hidden from the model and the student: next step `x^2-3x=0`, answer `x=3`.

**A.** Desfă (x-1)^2 și scade x+1 din ambii membri.

**B.** Pentru a izola x, extinde pătratul (x-1)^2 și scade x+1 de pe ambele părți.

**C.** Ai pătrățimat ambele părți, așa că verifică soluțiile la final pentru a elimina pe cele false. Extinde pătratul și mută totul într-o parte pentru a rezolva ecuația pătratică.

**D.** Ai păstrat ecuația echivalentă după pătrunderea pătratului, dar acum trebuie să dezvolți (x-1)^2 și să aduni sau scazi termenii pentru a obține o ecuație de gradul doi.

**E.** Trebuie să dezvolți pătratul și să muti termenii pentru a forma o ecuație pătratică.

**F.** Ai ridicat la pătrat ambele părți, deci trebuie să verifici soluțiile la final. Încearcă să dezvolți (x-1)^2 și să muti termenii în aceeași parte.

**G.** Ai ridicat la pătrat ambii membri, dar acum trebuie să dezvoltai expresia și să aduni termenii similari pentru a obține o ecuație de gradul al doilea.

## wrong-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pasul doi nu este echivalent cu pasul unu. Încearcă să aplici o operație pentru a izola termenul cu x.

**B.** Ai început bine, dar verifică cum ai trecut de la ecuația inițială la următoarea formă. Asigură-te că acțiunea aplicată păstrează echivalența ecuației.

**C.** Pasul 2 nu este echivalent cu pasul 1. Verifică din nou cum se obține o nouă ecuație din cea anterioară.

**D.** Pasul 2 nu este echivalent cu pasul 1; încearcă să transformi ecuația din pasul 1 corect pentru a obține o expresie echivalentă.

**E.** Pasul 2 nu rezultă din pasul 1. Indiciile pornesc de la pasul 1.

**F.** Pentru a ajunge la pasul 2, trebuie mai întâi să înmulțiți ambele părți ale ecuației cu 2.

## wrong-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Pentru a izola x, trebuie mai întâi să înlături parantezele. În pasul 2, ai uitat să înlături parantezele din expresia 2x.

**B.** Pentru a izola x, trebuie să anulezi operațiile în ordine inversă. Începe prin a scădea 3 din ambele părți pentru a obține 2x = 10.

**C.** Pasul 2 nu este echivalent cu pasul 1. Pentru a izola x, trebuie să anulezi operațiile în ordinea inversă.

**D.** Pornind de la pasul 1: izolează x anulând operațiile în ordine inversă.

**E.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă. Verifică dacă pasul doi este echivalent cu pasul unu.

**F.** Ai început bine, dar trebuie să iei în considerare și partea cu 3 când vei elimina termenul cu x. Încearcă să te gândești cum să compensezi adunarea cu 3.

**G.** Metoda este să izolezi x anulând operațiile în ordine inversă. Verifică dacă pasul tău este echivalent cu pasul anterior.

## wrong-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Ai scăzut 3 din ambele părți, dar rezultatul nu este echivalent cu ecuația inițială. Încearcă din nou să izolezi x prin a scădea 3 din ambii membri ai ecuației 2x+3=7.

**B.** Trebuie să scazi 3 din ambele părți pentru a izola termenul cu x.

**C.** Ai început bine, dar acum trebuie să elimineți termenul constant de pe partea stângă. Încearcă să scazi 3 din ambele părți ale ecuației.

**D.** Pentru a izola x, trebuie să anulezi operațiile din ordine inversă. Încearcă să scazi 3 din ambele părți.

**E.** Înainte de a trece la pasul următor, asigură-te că pasul tău este echivalent cu pasul anterior. Încearcă să scazi 3 din ambele părți.

**F.** Pornind de la pasul 1: scade 3 din ambii membri.

**G.** Pentru a izola x, trebuie să scapi 3 din ambele părți ale ecuației. Asta nu este echivalent cu pașii tăi actuali.

## dec-r1-ro

Goal: solve for x. Language of the hints: Romanian. Rung 1.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Pentru a rezolva ecuația pentru x, începe prin a combina termenii care conțin variabila x din partea stângă a ecuației.

**B.** Scopul este să rezolvi în raport cu x. x nu este încă izolat.

**C.** Nu ai izolat încă variabila x. Încearcă să grupezi termenii care conțin x.

**D.** Pentru a izola x, trebuie să combini termenii care conțin x din partea stângă.

**E.** Ai obținut o ecuație cu termenii de x la stânga. Acum trebuie să aduni coeficienții lui x pentru a simplifica expresia.

**F.** Începe prin a combina termenii care conțin variabila x pentru a simplifica ecuația.

**G.** Pentru a izola x, trebuie să înmulțiți ambele părți ale ecuației cu 2.

## dec-r2-ro

Goal: solve for x. Language of the hints: Romanian. Rung 2.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Combina termenii cu x și apoi împarte rezultatul la coeficientul lui x.

**B.** Pentru a izola x, combină termenii cu x și împarte rezultatul la coeficientul lui x.

**C.** Reduce termenii în x, apoi împarte la coeficient.

**D.** Încearcă să combini termenii asemenea din partea stângă. Apoi, împărțirea la coeficientul lui x va te ajuta să izolezi variabila.

**E.** Încearcă să combini termenii care conțin x, apoi împărțirea la coeficientul lui x.

**F.** Pentru a rezolva ecuația, adună termenii care conțin x, apoi împarte rezultatul la coeficientul lui x.

**G.** Începe prin combinarea termenilor asemănători care conțin x pentru a simplifica ecuația.

## dec-r3-ro

Goal: solve for x. Language of the hints: Romanian. Rung 3.
Student steps: (1) `0,5x+0,25x=3`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `0,75x=3`, answer `x=4`.

**A.** Ai adunat deja termenii cu x, acum trebuie să împarți ambii membri ai ecuației la coeficientul lui x pentru a izola x.

**B.** Încearcă să aduni termenii care conțin x din partea stângă a ecuației.

**C.** Pentru a izola x, adună termenii cu x: 0,5x și 0,25x.

**D.** Încearcă să aduni termenii care conțin x din partea stângă a ecuației.

**E.** Pentru a izola variabila x, adună termenii similari care conțin x din ecuația ta.

**F.** Începe prin combinarea termenilor asemănători care conțin x. Adună valorile coeficienților lor.

**G.** Adună cei doi termeni în x: 0,5x și 0,25x.

## dom-r1-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 1.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Expresia nu este încă simplificată, deoarece este nedefinită unde numitorul este zero.

**B.** Încearcă să simplifici fracția prin factorizarea numitorului și numitorului, dacă este posibil.

**C.** Pentru a simplifica expresia, trebuie să o împarți la diferența a două pătrate.

**D.** Pentru a simplifica expresia, trebuie să elimeni factorul comun din numărător și numitor, dar să ții cont de condiția ca numitorul să nu fie zero.

**E.** Expresia nu este încă simplificată și este nedefinită unde numitorul este zero. Încearcă să descompui numărătorul în factori pentru a vedea dacă se pot simplifica cu numitorul.

**F.** Scopul este să simplifici expresia. Nu este încă simplificată și nu este definită acolo unde numitorul este zero.

**G.** Expresia nu este încă simplificată, deoarece este nedefinită acolo unde numitorul este zero. Încearcă să simplifici fracția.

## dom-r2-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 2.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Descompune numărătorul, apoi simplifică factorul comun, ținând cont unde numitorul este zero.

**B.** Încearcă să factorizezi numărătorul și apoi să anulezi factorul comun, dar fii atent la unde numitorul este zero.

**C.** Factorizează numărătorul expresiei și anulează factorul comun cu numitorul, ținând cont de unde expresia este nedeterminată.

**D.** Încearcă să descompui numitorul și numitorul pentru a vedea dacă există un factor comun care poate fi anulat. Fii atent la valorile lui x pentru care expresia nu este definită!

**E.** Factor the numerator to find the common factor with the denominator, then cancel them while noting where the expression is undefined.

**F.** Încearcă să factorizezi numărătorul, apoi să anulezi factorul comun, dar nu uita să menționezi unde este numitorul zero.

**G.** Expresia nu este simplificată încă și este nedefinită unde numitorul este zero. Factorează numitorul și apoi elimină factorul comun, notând unde numitorul este zero.

## dom-r3-ro

Goal: simplify the expression. Language of the hints: Romanian. Rung 3.
Student steps: (1) `\frac{x^2-1}{x-1}`
CAS verdicts: none. Ladder builds on step 1. Goal status: the expression is not simplified yet; it is undefined where the denominator is zero.
Hidden from the model and the student: next step `\frac{(x-1)(x+1)}{x-1}`, answer `x+1`.

**A.** Factor the numerator x^2-1 as a difference of squares to simplify the expression.

**B.** Descompune numărătorul x^2-1 ca diferență de pătrate.

**C.** Trebuie să factorizezi numărătorul ca diferență de pătrate.

**D.** Începe prin a factoriza numitorul din expresie, folosind formula diferenței pătratelor.

**E.** Încearcă să factorizezi numărătorul ca o diferență de pătrate.

**F.** Încearcă să factorizezi numărătorul, x^2-1, folosind diferența de pătrate.

**G.** Factorize numărătorul x^2-1 ca o diferență de pătrate, apoi simplifică expresia ținând cont de condițiile de existență.

## lin2-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** To solve for x, you need to isolate the variable. Start by subtracting 3 from both sides of the equation 2x+3=7.

**B.** You have the equation 2x+3=7, but x is not isolated yet. Use the subtraction method to apply the inverse operation of addition.

**C.** You need to isolate x by undoing the addition of 3. Subtract 3 from both sides of the equation.

**D.** The goal is to solve for x. x is not isolated yet.

**E.** You need to get x by itself. Try subtracting 3 from both sides of the equation.

**F.** You are not done solving for x yet. Try isolating the variable.

**G.** Your equation has x combined with other numbers. Try to get x by itself on one side.

## lin2-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** To solve for x, you need to isolate it by undoing the operations in reverse order. Start by subtracting 3 from both sides of the equation 2x+3=7.

**B.** To solve for x, you need to isolate x by undoing the operations in reverse order. Start by undoing the addition of 3 by subtracting 3 from both sides.

**C.** To get x by itself, you need to undo the operations in reverse order. What operation should you apply first?

**D.** To solve for x, isolate it by undoing the operations in reverse order. Start by subtracting 3 from both sides of the equation 2x+3=7.

**E.** Isolate x by undoing the operations in reverse order.

**F.** To solve for x, reverse the operations applied to it. Start by undoing the addition of 3.

**G.** To solve for x, you need to undo the operations in reverse order. What operation should you apply to both sides of the equation?

## lin2-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `2x+3=7`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Subtract 3 from both sides.

**B.** To isolate x, subtract 3 from both sides of the equation.

**C.** Subtract 3 from both sides to isolate x.

**D.** To start isolating x, what operation should you perform on both sides of the equation?

**E.** To solve for x, start by removing the constant term on the left side by performing the same operation on both sides of the equation.

**F.** To get x by itself, you need to undo the addition first. Try subtracting 3 from both sides of the equation.

**G.** To solve for x, subtract 3 from both sides of the equation 2x+3=7 to isolate the term with x.

## quad-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Since this is a quadratic equation, you'll need to use a specific method to solve for x.

**B.** You have a quadratic equation to solve. Try to rewrite it so that one side equals zero and the other side is a product of factors involving x.

**C.** To solve for x, you need to factor the quadratic equation x^2-5x+6=0.

**D.** Since this is a quadratic equation, you can use factoring to solve for x.

**E.** Since the equation is quadratic and x is not isolated yet, you can solve it by factoring the quadratic expression.

**F.** Since the equation is quadratic and x is not isolated yet, you should factor the quadratic expression to solve for x.

**G.** The goal is to solve for x. The equation is quadratic and x is not isolated yet.

## quad-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Factor the quadratic, then set each factor to zero.

**B.** Since the equation is quadratic and x is not isolated yet, factor the quadratic expression and then set each factor to zero.

**C.** Since this is a quadratic equation, try factoring it first. Then, set each factor equal to zero.

**D.** Your equation is quadratic. Try to factor it into two binomials that multiply to give the original expression.

**E.** Since the equation is quadratic and x is not isolated, factor the quadratic expression and set each factor to zero to solve for x.

**F.** Since this is a quadratic equation, try factoring it first. Then, you can set each factor equal to zero.

**G.** Factor the quadratic equation x^2-5x+6=0 to find the values of x.

## quad-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `x^2-5x+6=0`
CAS verdicts: none. Ladder builds on step 1. Goal status: the equation is quadratic and x is not isolated yet.
Hidden from the model and the student: next step `(x-2)(x-3)=0`, answer `x=2 \lor x=3`.

**A.** Factor the trinomial x^2-5x+6 into two linear factors.

**B.** Factor the trinomial x^2-5x+6 into two linear factors.

**C.** Since this is a quadratic equation, try factoring the trinomial first. What two binomials multiply to give you x^2-5x+6?

**D.** Your equation is quadratic, so try to factor it into two binomials that multiply to give the original expression.

**E.** Since the equation is quadratic and x is not isolated yet, factor the trinomial x^2-5x+6 into two linear factors, then set each factor to zero.

**F.** Since this is a quadratic equation, try factoring the trinomial into two linear factors.

**G.** Since the equation is quadratic and x is not isolated, factor the trinomial x^2-5x+6 into two linear factors.

## ineq-r1-en

Goal: solve the inequality for x. Language of the hints: English. Rung 1.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** To solve the inequality for x, you need to isolate the variable. Remember to divide both sides by the coefficient of x.

**B.** The goal is to solve the inequality for x. x is not isolated yet.

**C.** You need to isolate x in the inequality. Try dividing both sides by -2.

**D.** You need to solve the inequality ≤-2x>6≤ for x.

**E.** Your inequality has a variable on both sides. Try to move the term with x to one side to isolate it.

**F.** You need to isolate x to solve the inequality. What operation should you apply to both sides?

**G.** You have the inequality -2x > 6, but x is not isolated yet. To proceed, divide both sides by -2 and remember to reverse the inequality sign.

## ineq-r2-en

Goal: solve the inequality for x. Language of the hints: English. Rung 2.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** To isolate x, divide both sides by -2 and remember to reverse the inequality sign.

**B.** Divide both sides by the coefficient of x. Dividing by a negative number reverses the inequality sign.

**C.** You need to isolate x by dividing both sides by the coefficient of x. Remember that when you divide by a negative number, you must reverse the inequality sign.

**D.** You have an inequality involving x. To isolate x, consider dividing both sides by the coefficient of x, but remember how this affects the inequality sign.

**E.** To solve the inequality ≠-2x≠6, divide both sides by ∐2. Remember that dividing by a negative number reverses the inequality sign.

**F.** Remember that when you divide both sides by a negative number, you need to reverse the inequality sign.

**G.** To solve the inequality, divide both sides by the coefficient of x. Remember that dividing by a negative number reverses the inequality sign.

## ineq-r3-en

Goal: solve the inequality for x. Language of the hints: English. Rung 3.
Student steps: (1) `-2x>6`
CAS verdicts: none. Ladder builds on step 1. Goal status: x is not isolated yet.
Hidden from the model and the student: next step `x<-3`, answer `x<-3`.

**A.** Divide both sides by -2 and reverse the inequality sign.

**B.** To isolate x, divide both sides of the inequality by the coefficient of x, but remember to reverse the inequality sign when dividing by a negative number.

**C.** Remember that when you divide both sides by a negative number, you must reverse the inequality sign. Try dividing both sides by -2.

**D.** To solve the inequality, divide both sides by -2 and remember to reverse the inequality sign.

**E.** To isolate x, divide both sides by -2 and remember to reverse the inequality sign.

**F.** To solve the inequality ≠x>6, divide both sides by -2 and reverse the inequality sign.

**G.** To isolate x, you need to divide both sides by the coefficient of x and remember to reverse the inequality sign.

## wrong-r1-en

Goal: solve for x. Language of the hints: English. Rung 1.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Check if the second equation is equivalent to the first one. You need to perform an operation on both sides of the equation.

**B.** Your step 2 does not follow from step 1. Check your arithmetic to ensure the equation remains equivalent.

**C.** You need to undo the second operation to solve for x. Start by subtracting 3 from both sides.

**D.** Check if the second equation is equivalent to the first one. You should use the method of isolating the variable.

**E.** Step 2 doesn't follow from step 1. The hints build on step 1.

**F.** You started with the correct equation, but how can you get from 2x + 3 = 7 to 2x = 10? Think about what operation you can use to isolate the term with x.

**G.** Your second step does not follow from the first. Remember that to isolate x, you must perform the same operation on both sides of the equation.

## wrong-r2-en

Goal: solve for x. Language of the hints: English. Rung 2.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** Your second step does not follow from the first. Remember to isolate x by undoing the operations in reverse order.

**B.** Your step 2 does not follow from step 1. To isolate x, undo the operations in reverse order.

**C.** Starting from step 1: isolate x by undoing the operations in reverse order.

**D.** When you moved the constant term, the equation is no longer equivalent. Try isolating x by undoing the operations in reverse order.

**E.** You started correctly by isolating the term with x, but check how you moved the constant term to the other side—did you keep the equation balanced?

**F.** You need to undo the subtraction of 3 to isolate x. Start by subtracting 3 from both sides.

**G.** When you move from the first equation to the second, the steps are not equivalent. Try isolating x by undoing the operations in reverse order.

## wrong-r3-en

Goal: solve for x. Language of the hints: English. Rung 3.
Student steps: (1) `2x+3=7`; (2) `2x=10`
CAS verdicts: not equivalent. Ladder builds on step 1. Goal status: step 2 doesn't follow from step 1; the ladder builds on step 1.
Hidden from the model and the student: next step `2x=4`, answer `x=2`.

**A.** You subtracted 3 from both sides, but you should have done that first to isolate the term with x. Try undoing the addition before dealing with the coefficient of x.

**B.** To isolate x, you need to undo the addition first. Try subtracting 3 from both sides of the equation.

**C.** You made an error in the second step; remember to subtract 3 from both sides of the equation to keep it balanced.

**D.** Starting from step 1: subtract 3 from both sides.

**E.** You need to undo the operation you did to get from step 1 to step 2. Subtract 3 from both sides of the equation.

**F.** To isolate x, you need to undo the operations in reverse order. Try subtracting 3 from both sides.

**G.** To solve for x, you need to isolate it by undoing the operations in reverse order. First, subtract 3 from both sides of the equation.


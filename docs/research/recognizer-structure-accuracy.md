# Recognizer accuracy by structure type, and what each model can emit

Research note, 2026-10-23, for spike 2 ([#12](https://github.com/george-vrancianu/aequate/issues/12)). Question: how does handwritten-math recognition accuracy change with **structure type**, and which structures do the candidate models (Pix2Text MFR 1.5, TexTeller 3.0, BTTR) cover in their vocabulary and training data at all?

Builds on `docs/research/math-recognizers.md` (branch `research/math-recognizers`) and [`recognition-compute-split.md`](recognition-compute-split.md). Those notes already cover licenses, sizes and overall CROHME ExpRate, so this note does not repeat them. Every claim links to a source. **Unverified** marks anything I could not confirm in a primary source. *(assessment)* marks my own reasoning. I did not run any model. The vocabulary checks come from the tokenizer and dictionary files.

---

## Conclusion (TL;DR)

1. **Accuracy depends more on depth and length than on which symbols appear.** No paper reports ExpRate separately for fractions, roots, scripts and so on. They report results by nesting depth, structural complexity or length, and accuracy drops steeply on every one of those axes:
   - On PosFormer's MNE set, CoMER falls from 59.7% at nesting level 1 to 37.2% at level 2 and 24.0% at level 3 ([PosFormer Table 7](https://arxiv.org/html/2407.07764)).
   - On HME100K, BTTR scores 77.6% on Easy, 65.3% on Moderate and 46.0% on Hard ([SAN Table 3](https://ar5iv.labs.arxiv.org/html/2203.01601)).
2. **Most errors are symbol errors, not layout errors.** In CROHME 2019 the best system gets 80.73% of expressions fully right but 91.49% of layouts right when symbol labels are ignored ([CROHME 2019 Table II](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)). BTTR's structure rate is about 17 points above its ExpRate (71.40 vs 53.96 on CROHME 2014; [BTTR Table 1](https://arxiv.org/html/2105.02412)). So a correction UI mostly has to fix individual symbols: 2/z, 0/o, 1/i, 1/n, 3/z ([Uni-MuMER Table 4](https://arxiv.org/html/2505.23566v3)).
3. **Coverage separates the candidates sharply:**
   - **BTTR** has a 110-token CROHME dictionary. It has no matrix, `cases`, `aligned`, line break, `&`, `\mathrm`, `\ln`, `:`, `%`, `\circ`, Z or Q, and no lowercase δ/ε/ω ([dictionary.txt](https://github.com/Green-Wood/BTTR/blob/main/bttr/datamodule/dictionary.txt)). It cannot emit a system of equations, a matrix or units.
   - **Pix2Text MFR 1.5** (vocabulary of 1,868 tokens) and **TexTeller** (15,000 tokens) both use byte-level BPE tokenizers, so they can spell any LaTeX string. Both vocabularies have learned tokens for `frac`, `sqrt`, `matrix`, `cases`, `aligned`, `array`, `int`, `sum`, `lim`, Greek letters, `mathrm` and `operatorname` (§2.1).
4. **No candidate is known to have been trained on Romanian school notation:** `tg`/`ctg`, `:` used for division, a decimal comma, or the European long-division layout. Long division in particular is a 2-D layout that none of the training sets contain *(assessment)*. TexTeller's handwritten data is only 1.5% of its 78M training pairs ([dataset viewer](https://datasets-server.huggingface.co/size?dataset=OleehyO/latex-formulas-80M)). Pix2Text does not publish what share of its data is handwritten (**Unverified**).
5. **Post-processing is needed whatever model wins:**
   - Map `tg`/`ctg`, `:`, and `sin` written without a backslash to SymPy-parsable forms.
   - Resolve the decimal-comma ambiguity (`3,5` vs `3, 5`) from context.

   MathWriting-style labels write `\sin` as plain `sin` ([MathWriting §4.1](https://arxiv.org/html/2404.10690v1)), and TexTeller's handwritten subset contains labels like `sin(\frac{\pi y}{b})` ([first rows](https://datasets-server.huggingface.co/first-rows?dataset=OleehyO/latex-formulas-80M&config=handwritten_online&split=train)). `parse_latex` would read that `sin` as s·i·n *(assessment)*.
6. **Spike 2 test set:** use 12 categories. Score each category with ExpRate, a structure rate and a CAS-equivalence rate, and report confidence intervals. With 4–5 samples per category the 95% interval is about ±30 points (§5). Read the 50-sample run per category as a smoke test. Use CROHME 2019 bucketed by structure for the categories it covers, and collect about 20 samples per Romanian-notation category to make decisions on.

---

## 1. Benchmark breakdowns by structure and complexity

### 1.1 Nesting depth: MNE (PosFormer, ECCV 2024)

Definitions:
- The structural complexity of an expression is "the maximum nested levels of its substructures" ([PosFormer App. A.1](https://arxiv.org/html/2407.07764)).
- The substructures are superscript/subscript, fraction, radical and special operators ([PosFormer Fig. 2](https://arxiv.org/html/2407.07764)).
- N1 (1,875 images) and N2 (304) come from the CROHME test sets. N3 (1,464) started as 10 CROHME images and was expanded with public documents and real handwritten homework ([PosFormer §4.1](https://arxiv.org/html/2407.07764)).
- Level 4 was dropped because it makes up only 0.2% of public data (same).

ExpRate (%), [PosFormer Table 7](https://arxiv.org/html/2407.07764) and [Uni-MuMER Tables 20–21](https://arxiv.org/html/2505.23566v3):

| Model | N1 | N2 | N3 |
|---|---|---|---|
| SAN | – | – | 8.61 |
| CAN | – | – | 7.72 |
| CoMER | 59.73 | 37.17 | 24.04 |
| PosFormer | 60.59 | 38.82 | 34.08 |
| Uni-MuMER (Qwen2.5-VL-3B fine-tuned) | 70.08 | 55.59 | 38.53 |
| Uni-MuMER† (extra data) | 76.00 | 58.88 | 46.45 |

Uni-MuMER's table gives PosFormer 36.82 on N3, which is PosFormer's own "≤1 error" figure. I use the 34.08 from PosFormer's own table.

Fractions inside exponents appear in the PosFormer paper as a qualitative failure case: on `4^{x-\frac{1}{4}}`, CoMER's attention drifts ([PosFormer Fig. 5](https://arxiv.org/html/2407.07764)). The CROHME grammar explicitly allows a fraction as a superscript (`TERM_OR_BRACED_LR SUP FRACTION`, [CROHMELib grammar](https://gitlab.univ-nantes.fr/crohme/crohmelib/-/blob/master/grammar/00_HumanRedableGrammar4-revision2.txt)).

### 1.2 Length × complexity: HME100K Easy/Moderate/Hard (SAN, CVPR 2022)

The subsets are defined as follows ([SAN §5.5](https://ar5iv.labs.arxiv.org/html/2203.01601)):
- Easy: structural complexity 0–1 and fewer than 10 characters.
- Moderate: structural complexity 0–1 and 10–19 characters.
- Hard: everything else.

| HME100K test (n) | Easy (7,721) | Moderate (10,450) | Hard (6,436) | Total (24,607) |
|---|---|---|---|---|
| DWAP | 75.1 | 62.2 | 45.4 | 61.9 |
| DWAP-TD | 76.2 | 63.2 | 45.4 | 62.6 |
| **BTTR** | **77.6** | **65.3** | **46.0** | **64.1** |
| SAN | 79.2 | 67.6 | 51.5 | 67.1 |

Source: [SAN Table 3](https://ar5iv.labs.arxiv.org/html/2203.01601). HME100K is camera-captured, has about 10k writers and 245 symbol classes ([SAN Table 1](https://ar5iv.labs.arxiv.org/html/2203.01601)).

### 1.3 Expression length (CoMER) and branching complexity (TAMER, Uni-MuMER)

- **CoMER Fig. 3, CROHME 2014, by LaTeX length:** CoMER "can reach even 5× than 'BTTR (baseline)' when recognizing sequences longer than 50" and is far ahead for sequences longer than 20 ([CoMER §4.5](https://arxiv.org/html/2207.04410)). The per-bin numbers are only in the figure. *(assessment)* This means BTTR's accuracy on long lines, such as a full worked step, is far below its headline 54%.
- **TAMER:** complexity here is "the maximum number of nodes that have more than one child node across all search paths". TAMER's gain over CoMER grows to 5.31 points at complexity ≥5 on CROHME 2014 ([TAMER Fig. 5](https://arxiv.org/html/2408.08578)). On the most complex expressions, the share of outputs with correctly matched brackets is 77.14% for CoMER, 81.63% for ICAL and above 92.65% for TAMER on CROHME 2014 ([TAMER App. D](https://arxiv.org/html/2408.08578)). Unbalanced braces make the output unparseable, so this measures how often SymPy can parse the result at all *(assessment)*.
- **Uni-MuMER:** "The Vanilla model experiences a significant degradation in accuracy as structural complexity increases". The numbers are only in a figure ([Fig. 5a](https://arxiv.org/html/2505.23566v3)).

### 1.4 Structure rate vs. expression rate (CROHME)

CROHME 2019 "Structure Correct" counts the layout tree as right while ignoring symbol labels ([CROHME 2019 §VI](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)).

| CROHME 2019 test (1,199 expr) | ExpRate | ≤1 symbol err | ≤2 | Structure rate |
|---|---|---|---|---|
| USTC-iFLYTEK, strokes | 80.73 | 88.99 | 90.74 | 91.49 |
| MyScript, strokes | 79.15 | 86.82 | 89.82 | 90.66 |
| USTC-iFLYTEK, images | 77.15 | 86.82 | 88.99 | 89.49 |
| PAL-v2, images | 62.89 | 74.98 | 78.40 | 79.32 |

Source: [CROHME 2019 Table II](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf).

BTTR's own StruRate is 71.40 / 69.40 / 70.06 on CROHME 2014 / 2016 / 2019, against ExpRate 53.96 / 52.31 / 52.96 ([BTTR Table 1](https://arxiv.org/html/2105.02412)). The organizers add that "the most common error is missing symbols … in most cases, there is a shift in the structure causing missing nodes" ([CROHME 2019 §VI](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)).

### 1.5 Matrices (CROHME 2014 Task 3)

Matrices were a separate, experimental CROHME 2014 task:
- 362 training matrices and 175 test matrices ([CROHME 2014 slides p.4](https://iapr.org/archives/icfhr2014/wp-content/uploads/2015/02/ICFHR2014-CROHME.pdf)).
- Every matrix has at least 2 rows or 2 columns and is bracketed by `()`, `[]` or `||` ([Task 3 page](https://www.isical.ac.in/~crohme/CROHME_tasks3.html)).

Results ([slides p.7](https://iapr.org/archives/icfhr2014/wp-content/uploads/2015/02/ICFHR2014-CROHME.pdf)):

| | Valencia (System I) | MyScript (System III) |
|---|---|---|
| Expression rate | 31.15 | 53.28 |
| Matrix recall | 73.14 | 92.57 |
| Row recall | 70.59 | 92.00 |
| Column recall | 50.84 | 69.16 |
| Cell recall | 55.35 | 71.07 |

Both systems find columns much less reliably than rows. The training sets later papers use (8,836 expressions for BTTR, [BTTR §5.2](https://arxiv.org/html/2105.02412)) are the Task 2 expressions, and BTTR's dictionary has no matrix tokens (§2.2). **Unverified:** whether later CROHME editions (2016, 2019, 2023) kept a matrix task.

### 1.6 Multi-line (M2E)

M2E is "a multi-line handwritten mathematical expression benchmark" with 79,979 training, 9,992 validation and 9,985 test images from papers, exercise books and handwriting ([PosFormer §4.1](https://arxiv.org/html/2407.07764), citing Yang et al., ACM MM 2023). ExpRate on M2E: BTTR 55.25, CoMER 56.20, PosFormer 58.33 ([PosFormer Table 3](https://arxiv.org/html/2407.07764)). Those BTTR and CoMER numbers come from models retrained on M2E. The public BTTR checkpoint cannot emit line breaks (§2.2). No paper I found reports `cases`/`aligned` separately.

### 1.7 What I did not find

- No paper reports ExpRate separately for fraction, root, script, integral/sum/limit or Greek-letter expressions. All breakdowns use depth, length or branching.
- The MathWriting paper's error analysis is qualitative only ([§2.3, Fig. 2](https://arxiv.org/html/2404.10690v1); see §3).

---

## 2. Symbol and structure coverage per candidate

### 2.1 Pix2Text MFR 1.5 and TexTeller 3.0 (tokenizer check)

Both tokenizers are byte-level BPE with the GPT-2 split regex (`tokenizer.json`: `"type": "BPE"`, pre-tokenizer `ByteLevel`, `use_regex: true`). Details:
- **Pix2Text:** 1,868 tokens and 1,607 merges ([tokenizer.json](https://huggingface.co/breezedeus/pix2text-mfr-1.5/blob/main/tokenizer.json); `vocab_size: 1868` in [config.json](https://huggingface.co/breezedeus/pix2text-mfr-1.5/blob/main/config.json)).
- **TexTeller:** 11,500 BPE tokens plus 3,500 added CJK characters, for a `vocab_size` of 15,000 ([tokenizer.json](https://huggingface.co/OleehyO/TexTeller/blob/main/tokenizer.json), [added_tokens.json](https://huggingface.co/OleehyO/TexTeller/blob/main/added_tokens.json), [config.json](https://huggingface.co/OleehyO/TexTeller/blob/main/config.json)).

Consequences *(assessment)*:
- The split regex separates `\` from the letters after it, so `\frac` is encoded as `\` + `frac`. Below, "Y" means the command name is a learned whole token.
- Byte-level BPE can encode any string, so "–" means the name is spelled from smaller pieces, not that it is impossible.
- A learned token shows the string was frequent in the tokenizer's training corpus. It does not show the model emits it correctly from handwriting.

| Token (command name) | P2T 1.5 | TexTeller | Notes |
|---|---|---|---|
| `frac`, `sqrt`, `int`, `iint`, `oint`, `sum`, `prod`, `lim`, `limits` | Y | Y | `\sqrt[n]` uses the `[` `]` tokens |
| `dfrac` | – | Y | |
| `begin`, `matrix`, `array`, `cases`, `aligned` | Y | Y | |
| `pmatrix`, `bmatrix`, `vmatrix`, `gathered` | – | Y | P2T has `align`; TexTeller does not |
| `&`, `\\` | Y | Y | needed for matrices and systems |
| `alpha … omega`, `Gamma`, `Delta`, `Sigma`, `Omega`, `varphi`, `varepsilon` | Y | Y | every Greek name I checked |
| `mathrm`, `operatorname`, `text`, `mathbf`, `mathbb`, `mathcal` | Y | Y | |
| `ce` (mhchem `\ce`) | Y | Y | ambiguous: the token can come from other text. **Unverified** that either model emits `\ce{}` |
| `rightleftharpoons`, `xrightarrow`, `longrightarrow` | Y | Y | chemistry arrows |
| `tan`, `cot`, `arcsin`, `arctan`, `ln`, `lg`, `log` | Y | Y | |
| `tg` | – | Y | origin unknown. Neither has `ctg`, `cotg` or `arctg` |
| `times`, `cdot`, `div`, `:`, `\%`, `circ` | Y | Y | `degree` only in TexTeller |
| `{,}` (TeX decimal comma) | – | – | TexTeller has `{,` and `,}` pieces. A bare `,` can't be told apart from a list comma |
| `cancel`, `longdiv` | – | – | nothing for crossing out or long division |
| units `kg`, `km`, `dm`, `ml` | – | Y | `cm`, `mm` in both. `mol` in neither |

Checked by me against the files above with a token lookup script.

**Training data share that is handwritten:**
- **TexTeller 3.0:** `en` 72,350,351 + `zh` 4,595,560 + `handwritten_online` 834,964 + `handwritten_nature` 340,626 = 78.1M rows, so **1.50% handwritten** ([dataset size API](https://datasets-server.huggingface.co/size?dataset=OleehyO/latex-formulas-80M)). The handwritten subset "was collected entirely from existing open source work, which includes all test sets" ([dataset card](https://huggingface.co/datasets/OleehyO/latex-formulas-80M)). The labels in `handwritten_online` have MathWriting-style normalization (`sin(` without a backslash, `\le`) ([first rows](https://datasets-server.huggingface.co/first-rows?dataset=OleehyO/latex-formulas-80M&config=handwritten_online&split=train)), which points to MathWriting as a source *(assessment)*. The README claims TexTeller 2.0 was strong on "complex multi-line formulas, and matrices" ([model card](https://huggingface.co/OleehyO/TexTeller)). An Apache-2.0 model `OleehyO/TexTeller_en` exists ([HF API](https://huggingface.co/api/models/OleehyO/TexTeller_en)). A commented-out README line calls it the benchmark model "trained from scratch and had its handwritten subset filtered based on the test set" ([README source](https://github.com/OleehyO/TexTeller/blob/main/README.md)). **Unverified**, because the line is hidden and the technical report was withdrawn. If true, it is the clean TexTeller to benchmark on CROHME.
- **Pix2Text MFR 1.5:** the handwritten share is **not published**. The model card says only "retrained using a dataset of mathematical formula images" ([model card](https://huggingface.co/breezedeus/pix2text-mfr-1.5)). The v1.5 article says v1.0 was weak on radical (√) images and "专门加入了对应的训练数据" ("specifically added the corresponding training data"), plus "更多来自真实场景的图片标注数据" ("more annotated images from real-world scenarios") ([v1.5 article](https://www.breezedeus.com/article/pix2text-model-1.5)). The author's 485-image test set comes from user uploads to the web service and "includes… formula groups and even matrices" ([model card](https://huggingface.co/breezedeus/pix2text-mfr-1.5)). It is not separated by handwriting.

### 2.2 BTTR (CROHME dictionary)

[`bttr/datamodule/dictionary.txt`](https://github.com/Green-Wood/BTTR/blob/main/bttr/datamodule/dictionary.txt) has 110 tokens, plus `<pad>`, `<sos>` and `<eos>` ([vocab.py](https://github.com/Green-Wood/BTTR/blob/main/bttr/datamodule/vocab.py)). The vocabulary is closed, so any token not listed cannot be emitted.

- **Has:** digits; all 26 lowercase letters; uppercase `A B C E F G H I L M N P R S T V X Y`; `\frac \sqrt ^ _ { } [ ] ( ) \{ \} |`; `\int \sum \lim \limits \log \sin \cos \tan`; `\alpha \beta \gamma \Delta \lambda \mu \phi \pi \sigma \theta`; `\times \div \cdot \pm \neq \leq \geq < > = \rightarrow \infty \prime \ldots \cdots \exists \forall \in`; `, . ! ' / + -`.
- **Lacks** *(read off the file)*:
  - structure: matrix and environment tokens, `&`, `\\`
  - functions: `\ln`, `\cot`
  - sets and fonts: `\mathrm`, `\text`, `\mathbb`, uppercase `D J K O Q U W Z`
  - Greek: lowercase `\delta \epsilon \omega \rho \tau`
  - punctuation and units: `:`, `%`, `\circ`, `;`

  For Romanian school work this means no ℤ/ℚ sets, no `ln`, no `ctg`, no degrees, and no `:` *(assessment)*.

### 2.3 CROHME official symbol set

- **Count and contents:** 101 classes ([CROHME 2014 slides p.4](https://iapr.org/archives/icfhr2014/wp-content/uploads/2015/02/ICFHR2014-CROHME.pdf); [CROHME 2019 §I](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)). The official list file [`listSymbolsPart4-revised.txt`](https://gitlab.univ-nantes.fr/crohme/crohmelib/-/blob/master/grammar/listSymbolsPart4-revised.txt) has 102 lines, with `g` listed twice, so 101 unique. I diffed the two files. The CROHME list equals BTTR's dictionary minus `\frac ^ _ { } \limits \cdot \cdots '`, with `\lt`/`\gt` in place of BTTR's `<`/`>`.
- **The fraction bar has no class of its own.** `\frac` is not in the list. *(assessment)* The bar must be labelled with the `-` class, which is the minus/fraction-bar confusion built into the data.
- **Decimal separator:** the grammar allows a dot or a comma: `DECIMALSEP -> DOT | COMMA` ([grammar](https://gitlab.univ-nantes.fr/crohme/crohmelib/-/blob/master/grammar/00_HumanRedableGrammar4-revision2.txt)). How often the comma form actually occurs in the data is **Unverified**.
- **Matrices:** not in the main expression task. A separate matrix grammar (`GramCROHMEpart4Mat.xml`, with `bmatrix`/`pmatrix`) and the Task 3 data exist for 2014 only (§1.5).
- **Neighbouring vocabularies:** CROHME23 has 105 tokens and MathWriting has 254, including `\begin{matrix}`, `:`, `\%`, `\circ` and `\rightleftharpoons`. MathWriting has no `\lim` command (functions are written as letters), no `\mathrm`/`\text` (normalized away) and no `\ce` ([MathWriting §2.1, §4, App. C, Table 6](https://arxiv.org/html/2404.10690v1)).

---

## 3. Confusable symbol pairs

| Pair | Evidence |
|---|---|
| 2 ↔ z | "Two of the main causes of mistakes are mixing up similar looking characters like 'z' and '2', and incorrectly nesting a subexpression like not placing it in a subscript or superscript" ([MathWriting §2.3](https://arxiv.org/html/2404.10690v1)) |
| 2↔z 1.40%, 0↔o 1.48%, 3↔z 0.74%, 1↔i 0.89%, 1↔n 0.74% | Top-5 letter–number confusions for a fine-tuned Qwen2.5-VL-3B on the CROHME average, totalling 5.25 ([Uni-MuMER Table 4](https://arxiv.org/html/2505.23566v3)) |
| 1, \|, l, `,`, x, X, `\times` | The CROHME 2014 output-format example shows a ranked candidate list `1, \|, l, COMMA, junk, x, X, \times` ([Task 1 page](https://www.isical.ac.in/~crohme/CROHME_tasks1.html)). It illustrates the format and is not measured data |
| `1`, `+`, `−`, `2` | Among the most frequently mis-recognized symbols for the top CROHME 2019 systems ([Table III](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)). The extracted table is partly garbled, so treat the ranking as approximate |
| `\underline{a}/b` vs `a/\overline{b}`, `\overline\omega` vs `\varpi`, `\dagger`/`\top`/T, `\binom` vs a 2-element matrix, `\Sigma` vs `\sum` | Cannot be told apart from ink alone ([MathWriting §6.2–6.3, Fig. 13](https://arxiv.org/html/2404.10690v1)) |
| minus vs fraction bar | Same CROHME class (§2.3). No measured rate found (**Unverified**) |
| x ↔ ×, Σ ↔ E, 0 ↔ O, 5 ↔ S, 9 ↔ g, `:` ↔ `÷` | No quantitative analysis found (**Unverified**). These are well-known handwriting ambiguities *(assessment)*. `:` vs `÷` matters especially for Romanian work |

---

## 4. Gaps for Romanian and European school notation

| Notation | P2T 1.5 | TexTeller | BTTR | Implication *(assessment)* |
|---|---|---|---|---|
| Decimal comma `3,5` | can emit `,` | can emit `,` | can emit `,` | No candidate separates a decimal comma from a list comma. Rule: digit-comma-digit with no space becomes a decimal inside an arithmetic context. Show it in the correction UI |
| `tg x`, `ctg x` | spelled from pieces | `tg` token | t·g as letters | Expect `tg` → `t g` or `\tan`. Rule: rewrite `tg`/`ctg`/`arctg` letter sequences to `\tan`/`\cot`/`\arctan` before `parse_latex` |
| `:` as division | `:` token | `:` token | **no `:`** | Rule: in a numeric context, `a : b` means `a / b`. BTTR cannot output it at all, so it would need fine-tuning with an expanded vocabulary |
| `·` multiplication dot | `cdot` | `cdot` | `\cdot` | covered |
| Long-division layout (European) | – | – | – | Not in any training set I found. Its 2-D layout has no standard LaTeX form. Recommend recognizing each line as plain arithmetic, or keeping it out of v1 |
| Systems (`cases`, accolade) | tokens exist | tokens exist | impossible | Handwritten examples are probably rare (only M2E is multi-line). Spike 2 must measure it. Fallback: recognize line by line and join in the app |
| Matrices / determinants | `matrix`, `array` | `pmatrix`, `vmatrix` … | impossible | CROHME matrix data is tiny (362 training matrices). MathWriting has matrices |
| `\ln`, ℤ/ℚ, degrees | yes | yes | **no** | another BTTR gap |
| Units (`\mathrm{cm}`) | `mathrm` | `mathrm` | no `\mathrm` | MathWriting strips `\mathrm`, so handwriting-trained models may output `cm` as c·m. Use a units dictionary in post-processing |
| Chemistry (`\ce{H2O}`) | **Unverified** | **Unverified** | impossible | Treat as out of scope for v1, or accept plain sub/superscripts (`H_{2}O`) |

Fine-tuning implications *(assessment)*:
- Pix2Text and TexTeller need no tokenizer change for these structures, only handwritten examples. BTTR needs a vocabulary extension and a new output layer.
- The highest-value data to collect is Romanian: `tg`/`ctg`, `:`, decimal commas, systems, and multi-step lines.
- Rewrite rules are cheap and deterministic. Put them in the parse stage, keyed by `parser_backend`, as in `recognition-compute-split.md` §2.2.

---

## 5. Proposed test-set design for spike 2 (#12)

Issue #12 scopes "50 collected samples" ([issue](https://github.com/george-vrancianu/aequate/issues/12)). The 95% Wilson interval on a 60% ExpRate is [23%, 88%] at n=5, [39%, 78%] at n=20 and [42%, 75%] at n=30 (my calculation). So the run has two tiers.

**Tier A (50 samples, required by #12):** 12 categories × 4–5 samples, written by at least 3 people on the target tablet. These samples are a smoke test and feed the correction-UI review.

**Tier B (decision-grade):**
- **B1:** CROHME 2019 test (1,199 expressions), bucketed automatically with regexes on the ground-truth LaTeX, for the categories CROHME covers.
- **B2:** about 20 own samples per Romanian-only category (rows 9–12), roughly 80 extra.
- Do not use CROHME numbers for TexTeller 3.0, because its training data contains the CROHME test sets. Use TexTeller_en if it proves clean.

| # | Category (example) | Tier A n | Tier B source |
|---|---|---|---|
| 1 | Linear arithmetic / equation (`2x+3=7`) | 4 | CROHME19 (no `\frac`, `\sqrt`, `^`, `_`) |
| 2 | Simple fraction (`\frac{a}{b}`) | 4 | CROHME19 `\frac`, depth 1 |
| 3 | Nested fraction / fraction in exponent | 4 | CROHME19 nested `\frac`, or `^{…\frac` |
| 4 | Superscripts vs subscripts, including `x_1^2` | 4 | CROHME19 `^`/`_` |
| 5 | Square and n-th roots | 4 | CROHME19 `\sqrt`, `\sqrt[` |
| 6 | Greek letters | 4 | CROHME19 Greek tokens |
| 7 | Integrals, sums, limits | 4 | CROHME19 `\int`/`\sum`/`\lim` |
| 8 | Matrix / determinant | 4 | own (CROHME has none) |
| 9 | System (`cases`) / multi-line aligned step | 5 | own |
| 10 | Decimal comma + `:` division | 5 | own |
| 11 | `tg`/`ctg`, `ln`, `lg`, degrees | 4 | own |
| 12 | Units / simple chemistry (`5\,\mathrm{cm}`, `H_2O`) | 4 | own |
| | **Total** | **50** | |

Also tag each sample with any confusable pair it contains (2/z, 1/l, 0/o, x/×, `:`/÷, −/fraction bar), so error counts can be grouped by pair across categories.

**Metrics per model and category:**
1. **ExpRate:** exact match after normalization. Strip spaces and `\left`/`\right`, use MathWriting-style synonym folding ([§4.1](https://arxiv.org/html/2404.10690v1)), and normalize function names. Also report ≤1 and ≤2 token errors, following the CROHME convention ([CROHME 2019 Table II](https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf)).
2. **Structure rate:** layout correct with symbol labels ignored. Either convert the LaTeX to symLG with the official CROHME 2019 tools ([LgEval / CROHMELib](https://gitlab.univ-nantes.fr/crohme/lgeval)), or, more cheaply, compare the LaTeX token sequences after replacing every symbol leaf with a placeholder *(assessment: an approximation of symLG)*. A large gap between structure rate and ExpRate means "fix symbols in the UI". A small gap with low ExpRate means "the model breaks layout".
3. **CAS-equivalence rate** (Aequate-specific): `parse_latex(pred)` is equal to `parse_latex(gt)` via SymPy, after the §4 rewrite rules. Report it with and without the rules to measure what post-processing recovers.
4. **Parse-failure rate:** the share of outputs SymPy cannot parse, for example unbalanced braces ([TAMER App. D](https://arxiv.org/html/2408.08578) shows this rate depends on the model).
5. Report the Wilson 95% CI next to every per-category rate.

---

## Sources

Papers and competition reports
- CROHME 2014 slides (Mouchère et al., ICFHR 2014): https://iapr.org/archives/icfhr2014/wp-content/uploads/2015/02/ICFHR2014-CROHME.pdf
- CROHME 2014 Task 1 / Task 3 pages: https://www.isical.ac.in/~crohme/CROHME_tasks1.html, https://www.isical.ac.in/~crohme/CROHME_tasks3.html
- CROHME 2019 + TFD (Mahdavi et al., ICDAR 2019): https://www.cs.rit.edu/~rlaz/files/CROHME+TFD%e2%80%932019.pdf
- BTTR (Zhao et al., ICDAR 2021): https://arxiv.org/html/2105.02412
- CoMER (Zhao & Gao, ECCV 2022): https://arxiv.org/html/2207.04410
- SAN / HME100K (Yuan et al., CVPR 2022): https://ar5iv.labs.arxiv.org/html/2203.01601
- PosFormer / MNE (Guan et al., ECCV 2024): https://arxiv.org/html/2407.07764
- TAMER (Zhu et al., AAAI 2025): https://arxiv.org/html/2408.08578
- Uni-MuMER (2025): https://arxiv.org/html/2505.23566v3
- MathWriting (Gervais et al., 2024): https://arxiv.org/html/2404.10690v1

Official repos, model and dataset cards
- CROHMELib (symbol list, grammar): https://gitlab.univ-nantes.fr/crohme/crohmelib
- BTTR dictionary / vocab: https://github.com/Green-Wood/BTTR/tree/main/bttr/datamodule
- Pix2Text MFR 1.5 model card and tokenizer: https://huggingface.co/breezedeus/pix2text-mfr-1.5
- Pix2Text v1.5 article: https://www.breezedeus.com/article/pix2text-model-1.5
- TexTeller model card and tokenizer: https://huggingface.co/OleehyO/TexTeller
- TexTeller README: https://github.com/OleehyO/TexTeller
- TexTeller_en: https://huggingface.co/api/models/OleehyO/TexTeller_en
- TexTeller training data card and size API: https://huggingface.co/datasets/OleehyO/latex-formulas-80M, https://datasets-server.huggingface.co/size?dataset=OleehyO/latex-formulas-80M
- Spike issue: https://github.com/george-vrancianu/aequate/issues/12

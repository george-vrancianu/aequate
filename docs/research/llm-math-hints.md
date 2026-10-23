# Small local LLMs for math hints

Research note, 2026-10-23. Question from the ticket *Small local LLMs for math hints*: *"Which open-weight models that fit in about 8 GB of VRAM (4-bit) can phrase a math hint, given the problem's LaTeX steps, the CAS verdict and the goal, without stating the answer?"* The note covers licences and VRAM, published evidence of tutoring quality, prompt formats and leak checks, Romanian, latency, and CPU-only use.

Context: [`docs/handoff.md`](../handoff.md) section 6, [`recognition-compute-split.md`](recognition-compute-split.md), and the map *Wayfinder map: assist loop (transcribe, check, solve, hint)* (Notes: the CAS is the only judge, the LLM is an optional plugin that is off by default, and the last hint rung needs "solve allowed"). Each claim below links to its source. **Unverified** marks anything I could not confirm in a primary source. *Inference* marks my own reasoning from the cited facts. *Measured* marks numbers I produced on this machine for this note.

---

## Conclusion (TL;DR)

1. **Default pick: Qwen3.5-9B (Apache-2.0), with thinking off. Runner-up and low-VRAM pick: Qwen3.5-4B.** Its Q4_K_M GGUF is 5.29 GiB ([file list](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main)), so it fits 8 GB with room for a short context. It has the strongest published multilingual and math scores in this size class (MMMLU 81.2, WMT24++ 72.6, HMMT Feb 25 83.2; [card](https://huggingface.co/Qwen/Qwen3.5-9B)). Gemma 4 E4B (Apache-2.0, 4.28 GiB Q4_0) and Ministral 3 8B (Apache-2.0, 4.84 GiB Q4_K_M) are viable alternates to put in the same bake-off. Everything on the shortlist is Apache-2.0, which is compatible with AGPL self-hosting (§1).
2. **No published benchmark measures hint quality for any 2026 small model.** The tutoring literature tested 2024-era models, and its message is consistent: strong solvers are poor tutors and leak answers. Qwen2.5-Math-7B solves 0.88 of MathTutorBench problems but scores 0.06 on scaffolding ([MathTutorBench, Table 4](https://arxiv.org/html/2502.18940v2)). Untuned Qwen2.5-7B-Instruct leaks the solution in 29.3% of dialogues, and Qwen2.5-72B in 61.0% ([Dinucu-Jianu et al., Table 2](https://arxiv.org/html/2505.15607v2)). *Inference:* Aequate has to run its own small evaluation. The question cannot be answered from model cards.
3. **Aequate's design avoids most of the hard part.** Published leak rates come from multi-turn chat, where the tutor model also has to solve the problem and judge the student. Here the CAS produces the verdict, the error location and, at the last rung, the next step. The LLM only turns a fixed, rung-specific payload into a sentence. Grounding generation in a verifier's error description raised GPT-3.5's "correct" feedback from 37.5% to 62.5% ([Daheim et al., Table 3](https://arxiv.org/html/2407.09136)). *Inference:* do not give the model the next step or the answer at lower rungs. It cannot leak what it was not told, though it can still work it out from the steps.
4. **Leak prevention needs a gate after generation, not only a prompt.** Every system that reports low leakage uses a checker after generation, then a refiner or a fallback ([Zhao et al. 2026](https://arxiv.org/html/2604.18660v1), [Kadir 2026](https://arxiv.org/pdf/2608.00515)). Proposed Aequate gate (*inference*, §3.3): (a) a digit and number-word match against the CAS answer and next step; (b) SymPy-parse every math span in the hint and reject it if one is equal to the final answer or matches the next step side by side; (c) on rejection, regenerate once, then fall back to the CAS-rule hint the map already requires.
5. **Romanian has no direct evidence for the 2026 candidates.** None of the cards lists Romanian-specific scores. Qwen3 lists Romanian among its 119 languages ([Qwen3 blog](https://qwenlm.github.io/blog/qwen3/)). EuroLLM-9B lists Romanian explicitly ([card](https://huggingface.co/utter-project/EuroLLM-9B-Instruct)). The Gemma 4 and Ministral 3 cards do not list it. Romanian-tuned models (RoLlama, RoGemma) are CC-BY-NC-4.0 ([RoLlama3.1 card](https://huggingface.co/OpenLLM-Ro/RoLlama3.1-8b-Instruct-DPO-2025-04-23), [RoGemma3 card](https://huggingface.co/OpenLLM-Ro/RoGemma3-4B-Instruct)), so they are out for tutors who charge. Prompt in English and ask for the hint in Romanian: in the one multilingual hint study, native-language prompting had the highest leakage for an 8B tutor (up to 8.3%) ([Tonga et al., Table 2](https://arxiv.org/html/2506.04920)).
6. **Latency: about 1.5–3 s per hint on a GPU, if thinking is off.** A hint is a prompt of about 600 tokens and an output of about 100 tokens. Token generation is limited by memory bandwidth. On the llama.cpp CUDA scoreboard, a 3.56 GiB 7B model generates 75.6 tokens/s on an RTX 3060, 64 tokens/s on an RTX 4060 Ti 8 GB, and 108 tokens/s on an A10G ([llama.cpp #15013](https://github.com/ggml-org/llama.cpp/discussions/15013)). *Inference:* scaling to a 5.3 GiB model gives about 2–3 s on a consumer card or an L4 (300 GB/s, the same class as the 4060 Ti) and about 1.5 s on an A10 (600 GB/s) ([L4](https://www.nvidia.com/en-us/data-center/l4/), [A10](https://www.nvidia.com/en-us/data-center/products/a10-gpu/)). Thinking mode would add hundreds to thousands of tokens, which means tens of seconds.
7. **CPU-only is viable for a 4B model, borderline for 8–9B.** *Measured* on this machine (Ryzen 9 5950X, 16 threads, DDR4, WSL2, llama.cpp build c7fc50941, machine shared with other jobs): Qwen3.5-4B Q4_K_M processes prompts at 123 tokens/s and generates 8.4 tokens/s, Qwen3-8B Q4_K_M 67 and 6.1 tokens/s. *Inference:* that is about 15–20 s per hint for the 4B and 25–30 s for an 8–9B, about 5–10x slower than a GPU. With streaming and a cached system prompt, the first words appear after a few seconds. That is acceptable for an occasional hint, and the CAS-rule template remains the instant fallback (§5.2). The handoff's "CPU-only is summaries-only" ([§6](../handoff.md)) is too pessimistic for a 4B model.

| Model | Licence | Q4 GGUF size | Romanian evidence | Role |
|---|---|---|---|---|
| **Qwen3.5-9B** | Apache-2.0 | 5.29 GiB Q4_K_M | Family lists Romanian (Qwen3), WMT24++ includes en-ro | Default |
| **Qwen3.5-4B** | Apache-2.0 | 2.55 GiB Q4_K_M | Same | Low VRAM, CPU fallback |
| Gemma 4 E4B | Apache-2.0 | 4.28 GiB Q4_0 | Not listed (35+ languages, unnamed) | Alternate |
| Gemma 4 12B | Apache-2.0 | 6.63 GiB Q4_K_M | Not listed | Too tight for 8 GB with context (*inference*) |
| Ministral 3 8B | Apache-2.0 | 4.84 GiB Q4_K_M | Not listed (11 languages) | Alternate |
| EuroLLM-9B-Instruct | Apache-2.0, gated | 5.20 GiB Q4_K_M | Lists Romanian | Romanian-fluency control, weak on maths (no math scores published) |
| TutorRL-7B | Apache-2.0 | ~4.7 GB (*inference*, Qwen2.5-7B base) | None | Research baseline: RL-trained not to leak, English only |

---

## 1. Shortlist: licences and VRAM

### 1.1 Candidates

| Model | Params | Licence | Q4 file | Context | Notes |
|---|---|---|---|---|---|
| Qwen3.5-9B | 9B (10B incl. vision encoder in safetensors) | Apache-2.0 ([card](https://huggingface.co/Qwen/Qwen3.5-9B)) | Q4_0 5.01 GiB, Q4_K_M 5.29 GiB ([files](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main)) | 262,144 | Hybrid Gated DeltaNet + gated attention. Thinking is on by default, turned off with `enable_thinking: False`. The `/think` and `/nothink` switches of Qwen3 are not supported ([card](https://huggingface.co/Qwen/Qwen3.5-9B)). The card's highlights mention "sparse Mixture-of-Experts", but its 9B overview lists a plain FFN, so the card is inconsistent |
| Qwen3.5-4B | 4B (5B in safetensors) | Apache-2.0 ([card](https://huggingface.co/Qwen/Qwen3.5-4B)) | Q4_K_M 2.55 GiB ([files](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main)) | 262,144 | Non-thinking settings: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 ([card](https://huggingface.co/Qwen/Qwen3.5-4B)) |
| Gemma 4 E4B | 4.5B effective, 8B with embeddings | Apache-2.0 ([card](https://huggingface.co/google/gemma-4-E4B-it)) | Q4_0 4.28 GiB ([ggml-org](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF/tree/main)), Q4_K_M 4.64 GiB ([unsloth](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/tree/main)) | 128K | Thinking via `<\|think\|>` in the system prompt, so it is off unless asked ([card](https://huggingface.co/google/gemma-4-E4B-it)) |
| Gemma 4 12B | 11.95B | Apache-2.0 ([card](https://huggingface.co/google/gemma-4-12b-it)) | Q4_K_M 6.63 GiB ([files](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/tree/main)) | 256K | Better scores, but 6.6 GiB of weights leaves little of 8 GB for the KV cache and the CUDA context (*inference*) |
| Ministral 3 8B Instruct 2512 | 8.4B LM + 0.4B vision | Apache-2.0 ([card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512)) | Q4_K_M 4.84 GiB ([official GGUF](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF/tree/main)) | 256K | "fitting in 12GB of VRAM in FP8". Recommended temperature below 0.1 ([card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512)) |
| EuroLLM-9B-Instruct | 9.154B | Apache-2.0, gated download ([card](https://huggingface.co/utter-project/EuroLLM-9B-Instruct)) | Q4_K_M 5.20 GiB ([files](https://huggingface.co/bartowski/EuroLLM-9B-Instruct-GGUF/tree/main)) | **Unverified** | "has not been aligned to human preferences" ([card](https://huggingface.co/utter-project/EuroLLM-9B-Instruct)) |
| TutorRL-7B / -think | 7.6B (Qwen2.5-7B-Instruct base) | Apache-2.0 ([HF API](https://huggingface.co/api/models/eth-nlped/TutorRL-7B)) | **Unverified** (no official GGUF) | 32K (*inference*, base model) | RL-trained against leakage (§2). English only |

GGUF sizes come from the Hugging Face tree API. Third-party quantisations (unsloth, bartowski) are used where the vendor publishes none. *Inference:* plan for weights + about 0.5–1 GB of KV cache and runtime overhead at a 2–4K context. That leaves the 9B at about 6–6.5 GB on an 8 GB card, and the Gemma 4 12B at about 7.5 GB or more, which is too tight.

### 1.2 Benchmarks from the cards (not tutoring)

| Model | Math | Multilingual | Source |
|---|---|---|---|
| Qwen3.5-9B | HMMT Feb 25 83.2, PolyMATH 57.3 | MMMLU 81.2, MMLU-ProX 76.3, WMT24++ 72.6 | [card](https://huggingface.co/Qwen/Qwen3.5-9B) |
| Qwen3.5-4B | HMMT Feb 25 74.0, PolyMATH 51.1 | MMMLU 76.1, MMLU-ProX 71.5, WMT24++ 66.6 | [card](https://huggingface.co/Qwen/Qwen3.5-4B) |
| Gemma 4 E4B | AIME 2026 42.5% | MMMLU 76.6% | [card](https://huggingface.co/google/gemma-4-E4B-it) |
| Gemma 4 12B | AIME 2026 77.5% | MMMLU 83.4% | [E4B card, comparison table](https://huggingface.co/google/gemma-4-E4B-it) |
| Ministral 3 8B | MATH maj@1 0.876 | Multilingual MMLU (base) 0.706 | [card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512) |
| Phi-4-mini (3.8B, MIT) | MATH 64.0 | Multilingual MMLU 49.3; Romanian not among its 23 languages | [card](https://huggingface.co/microsoft/Phi-4-mini-instruct) |

The Qwen3.5 cards do not say whether the scores were measured with thinking on ([card](https://huggingface.co/Qwen/Qwen3.5-4B)). *Inference:* they probably were, so the non-thinking mode Aequate would use is weaker than the table suggests. For phrasing a hint, solving ability matters less than following instructions. MathTutorBench shows the two can even trade off (§2).

### 1.3 Licence compatibility with AGPL self-hosting

- **Apache-2.0 (Qwen3.5, Gemma 4, Ministral 3, EuroLLM, TutorRL):** no field-of-use or user-count restrictions. Gemma moved to Apache-2.0 with Gemma 4 ([card](https://huggingface.co/google/gemma-4-E4B-it)). *Inference:* Aequate does not need to bundle the weights. The Compose file pulls them into an Ollama or llama.cpp container that the tutor runs, so the weights stay a separate work and the AGPL does not reach them. Apache-2.0 is also one-way compatible with GPLv3/AGPLv3 if anything is ever bundled.
- **Llama 3.1 Community License: not shortlisted.** It requires a visible "Built with Llama", names of derived models must begin with "Llama", it incorporates an Acceptable Use Policy, and products above 700M MAU need a separate licence ([LICENSE](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/LICENSE)). *Inference:* it is usable, but adds obligations an Apache model does not.
- **CC-BY-NC-4.0 (OpenLLM-Ro RoLlama3.1, RoGemma3): excluded.** Tutors running Aequate commercially would breach the non-commercial term ([RoLlama3.1](https://huggingface.co/OpenLLM-Ro/RoLlama3.1-8b-Instruct-DPO-2025-04-23), [RoGemma3](https://huggingface.co/OpenLLM-Ro/RoGemma3-4B-Instruct)).
- **MIT (Phi-4-mini):** compatible, but the card warns that languages other than English "will experience worse performance", and Romanian is not supported ([card](https://huggingface.co/microsoft/Phi-4-mini-instruct)).

---

## 2. Published evidence on hint and tutoring quality

### 2.1 What the benchmarks measure

| Benchmark | What it scores | Leak dimension | Source |
|---|---|---|---|
| MathDial (EMNLP 2023 Findings) | 3k teacher–student dialogues on multi-step word problems | Motivated by LLMs being "prone to revealing solutions to students too early" | [arXiv 2305.14536](https://arxiv.org/abs/2305.14536) |
| MRBench / AI tutor evaluation taxonomy | 8 human-annotated dimensions, including "Revealing of the answer" (desired: No) | Yes, explicit | [arXiv 2412.09416](https://arxiv.org/html/2412.09416) |
| BEA 2025 shared task | Mistake identification and location, providing guidance, actionability | Folded into "providing guidance" | [Findings](https://arxiv.org/html/2507.10579v1) |
| MathTutorBench (EMNLP 2025) | 9 tasks: solving, Socratic questioning, mistake location and correction, scaffolding, pedagogical instruction following | Indirect, through a reward model trained on MRBench's "Revealing" criterion | [arXiv 2502.18940](https://arxiv.org/html/2502.18940v2) |
| PedagogicalRL (EMNLP 2025) | Student solve-rate gain against % of dialogues with a leaked solution | Yes, LLM judge | [arXiv 2505.15607](https://arxiv.org/html/2505.15607v2) |

### 2.2 Results for small models

**MRBench, human annotation ([Table 3](https://arxiv.org/html/2412.09416)).** The share of responses that did *not* reveal the answer (higher is better) was 73.96% for both Llama-3.1-8B and Phi-3, 86.46% for Mistral, 94.79% for Sonnet and 53.12% for GPT-4. Expert human tutors scored 90.62%. On providing guidance, Llama-3.1-8B scored 45.31%, Phi-3 17.71% and experts 67.19%. *Inference:* about one in four responses from an untuned 8B model reveals the answer.

**MathTutorBench ([Table 4](https://arxiv.org/html/2502.18940v2)).** Scaffolding win rate over human teachers: Llama-3.1-8B 0.61, LearnLM-1.5-Pro 0.64, GPT-4o 0.50, Qwen2.5-7B-SocraticLM 0.39, Qwen2.5-Math-7B 0.06. The paper's conclusion: "Math expertise does not translate directly to student understanding and pedagogy." The scorer is a Qwen2.5-1.5B reward model with 0.84 accuracy at preferring expert over novice responses. LLM-as-judge prompts stayed below 0.7 ([§6.2](https://arxiv.org/html/2502.18940v2)). That reward model is published under CC-BY-4.0 ([HF API](https://huggingface.co/api/models/eth-nlped/Qwen2.5-1.5B-pedagogical-rewardmodel)).

**PedagogicalRL, held-out BigMath ([Table 2](https://arxiv.org/html/2505.15607v2)).**

| Tutor | Δ solve rate | Leaked solution |
|---|---|---|
| Qwen2.5-3B-Instruct | 5.2 | 34.6% |
| Qwen2.5-7B-Instruct | 11.3 | 29.3% |
| Qwen2.5-7B SFT (MathDial-style) | 8.9 | 36.0% |
| SocraticLM | 15.9 | 40.4% |
| Qwen2.5-7B-RL, λ=0.75 | 25.3 | 10.6% |
| Qwen2.5-7B-RL, λ=1.5 | 21.2 | 5.4% |
| Qwen2.5-14B-Instruct | 29.3 | 41.9% |
| GPT-4o-2024-11-20 | 33.1 | 35.2% |
| LearnLM 2.0 Flash | 4.3 | 0.9% |

Leakage was judged by Gemma3-27B with an OK/REJECT rubric ([§5.2, Fig. 14](https://arxiv.org/html/2505.15607v2)). The RL checkpoints are public as `eth-nlped/TutorRL-7B` and `-think` (Apache-2.0, [HF API](https://huggingface.co/api/models/eth-nlped/TutorRL-7B)). Adding hidden thinking gave mixed results: at λ=1.5 leakage rose from 5.4% to 7.4% ([Table 2](https://arxiv.org/html/2505.15607v2)).

**Adversarial students ([Zhao, Knežević, Käser 2026, Table 2](https://arxiv.org/html/2604.18660v1)).** When a student keeps pushing for the answer, Qwen2.5-7B leaked in 75–82% of dialogues and Llama-3.1-8B in 34–40%. A judge-and-refiner loop cut Llama-8B to 6–9% but Qwen-7B only to 49–61%. TutorRL-7B reached up to 85% under "interpersonal influence" attacks.

**Grounding in a verifier ([Daheim et al., Table 3](https://arxiv.org/html/2407.09136)).** Feeding GPT-3.5 an error description from a verifier raised "targeted" feedback from 30.0% to 57.5% and "correct" from 37.5% to 62.5%. The same paper found that LLMs are poor at finding the error themselves: GPT-3.5 locates the first wrong step with micro-F1 0.42 without a reference solution ([Table 1](https://arxiv.org/html/2407.09136)). Inter-annotator agreement was low (κ 0.13–0.25).

### 2.3 What this means for Aequate (*inference*)

- The benchmarks above are multi-turn chats where the model also judges the student and solves the problem. Aequate's hint is a **single turn**, the CAS does the judging, and the student cannot type free text into the hint generator. That removes the adversarial-student attack surface and the verification failure mode, which are the two largest sources of error above.
- No 2026 model (Qwen3.5, Gemma 4, Ministral 3) appears in any tutoring benchmark I found. The relevant evidence is about prompting style (grounding, rung contracts, gates), and that transfers. The model ranking does not.
- TutorRL-7B is the only small model trained against leakage. It is English-only, built on a 2024 base, and does not follow Aequate's rung structure. Use it as a baseline in the bake-off, not as the default.

---

## 3. Keeping the answer out of the hint

### 3.1 The hint ladder in tutoring research

VanLehn's description of tutoring systems gives the standard sequence **Point → Teach → Bottom-out**. "Pointing hints mention problem conditions that should remind the student of the knowledge component's relevance. Teaching hints describe the knowledge component briefly and show how to apply it. Bottom-out hints tell the student the step" ([VanLehn 2006, p. 16](https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf)). His algebra example for the wrong step `2+3x=20 → 5x=20` runs from "You seem to have added 2+3. Is that really appropriate?" to "You should enter 3*x=20-2", built by filling templates from an "error description" ([same, pp. 17–18](https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf)). He also notes that students click rapidly through to the bottom-out hint, and that adding a delay discourages it ([p. 16](https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf)).

Kadir (2026) turns this into five "disclosure contracts" enforced outside the model ([Table 1](https://arxiv.org/pdf/2608.00515)): A0 elicit the next step, withholding numeric and procedural content; A1 scaffold a subgoal while withholding the decisive calculation; A2 state a concept without applying it to the target quantities; A3 name a local procedure while leaving execution to the learner; A4 release a worked answer only under trusted, problem-scoped authorisation. The paper defines leakage to include "decisive calculation disclosure", not only the final answer, and treats the generator as untrusted ([§1, §3.1](https://arxiv.org/pdf/2608.00515)).

**Mapping onto Aequate's ladder (*inference*):**

| Rung | Contract | Payload the LLM receives |
|---|---|---|
| 1. Point | A0/A2 | Goal, steps, verdict, the location of the error (from the CAS) |
| 2. Teach | A2/A3 | Above + the name of the rule or transformation that applies (from CAS rules) |
| 3. Next step (needs "solve allowed") | A4 | Above + the next step LaTeX, computed by SymPy |

The authorisation for rung 3 comes from assist permissions on the server, never from the prompt. This matches Kadir's rule that "a user's self-asserted request cannot activate" A4 ([§3.2](https://arxiv.org/pdf/2608.00515)).

### 3.2 Prompt format

Elements with published support:

- **Ground on the verifier output.** Pass the CAS verdict and the error location as data ([Daheim et al.](https://arxiv.org/html/2407.09136)).
- **Explicit prohibition plus brevity.** PedagogicalRL's tutor prompt says "You must not reveal the answer to the problem to the student at any point in time" and asks for short replies ([Fig. 13](https://arxiv.org/html/2505.15607v2)). Prompting alone still leaves 29% leakage for Qwen2.5-7B in multi-turn use ([Table 2](https://arxiv.org/html/2505.15607v2)), so the gate in §3.3 is required.
- **English instructions, Romanian output.** In the multilingual hint study, the "EN→L" setting (English prompt, hint in the target language) had leakage of 0.17–1.6%. Native-language prompts ("L→L") reached up to 8.3% for an 8B tutor on low-resource languages ([Tonga et al., Table 2](https://arxiv.org/html/2506.04920)). Romanian was not among the 11 languages tested.
- **Constrained output.** Ollama accepts a JSON schema in `format` (and `response_format` through its OpenAI-compatible API) ([docs](https://docs.ollama.com/capabilities/structured-outputs)). *Inference:* ask for `{"hint": string, "math": [latex]}` with every formula also listed in `math`, so the gate parses formulas without having to find them in prose.
- **No thinking.** Thinking adds latency (§5) and did not reliably reduce leakage ([PedagogicalRL Table 2](https://arxiv.org/html/2505.15607v2)). For Qwen3.5 this means `enable_thinking: False` ([card](https://huggingface.co/Qwen/Qwen3.5-9B)).

A sketch of the prompt (*inference*):

```text
SYSTEM (English, fixed):
You write one hint for a student. Output language: {ro|en}.
Rung: {point|teach|next_step}. Rules for this rung: {contract text}.
The verdict below is final; never say a correct step is wrong or vice versa.
Never state the value of the unknown. Never write an equation that the student
has not written yet, unless rung = next_step. At most 2 sentences.
Return JSON: {"hint": "...", "math": ["<every LaTeX formula in the hint>"]}

USER (data only):
goal: solve for x
steps: ["2+3x=20", "5x=20"]
verdict: step 2 is NOT equivalent to step 1
error_at: step 2
rule: (rung >= teach only) "subtract the constant term from both sides"
next_step: (rung = next_step only) "3x = 18"
```

### 3.3 Automatic leak checks

Published checkers:

- **Digit or regex match.** Flag the hint if the gold answer appears as a standalone number ([Tonga et al.](https://arxiv.org/html/2506.04920); [Zhao et al.](https://arxiv.org/html/2604.18660v1)). Cheap, with known false positives.
- **LLM judge.** Gemma3-27B ([PedagogicalRL](https://arxiv.org/html/2505.15607v2)) or Llama-3.1-70B, with κ 0.81 against humans on tutor turns ([Zhao et al.](https://arxiv.org/html/2604.18660v1)). These judges are too large for an 8 GB box. Small LLM critics (Llama-3.1-8B, Prometheus2) correlated *negatively* with humans on MRBench's pedagogical dimensions ([MRBench §6](https://arxiv.org/html/2412.09416)). *Inference:* do not use the same small model as a leak judge in production.
- **Deterministic checker + fallback.** Kadir's "fast checker" restricts the reference answer and derived numbers, equations and decisive operations. On rejection it releases a deterministic fallback. Strict mediation cut panel-flagged leaks from 181 to 0 out of 599, but replaced 581 responses and lowered helpfulness ([abstract](https://arxiv.org/pdf/2608.00515)).

**Proposed CAS gate for Aequate (*inference*; no published system uses SymPy this way, as far as I found).** Inputs: the hint JSON, the student's steps S, the CAS next step N (an equation), and the final answer A (for example `x = 6`).

1. **Numbers.** Collect the numbers and Romanian or English number words in the hint text. Reject on a match with any number that appears in N or A but not in S or the problem.
2. **Formulas.** Parse each `math` entry with the same pinned SymPy LaTeX parser as the checker (see [`recognition-compute-split.md`](recognition-compute-split.md) §2.2 on parser backends). Reject if an expression:
   - equals the value in A (for example `6`, or `x = 6`, or an equivalent form such as `x=\frac{12}{2}`); or
   - is an equation whose sides each match the sides of N up to `simplify(a - b) == 0`, in either order, at rungs below "next step".
   Do **not** test for the same solution set. Every correct step has the same solution set as the next one, so that test would reject every formula the student already wrote.
3. **Unparsed math.** If the hint contains LaTeX-looking text that is not listed in `math`, or a `math` entry fails to parse, reject (fail closed).
4. **Contradiction.** Reject hints that describe a correct step as wrong or the reverse. A keyword check against the verdict is enough for a first version. The earlier research note already proposes contradiction of the verdict as a hard failure metric ([`recognition-compute-split.md`](recognition-compute-split.md) §4).
5. On rejection, regenerate once at temperature 0 with the reason appended. If it fails again, show the CAS-rule template hint (the fallback settled on the map).

Limits: this gate catches the answer and the next step in symbolic form. It does not catch a paraphrase ("subtract two from both sides" at the Point rung). The rung payload (§3.1) is the defence there: at rung 1 the model is never given the rule.

---

## 4. Romanian

- **What the cards say.**

| Model | Romanian listed? | Romanian-specific score |
|---|---|---|
| Qwen3 family | Yes, in the 119 languages ([blog](https://qwenlm.github.io/blog/qwen3/)) | None |
| Qwen3.5 | "201 languages and dialects", list not reproduced on the card ([card](https://huggingface.co/Qwen/Qwen3.5-9B)) | Only inside averages: WMT24++ includes `en-ro_RO` ([dataset](https://huggingface.co/datasets/google/wmt24pp)). MMLU-ProX's 29 languages ([paper](https://arxiv.org/html/2503.10497)) and INCLUDE's 44 ([dataset](https://huggingface.co/datasets/CohereLabs/include-base-44)) do **not** include Romanian |
| Gemma 4 | "35+ languages" out of the box, unnamed ([card](https://huggingface.co/google/gemma-4-E4B-it)) | None. **Unverified** whether Romanian is among the 35 |
| Ministral 3 8B | No (11 listed) ([card](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512)) | None |
| EuroLLM-9B | Yes (35 languages) ([card](https://huggingface.co/utter-project/EuroLLM-9B-Instruct)) | None in text (tables are images) |
| Phi-4-mini | No ([card](https://huggingface.co/microsoft/Phi-4-mini-instruct)) | None |

- **Older evidence that small models handle Romanian math.** RoMath (MathNLP 2025) found that English-centric 7B models such as deepseek-math-7b handled Romanian problems "outputting proper solutions in Romanian". Machine-translating problems into English *hurt* badly, for example deepseek-math-7b on Baccalaureate questions fell from 0.56 to 0.05 ([RoMath, Tables 4–5](https://arxiv.org/html/2409.11074v2)). Llama-3.1-8B-Instruct answered in Romanian on 160/160 MT-Bench-ro prompts and scored 5.69/10. The Romanian-tuned DPO version scored 7.00 but did worse on Romanian GSM8K (31.54 against 35.56) ([RoLlama3.1 card](https://huggingface.co/OpenLLM-Ro/RoLlama3.1-8b-Instruct-DPO-2025-04-23)).
- *Inference:* Romanian fluency at 8B was adequate in 2024 and has probably improved. Grammar, diacritics (ș, ț with comma-below, not cedilla) and math terms ("necunoscuta", "membru", "a trece în celălalt membru") are the risks. Nothing published measures them for the 2026 candidates. The bake-off must have a Romanian speaker rate the hints.
- **Notation.** Romanian uses a decimal comma. *Inference:* keep formulas in LaTeX from the student's steps and let the gate's number check handle both `2.5` and `2,5`.

---

## 5. Latency

### 5.1 GPU

Token generation for a single request is limited by memory bandwidth, so speed scales roughly with bandwidth divided by model size (*inference*, consistent with the scoreboard below). Data from the llama.cpp CUDA scoreboard, Llama 2 7B Q4_0 (3.56 GiB), flash attention off ([#15013](https://github.com/ggml-org/llama.cpp/discussions/15013)):

| GPU | Prompt pp512 (tok/s) | Generation tg128 (tok/s) |
|---|---|---|
| RTX 3060 12 GB | 2,138 | 75.6 |
| RTX 4060 Ti 8 GB | 3,395 | 63.9 |
| RTX 5060 8 GB | 3,269 | 96.7 |
| RTX 3080 10 GB | 5,014 | 139.7 |
| Tesla T4 | 1,219 | 46.4 |
| A10G | 2,354 | 108.3 |

L4 and A10 are not on the scoreboard. The L4 has 300 GB/s of memory bandwidth and the A10 600 GB/s ([L4](https://www.nvidia.com/en-us/data-center/l4/), [A10](https://www.nvidia.com/en-us/data-center/products/a10-gpu/)).

**Estimated time per hint** (*inference*: 600-token prompt, 100-token output, no thinking, model already loaded; tokens/s scaled by 3.56 / model GiB):

| Hardware | Qwen3.5-4B (2.55 GiB) | Qwen3.5-9B (5.29 GiB) |
|---|---|---|
| RTX 3060 / 4060 Ti class | ~1–1.5 s | ~2–3 s |
| Modal L4 (≈ 4060 Ti bandwidth) | ~1.5 s | ~2.5–3 s |
| Modal A10 (≈ A10G) | ~1 s | ~1.5 s |

Caveats: Qwen3.5 uses a hybrid linear-attention architecture, so the Llama 2 scaling is approximate. **Unverified:** no published llama.cpp numbers for Qwen3.5 on these GPUs. The cold start on Modal (container + weights load) comes on top. See [`recognition-compute-split.md`](recognition-compute-split.md) §3.2 on Volumes, snapshots and `scaledown_window`. At [Modal's list prices](https://modal.com/pricing) (L4 $0.000222/s, A10 $0.000306/s), a warm hint costs well under $0.001. *Inference:* a 10-minute `scaledown_window` costs $0.13 (L4) per session in idle time, which is far more than the hints themselves.

Thinking mode, the default for Qwen3.5 ([card](https://huggingface.co/Qwen/Qwen3.5-9B)), would multiply output tokens. *Inference:* 1,000 reasoning tokens at 45 tok/s adds about 20 s, so it must be disabled.

### 5.2 CPU-only

*Measured* for this note with `llama-bench` (`-p 512 -n 128 -r 2`) in the official `ghcr.io/ggml-org/llama.cpp:full` image, build c7fc50941. Hardware: AMD Ryzen 9 5950X (16 cores), 31 GB DDR4, under WSL2. The machine was running other jobs at the same time (load average about 14), so treat these as lower bounds.

| Model (GGUF) | Size | Threads | Prompt pp512 (tok/s) | Generation tg128 (tok/s) |
|---|---|---|---|---|
| Qwen3.5-4B Q4_K_M ([file](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main)) | 2.54 GiB | 16 | 122.7 | 8.4 |
| Qwen3.5-4B Q4_K_M | 2.54 GiB | 8 | 90.2 | 8.9 |
| Qwen3-4B Q4_K_M ([official](https://huggingface.co/Qwen/Qwen3-4B-GGUF)) | 2.32 GiB | 16 | 124.8 | 10.9 |
| Qwen3-8B Q4_K_M ([official](https://huggingface.co/Qwen/Qwen3-8B-GGUF)) | 4.68 GiB | 16 | 67.3 | 6.1 |
| Qwen3-8B Q4_K_M | 4.68 GiB | 8 | 47.2 | 5.6 |

**Time per hint on CPU** (*inference*, from the measured rates: 600-token prompt, 100-token output):
- Qwen3.5-4B: about 5 s of prompt processing + 12 s of generation, so **about 17 s**.
- Qwen3-8B: about 9 s + 16.5 s, so **about 25 s**. Qwen3.5-9B is about 13% larger (5.29 against 4.68 GiB), so **about 28 s** or more.
- The system prompt and rung rules are identical across requests. llama.cpp and Ollama can reuse the cached prompt prefix, which cuts the prompt phase to the per-hint data. **Unverified:** how much that saves for Qwen3.5's hybrid attention.

**Verdict (*inference*):** a CPU-only fallback is **viable with the 4B model** as a slow hint (stream it and show a "writing a hint…" state), and borderline with 8–9B. A server with fast memory (more channels, DDR5) would do better than this desktop, because generation is bandwidth-bound. Two settled rules make this acceptable: the LLM is off by default, and the CAS-rule template hint is always available instantly. A tutor without a GPU can choose between the slow LLM hint and the template.

---

## 6. Recommendation and next experiment

**Recommendation (*inference*):**
- Provider: an Ollama or llama.cpp container serving one GGUF, behind the `/suggest` boundary from [handoff §6](../handoff.md). Default model **Qwen3.5-9B Q4_K_M** with an 8 GB GPU, **Qwen3.5-4B Q4_K_M** below that or on CPU. Thinking off, temperature low (0–0.3) for repeatable hints.
- Rung payloads as in §3.1, an English system prompt, output in the session locale, JSON output, and the CAS gate in §3.3 with the CAS-rule template as fallback. The tutor-approval and "solve allowed" checks live in the server, never in the prompt.
- Record each hint with the model id, quantisation, prompt version, rung and gate result so the tutor review screen can show which hints were LLM-written and which were fallbacks.

**Bake-off (tied to [handoff §10](../handoff.md) step 10, "Shortlist two open-weight math models; benchmark on 50 real student errors; define the hint-ladder prompt format"):**
1. Build 50 errorful worked solutions (linear and quadratic equations, fractions, simplification), half in Romanian, each with the SymPy verdict, error location, rule and next step.
2. Generate rungs 1–3 with Qwen3.5-9B, Qwen3.5-4B, Gemma 4 E4B, Ministral 3 8B and TutorRL-7B, in English and Romanian.
3. Measure automatically: gate rejection rate per rung, verdict contradictions (hard failure), and latency on a local 8 GB card and on Modal L4 and A10.
4. Have humans rate (the tutor and one Romanian speaker) a sample on MRBench's dimensions: revealing the answer, providing guidance, actionability, coherence ([taxonomy](https://arxiv.org/html/2412.09416)). Optionally score with the open pedagogical reward model ([HF](https://huggingface.co/eth-nlped/Qwen2.5-1.5B-pedagogical-rewardmodel)), noting it was trained on English data.
5. Decide the default model and whether the 4B is good enough to be the only option.

**Open risks**
- No published hint-quality numbers for any 2026 small model, and none for Romanian.
- The gate cannot catch paraphrased leaks. Rung payload design carries that risk.
- Card benchmarks are probably reported in thinking mode, so non-thinking quality is lower than they suggest.
- Qwen3.5's hybrid architecture is newer in llama.cpp and Ollama. Check its support in the versions pinned in Compose.

---

## Sources

- Aequate: [`docs/handoff.md`](../handoff.md), [`docs/research/recognition-compute-split.md`](recognition-compute-split.md)
- Model cards: [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/), [Gemma 4 E4B](https://huggingface.co/google/gemma-4-E4B-it), [Gemma 4 12B](https://huggingface.co/google/gemma-4-12b-it), [Ministral 3 8B](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512), [EuroLLM-9B-Instruct](https://huggingface.co/utter-project/EuroLLM-9B-Instruct), [Phi-4-mini](https://huggingface.co/microsoft/Phi-4-mini-instruct), [RoLlama3.1-8b DPO](https://huggingface.co/OpenLLM-Ro/RoLlama3.1-8b-Instruct-DPO-2025-04-23), [RoGemma3-4B](https://huggingface.co/OpenLLM-Ro/RoGemma3-4B-Instruct), [TutorRL-7B](https://huggingface.co/eth-nlped/TutorRL-7B), [pedagogical reward model](https://huggingface.co/eth-nlped/Qwen2.5-1.5B-pedagogical-rewardmodel)
- GGUF file listings: [Qwen3.5-9B](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main), [Qwen3.5-4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main), [Gemma 4 E4B (ggml-org)](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF/tree/main), [Gemma 4 E4B (unsloth)](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/tree/main), [Gemma 4 12B](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/tree/main), [Ministral 3 8B](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF/tree/main), [EuroLLM-9B](https://huggingface.co/bartowski/EuroLLM-9B-Instruct-GGUF/tree/main), [Qwen3 GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF)
- Licence: [Llama 3.1 LICENSE](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/LICENSE)
- Tutoring research: [MathDial](https://arxiv.org/abs/2305.14536), [MRBench taxonomy](https://arxiv.org/html/2412.09416), [BEA 2025 findings](https://arxiv.org/html/2507.10579v1), [MathTutorBench](https://arxiv.org/html/2502.18940v2), [PedagogicalRL](https://arxiv.org/html/2505.15607v2), [Daheim et al., stepwise verification](https://arxiv.org/html/2407.09136), [Zhao et al., adversarial leakage](https://arxiv.org/html/2604.18660v1), [Kadir, auditable release control](https://arxiv.org/pdf/2608.00515), [Tonga et al., multilingual hints](https://arxiv.org/html/2506.04920), [VanLehn 2006](https://www.cs.uky.edu/~sgware/reading/papers/vanlehn2006behavior.pdf)
- Romanian: [RoMath](https://arxiv.org/html/2409.11074v2), [WMT24++](https://huggingface.co/datasets/google/wmt24pp), [MMLU-ProX](https://arxiv.org/html/2503.10497), [INCLUDE](https://huggingface.co/datasets/CohereLabs/include-base-44)
- Runtime and hardware: [llama.cpp CUDA scoreboard #15013](https://github.com/ggml-org/llama.cpp/discussions/15013), [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [NVIDIA L4](https://www.nvidia.com/en-us/data-center/l4/), [NVIDIA A10](https://www.nvidia.com/en-us/data-center/products/a10-gpu/), [Modal pricing](https://modal.com/pricing)

# Recognition vs. compute: one model or separate stages?

Research note, 2026-10-23. Question from the team: *"With Modal, we want a model that calculates math equations and reads handwriting. Is reading and computing one model, or can we delegate to different models, so we can cache the handwriting decode when new text is added to an ongoing exercise?"*

Context: [`docs/handoff.md`](../handoff.md) sections 4–6. Each claim below links to its source. **Unverified** marks anything I could not confirm in a primary source. *Inference* marks my own reasoning from the cited facts.

---

## Conclusion (TL;DR)

1. **Use separate stages. Do not use one model.** The pipeline is: recognizer (strokes or image → LaTeX) → SymPy parse → SymPy equivalence check, with an optional LLM after that for explanations only. "Calculating" is SymPy's job. SymPy is deterministic code, not a neural model. No neural stage ever produces a verdict. This is the only layout consistent with the handoff rule "the CAS decides correctness" ([handoff §6](../handoff.md)).
2. **End-to-end VLMs are weaker at both jobs.** Zero-shot Qwen2.5-VL-7B gets about 50–56% of CROHME handwritten expressions exactly right. Specialist HMER models get about 58–62% ([Uni-MuMER, Table 1](https://arxiv.org/html/2505.23566v3)). Qwen2.5-VL-7B scores 68.2 on MathVista and 25.07 on MathVision ([model card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)), so it gets roughly a third or more of visual-math answers wrong. LLM math answers also shift when only the numbers change, and drop by up to 65% when an irrelevant clause is added ([GSM-Symbolic](https://arxiv.org/abs/2410.05229)). Even the math-tuned Qwen2.5-Math recommends delegating computation to tool-integrated (Python) reasoning for "precise computation" ([model card](https://huggingface.co/Qwen/Qwen2.5-Math-7B-Instruct)).
3. **Caching works because the stages are separate.** Segment the board into lines (stroke groups). Cache `recognize(line)` under a key of hash(canonical strokes of the line + recognizer id/version + preprocessing version). Then cache `parse(latex)` and `check(prev_step, step)` the same way. Adding a line costs one recognition plus one or two checks. The rest of the exercise is cache hits.
4. **On Modal, deploy three units:** a GPU `@app.cls` for the recognizer (TexTeller has about 298M parameters, so a T4 or L4 is enough), a CPU function for SymPy, and an optional GPU class for the LLM. Each unit loads once in `@modal.enter`, scales to zero, and has its own `scaledown_window`. Keep the cache **outside** Modal, in the app's Postgres. Production is self-hosted Docker Compose with no Modal ([handoff §4](../handoff.md)). `modal.Dict` is acceptable as a dev-only cache.
5. **CUDA is only needed for optional neural stages.** Checking correctness (SymPy, Pint) and caching run on CPU.

| Stage | Runs on | CUDA? |
|---|---|---|
| Recognition, default stroke model | Student's browser (ONNX) | No |
| Recognition, TexTeller | Server | Yes, preferred. It ships ONNX exports, so a CPU fallback may work (*unmeasured*; test in spike 2) |
| Recognition, MyScript / Mathpix | Vendor servers via API key | No |
| Parse + equivalence check (SymPy, Pint) | Server CPU | No |
| Cache | Postgres (dev: `modal.Dict`) | No |
| LLM explanations / hints | Server | Yes. CPU-only is summaries-only ([handoff §6](../handoff.md)) |
| Qwen-VL "pro" recognizer | Server | Yes, 24 GB class |

On Modal, only the recognizer and LLM classes request a GPU. The SymPy function stays CPU-only, so checks never pay GPU rates.

---

## 1. One model vs. separate stages

| | End-to-end VLM (image → "solve/check") | Pipeline: recognizer → LaTeX → SymPy (+ LLM explains) |
|---|---|---|
| Reading accuracy | Qwen2.5-VL zero-shot CROHME ExpRate: 3B 37–39%, 7B 50–56%, 72B 54–60%. GPT-4o 46–51%, Gemini 2.5 Flash 53–58% ([Uni-MuMER Table 1](https://arxiv.org/html/2505.23566v3)) | Specialists: CoMER 57–59%, TAMER 60–61%, SSAN 60–62%. A fine-tuned Qwen2.5-VL-3B (Uni-MuMER) reaches 71–75%, or 78–82% with extra data ([same table](https://arxiv.org/html/2505.23566v3)) |
| Computing / judging | Neural, so it can be wrong. MathVista 68.2 and MathVision 25.07 for Qwen2.5-VL-7B ([card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)). Sensitive to number changes and distractors ([GSM-Symbolic](https://arxiv.org/abs/2410.05229)) | SymPy is deterministic code. `==` is structural only. Mathematical equality is "in general … computationally impossible to determine" ([SymPy best practices](https://docs.sympy.org/latest/explanation/best-practices.html)), so `Expr.equals` can return `None` (undetermined) ([source](https://github.com/sympy/sympy/blob/master/sympy/core/expr.py)). An honest "unknown" is better than a confident wrong answer |
| Determinism | Depends on sampling settings. Even greedy decoding is a learned guess | Recognition is greedy by default: TexTeller's `img2latex` uses `do_sample=False`, `num_beams=1` ([source](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/inference.py)). CAS output is a pure function of its input |
| Fit with "CAS is the only judge" | Violates it unless the VLM output is thrown away and re-checked anyway | Matches it directly. The LLM gets LaTeX plus the verdict and never strokes ([handoff §6](../handoff.md)) |
| Latency / cost | 7B VLM needs a 24 GB-class GPU for bf16 weights. *Inference:* 7B × 2 bytes ≈ 15 GB. The handoff estimates "seconds of latency" ([handoff §5](../handoff.md)) | TexTeller has 298,101,248 F32 parameters, about 1.2 GB ([HF API](https://huggingface.co/api/models/OleehyO/TexTeller)), and ships ONNX exports, so it also runs on CPU. SymPy runs on CPU at $0.0000131 per core-second on Modal ([pricing](https://modal.com/pricing)) |
| Cacheability | One opaque call per image. Any new stroke invalidates the whole answer | Each stage caches separately (§2) |
| Swappability | One vendor/model for everything | Matches the handoff's adapter interface (browser ONNX, TexTeller, Qwen-VL pro, MyScript/Mathpix) ([handoff §5](../handoff.md)) |

**Recommendation:** keep reading and computing separate. If Qwen-VL is used at all, use it only as a *recognizer adapter* that is prompted to emit LaTeX and nothing else. Its output still goes through SymPy. The LLM (7–8B, 4-bit) only explains a verdict the CAS has already produced.

---

## 2. Caching the decode phase for incremental writing

### 2.1 What the recognizers accept

**TexTeller (image → LaTeX)**
- The input is one formula image per entry: `img2latex(model, tokenizer, images: list[str] | list[np.ndarray], ...)` ([source](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/inference.py)). It batches a list of images, so you can send several changed lines in one call.
- Every image is grayscaled, white-border-trimmed, and resized so its longer side is at most **448 px** (`FIXED_IMG_SIZE = 448`) ([constants](https://github.com/OleehyO/TexTeller/blob/main/texteller/constants.py), [image utils](https://github.com/OleehyO/TexTeller/blob/main/texteller/utils/image.py)). *Inference:* a whole multi-line board squeezed to 448 px loses detail. Send **cropped per-line images**.
- Formula detection is a separate model. `latex_detect(img_path, load_latexdet_model())` is an RT-DETR ONNX model that labels boxes `isolated` or `embedding` ([source](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/detection/detect.py)). `paragraph2md` chains detection, text OCR, and `img2latex` on the crops ([source](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/inference.py)). The README describes the detector as trained on 3,415 Chinese-material images and 8,272 IBEM images ([README](https://github.com/OleehyO/TexTeller)), which are printed documents. *Inference:* Aequate already has strokes, so it can segment lines from stroke geometry and skip the detector entirely.
- The training normalization mean is 0.954 (`IMAGE_MEAN`) ([constants](https://github.com/OleehyO/TexTeller/blob/main/texteller/constants.py)), which suggests mostly-white images. *Inference:* render the crop as dark ink on white, not chalk on the green board (`#1F3A33`).
- Handwriting: the README lists "handwritten formulas" under the 3.0 release and the plans checklist marks it done. The handwritten subset of the training data comes from existing open datasets ([README](https://github.com/OleehyO/TexTeller)). License: Apache-2.0 ([README](https://github.com/OleehyO/TexTeller)).
- Serving: `texteller launch` starts a Ray Serve server with `POST /predict` (field `img`) and flags `--ngpu-per-replica` and `--use-onnx` ([README](https://github.com/OleehyO/TexTeller)). On Modal, calling the Python API directly in a class is simpler.

**MyScript iink (stroke-based, commercial)**
- iinkTS has two modes. `INTERACTIVE_INK` is a stateful WebSocket session where the client sends `addStrokes` / `eraseStrokes` / `replaceStrokes` deltas and the server replies `contentChanged`, with exports (JIIX) on request. `INK_V2` is a "stateless" HTTP batch mode ([websocket protocol](https://github.com/MyScript/iinkTS/blob/master/architecture/websocket-protocol.md), [ink-canvas](https://github.com/MyScript/iinkTS/blob/master/architecture/ink-canvas.md)). In `INK_V2` the client posts **all** model strokes on each request ([InkCanvas.ts](https://github.com/MyScript/iinkTS/blob/master/src/canvas/variants/InkCanvas.ts)), and `MATH` is a supported recognition type ([HTTPClientV2.ts](https://github.com/MyScript/iinkTS/blob/master/src/client/HTTPClientV2.ts)).
- So incremental recognition exists in MyScript, but the session state lives **on MyScript's server**. Our cache does not help it, and strokes leave the self-hosted box, which matters for minors ([handoff §7](../handoff.md)).
- The iink protocol also has a `mathSolver` round trip ([protocol](https://github.com/MyScript/iinkTS/blob/master/architecture/websocket-protocol.md)). Do not use it as a judge, because the rule says CAS only.
- **Unverified:** an official MyScript doc page on math-specific incremental or "prediction" behavior. The developer.myscript.com doc URLs returned 404 / a JS-only SPA when fetched, so the claims above rest on the iinkTS source.

**Mathpix (strokes API, commercial)**
- Each request is stateless: "There is no memory of what you sent before, and sending the same session ID does not carry context forward." Mathpix recommends **one expression per request**, split on the client ([Mathpix strokes guide](https://docs.mathpix.com/guides/strokes)). Stroke-session tokens last at most 300 s, and live sessions are billed differently, "the first time strokes are sent for a session" ([same](https://docs.mathpix.com/guides/strokes)). Client-side line segmentation plus our cache fits this API well.

**CROHME-style online HMER (browser ONNX default)**
- *Inference:* encoder–decoder HMER models such as CoMER and TAMER from the Uni-MuMER comparison decode a whole expression at once. Adding a stroke to a line means re-decoding that line, but other lines are unaffected. **Unverified:** any open CROHME model with true stroke-incremental decoding.

### 2.2 Segmentation and cache keys (proposed design, *inference*)

1. **Unit of recognition = a line (stroke group).** Group strokes by pen-up debounce plus vertical-gap clustering on the board. Let the tutor/student split or merge lines in the correction UI ([handoff §5](../handoff.md) promises "recognize on pen-up with correction UI"). Each stroke already has a stable Yjs id.
2. **Recognition key**
   `rk = sha256(recognizer_id ‖ model_version ‖ preprocess_version ‖ canonical(strokes))`
   where `canonical` = strokes sorted by id, points translated to the group's bounding-box origin and quantized (for example to 0.5 px). Pressure is dropped if the model ignores it. For image backends, also include the render settings (target height, stroke width, colors), or hash the rendered PNG bytes. Translating to the origin means a line the student moves still hits the cache.
   Value: `{latex, confidence/alternatives, created_at}`.
3. **Parse key**
   `pk = sha256(sympy_version ‖ parser_backend ‖ normalized_latex)` → `srepr(expr)` or a parse error.
   Pin the parser backend. With ANTLR, `parse_latex(r'x -')` silently returns `x`. Lark raises an error instead, and `strict=True` exists only on ANTLR ([SymPy parsing docs](https://docs.sympy.org/latest/modules/parsing.html)). The parser is labeled "experimental" and the API may change ([same](https://docs.sympy.org/latest/modules/parsing.html)), so the SymPy version belongs in the key.
4. **Step-check key**
   `ck = sha256(cas_version ‖ check_mode ‖ assumptions/locale ‖ srepr(prev) ‖ srepr(curr))` → `{verdict: equivalent | not | unknown, detail}`.
   SymPy also has an in-process `lru_cache` (`SYMPY_CACHE_SIZE`, default 1000, `0` disables it, `None` makes it unbounded) ([cache.py](https://github.com/sympy/sympy/blob/master/sympy/core/cache.py)). That cache is per container, so it disappears when Modal scales to zero. The persistent cache has to live elsewhere.
5. **Invalidation:** when a stroke in line *n* changes, only `rk(n)` changes. Then `ck(n-1,n)` and `ck(n,n+1)` change. Everything else is a hit. Tutor corrections of LaTeX are authoritative data, so store them in Postgres as the line's LaTeX rather than as a cache entry.
6. **Where:** a Postgres table in the main app, keyed by hash. It is self-hosted, already in the stack ([handoff §4](../handoff.md)), and the same in dev and prod. The Modal functions stay stateless, so the caller checks the cache first.

---

## 3. Layout on Modal

### 3.1 Units

| Unit | Modal shape | Resources |
|---|---|---|
| `Recognizer` (TexTeller, later Qwen-VL adapter) | `@app.cls(gpu=...)` + `@modal.enter` loads the model once; `@modal.method` `recognize(list[png]) -> list[latex]` | T4 or L4 for TexTeller. 24 GB-class GPU for a 7B VLM (see the memory row below) |
| `Checker` (SymPy + Pint) | `@app.function` (CPU), optional `enable_memory_snapshot=True` to skip import time | 1 core is enough. **Unverified:** SymPy import time and the snapshot's speedup |
| `Explainer` (optional 7–8B LLM) | Separate `@app.cls(gpu=...)` so it scales independently | L4/A10 for 4-bit 7–8B ([handoff §6](../handoff.md) estimates 5–8 GB VRAM) |

Separate classes autoscale and scale down independently. `Cls.with_options(gpu=..., scaledown_window=..., timeout=...)` returns a variant "that autoscales independently", which lets you try GPU types without code changes ([modal.Cls](https://modal.com/docs/reference/modal.Cls)). Call deployed classes from the app server via `modal.Cls.from_name("app", "Recognizer")` ([same](https://modal.com/docs/reference/modal.Cls)).

### 3.2 Lifecycle and cold starts
- `@modal.enter()` runs once per container start, so put model loading there. `@modal.exit()` handles cleanup ([lifecycle docs](https://modal.com/docs/guide/lifecycle-functions)).
- Weights: store them in the Image or a `modal.Volume` so they aren't downloaded on every boot. Per the docs this cuts multi-GB boots "from minutes to seconds" ([cold start](https://modal.com/docs/guide/cold-start)). Volumes are "write-once, read-many … model weights" storage: `Volume.from_name(..., create_if_missing=True)`, mounted with `volumes={"/path": vol}`, plus `commit()` / `reload()` ([volumes](https://modal.com/docs/guide/volumes)). Volumes v2 is Beta ("cannot yet guarantee that no data will be lost") ([same](https://modal.com/docs/guide/volumes)), which is fine for re-downloadable weights.
- Memory snapshots: `enable_memory_snapshot=True` plus `@modal.enter(snap=True)`, "3-10x faster" starts for init-heavy functions. Snapshots are only created for deployed apps (`modal deploy`) ([memory snapshot](https://modal.com/docs/guide/memory-snapshot)). CPU snapshots block GPU access during `snap=True`. The pattern is to load to CPU in `snap=True` and move to GPU in a plain `@modal.enter()` ([same](https://modal.com/docs/guide/memory-snapshot)).
- GPU snapshots: `experimental_options={"enable_gpu_snapshot": True}`. They are **alpha**, don't speed up weight loading from storage, and can break with `torch.compile` ([same](https://modal.com/docs/guide/memory-snapshot)). *Inference:* not worth it for a 1.2 GB TexTeller. Try it later for the VLM/LLM.
- Idle timeout: `scaledown_window` defaults to 60 s and ranges from 2 s to 20 min. `min_containers` and `buffer_containers` keep containers warm at a cost ([cold start](https://modal.com/docs/guide/cold-start)). All of these, plus `enable_memory_snapshot`, `experimental_options`, `volumes`, `gpu`, `timeout` (default 300), are parameters of `App.cls` in the current client source ([app.py](https://github.com/modal-labs/modal-client/blob/main/py/modal/app.py)). For "a few minutes every couple of hours", use `min_containers=0` and `scaledown_window` of about 300–600 s so a test session stays warm, then scales to zero.

### 3.3 `modal.Dict` as a cache
- It is a persisted, distributed KV store: `Dict.from_name(name, create_if_missing=True)` with `get(key, default)`, `put(key, value, skip_if_exists=...)`, `contains`, `pop`, `update` ([reference](https://modal.com/docs/reference/modal.Dict)).
- Limits: entries **expire after 7 days without reads or writes**. Values are at most 100 MiB, with under 5 MiB recommended. Each access adds "a few dozen ms" over the network. Values are cloudpickled ([dicts guide](https://modal.com/docs/guide/dicts)).
- Verdict: **fine for dev** (LaTeX strings and verdicts are tiny, and the 7-day TTL is acceptable for a cache). **Not the system of record**, because self-hosted prod has no Modal. Put the cache behind the same interface in the app server, backed by Postgres, and optionally use `modal.Dict` during dev only.

### 3.4 GPU choice and price (list prices, [modal.com/pricing](https://modal.com/pricing))

| GPU (`gpu=` string, [GPU docs](https://modal.com/docs/guide/gpu)) | $/s | ≈ $/h | ≈ $ per 5-min burst |
|---|---|---|---|
| `T4` | 0.000164 | 0.59 | 0.049 |
| `L4` | 0.000222 | 0.80 | 0.067 |
| `A10` | 0.000306 | 1.10 | 0.092 |
| `L40S` (48 GB; Modal's suggested default) | 0.000542 | 1.95 | 0.163 |
| `A100-40GB` | 0.000583 | 2.10 | 0.175 |
| `H100` | 0.001097 | 3.95 | 0.329 |

CPU costs $0.0000131 per physical core-second, memory $0.00000222 per GiB-second, and the Starter plan includes $30/month in credits ([pricing](https://modal.com/pricing)). Per-burst figures are *inference* (rate × 300 s, GPU only, excluding the idle `scaledown_window` tail). **Unverified:** whether GPU containers are additionally billed for their CPU/memory. Also unverified on Modal's page are the per-GPU memory figures for T4/L4/A10 (commonly 16/24/24 GB per NVIDIA specs). Suggested picks: **T4 or L4 for TexTeller**, **L4/A10 for a 4-bit 7–8B LLM**, and **L40S** if trying a bf16 Qwen-VL-7B.

### 3.5 Sketch (API names checked against the docs and source cited above)

```python
import modal

app = modal.App("aequate-dev")
weights = modal.Volume.from_name("aequate-weights", create_if_missing=True)
rec_image = modal.Image.debian_slim().uv_pip_install("texteller")  # pin versions in practice
cas_image = modal.Image.debian_slim().uv_pip_install("sympy", "pint", "lark")

@app.cls(gpu="L4", image=rec_image, volumes={"/weights": weights},
         scaledown_window=600, enable_memory_snapshot=True)
class Recognizer:
    @modal.enter(snap=True)          # snapshotted: imports + load on CPU
    def load(self):
        from texteller import load_model, load_tokenizer
        self.model = load_model(model_dir="/weights/texteller", use_onnx=False)
        self.tok = load_tokenizer(tokenizer_dir="/weights/texteller")

    @modal.enter()                   # after restore: GPU is available
    def to_gpu(self):
        self.model = self.model.to("cuda")

    @modal.method()
    def recognize(self, line_images: list) -> list[str]:   # numpy RGB arrays, one per line
        from texteller import img2latex
        import torch
        return img2latex(self.model, self.tok, line_images, device=torch.device("cuda"))

@app.function(image=cas_image, enable_memory_snapshot=True, scaledown_window=600)
def check_step(prev_latex: str, curr_latex: str) -> dict:
    ...  # parse_latex(..., backend="lark"); Expr.equals -> True/False/None
```

The caller (app server) checks the Postgres cache by `rk` / `ck`, sends only the misses to `Recognizer().recognize.remote(...)` / `check_step.remote(...)`, and stores the results. `load_model(model_dir=...)` / `load_tokenizer(tokenizer_dir=...)` take a local directory, and passing `None` pulls the default HF repo ([load.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/load.py), [models/texteller.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/models/texteller.py)). Note that the docstring example in `inference.py` uses `model_path=` / `tokenizer_path=`, which do not match the real signatures. Use the signatures.

---

## 4. Open risks and next experiments

**Risks**
- *Real-handwriting accuracy is unknown.* CROHME ExpRates (≤62% for specialists, zero-shot) mean roughly 4 in 10 expressions need correction ([Uni-MuMER](https://arxiv.org/html/2505.23566v3)). The correction UI is load-bearing.
- *Parser silent truncation.* The ANTLR backend can drop input without warning ([SymPy parsing](https://docs.sympy.org/latest/modules/parsing.html)). A wrong parse gives a wrong verdict.
- *Equivalence is undecidable in general.* `equals` → `None` needs a UX path ("tutor decides") ([SymPy](https://docs.sympy.org/latest/explanation/best-practices.html)).
- *TexTeller domain gap.* The detector was trained on printed docs and the handwritten training data is limited ([README](https://github.com/OleehyO/TexTeller)). Rendering choices (ink color, crop padding) may matter (*inference*).
- *Commercial backends* keep state or send strokes off-box (MyScript sessions, Mathpix per-session billing). This is a privacy and cost issue, not a caching one.
- *Modal-specific features* (GPU snapshots, alpha; Volumes v2, beta) may change. Keep Modal behind the adapter interface so Compose prod doesn't depend on it.

**Experiments, tied to the handoff's next steps ([§10](../handoff.md))**
- **Spike 2 (browser stroke ONNX, 50 samples):** collect samples *as lines with stroke ids*. Measure ExpRate per line for (a) the browser ONNX model, (b) TexTeller on rendered crops (T4 vs L4 on Modal, warm and cold latency), and (c) Qwen2.5-VL-7B zero-shot as the "pro" baseline. Replay the sessions to measure the cache hit rate when lines are appended or edited, and how often segmentation errors break lines.
- **Spike 4 (SymPy equivalence, 20 steps):** compare the ANTLR, ANTLR `strict=True`, and Lark backends for parse failures. Measure the `equals` True/False/None distribution and time per check, with and without memory snapshot on Modal. Settle the `ck` key fields (assumptions, factored vs expanded mode, [handoff §9](../handoff.md)).
- **Step 10 (LLM shortlist, 50 student errors):** feed only LaTeX plus the CAS verdict. Track the rate at which the LLM's explanation *contradicts* the verdict, and treat that as a hard failure metric. Benchmark on L4/A10 with `scaledown_window` tuned for burst sessions.

---

## Sources

- Aequate handoff: [`docs/handoff.md`](../handoff.md)
- TexTeller README: https://github.com/OleehyO/TexTeller
- TexTeller source (commit 9b88cec, 2025-08-22): [api/inference.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/inference.py), [api/detection/detect.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/api/detection/detect.py), [constants.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/constants.py), [utils/image.py](https://github.com/OleehyO/TexTeller/blob/main/texteller/utils/image.py)
- TexTeller weights metadata: https://huggingface.co/api/models/OleehyO/TexTeller
- MyScript iinkTS (commit dc61755, 2026-08-25): [websocket-protocol.md](https://github.com/MyScript/iinkTS/blob/master/architecture/websocket-protocol.md), [ink-canvas.md](https://github.com/MyScript/iinkTS/blob/master/architecture/ink-canvas.md), [InkCanvas.ts](https://github.com/MyScript/iinkTS/blob/master/src/canvas/variants/InkCanvas.ts), [HTTPClientV2.ts](https://github.com/MyScript/iinkTS/blob/master/src/client/HTTPClientV2.ts)
- Mathpix strokes guide: https://docs.mathpix.com/guides/strokes
- Uni-MuMER (NeurIPS 2025), CROHME table: https://arxiv.org/html/2505.23566v3
- Qwen2.5-VL-7B-Instruct model card: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct
- Qwen3-VL-8B-Instruct model card (benchmarks shown only as an image, not transcribed): https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct
- Qwen2.5-Math-7B-Instruct model card: https://huggingface.co/Qwen/Qwen2.5-Math-7B-Instruct
- GSM-Symbolic: https://arxiv.org/abs/2410.05229
- SymPy: [parsing docs](https://docs.sympy.org/latest/modules/parsing.html), [best practices](https://docs.sympy.org/latest/explanation/best-practices.html), [core/cache.py](https://github.com/sympy/sympy/blob/master/sympy/core/cache.py), [core/expr.py](https://github.com/sympy/sympy/blob/master/sympy/core/expr.py)
- Modal: [pricing](https://modal.com/pricing), [lifecycle functions](https://modal.com/docs/guide/lifecycle-functions), [memory snapshots](https://modal.com/docs/guide/memory-snapshot), [cold start](https://modal.com/docs/guide/cold-start), [volumes](https://modal.com/docs/guide/volumes), [GPU](https://modal.com/docs/guide/gpu), [Dict guide](https://modal.com/docs/guide/dicts), [Dict reference](https://modal.com/docs/reference/modal.Dict), [Cls reference](https://modal.com/docs/reference/modal.Cls), [client app.py](https://github.com/modal-labs/modal-client/blob/main/py/modal/app.py)

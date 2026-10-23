# Ranked alternatives from the browser recognizer

Research note, 2026-10-23. Question from the ticket "Ranked alternatives from the browser recognizer" (part of "Wayfinder map: assist loop (transcribe, check, solve, hint)"): *can Pix2Text MFR 1.5 (first) and BTTR (second) return the top-k readings with a confidence score when run with ONNX Runtime Web in the browser? How do the server-side adapters (TexTeller, Mathpix, MyScript) expose alternatives?*

Context: the confirmation view shows the transcription plus up to three ranked alternatives. The browser default comes from the earlier survey ([math-recognizers.md](https://github.com/george-vrancianu/aequate/blob/research/math-recognizers/docs/research/math-recognizers.md)): Pix2Text MFR 1.5, rasterized on pen-up, with BTTR as the second choice and TexTeller on the GPU server. Each claim below links to its source. Source-code links are pinned to the commit I read. **Unverified** marks anything I could not confirm in a primary source. *Inference* marks my own reasoning from the cited facts. **Measured** marks numbers I produced myself (method in §6).

---

## Conclusion (TL;DR)

1. **Yes for both, but we write the beam search ourselves in JS.** Neither model ships an ONNX graph that contains the decoding loop. Pix2Text MFR 1.5 ships `encoder_model.onnx` plus a single-step `decoder_model.onnx` (inputs `input_ids`, `encoder_hidden_states`, output `logits`). It has no `Loop`/`If`/`BeamSearch` nodes and no KV-cache inputs (**Measured**, graph inspection). BTTR ships no ONNX at all. A k=3 beam search over the step decoder is roughly 60 lines of JS (*Inference*). The reference algorithms to port are HF `generate` for Pix2Text and BTTR's own `beam_search` for BTTR.
2. **No off-the-shelf JS library returns top-k.** transformers.js (`main`, v4.3.1) has a `BeamSearchSampler`, but its generate loop takes the first candidate and then `break`s, under a `// TODO: Support beam search` comment. It returns no scores ([modeling_utils.js L1009–1018](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/models/modeling_utils.js#L1009-L1018)). ORT's in-graph `com.microsoft.BeamSearch` op has the right outputs (`sequences`, `sequences_scores`), but its converter only accepts `gpt2`, `t5` and `mt5` ([convert_generation.py](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/onnxruntime/python/tools/transformers/convert_generation.py)), and the WebGPU web builds compile it out (`--disable_generation_ops`) ([linux-wasm-ci.yml L60](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/tools/ci_build/github/azure-pipelines/templates/linux-wasm-ci.yml#L60)). Optimum's `ORTModelForVision2Seq` does beam search, but in Python through `GenerationMixin`, so it only helps on the server.
3. **The scores are log-probabilities, and they are not calibrated confidences.** Pix2Text's own wrapper reports either the geometric mean of the per-token max probabilities (greedy) or `exp(sequences_scores)` (beam), where HF divides the summed log-probability by `length ** length_penalty` ([latex_ocr.py L211–230](https://github.com/breezedeus/Pix2Text/blob/f52e671247c14a29aa59b44e99849e00aee984cd/pix2text/latex_ocr.py#L211-L230), [HF utils.py L3537](https://github.com/huggingface/transformers/blob/944e22eb226890dec60299386579275a66b3b44d/src/transformers/generation/utils.py#L3537)). In my five-image run, that length-normalised number stayed at 0.95 for a reading that was visibly wrong (`\frac{cx}{dx}`), while the un-normalised sequence probability fell to 0.02 (**Measured**, §6). BTTR's score is a sum of left-to-right and right-to-left log-likelihoods ([decoder.py L236–300](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/model/decoder.py#L236-L300)), so it is not a probability at all. Encoder-decoder models are known to be miscalibrated, especially at EOS ([Kumar & Sarawagi 2019](https://arxiv.org/abs/1903.00802)). **Use the scores to rank, not as a displayed percentage**, unless we fit a temperature on our own held-out set.
4. **k=3 costs about 3× greedy decoding with this export.** Native ORT CPU, Ryzen 9 5950X: greedy 35–564 ms, beam-3 150–1530 ms, ratio 2.7–4.3× (median about 2.85×). The encoder (about 90 ms at 4 threads, 300 ms at 1 thread) runs once either way (**Measured**, §6). The ratio is that high because the official decoder has no KV cache, so every step re-runs the full prefix for each beam. No published browser measurement exists for these models. *Inference:* on WASM, absolute times will be several times higher, but the ratio should hold, since both modes are compute-bound on the same kernels. Memory grows only by activations (k copies of a 578×384 encoder state, about 0.9 MB each, plus k×L×1868 logits per step). The weights (about 120 MB fp32) are shared.
5. **Server adapters differ:**
   - **TexTeller** can produce top-k (it is a stock `VisionEncoderDecoderModel` with optimum ONNX including `decoder_with_past`), but its `img2latex` exposes only `num_beams` and returns one `str` per image ([inference.py L36–121](https://github.com/OleehyO/TexTeller/blob/9b88cec77bda735aa16f9fc7e4ccb4eb1500a8b2/texteller/api/inference.py#L36-L121)). The adapter must call `model.generate(..., num_beams=k, num_return_sequences=k, output_scores=True, return_dict_in_generate=True)` itself.
   - **Mathpix**: current endpoints (`v3/text`, `v3/strokes`) return one result with `confidence` ("Estimated probability 100% correct") and `confidence_rate`. Only the **deprecated** `v3/latex` takes `beam_size` and `n_best` and returns `candidates` ([v3/text](https://docs.mathpix.com/reference/post-v3-text), [v3/strokes](https://docs.mathpix.com/reference/post-v3-strokes), [v3/latex](https://docs.mathpix.com/reference/post-v3-latex)).
   - **MyScript iink**: JIIX math gives **per-symbol** `candidates: string[]` on number, symbol and operator nodes, with no expression-level alternatives and no scores ([ExportMath.ts](https://github.com/MyScript/iinkTS/blob/dc61755198608b5025cefb6b9f9987f8e5425193/src/model/ExportMath.ts)).
6. **Recommended adapter output:** an ordered list, best first, of at most `k` deduplicated readings. Each reading carries `latex`, a backend-native `score` used only for ordering within one call, and an optional `confidence` in [0,1] that is present only when the backend or our own calibration provides one. The full shape is in §5.

---

## 1. What the exported graphs contain

### 1.1 Pix2Text MFR 1.5

| Fact | Source |
|---|---|
| The repo ships `encoder_model.onnx` (87.5 MB) and `decoder_model.onnx` (32.0 MB). It has no `decoder_with_past_model.onnx` and no `decoder_model_merged.onnx` | [HF API file list](https://huggingface.co/api/models/breezedeus/pix2text-mfr-1.5) |
| Architecture: `VisionEncoderDecoderModel`, DeiT encoder (384×384, patch 16) and TrOCR decoder (6 layers, d_model 256, vocab 1868). `use_cache: false`. `decoder_start_token_id` 1, `eos_token_id` 2, `pad_token_id` 0 | [config.json](https://huggingface.co/breezedeus/pix2text-mfr-1.5/blob/main/config.json) |
| `generation_config.json` sets no `num_beams`, so HF defaults to greedy decoding. `max_new_tokens` is 1024 | [generation_config.json](https://huggingface.co/breezedeus/pix2text-mfr-1.5/blob/main/generation_config.json) |
| Decoder graph: inputs `input_ids [batch, dec_len] int64` and `encoder_hidden_states [batch, enc_len, 384] float`. Output `logits [batch, dec_len, 1868]`. Opset 14, exported by PyTorch 2.7.0, 1498 nodes, **0 `Loop`/`If`/`Scan`/`BeamSearch`/`TopK`** | **Measured**: `onnx.load` on the downloaded file |
| Encoder graph: `pixel_values [b, 3, h, w]` → `last_hidden_state`. No control flow | **Measured**, same method |
| Model card usage: `ORTModelForVision2Seq.from_pretrained(..., use_cache=False)` then `model.generate(pixel_values)` | [model card](https://huggingface.co/breezedeus/pix2text-mfr-1.5) |

So the graph is a **per-step decoder without a KV cache**. Each call recomputes attention over the whole prefix, and the caller owns the loop. The batch dimension is dynamic, so the k beams can go through one batched `session.run` per step (**Measured**: my benchmark does exactly this).

*Inference:* re-exporting with `optimum-cli export onnx --task image-to-text-with-past` would produce `decoder_with_past`/`decoder_model_merged` and cut the per-step cost. That is the same layout TexTeller ships ([TexTeller file list](https://huggingface.co/api/models/OleehyO/TexTeller)). The trade-off is that the beam loop must then reorder `past_key_values` by beam index each step. I did not test this re-export.

### 1.2 BTTR

| Fact | Source |
|---|---|
| License MIT. A pretrained checkpoint `pretrained-2014.ckpt` (77.5 MB, Lightning checkpoint) is published as a GitHub **release asset** (v2.0, 2021-06-15). The earlier survey said "not in repo tree"; that is true of the tree, but the weights do exist | [releases](https://github.com/Green-Wood/BTTR/releases/tag/v2.0), [LICENSE](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/LICENSE) |
| No ONNX export exists in the repo | [repo tree](https://github.com/Green-Wood/BTTR/tree/43cabd43a3447ed62900182826325bd8810b9238) |
| The decoder is `nn.TransformerDecoder`, run as `forward(src, src_mask, tgt) → [b, l, vocab]` over the full target prefix with a causal mask. It has no KV cache | [decoder.py L72–122](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/model/decoder.py#L72-L122) |
| Beam search is Python code: `_beam_search` runs one direction (L2R starts at SOS, R2L at EOS). The beam shrinks as hypotheses finish. Batch size must be 1 | [decoder.py L124–234](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/model/decoder.py#L124-L234) |
| `beam_search` runs L2R beam search, rescores those hypotheses with the R2L decoder (`_cross_rate_score` adds `-sum(CE)`), then does the same in reverse. It returns all `2 × beam_size` hypotheses | [decoder.py L236–300](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/model/decoder.py#L236-L300) |
| The final pick is `max(hyps, key=h.score / len(h) ** alpha)`, with defaults `beam_size: 10` and `alpha: 1.0` | [lit_bttr.py L69–98](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/lit_bttr.py#L69-L98), [config.yaml](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/config.yaml) |

*Inference:* BTTR is a natural top-k producer, since it already computes a scored list and throws all but one away. A browser port needs (a) an ONNX export of the DenseNet encoder and (b) an export of `Decoder.forward` with dynamic `l` and batch. The direction is encoded only by which start token is fed, so one decoder graph serves both directions. The port also needs (c) the bidirectional beam search plus cross-rescoring in JS. Cost per recognition is two beam searches plus two batched rescoring passes. That is roughly 2× Pix2Text's beam cost for the same k, before differences in model size. Not measured. A third-party GGUF conversion exists on HF ([cstr/bttr-handwritten-math-gguf](https://huggingface.co/cstr/bttr-handwritten-math-gguf)), but it is not ONNX and not first-party, so it is **Unverified** as a basis.

### 1.3 Do transformers.js or ORT already provide beam search?

- **transformers.js** (`main` at the pinned commit, package v4.3.1):
  - `LogitsSampler.getSampler` returns a `BeamSearchSampler` when `num_beams > 1`, and the greedy path throws if `num_return_sequences > 1` ([logits_sampler.js L80–101](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/generation/logits_sampler.js#L80-L101)).
  - `generate` keeps only the first sampled token per row (`// TODO: Support beam search` then `break;`) and says "For now, we don't support spawning new beams" ([modeling_utils.js L957–1018](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/models/modeling_utils.js#L957-L1018)). In effect, `num_beams=3` gives a greedy result.
  - The `scores` it accumulates are never returned (`// TODO: scores,` in the return dict, [L1062–1071](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/models/modeling_utils.js#L1062-L1071)). The greedy sampler's score is documented as "meaningless" ([logits_sampler.js L108–122](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/generation/logits_sampler.js#L108-L122)).
  - It also expects `encoder_model` plus `decoder_model_merged` for `Vision2Seq` ([session_config.js L36–40](https://github.com/huggingface/transformers.js/blob/94587c4652e3debc02f2e73ef688679d04792e3a/packages/transformers/src/models/session_config.js#L36-L40)), which Pix2Text does not ship.
  - **Verdict:** transformers.js gives neither top-k nor scores. Use plain `onnxruntime-web` and our own loop.
- **ORT `com.microsoft.BeamSearch`**:
  - The op takes `num_beams` and `num_return_sequences`, and outputs `sequences (batch, num_return_sequences, len)` and `sequences_scores` ([ContribOperators.md](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/docs/ContribOperators.md#com.microsoft.BeamSearch)).
  - The converter supports only `gpt2`, `t5` and `mt5` ([convert_generation.py L121–128](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/onnxruntime/python/tools/transformers/convert_generation.py#L121-L128)).
  - ORT Web's WebGPU builds pass `--disable_generation_ops` ("Disable generation contrib operators (BeamSearch, WhisperBeamSearch, GreedySearch, Sampling)") ([linux-wasm-ci.yml L60, L151, L164](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/tools/ci_build/github/azure-pipelines/templates/linux-wasm-ci.yml#L60), [build_args.py](https://github.com/microsoft/onnxruntime/blob/84829e76d4fbb4a7258202f777fa4ff0876a3564/tools/ci_build/build_args.py)). The plain WASM build does not pass that flag (L125), so the op may be present on the CPU WASM path. **Unverified**: I did not test it in a browser.
  - *Inference:* hand-wiring a TrOCR graph into this op is not worth it for k=3.
- **Optimum** `ORTModelForVision2Seq` subclasses `ORTModelForConditionalGeneration(..., GenerationMixin)` ([modeling_seq2seq.py L750, L1459](https://github.com/huggingface/optimum-onnx/blob/46533fb66570021f52a39d77112b703762fdaada/optimum/onnxruntime/modeling_seq2seq.py#L750)). Beam search runs in Python around the ONNX sessions, which is good for a server adapter and irrelevant for the browser.

---

## 2. How sequence scores are exposed

| Source | What the number is |
|---|---|
| HF `generate`, beam | `sequences_scores` is the "final beam score": the summed token log-probabilities divided by `generated_len ** length_penalty`, with `length_penalty` defaulting to 1.0 ([utils.py L270–282](https://github.com/huggingface/transformers/blob/944e22eb226890dec60299386579275a66b3b44d/src/transformers/generation/utils.py#L270-L282), [L3537](https://github.com/huggingface/transformers/blob/944e22eb226890dec60299386579275a66b3b44d/src/transformers/generation/utils.py#L3537), worked example reconstructing it at [L1797–1806](https://github.com/huggingface/transformers/blob/944e22eb226890dec60299386579275a66b3b44d/src/transformers/generation/utils.py#L1797-L1806)) |
| Pix2Text `LatexOCR.recognize` | Returns `{'text', 'score'}`. For beam: `outs.sequences_scores.exp()`. For greedy: the geometric mean of each step's max softmax probability ("获得几何平均值", "take the geometric mean") ([latex_ocr.py L190–230](https://github.com/breezedeus/Pix2Text/blob/f52e671247c14a29aa59b44e99849e00aee984cd/pix2text/latex_ocr.py#L190-L230)). It asserts one output per image (L204), so its wrapper **cannot** return `num_return_sequences > 1`. Top-k must bypass it |
| BTTR | The `Hypothesis.score` of the finished beam is raw summed log-prob (not length-normalised) plus `-CE` from the opposite-direction decoder, ranked by `score / len ** alpha` ([decoder.py](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/model/decoder.py#L196-L215), [lit_bttr.py L97](https://github.com/Green-Wood/BTTR/blob/43cabd43a3447ed62900182826325bd8810b9238/bttr/lit_bttr.py#L97)). Range (−∞, 0], roughly 2× a single-direction log-prob |
| transformers.js | Not exposed (§1.3) |

### Are they calibrated enough to show as a confidence?

- **Literature (NMT, same encoder-decoder family):** "most modern NMT models are surprisingly miscalibrated even when conditioned on the true previous tokens", with "severe miscalibration of EOS" as a main cause ([Kumar & Sarawagi 2019](https://arxiv.org/abs/1903.00802)). Models "tend to spread too much probability mass over the hypothesis space" ([Ott et al. 2018](https://arxiv.org/abs/1803.00047)). Temperature scaling on a held-out set is the standard cheap fix for classifiers ([Guo et al. 2017](https://arxiv.org/abs/1706.04599)). I found no HMER-specific calibration study for Pix2Text, BTTR or TexTeller (**Unverified** that none exists).
- **What I saw (Measured, n=5, anecdotal):** the length-normalised score (`exp(sequences_scores)`, Pix2Text's own `score`) sat between 0.95 and 1.00 for every top reading, *including* `hw-formula3.png`. There, greedy and beam-1 both read `\frac{cx}{dx}` where the image says `\frac{dy}{dx}`. The **un-normalised** sequence probability `exp(Σ log p)` separated cases better: 0.99–1.00 on the easy images, 0.30–0.35 on the long handwritten ones, and 0.023 on the wrong one. The alternatives were sensible near-misses (`x_{j}` vs `x_{1}`, `v` vs `\times`, `s` vs `S`, `c x` vs `c d y`), which is exactly the confusion set the confirmation view is for.
- *Inference:* use the score **only to order** alternatives and to decide whether to show them (for example, auto-expand alternatives when the best sequence probability is below a threshold). Do not render it as "92% sure". If a number is wanted, renormalise within the returned k (`p_i / Σ p_j`) and label it "relative". Otherwise fit a temperature on the CROHME-2019/MathWriting evaluation harness the survey already calls for.

---

## 3. Latency and memory: k=3 vs greedy

No published measurement exists of beam vs greedy for Pix2Text MFR or BTTR under onnxruntime-web (**Unverified** absence; I searched the model card, the Pix2Text repo and docs, and the BTTR repo). My own numbers follow, for native ORT 1.31.0 CPU on an AMD Ryzen 9 5950X, official fp32 ONNX, my JS-equivalent beam loop in Python (§6). All of it is **Measured**.

| Image | Tokens | Encoder | Greedy | Beam-3 | Ratio |
|---|---|---|---|---|---|
| `18_em_1.bmp` (CROHME, `\sqrt{48}`) | 7 | 94 ms | 35 ms | 150 ms | 4.3× |
| `hw-formula1.png` | 34 | 88 ms | 184 ms | 515 ms | 2.8× |
| `math-formula-42.png` | 43 | 94 ms | 267 ms | 823 ms | 3.1× |
| `hw-formula2.png` | 73 | 97 ms | 465 ms | 1326 ms | 2.9× |
| `hw-formula3.png` (two-line system) | 73 | 93 ms | 564 ms | 1530 ms | 2.7× |
| `hw-formula1.png`, **1 thread** | 34 | 304 ms | 586 ms | 1612 ms | 2.8× |
| `hw-formula2.png`, **1 thread** | 73 | 299 ms | 1401 ms | 4056 ms | 2.9× |

(4 intra-op threads unless noted. The encoder runs once and is excluded from the greedy and beam columns.)

- **Why about 3×:** the official decoder has no KV cache, so each step processes the full `[k, L]` prefix. The beam batch is k times larger per step and decoding runs a similar number of steps. Short inputs show a higher ratio because the beam runs a few extra steps to fill k finished hypotheses (7 vs 11 steps).
- **Single-line selections** (Aequate splits multi-line selections per line using stroke geometry; see the map) are typically 10–40 tokens. *Inference:* on this desktop CPU that is roughly 0.1–0.5 s extra for k=3, and several times more on WASM on a student tablet. The survey's spike should measure that.
- **Mitigations** (*Inference*, untested):
  1. Show the greedy result immediately and stream the alternatives in when beam-3 finishes. Beam-1 equalled greedy on all five images.
  2. Re-export with a KV cache (§1.1).
  3. Run beam search only when greedy's sequence probability is below a threshold.
  4. Run in a Web Worker so the canvas never blocks.
- **Memory** (*Inference* from tensor shapes): the weights (about 120 MB fp32, per the survey) are shared across beams. The extra cost is `k × 578 × 384` floats of repeated encoder state (about 0.9 MB per copy) plus `k × L × 1868` logits per step (about 2.2 MB at k=3, L=100, because this export returns logits for the whole prefix). That is negligible next to the weights.

---

## 4. Server-side adapters

### 4.1 TexTeller

- `img2latex(model, tokenizer, images, ..., num_beams=1, no_repeat_ngram_size=0) -> list[str]` builds a `GenerationConfig(num_beams=num_beams, do_sample=False, ...)`, calls `model.generate`, and then post-processes each string (`to_katex`, `remove_style`, `format_latex`, `add_newlines`). It has no `num_return_sequences` and no scores ([inference.py L36–121](https://github.com/OleehyO/TexTeller/blob/9b88cec77bda735aa16f9fc7e4ccb4eb1500a8b2/texteller/api/inference.py#L36-L121)).
- `texteller launch` exposes `--num-beams` and the Ray Serve `predict` returns one `str` ([launch/\_\_init\_\_.py](https://github.com/OleehyO/TexTeller/blob/9b88cec77bda735aa16f9fc7e4ccb4eb1500a8b2/texteller/cli/commands/launch/__init__.py), [server.py L43–51](https://github.com/OleehyO/TexTeller/blob/9b88cec77bda735aa16f9fc7e4ccb4eb1500a8b2/texteller/cli/commands/launch/server.py#L43-L51)).
- The model is `class TexTeller(VisionEncoderDecoderModel)`, or `ORTModelForVision2Seq` with `use_onnx` ([texteller.py](https://github.com/OleehyO/TexTeller/blob/9b88cec77bda735aa16f9fc7e4ccb4eb1500a8b2/texteller/models/texteller.py)). The HF repo ships `decoder_with_past_model.onnx` and `decoder_model_merged.onnx` ([file list](https://huggingface.co/api/models/OleehyO/TexTeller)). Both paths therefore support HF beam search with `num_return_sequences=k, output_scores=True, return_dict_in_generate=True`, which returns `sequences` plus length-normalised `sequences_scores` (§2).
- **Adapter:** call `model.generate` directly with those flags, then apply TexTeller's post-processing functions to each sequence. **Deduplicate after post-processing**, because `remove_style`/`format_latex` can collapse distinct token sequences into the same string (*Inference*). Its default is greedy (`num_beams=1`), as the compute-split note already recorded.

### 4.2 Mathpix

- **`v3/text`** (current) returns one result: `text`, `latex_styled`, `confidence` ("Estimated probability 100% correct", [0,1]) and `confidence_rate` ("Estimated confidence of output quality", [0,1]). With `include_line_data`, each `LineData` has its own `confidence`/`confidence_rate`. Request knobs `confidence_threshold` and `confidence_rate_threshold` (default 0.75) turn low confidence into a `math_confidence` error ([v3/text reference](https://docs.mathpix.com/reference/post-v3-text)). It offers no alternatives.
- **`v3/strokes`** (ink input) returns the same `confidence`/`confidence_rate` pair and no alternatives ([v3/strokes reference](https://docs.mathpix.com/reference/post-v3-strokes)).
- **`v3/latex`** ("Deprecated - use v3/text instead") is the only endpoint with n-best. It takes `beam_size` ([1,10], "Number of results to consider") and `n_best` ([1, beam_size], "Number of highest-confidence results to return. Requires beam_size"), and returns `candidates: object[]` ("n_best results") plus `latex_confidence` and `latex_confidence_rate` ([v3/latex reference](https://docs.mathpix.com/reference/post-v3-latex)). The fields inside each candidate object are not documented on that page (**Unverified**).
- *Inference:* Mathpix is the only backend that claims a calibrated probability ("probability 100% correct"), but only for the single top result. An adapter on `v3/text`/`v3/strokes` returns k=1 with `confidence`. Using `v3/latex` for alternatives means building on a deprecated endpoint.

### 4.3 MyScript iink

- In JIIX, a math element is an expression tree (`expressions: TJIIXMathExpression[]`). Number, symbol and operator nodes carry `symbols?: { symbol: string; candidates?: string[] }[]`. These are per-symbol alternatives with **no scores** and no whole-expression n-best ([iinkTS ExportMath.ts](https://github.com/MyScript/iinkTS/blob/dc61755198608b5025cefb6b9f9987f8e5425193/src/model/ExportMath.ts)). Text words and characters have the analogous `candidates?: string[]` ([ExportCommon.ts](https://github.com/MyScript/iinkTS/blob/dc61755198608b5025cefb6b9f9987f8e5425193/src/model/ExportCommon.ts)), and iinkTS's smart guide renders them as a pick list for text ([InteractiveInkSSRSmartGuide.ts](https://github.com/MyScript/iinkTS/blob/dc61755198608b5025cefb6b9f9987f8e5425193/src/smartguide/InteractiveInkSSRSmartGuide.ts)).
- The official JIIX reference pages on developer.myscript.com returned HTTP 404 to every fetch I tried, so these facts come from MyScript's own TypeScript types, not the prose docs. Whether math symbol candidates need an `export.jiix.*` flag to appear is **Unverified**.
- *Inference:* the adapter can synthesise up to k whole-expression alternatives. Substitute one symbol candidate at a time into the top label (the LaTeX label via `export.jiix.math-label`) and rank by position in the candidate list. The result has `score` null and is ordinal only.

---

## 5. Recommended adapter output shape

Every recognizer adapter (browser Pix2Text or BTTR, TexTeller, Mathpix, MyScript) returns the same shape:

```ts
type Reading = {
  latex: string;          // normalised LaTeX, after the adapter's post-processing
  score: number | null;   // backend-native ranking score; comparable ONLY within one result
  confidence?: number;    // [0,1], present only if calibrated (Mathpix top-1, or our own temperature fit)
};

type RecognitionResult = {
  readings: Reading[];    // best first, deduplicated on `latex`, length 1..k (k ≤ 3 for the view)
  scoreKind: 'logprob' | 'logprob_norm' | 'bidir_logprob' | 'vendor_confidence' | 'ordinal';
  recognizer: { id: string; version: string };   // already part of the cache key (compute-split note §2)
};
```

Rationale (*Inference* from §§1–4):

- **A list of `{latex, score}` is enough for the view**, but the scores are not comparable across backends: log-prob, length-normalised log-prob, BTTR's bidirectional sum, Mathpix probability, and MyScript's lack of any score. `scoreKind` makes that explicit, so nobody shows a TexTeller log-prob next to a Mathpix probability.
- **For the beam backends, store the un-normalised sequence log-prob** (`Σ log p`) as `score`. In the measurements it tracked "this might be wrong" better than the length-normalised value. The adapter can still *order* by the length-normalised value, as HF does. Recomputing one from the other only needs the token count.
- **Keep `confidence` optional and separate.** It is filled only by a vendor that documents it as a probability (Mathpix `confidence`), or later by a per-recognizer temperature fitted on the evaluation harness.
- **Deduplicate after normalisation, and allow fewer than k readings.** Beams often differ only in tokens that post-processing removes (`\mathrm{...}`, a leading `~`, as in the `18_em_1.bmp` run). The view must handle 1–3 readings.
- **Cache the whole `RecognitionResult`, not just the top reading**, under the existing key (strokes hash + recognizer id/version + preprocessing version). Then picking an alternative never re-runs recognition.

---

## 6. Method for the measured numbers

- **Graph inspection:** I downloaded `encoder_model.onnx` and `decoder_model.onnx` from `breezedeus/pix2text-mfr-1.5` (main, 2026-10-23) and listed graph inputs and outputs and op-type counts with `onnx.load`.
- **Benchmark:**
  - Setup: onnxruntime 1.31.0 (Python, CPUExecutionProvider), `intra_op_num_threads` 4 or 1.
  - Preprocessing: matches `preprocessor_config.json` (RGB, bicubic resize to 384×384, rescale 1/255, normalise mean 0.5 / std 0.5).
  - Greedy: argmax per step until EOS.
  - Beam-3: one batched decoder call per step over the live beams. Take the top 2k continuations per beam, keep the best k non-EOS, and move EOS hypotheses to a finished list scored by `Σ log p / len`. Stop once k hypotheses are finished and the best live beam's normalised score cannot beat the worst finished one (HF's `early_stopping=False` heuristic).
  - Timing: one warm-up, then the mean of 3 runs.
- **Images:** `hw-formula{1,2,3}.png` and `math-formula-42.png` from [Pix2Text docs/examples](https://github.com/breezedeus/Pix2Text/tree/f52e671247c14a29aa59b44e99849e00aee984cd/docs/examples), and `18_em_1.bmp` (a CROHME sample) from [BTTR example/](https://github.com/Green-Wood/BTTR/tree/43cabd43a3447ed62900182826325bd8810b9238/example).
- **Limits:** five images is anecdotal. These are native-CPU numbers, not WASM, not a tablet, and fp32 rather than int8. The Pix2Text wrapper's own preprocessing may differ slightly from the bare processor config.

Top-3 readings from the run (abridged; `p` is `exp(Σ log p)`):

| Image | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| hw-formula1 | `… ^{t_{2}} v\,dt` (p 0.30) | `… \times dt` (0.12) | `… \cup dt` (0.04) |
| hw-formula2 | `… \frac{i x_{j}}{2t} …` (0.35) | `… x_{1} …` (0.21) | `… e^{-tS^{2}} …` (0.06) |
| hw-formula3 | `… 3(\frac{cx}{dx})^{3} …` (0.023) | `… \frac{c d y}{dx} …` (0.010) | `… \frac{c \times y}{dx} …` (0.008) |
| 18_em_1 | `\sqrt{48}` (0.9999) | `\mathrm{\sqrt{48}}` (≈0) | `~\sqrt{48}` (≈0) |
| math-formula-42 | `\lim_{x\to\frac14}\frac{1-4^{x-\frac14}}{1-4x}` (0.99) | `… 4^{^{x-…}}` (0.005) | `… 4^{\pi-…}` (0.0003) |

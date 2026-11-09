---
status: accepted (provisional)
---

# Pix2Text MFR 1.5 in the browser, with TexTeller and Mathpix adapters

The default recognizer is Pix2Text MFR 1.5, run in the student's browser with `onnxruntime-web`. Each line of a selection is drawn as dark ink on white and read as an image. We write the k=3 beam search ourselves, because the official ONNX graphs are single-step and no JS library returns ranked readings. Two more adapters ship behind the same interface: TexTeller on the server, offered only in the GPU Compose profile, and Mathpix (`v3/strokes`) when an admin configures a key. The admin picks one recognizer per instance. We chose an image model even though we store strokes because no open stroke model is usable: TAP has no license, Seshat is GPL and weak, and Google's MathWriting model has no released weights and non-commercial training data. Pix2Text is MIT, ships official ONNX of about 120 MB and can spell any LaTeX. The product promise is "recognise on selection, always confirmed", replacing the handoff's "recognise on pen-up": no transcription becomes a step until the student confirms it.

The decision is provisional because the recognition spike was deferred until the app produces usage data from confirmed selections. Revisit the choice between Pix2Text, BTTR, distilling TexTeller and training a stroke model if, in real use, the first reading is accepted unchanged on fewer than about 60% of confirmed selections, students edit the LaTeX by hand on more than about 25% of them, or the median time from selection to readings on the target iPad exceeds about 3 s.

## Considered Options

- **BTTR in the browser.** MIT, but its 110-token CROHME dictionary cannot emit systems, matrices or `cases`, and it has no ONNX export. Kept as a documented fallback, not shipped.
- **Distilling TexTeller into a small model.** Its Apache-2.0 license allows it, but the provenance of its handwritten training data is unconfirmed and may carry non-commercial terms.
- **Training a stroke model on the MathWriting recipe.** The strongest published approach, but the data is CC BY-NC-SA, whether shipped weights inherit that is unsettled, and it costs GPU-days of training.
- **MyScript iink as the commercial adapter.** Its interactive mode is a stateful WebSocket with a heavier client SDK and gives only per-symbol candidates. It can come later behind the same interface.
- **TexTeller on CPU.** It ships ONNX, but at about 1.25 GB its CPU latency is unmeasured.
- **Choosing the recognizer per student or per board.** More settings for no gain at v1's scale.

## Consequences

- The adapter takes one line's strokes and k, and returns `{readings: [{latex, score, confidence?}], scoreKind, recognizer}`. Image adapters share one drawing module. Lines are split from stroke geometry before the adapter.
- A notation normalizer (Romanian notation, the decimal comma, `sin` without a backslash) runs after every adapter, so no adapter handles locale.
- Each transcription records the recognizer and its version. If a server adapter fails or the app is offline, recognition falls back to the browser model and the student sees which one ran.
- Mathpix returns one reading, so it offers no alternatives in the confirmation view. It sends students' ink to a third party, so it is off by default, enabled only by an admin after a warning, and named in the privacy notice while active.
- The model is served by the instance, downloaded lazily on the first selection with a progress bar and cached by the service worker. v1 ships fp32; int8 replaces it only if the rate of correct first readings holds within a couple of points.
- This refines ADR 0003's offline queue: with the model cached, recognition runs offline right away, and only checks, solves and hints wait. A selection waits too if the model is not cached yet.
- The PaddleOCR text layer and the Qwen-VL adapter are out of v1.

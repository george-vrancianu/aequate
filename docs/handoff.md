# Aequate – Handoff

Open-source, self-hosted shared blackboard for private tutors teaching math and sciences live to 1–5 students: stylus handwriting, math recognition, automatic step checking, built-in video and chat.

Date: 2026-10-08. Working name: **Aequate** (Latin *aequare*, to make equal). Availability of GitHub org, npm scope and domain not yet checked.

Companion artifacts:
- Full spec (live doc): https://claude.ai/artifact/FnXgkz7SduhhxhMkYkUr4D
- Design canvas, three screens: https://claude.ai/artifact/7XdNWBAukNKMhR89ijwMpt

---

## 1. Decisions

| Area | Decision |
| --- | --- |
| Customer | Private tutors; 1:1 and small groups (2–5 students) |
| Platforms | Web + tablet with stylus at launch; phone view-only later |
| Model | Free, open source, self-hostable only (no project-run cloud) |
| Hardware | Runs on a cheap VPS; GPU optional and auto-detected |
| Subject focus | Math and sciences first |
| Video/voice | Built in at launch, SFU-based |
| Recognition | Pluggable backend; strokes always stored |
| Auto-checking | Real-time, as the student writes; CAS is the only judge |
| Check visibility | Tutor sees results; can reveal to student |
| Accounts | Tutors only; students join by link/code, optional device token |
| Async work | Secondary; live sessions are the product |
| i18n | Full from day one; English and Romanian maintained by core |
| LLM | Optional plugin, off by default; local model preferred |
| Recording | Nice to have, not MVP |
| License | Leaning AGPL-3.0 server + MIT plugin SDK/client libs (confirm with a lawyer) |

## 2. MVP scope

**Board** – infinite canvas with pages; low-latency stylus ink with pressure and palm rejection; pen, highlighter, eraser, text, shapes with snapping; templates (grid, graph, axes, periodic table); image/PDF upload and annotation; multi-cursor presence; per-user undo; strokes never flattened.

**Session** – shared teacher board + one private board per student; tutor dashboard with a live tile per student and check status; join by link or 6-character code; "remember this device"; device pairing (laptop for video, tablet for ink).

**Communication** – built-in video/voice (2–6 participants), screen share, audio-only fallback; chat with LaTeX rendering and image paste; "I'm stuck" button.

**Tutor controls** – lock/unlock editing per student or all; spotlight a region; pull a student's private board into shared view; mute/pin/remove; breakout boards with timer; raise hand.

**Math** – stroke-based recognition on pen-up, optional heavier re-recognize; recognized layer beside ink with inline correction; locale-aware notation (decimal comma, tg/tan, European division layout); CAS equivalence check per line, incremental and cached; tutor-only green/amber/red ticks and cross-student heatmap; hint ladder; unit-aware physics (Pint); chemistry balancing; graph a recognized function with parameter sliders; problem bank with per-student copies.

**Export** – PDF, PNG, Markdown + LaTeX; read-only recap link.

## 3. Deferred (v2+)

Session recording and replay (strokes + audio); homework mode; photo-to-board; LLM plugin UI; subject plugins (circuits, geometry constructions, music staff, chemistry structures); accessibility modes (TTS, high contrast); parent portal; phone clients; opt-in anonymous metrics; multi-tenant mode.

## 4. Architecture

One Docker Compose stack; GPU-only services start only when CUDA is detected.

```
Browser/tablet client ── WebSocket/CRDT ── Realtime sync ── Postgres + object storage
   │                                            │
   │  WebRTC                                    ▼
   └──────── Media SFU (LiveKit) + TURN     Recognition service ──► CAS checker ──► results to tutor sockets only
                                                                           │
                                                                           ▼ (optional, off by default)
                                                                      Local LLM plugin
```

| Layer | Choice | Why |
| --- | --- | --- |
| Client | TypeScript; React or Svelte; Perfect Freehand or tldraw-style ink engine | Stylus/pressure support, ecosystem |
| Sync | Yjs CRDT over WebSocket (Hocuspocus or y-websocket) | Local-first, offline-safe merge |
| API/auth | Node (Fastify) or Go; Lucia or Auth.js | Light, easy to self-host |
| Recognition | Python service with adapter interface; ONNX stroke model in browser by default | Pluggable, CPU-friendly |
| CAS | Python, SymPy, Pint; worker queue | Mature, deterministic |
| Media | LiveKit + coturn | Scales to small groups |
| Storage | PostgreSQL + MinIO (S3-compatible) | Standard, portable |
| i18n | ICU message format; Weblate | Community translations |
| Deploy | Docker Compose, single .env, GPU profile | One-command install |

**Routing rule that must hold:** check results are computed server-side and delivered only to tutor sockets until the tutor reveals them. Student clients never receive verdicts by default.

## 5. Recognition backends

Store strokes for every mark. Stroke-based (online) recognition is cheaper and more accurate than image-based.

| Option | Examples | Role |
| --- | --- | --- |
| Commercial stroke SDK | MyScript iink, Mathpix | "Bring your own key" plugin |
| Open image-to-LaTeX | TexTeller, pix2tex, Pix2Text | Default GPU backend (check licenses; synthetic-trained) |
| Open-weight VLM | Qwen-VL family | Optional "pro" backend; needs real GPU, seconds of latency |
| Academic stroke models | CROHME-style HMER | Default CPU/browser backend via ONNX; needs fine-tuning work |
| Text OCR | Tesseract (easy), PaddleOCR (better handwriting) | Non-math text layer |

Launch with three adapters: browser stroke model, TexTeller when CUDA present, commercial API when a key is configured. Promise "recognize on pen-up with correction UI", not flawless live recognition.

## 6. Local LLM for math

The CAS decides correctness; the LLM only explains and suggests, always given the recognized LaTeX and the CAS verdict as input, never raw strokes.

| Job | Who |
| --- | --- |
| Is this step correct? | CAS |
| Why is it wrong, in plain words | Local LLM |
| Hint ladder (next nudge) | Local LLM, tutor approves |
| Generate practice problems | LLM drafts, CAS verifies answer key |
| Session summary | Local LLM, post-session |
| Handwriting → LaTeX | Stroke recognizer; VLM only as pro adapter |

Hardware: 7–8B math-tuned model, 4-bit, ~5–8 GB VRAM, 2–10 s per hint on a consumer GPU; 14B ~10–12 GB, better reasoning; CPU-only is summaries-only. Integration: Ollama or llama.cpp container, one `/suggest` endpoint behind the provider interface; hosted API adapters share the interface; prompts carry locale.

## 7. Privacy and i18n

- Students are often minors; the self-hosting tutor is the data controller. Ship retention settings and one-click purge per student and per session.
- Video, chat, recordings never leave the self-hosted server; recordings off by default; no telemetry unless opted in.
- ICU message format, RTL-safe layout; locale drives notation in recognition and checking; board content stays locale-neutral.

## 8. Design direction (from the canvas)

Three screens exist: tutor live session (1440 wide, fluid), student tablet board (1180×820), student join-by-code (1280, fluid).

- Ground `#F4F3EE`, surfaces `#FFFFFF`, borders `#DEDCD3`, text `#1B1B1A`, secondary text `#52514C`
- Board `#1F3A33` (deep green), chalk ink `#F3EFE4`, highlighter `#F2C94C`, second pen `#7FB8F0`
- Action/link `#2F6FED` (hover `#1F4FB3`); status good `#3E8E5A`, warn `#C98A1B`, bad `#D1513E`
- Type: IBM Plex Sans (UI), IBM Plex Mono (recognized math, codes)
- Radii 8–12 px; touch targets ≥44 px; tutor-only check ticks float on the board's top-right; hints appear bottom-left on the student board

## 9. Open questions

- Which recognition model ships as the browser default: fine-tune a CROHME model or distil TexTeller?
- How does the CAS treat multiple valid forms (factored vs expanded) when deciding "equivalent"?
- Does a Yjs doc stay manageable at thousands of strokes, or do boards chunk per page?
- Will students ever get accounts (progress history)?
- Dual licensing yes/no — decides whether a CLA is needed from the first contributor.

## 10. Next steps (in order)

1. Check Aequate availability: GitHub org, npm scope, domain, RO/EU trademark search
2. Decide license; add LICENSE, CONTRIBUTING, CLA if needed
3. Spike 1 – ink engine on iPad and Surface; measure pen-to-pixel latency
4. Spike 2 – browser stroke recognition via ONNX on 50 real handwritten samples
5. Spike 3 – LiveKit with 6 participants on a 2 vCPU VPS
6. Spike 4 – SymPy equivalence on 20 typical algebra steps
7. Write the recognition adapter interface and the check-result routing rule
8. Docker Compose skeleton with CPU and GPU profiles
9. Weblate with English and Romanian
10. Shortlist two open-weight math models; benchmark on 50 real student errors; define the hint-ladder prompt format

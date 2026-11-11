# Aequate

An open-source, self-hosted shared blackboard for private tutors teaching math and sciences live to one to five students: stylus handwriting, math recognition, automatic step checking, and built-in video and chat.

## Status

Research and decisions. There is no application code yet. This repository holds the spec, the architecture decision records and the research notes behind them. Prototypes and further notes live on their own branches.

## How it is meant to work

1. A student writes by hand on a private board. Strokes are always stored.
2. A recognizer turns the strokes into LaTeX.
3. SymPy parses the LaTeX and checks each step against the previous one.
4. The verdict goes to the tutor only, until the tutor chooses to reveal it.
5. An optional local LLM rewords hints. It never decides whether a step is correct.

The rule that holds throughout: the computer algebra system is the only judge.

## Decisions so far

| ADR | Decision |
| --- | --- |
| [0001](docs/adr/0001-llm-only-rewords-cas-hints.md) | The LLM only rewords CAS hints |
| [0002](docs/adr/0002-check-verdicts-over-real-solution-sets.md) | Check verdicts over real solution sets |
| [0003](docs/adr/0003-react-spa-with-own-ink-engine.md) | React SPA with its own ink engine |
| [0004](docs/adr/0004-pix2text-in-the-browser-with-server-and-key-adapters.md) | Pix2Text in the browser, with server and bring-your-own-key adapters |
| [0005](docs/adr/0005-hint-llm-behind-openai-compatible-endpoint-checked-before-display.md) | Hint LLM behind an OpenAI-compatible endpoint, checked before display |
| [0006](docs/adr/0006-student-work-private-per-student-grants.md) | Student work is private, with per-student grants |
| [0007](docs/adr/0007-agpl-with-dco-no-dual-licensing.md) | AGPL with DCO, no dual licensing |
| [0008](docs/adr/0008-yjs-hocuspocus-doc-per-page-plus-board-doc.md) | Yjs with Hocuspocus: one document per page plus a board document |

## Research so far

- [Yjs at thousands of strokes](docs/research/yjs-scaling.md): whether one Yjs document stays manageable at thousands of ink strokes, which sync server suits Postgres persistence, and what tldraw and Excalidraw do. Led to ADR 0008.
- [Recognition vs. compute](docs/research/recognition-compute-split.md): use separate stages, not one model. Recognizer, then SymPy parse, then SymPy equivalence check, with an optional LLM afterwards for explanations only.
- [Recognizer accuracy by structure type](docs/research/recognizer-structure-accuracy.md): accuracy depends more on nesting depth and length than on which symbols appear. Compares Pix2Text MFR 1.5, TexTeller 3.0 and BTTR from their papers and vocabularies; no model was run.
- [SymPy LaTeX parser coverage](docs/research/sympy-latex-parser-coverage.md): use the ANTLR parser in strict mode behind a normalizer and two post-parse guards, with Lark as a cross-check that rejects on disagreement.

More notes and prototypes are on branches, including `research/math-recognizers`, `research/sympy-equivalence`, `prototype/cas-hard-steps`, `prototype/cas-domain-tracking`, `prototype/hocuspocus-incremental-store`, `prototype/yjs-churn-and-tablet` and `prototype/hint-model-bakeoff`.

## Planned stack

React and TypeScript client with its own ink engine · Yjs and Hocuspocus for sync · Pix2Text recognition in the browser · Python with SymPy and Pint for checking · LiveKit for video · PostgreSQL and S3-compatible object storage · Docker Compose for self-hosting.

## Docs

- [Handoff](docs/handoff.md): scope, architecture and open questions
- [Glossary](GLOSSARY.md): the domain language
- [Contributing](CONTRIBUTING.md): licensing and sign-off

## License

AGPL-3.0-or-later for code; documentation, the glossary and ADRs are under CC-BY-4.0. External pull requests are on hold until the licensing review is done; issues and discussion are welcome.

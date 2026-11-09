# PROTOTYPE (throwaway): Yjs board under churn, and on a low-end tablet

Answers Wayfinder ticket #39. Throwaway code, no tests, not for production. Branch: `prototype/yjs-churn-and-tablet` (built on `prototype/yjs-board-sync`).

Results: [RESULTS.md](RESULTS.md). Raw data: `results.json`, `results/*.json` (churn), `tablet/desktop-baseline.json` (desktop browser).

Reuse note: the stroke generator, packing (`pack`/`unpack`), seeded RNG and `median`/`pct` are **copied** into `lib.js` from `../yjs-board-sync/lib.js` (importing it would resolve `yjs` from that folder's node_modules, which this folder does not have). The churn model (per-origin UndoManager, stack cap by trimming on `stack-item-added`) follows `../yjs-board-sync/undo.js`.

## Setup

```
npm install                          # once (esbuild, playwright, yjs, hocuspocus)
npx playwright install chromium-headless-shell   # only for the local desktop verification
```

## Part 1: churn (`churn.js`)

```
npm run churn          # ~15 min: 1k/5k/10k x {board, page} x gc {true,false}, plus retention variants at 5k. Writes results/*.json and results.json
node --expose-gc churn.js quick   # 1k smoke test (writes results/quick.json)
```

Each config runs in its own child process (`--max-old-space-size=4096`, waits while host memory used > 18 GB). Generate the tables in RESULTS.md with `node tables.js`.

## Part 2: tablet (`tablet/`)

```
npm run tablet                       # Hocuspocus + page on 0.0.0.0:8787 (PORT=1234 npm run tablet, or --port 1234)
npm run tablet:verify                # headless Chromium against an ephemeral port, writes tablet/desktop-baseline.json
```

Human steps (port proxy, firewall, iPad): [TABLET.md](TABLET.md).

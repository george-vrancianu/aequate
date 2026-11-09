# Incremental Hocuspocus store: update log plus compaction (PROTOTYPE, ticket #38)

Question: does an incremental store (append each update to a log, compact now and then) make one Yjs doc per board viable at 10k strokes, or does it still point to one doc per page?

Setup: WSL2, Ryzen 9 5950X, Node 24, Yjs 13.6.x, Hocuspocus server 4.8.0 and provider 4.x over loopback WebSocket, SQLite via `node:sqlite` (WAL, synchronous=NORMAL) on real disk. All numbers are relative, not absolute. Server, 4 to 5 clients and the benchmark share ONE Node process and event loop, so ping and latency figures are pessimistic and noisy (the "no storage" row shows the noise floor). Server config: `debounce` 100 ms, `maxDebounce` 500 ms (scaled down from the 2 s / 10 s defaults). Stroke generator is the sync spike's (lib.js, 50 to 300 points, packed ~0.45 to 0.8 KB). Board = one Y.Doc with 5 root maps `strokes:<page>` (layout A); "per page" = 20 docs `pg:<N>:<p>` (layout C). Raw data: `results.json`; all generated tables (every size): `results-tables.md`.

Stores compared (all are real Hocuspocus extensions, see store.js):
- **full**: stock Database-extension pattern, `onStoreDocument` writes whole `Y.encodeStateAsUpdate`, `onLoadDocument` applies it. Baseline, re-measured here.
- **log**: `onChange` appends `payload.update` as one row per update (synchronous `INSERT` in the hook). Compaction (one SQLite transaction: write snapshot, delete rows up to max id) triggered by **count** (500 updates), **bytes** (512 KiB of log), or **last disconnect** (`onDisconnect` with `clientsCount === 0`). Snapshot = `encodeStateAsUpdate(live doc)` ("doc" mode) unless noted; "merge" mode = `Y.mergeUpdates(snapshot + rows)`.
- **batched log**: `onChange` queues, `onStoreDocument` appends ONE `Y.mergeUpdates` row per debounced save; compaction on last disconnect.
- **per page**: one doc per page (20 pages), full rewrite. Reference point.

## 1. Facts

### 1.1 Bytes written and write latency for one added stroke (steady state)

| strokes on board | full rewrite, doc per board | full rewrite, doc per page (20) | update log row | batched log row |
|---|---|---|---|---|
| 1k | 558 KB, 2.7 ms | 31 KB, 0.3 ms | 443 B, 0.1 ms | 443 B, 0.1 ms |
| 3k | 1.70 MB, 11 ms | 83 KB, 0.5 ms | 752 B, 0.1 ms | 752 B, 0.1 ms |
| 5k | 2.81 MB, 21 ms | 140 KB, 0.9 ms | 831 B, 0.1 ms | 831 B, 0.1 ms |
| 10k | 5.64 MB, 50 ms | 274 KB, 1.2 ms | 642 B, 0.1 ms | 642 B, 0.1 ms |

(Time is encode + SQLite write, on the server event loop. Batched equals per-update here because one stroke is saved at a time; its benefit shows in the session table.) At 10k the log writes about 8,800 times fewer bytes per save than the board rewrite. The update per stroke is ~0.4 to 0.8 KB at any board size.

### 1.2 Load time: log replay vs snapshot + tail (cold open through Hocuspocus; server-side `onLoadDocument` ms in brackets)

Log built by a real client writing N strokes, then erasing 10% (one update per op), so rows = 1.1 N.

| strokes | log rows / MB | live state MB | log replay, direct, no server | `mergeUpdates` then apply, direct | open, log NOT compacted | open after compaction (snapshot only) | open snapshot + 100-row tail |
|---|---|---|---|---|---|---|---|
| 1k | 1,100 / 0.54 | 0.48 | 14 ms | 47 ms | 94 ms (30) | 12 ms (2.4) | 15 ms (3.3) |
| 3k | 3,300 / 1.65 | 1.47 | 30 ms | 140 ms | 118 ms (80) | 19 ms (5.7) | 21 ms (7.3) |
| 5k | 5,500 / 2.73 | 2.42 | 40 ms | 396 ms | 213 ms (156) | 39 ms (12) | 31 ms (10) |
| 10k | 11,000 / 5.49 | 4.87 | 105 ms | 1,518 ms | 442 ms (381) | 93 ms (24) | 84 ms (25) |

An uncompacted log at 10k is ~16x slower to load on the server than a snapshot (381 vs 24 ms) and ~13% larger than the live state (per-row overhead and erased content kept). A short tail (100 rows) costs next to nothing. `Y.mergeUpdates` over thousands of rows is far slower than applying them row by row (superlinear), so do not use it as the load path.

### 1.3 Compaction cost, and does it block other connections

Compacting the whole 1.1 N-row log on a live server doc while a second pair of clients pings through the same server (a ping arrives every 5 ms; "gap" = time between consecutive arrivals).

| strokes | mode | compaction ms | snapshot size | biggest ping arrival gap during compaction |
|---|---|---|---|---|
| 1k | doc (`encodeStateAsUpdate`) | 36 | 0.48 MB | 41 ms |
| 1k | merge (`Y.mergeUpdates`) | 20 | 0.53 MB | 26 ms |
| 3k | doc | 46 | 1.47 MB | 51 ms |
| 3k | merge | 163 | 1.62 MB | 168 ms |
| 5k | doc | 53 | 2.42 MB | 56 ms |
| 5k | merge | 394 | 2.68 MB | 398 ms |
| 10k | doc | 86 | 4.87 MB | 90 ms |
| 10k | merge | 1,491 | 5.38 MB | 1,496 ms |

Compaction is synchronous JavaScript plus a SQLite transaction, so it **blocks every connection on that server process** for its whole duration (gap = compaction time; calm gap is 5 ms). Doc mode (encode the live doc) is the cheap one (86 ms at 10k); merge mode costs 1.5 s at 10k and keeps erased content (snapshot ~10% larger). The stock full rewrite has the same kind of stall on *every save*: the whole-board save is 50 ms at 10k (encode alone), visible below.

### 1.4 Session: a student writes 2,000 strokes with ~10% erase or undo (222 extra ops), two sessions of 1,000 strokes with disconnect and reconnect, board already holding N strokes

Strokes are issued every ~4 ms (about 250x faster than a person), so with `debounce` 100 ms the stock store coalesces ~110 strokes per save (18 saves in total). This **flatters the full-rewrite totals**: at a human pace with Hocuspocus defaults (2 s debounce, a stroke every second or so) each save carries about one stroke, so the full-rewrite total would be near 2,000 x (bytes per save in 1.1), e.g. ~11 GB at 10k (extrapolation, not measured). Log appends are per update whatever the pace.

Totals over both sessions (bytes include compaction snapshots). "Rows left" = log rows/KB still stored after session 1 / session 2.

| strokes on board | store | writes | bytes written | bytes per stroke | median bytes per write | compactions (ms) | rows left after s1 / s2 | worst ping arrival gap (ms) |
|---|---|---|---|---|---|---|---|---|
| 10k | full rewrite, doc per board | 18 | 106.4 MB | 54 KB | 6,055 KB | - | - | 87 |
| 10k | full rewrite, doc per page | 20 | 8.7 MB | 4.4 KB | 454 KB | - | - | 28 |
| 10k | log, compact @500 updates | 2,208 | 24.8 MB | 13 KB | 0.5 KB | count: 58, 47, 56, 74 | 121 / 208 | 84 |
| 10k | log, compact @512 KiB | 2,208 | 13.2 MB | 6.7 KB | 0.5 KB | bytes: 66, 54 | 93 / 188 | 76 |
| 10k | log, compact on last disconnect | 2,208 | 13.3 MB | 6.8 KB | 0.5 KB | disconnect: 71, 76 | 0 / 0 | 32 |
| 10k | batched log, compact on disconnect | 18 | 13.3 MB | 6.8 KB | 66 KB | disconnect: 64, 62 | 0 / 0 | 22 |
| 10k | no storage (noise floor) | - | 0 | - | - | - | - | 10 |
| 1k | full rewrite, doc per board | 18 | 19.2 MB | 9.8 KB | 1,095 KB | - | - | 39 |
| 1k | log, compact @500 updates | 2,208 | 5.4 MB | 2.8 KB | 0.5 KB | count: 3, 28, 30, 32 | 121 / 208 | 42 |
| 1k | log, compact on last disconnect | 2,208 | 3.6 MB | 1.9 KB | 0.5 KB | disconnect: 5, 33 | 0 / 0 | 50 |

All four sizes are in `results-tables.md`. The 5k and 3k rows follow the same shape. In the log rows, the bytes beyond ~1.3 MB (the 2,208 appended updates) are compaction snapshots: each compaction rewrites the whole ~5 MB board, so **count-based compaction at 10k (4 compactions) writes ~2x the bytes of a bytes- or disconnect-triggered one**. A pure threshold that ignores board size is the wrong policy; the cost of a compaction scales with the board, the benefit with the log length.

Log growth (rows / KB after every 200 strokes, 10k board, no compaction until disconnect): session 1: 220/109, 438/224, 672/336, 897/446, 1120/558; session 2 restarts from 0 after the disconnect compaction and reaches 1086/564. About 560 KB of log per 1,000 strokes, i.e. ~0.5 KB per update, ~11% more rows than strokes. A heavy erase/undo session did not change the picture (stored strokes after reload always equal live strokes, see 1.5).

Write latency of a log append: p50 0.08 to 0.11 ms, p99 0.2 to 0.4 ms, with rare ~20 ms outliers (up to 63 ms once at 5k; likely SQLite WAL checkpoints on WSL2). Whole-board full rewrite at 10k: p50 63 ms, max 82 ms per save.

### 1.5 Correctness (PASS/FAIL: state vector AND content digest (sha1 of every key and packed stroke) of the doc reloaded from storage only vs the live client doc)

| check | 1k | 3k | 5k | 10k |
|---|---|---|---|---|
| log replay == live | PASS | PASS | PASS | PASS |
| `Y.mergeUpdates` of log == live | PASS | PASS | PASS | PASS |
| after compaction (doc mode) == live | PASS | PASS | PASS | PASS |
| after compaction (merge mode) == live | PASS | PASS | PASS | PASS |
| snapshot + 100-row tail == live | PASS | PASS | PASS | PASS |
| session 1 and session 2 reload == live, every storing variant (6 variants x 2 sessions) | PASS | PASS | PASS | PASS |

Crash tests (separate process running a real server and client; after writing 600 strokes with ~10% erases onto a 1,000-stroke board the process kills itself with SIGKILL: no unload, no flush, no compaction; then the sqlite file is reopened and loaded with no server):

| scenario | recovered / expected strokes | state vector equal | content equal | result |
|---|---|---|---|---|
| log, one row per update (`onChange`), killed before any compaction | 1530 / 1530 | yes | yes | PASS |
| log + count compaction already ran mid-session, then killed | 1530 / 1530 | yes | yes | PASS |
| log, killed inside the compaction transaction before COMMIT (snapshot written, rows deleted, not committed) | 1530 / 1530 (log left intact, snapshot unchanged) | yes | yes | PASS |
| batched log (row per `onStoreDocument`), killed | 1411 / 1530 | no | no | FAIL (loses the unsaved debounce window) |
| stock full rewrite, killed | 1413 / 1530 | no | no | FAIL (loses everything since the last debounced save) |

The two FAILs are the baseline's own durability gap, shown for contrast, not a bug in the log. The per-update log loses nothing that the server had received.

## 2. Hocuspocus specifics (installed 4.8.0; file `node_modules/@hocuspocus/server/dist/hocuspocus-server.esm.js`)

- **Debounce**: defaults `debounce: 2e3`, `maxDebounce: 1e4` (lines 1244-1245). `storeDocumentHooks` (1548-1570) calls `debouncer.debounce(id, fn, debounce, maxDebounce)`. Every update re-arms the timer; once `Date.now() - start >= maxDebounce` it runs immediately (1211). A continuously writing user is therefore saved on the `maxDebounce` clock, not the `debounce` one (that is why the session above saved ~every 500 ms).
- **`onChange` has the update bytes**: `Document.handleUpdate` (line 682) passes the Yjs `update` (v1 bytes) to `onUpdate`, wired at 1502 (registered AFTER `onLoadDocument` finishes, so updates applied while loading from storage are not logged). `handleDocumentUpdate` puts `update`, `transactionOrigin`, `connection`, `context`, `documentName`, `document` in the `onChange` payload (1415-1427). So an extension gets the raw update without hooking Yjs itself. `onChange` also fires for updates from other origins (e.g. server-side `DirectConnection.transact`, redis); only the *store* hooks are skipped by `shouldSkipStoreHooks` (1428), which is true for `redis` origins and `skipStoreHooks` locals. With the redis extension and several servers every server would log the same update; harmless (idempotent) but duplicates.
- **Ordering of `onChange`**: the Yjs `update` event is synchronous, but `this.hooks("onChange", ...)` (1427) is **not awaited**; `hooks()` (1575-1585) chains extension calls as promises, so the extension function runs one microtask later. Calls for successive updates start in update order (microtask FIFO), and my hook does its `INSERT` before any `await`, so rows are in order (`id` autoincrement). An `onChange` that awaits before writing could interleave; do the write first or serialise through a queue. Because the call is un-awaited and the returned promise is dropped, **an exception in `onChange` (e.g. SQLite error) becomes an unhandled rejection** (and `hooks()` rethrows after `console.error`); it cannot back-pressure the client or stop it from being acked.
- **`onStoreDocument` cannot overlap itself for one document**: the body runs inside `document.saveMutex.runExclusive` (1552; mutex created at 501), and the debouncer's `run` awaits the previous `runningExecutions` entry (1202). Even if two runs queue up behind the same previous execution, the mutex serialises them. Different documents do run concurrently. Errors in a store hook are caught and logged, "Document stays in memory" (1563), and the next update retries.
- **Unload with a store pending**: `shouldUnloadDocument` (1587-1589) is false while a store is debounced, executing, or the mutex is locked. On last-client close, if a store is debounced and `unloadImmediately` (default true) the store runs NOW (1397-1400) and the document unloads after it (1560, 1567). On `Server.destroy` `flushPendingStores()` runs the pending stores first (1754). So a graceful close never loses the pending save; a crash loses up to `maxDebounce` (10 s by default) of strokes under the stock store. `onDisconnect` is awaited (1081) before the unload logic, with `clientsCount` already excluding the closing connection (observed 0 for the last client, `hooks` in results.json), so compaction on last disconnect can run there.
- **Gotcha for log stores**: no hook says "update N is durable"; the log extension is the only durability. Also `Y.encodeStateAsUpdate(document)` inside compaction contains everything already applied, including updates whose `onChange` microtask has not run yet, so snapshot-then-delete-rows-up-to-max-id never drops an update (late rows are just redundant, Yjs updates are idempotent).

## 3. Answer (conclusion after the facts)

**Does an incremental store make one doc per board viable at 10k strokes?** On the write side, yes. It removes the cost that the sync spike named as the main price of one doc per board: 642 B per save instead of 5.6 MB (0.1 ms instead of 50 ms), ~0.5 KB of log per stroke, no data loss on crash that the server had received (PASS, including a kill inside a compaction), and correct reload at every size (all PASS). Compaction keeps load at ~24 ms server-side at 10k (log replay uncompacted is 381 ms) and one 10k compaction costs ~86 ms.

**It does not make the per-page structure pointless; what it leaves unsolved is the read side and the stalls.** Those are board-size costs an update log cannot touch:
- every connect to a board still loads and ships the whole ~5 MB board (open ~93 ms through Hocuspocus at 10k, one page of a per-page layout is ~7 ms per the sync spike), and the server holds all 10k strokes in memory per open board;
- compaction (and every cold load) is stop-the-world for the single Node event loop: ~90 ms at 10k, 1.5 s with `mergeUpdates`; each compaction rewrites ~5 MB, so the policy must scale with board size (bytes or disconnect, not a fixed update count; fixed 500 updates doubled the bytes written at 10k);
- one doc per page with a plain full rewrite is already cheap (274 KB and 1.2 ms per save at 10k/20 pages) with no log, no compaction policy and no new failure modes.

So: the incremental store turns the write-amplification objection into a solved problem and makes **one doc per board viable at 10k strokes** if the whole-board open (~5 MB, ~0.1 s locally) and ~100 ms compaction stalls are acceptable. If they are not, or if the simplest design is preferred, the evidence still points at **one doc per page with the stock full-rewrite store**, and the decision now rests on read-side cost and on how often 10k-stroke boards occur, not on write cost. Either choice can later add a log to the doc it uses: an update log is a store detail, not a document-structure decision, so choosing per page now does not close the door.

## 4. Caveats
- WSL2, one shared event loop for server and clients, relative numbers only. Compaction stalls on a dedicated server process would be similar (they are CPU-bound in the server) but ping tails here include client work.
- Synthetic strokes, strokes paced ~250x faster than a person (see 1.4 on what that does to full-rewrite totals). Erase/undo is 10% of ops, one update each.
- WAL with `synchronous=NORMAL` (no fsync per commit). With `synchronous=FULL` or Postgres, per-update appends cost more than 0.1 ms (a batched log, one row per `onStoreDocument`, is then attractive, at the cost of a debounce-sized loss window in a crash).
- One server process, no redis/multi-instance; one writer per board; no tests of concurrent compaction by two servers.
- Compaction ran on the event loop; moving it to a worker thread or running it from a separate process (reading rows only, `mergeUpdates` is slow, so it would load into a `Y.Doc`) was not tried.

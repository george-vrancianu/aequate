# Incremental Hocuspocus store: update log plus compaction (PROTOTYPE, ticket #38)

**Answer: the write side is solved (log append ~0.6 KB payload / ~12 KB on disk per save vs 5.6 MB for a board rewrite at 10k, ~460x less on disk), so one doc per board is viable at 10k; but one doc per page already costs only ~284 KB on disk per save and wrote the fewest bytes in the fast-paced session, so per page stays the simpler default and the choice now hinges on read-side cost (whole-board open ~5 MB, ~81 ms) and ~55 ms compaction stalls.**

Question: does an incremental store (append each update to a log, compact now and then) make one Yjs doc per board viable at 10k strokes, or does it still point to one doc per page?

Setup: WSL2, Ryzen 9 5950X, Node 24, Yjs 13.6.x, Hocuspocus server 4.8.0 and provider 4.x over loopback WebSocket, SQLite via `node:sqlite` (WAL, synchronous=NORMAL) on real disk. All numbers are relative, not absolute. Server, 4 to 5 clients and the benchmark share ONE Node process and event loop, so ping and latency figures are pessimistic and noisy (the "no storage" row shows the noise floor). Server config: `debounce` 100 ms, `maxDebounce` 500 ms (scaled down from the 2 s / 10 s defaults). Stroke generator is the sync spike's (lib.js, 50 to 300 points, packed ~0.45 to 0.8 KB). Board = one Y.Doc with 5 root maps `strokes:<page>` (layout A); "per page" = 20 docs `pg:<N>:<p>` (layout C). Raw data: `results.json`; all generated tables (every size): `results-tables.md`.

Stores compared (all are real Hocuspocus extensions, see store.js):
- **full**: stock Database-extension pattern, `onStoreDocument` writes whole `Y.encodeStateAsUpdate`, `onLoadDocument` applies it. Baseline, re-measured here.
- **log**: `onChange` appends `payload.update` as one row per update (synchronous `INSERT` in the hook). Compaction (one SQLite transaction: write snapshot, delete rows up to max id) triggered by **count** (500 updates), **bytes** (512 KiB of log), or **last disconnect** (`onDisconnect` with `clientsCount === 0`). Snapshot = `encodeStateAsUpdate(live doc)` ("doc" mode) unless noted; "merge" mode = `Y.mergeUpdates(snapshot + rows)`.
- **batched log**: `onChange` queues, `onStoreDocument` appends ONE `Y.mergeUpdates` row per debounced save; compaction on last disconnect.
- **per page**: one doc per page (20 pages), full rewrite. Reference point.

## 1. Facts

### 1.1 Bytes written and write latency for one added stroke (steady state)

Two byte figures per save: **payload** = bytes handed to SQLite (blob size), **on-disk (WAL)** = growth of the SQLite WAL file around the write, measured in the bench with `PRAGMA wal_autocheckpoint=0` (the WAL is never reset during a run, so its size delta is the physical bytes SQLite appended: whole 4 KiB page frames plus 24 B frame headers, no checkpoint traffic). The WAL figure is what actually hits the disk (before the later checkpoint into the main file, which writes the changed pages again).

| strokes on board | full rewrite, doc per board | full rewrite, doc per page (20) | update log row | batched log row |
|---|---|---|---|---|
| 1k | 558 KB payload / 573 KB WAL, 2.7 ms | 31 KB / 41 KB, 0.3 ms | 443 B / 12.4 KB, 0.1 ms | 443 B / 12.4 KB, 0.1 ms |
| 3k | 1.70 MB / 1.72 MB, 7.0 ms | 83 KB / 95 KB, 0.5 ms | 752 B / 12.4 KB, 0.1 ms | 752 B / 12.4 KB, 0.1 ms |
| 5k | 2.81 MB / 2.84 MB, 13.8 ms | 140 KB / 152 KB, 1.0 ms | 831 B / 12.4 KB, 0.2 ms | 831 B / 12.4 KB, 0.1 ms |
| 10k | 5.64 MB / 5.70 MB, 23.7 ms | 274 KB / 284 KB, 1.2 ms | 642 B / 12.4 KB, 0.1 ms | 642 B / 12.4 KB, 0.1 ms |

(Time is encode + SQLite write, on the server event loop; WAL stat calls are outside the timed region. Batched equals per-update here because one stroke is saved at a time; its benefit shows in the session table.)

A log append of ~0.6 KB costs ~12.4 KB of WAL (3 page frames: table leaf, the `updates_doc` index leaf, and the `sqlite_sequence` row for `AUTOINCREMENT`), about 20 to 30x its payload. A whole-board rewrite is ~1.01x its payload. So at 10k the log writes **~8,800x fewer payload bytes but only ~460x fewer bytes on disk** per save than the board rewrite (5.70 MB / 12.4 KB). Against one doc per page the on-disk gap is ~23x (284 KB / 12.4 KB), not the 430x that payload suggests. Dropping `AUTOINCREMENT` (plain `INTEGER PRIMARY KEY`) would remove one of the three frames; not done here. The update per stroke is ~0.4 to 0.8 KB at any board size.

### 1.2 Load time: log replay vs snapshot + tail (cold open through Hocuspocus; server-side `onLoadDocument` ms in brackets)

Log built by a real client writing N strokes, then erasing 10% (one update per op), so rows = 1.1 N.

| strokes | log rows / MB | live state MB | log replay, direct, no server | `mergeUpdates` then apply, direct | open, log NOT compacted | open after compaction (snapshot only) | open snapshot + 100-row tail |
|---|---|---|---|---|---|---|---|
| 1k | 1,100 / 0.54 | 0.48 | 14 ms | 24 ms | 62 ms (22) | 14 ms (3.2) | 15 ms (3.0) |
| 3k | 3,300 / 1.65 | 1.47 | 27 ms | 160 ms | 149 ms (100) | 29 ms (14) | 30 ms (7.1) |
| 5k | 5,500 / 2.73 | 2.42 | 49 ms | 296 ms | 216 ms (160) | 47 ms (17) | 46 ms (11) |
| 10k | 11,000 / 5.49 | 4.87 | 97 ms | 1,494 ms | 394 ms (343) | 81 ms (36) | 76 ms (22) |

An uncompacted log at 10k is ~10x slower to load on the server than a snapshot (343 vs 36 ms) and ~13% larger than the live state (per-row overhead and erased content kept). A short tail (100 rows) costs next to nothing. `Y.mergeUpdates` over thousands of rows is far slower than applying them row by row (superlinear), so do not use it as the load path. The server-side load of the uncompacted log (343 ms) is ~3.5x the raw direct replay (97 ms): a Hocuspocus `Document` registers `this.on("update", handleUpdate)` at construction (hocuspocus-server.esm.js:513), so every row applied inside `onLoadDocument` also runs through `handleUpdate` (broadcast and pending-flush bookkeeping). The `onChange` wiring is attached only after load (1502), so rows are not re-logged, but the per-row listener cost is real and applies to any store that replays rows into the server doc.

### 1.3 Compaction cost, and does it block other connections

Compacting the whole 1.1 N-row log on a live server doc while a second pair of clients pings through the same server (a ping arrives every 5 ms; "gap" = time between consecutive arrivals).

| strokes | mode | compaction ms | snapshot size | biggest ping arrival gap during compaction |
|---|---|---|---|---|
| 1k | doc (`encodeStateAsUpdate`) | 5 | 0.48 MB | 8 ms |
| 1k | merge (`Y.mergeUpdates`) | 24 | 0.53 MB | 28 ms |
| 3k | doc | 12 | 1.47 MB | 14 ms |
| 3k | merge | 145 | 1.62 MB | 148 ms |
| 5k | doc | 22 | 2.42 MB | 25 ms |
| 5k | merge | 374 | 2.68 MB | 377 ms |
| 10k | doc | 53 | 4.87 MB | 58 ms |
| 10k | merge | 1,437 | 5.38 MB | 1,445 ms |

Compaction is synchronous JavaScript plus a SQLite transaction (store.js `compact`), so it **blocks every connection on that server process** for its whole duration. Caveat on the evidence: the pinging clients share the server's event loop (see Setup), so the ping gap is at least the compaction time whoever is blocking; the measurement alone cannot attribute the stall to the server. The "blocks every connection" claim rests on compaction being synchronous server code, and the gap (58 ms vs compaction 53 ms; calm gap 5 ms) is consistent with it. Doc mode (encode the live doc) is the cheap one (53 ms at 10k); merge mode costs 1.4 s at 10k and keeps erased content (snapshot ~10% larger). The stock full rewrite has the same kind of stall on *every save*: the whole-board save is ~24 ms at 10k in the single-stroke test (up to ~29 to 32 ms in the sessions), visible below.

### 1.4 Session: a student writes 2,000 strokes with ~10% erase or undo (222 extra ops), two sessions of 1,000 strokes with disconnect and reconnect, board already holding N strokes

Strokes are issued every ~4 ms (about 250x faster than a person), so with `debounce` 100 ms the stock store coalesces ~110 strokes per save (18 saves in total). This **flatters the full-rewrite totals** (and the per-page ones): at a human pace with Hocuspocus defaults (2 s debounce, 10 s maxDebounce) the strokes per save depend on the pauses (derived from the measured per-save numbers in 1.1, not measured sessions). A debounced save fires only after 2 s of silence or once 10 s have passed since the first pending update (hocuspocus-server.esm.js:1211). Continuous writing at ~1 stroke/s never has 2 s of silence, so saves run on the 10 s clock with ~10 strokes each; the full-rewrite total would then be about 200 saves x 5.70 MB ~ 1.1 GB WAL for 2,000 strokes at 10k. Only a writer who pauses more than 2 s after every stroke gets one stroke per save (about 2,000 x 5.7 MB ~ 11 GB). Log appends are per update whatever the pace.

Totals over both sessions, both byte figures (compaction snapshots included; WAL = physical bytes, see 1.1). "Rows left" = log rows/KB still stored after session 1 / session 2.

| strokes on board | store | writes | payload bytes | on-disk (WAL) bytes | WAL bytes per stroke | median payload / WAL per write | compactions (ms) | rows left after s1 / s2 | worst ping arrival gap (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 10k | full rewrite, doc per board | 18 | 106.4 MB | 107.4 MB | 55 KB | 6,055 KB / 6,110 KB | - | - | 37 |
| 10k | full rewrite, doc per page | 20 | 8.6 MB | 8.9 MB | 4.6 KB | 452 KB / 470 KB | - | - | 10 |
| 10k | log, compact @500 updates | 2,208 | 24.8 MB | 54.8 MB | 28 KB | 0.5 KB / 12 KB | count: 30, 26, 34, 32 | 121 / 208 | 38 |
| 10k | log, compact @512 KiB | 2,208 | 13.2 MB | 45.1 MB | 23 KB | 0.5 KB / 12 KB | bytes: 29, 29 | 93 / 188 | 35 |
| 10k | log, compact on last disconnect | 2,208 | 13.3 MB | 44.5 MB | 23 KB | 0.5 KB / 12 KB | disconnect: 36, 32 | 0 / 0 | 8 |
| 10k | batched log, compact on disconnect | 18 | 13.3 MB | 13.8 MB | 7.1 KB | 66 KB / 89 KB | disconnect: 32, 29 | 0 / 0 | 10 |
| 10k | no storage (noise floor) | - | 0 | 0 | - | - | - | - | 13 |
| 1k | full rewrite, doc per board | 18 | 19.2 MB | 19.5 MB | 10 KB | 1,097 KB / 1,114 KB | - | - | 16 |
| 1k | full rewrite, doc per page | 20 | 3.9 MB | 4.1 MB | 2.1 KB | 211 KB / 225 KB | - | - | 7 |
| 1k | log, compact @500 updates | 2,208 | 5.4 MB | 35.3 MB | 18 KB | 0.5 KB / 12 KB | count: 4, 4, 6, 7 | 121 / 208 | 14 |
| 1k | log, compact on last disconnect | 2,208 | 3.6 MB | 33.9 MB | 17 KB | 0.5 KB / 12 KB | disconnect: 6, 7 | 0 / 0 | 11 |

All four sizes are in `results-tables.md`. The 5k and 3k rows follow the same shape.

**Payload already says one doc per page wins the fast-paced session (8.6 MB vs 13.3 MB for the cheapest log, 0.6 KB vs 274 KB per save notwithstanding). On disk the gap widens: one doc per page writes the fewest physical bytes (8.9 MB), 5 to 6x fewer than any per-update log variant (44.5 to 54.8 MB), because each tiny append costs ~12 KB of WAL and there are 2,208 of them, while per page coalesces ~110 strokes into each ~470 KB save (session saves hold more strokes per page than the 1.1 single-save page).** The batched log (13.8 MB WAL) sits between them, and all log variants are 2 to 8x below the stock board rewrite (107 MB). **At a human pace the answer depends on pauses, and the per-update log wins clearly only for sparse edits.** Derived from the measured per-save WAL numbers at 10k (not measured sessions; log = 12.4 KB per append plus ~7 KB per stroke of amortised disconnect compaction at 1,000 strokes per session, ~20 KB, 23 KB measured in the fast session):

| writing pattern (Hocuspocus defaults) | strokes per save | per page, WAL per stroke | log, WAL per stroke | board rewrite, WAL per stroke |
|---|---|---|---|---|
| paused: more than 2 s between strokes | 1 | ~284 KB | ~20 KB (~14x less than per page) | ~5.7 MB |
| continuous, ~1 stroke/s (saves on the 10 s maxDebounce clock) | ~10 | ~28 KB | ~20 KB (~1.4x less) | ~570 KB |
| continuous, several strokes/s | 30 or more | ~10 KB or less | ~20 KB (log is worse) | ~190 KB or less |
| measured: 4 ms pacing, ~110 strokes per save | ~110 | ~4.6 KB | 23 KB (~5x worse) | 55 KB |

So the log's physical advantage over per page is about 14x for sparse single-stroke edits, roughly parity (1.4x) for continuous writing at ~1 stroke/s, and negative for fast writing; the whole-board rewrite is worse than both at every pace.

In the log rows, payload bytes beyond ~1.3 MB (the 2,208 appended updates) are compaction snapshots: each compaction rewrites the whole ~5 MB board (~6.9 MB WAL), so **count-based compaction at 10k (4 compactions) writes ~2x the payload bytes (24.8 vs 13.3 MB) and ~10 MB more WAL (54.8 vs 44.5 MB) than a bytes- or disconnect-triggered one**. A pure threshold that ignores board size is the wrong policy; the cost of a compaction scales with the board, the benefit with the log length.

Log growth (rows / KB after every 200 strokes, 10k board, no compaction until disconnect): session 1: 220/109, 438/224, 672/336, 897/446, 1120/558; session 2 restarts from 0 after the disconnect compaction and reaches 1086/564. About 560 KB of log per 1,000 strokes, i.e. ~0.5 KB per update, ~11% more rows than strokes. A heavy erase/undo session did not change the picture (stored strokes after reload always equal live strokes, see 1.5).

Write latency of a log append: p50 0.09 to 0.10 ms, p99 0.2 to 0.25 ms, with rare outliers up to ~9 ms in this run (an earlier run of the same code showed ~20 ms and once 63 ms at 5k; likely SQLite or WSL2 file-system hiccups, not examined). Whole-board full rewrite at 10k: p50 23 to 29 ms, max 32 ms per save.

### 1.5 Correctness (PASS/FAIL: state vector AND content digest (sha1 of every key and packed stroke) of the doc reloaded from storage only vs the live client doc)

| check | 1k | 3k | 5k | 10k |
|---|---|---|---|---|
| log replay == live | PASS | PASS | PASS | PASS |
| `Y.mergeUpdates` of log == live | PASS | PASS | PASS | PASS |
| after compaction (doc mode) == live | PASS | PASS | PASS | PASS |
| after compaction (merge mode) == live | PASS | PASS | PASS | PASS |
| snapshot + 100-row tail == live | PASS | PASS | PASS | PASS |
| session 1 and session 2 reload == live, every storing variant (6 variants x 2 sessions) | PASS | PASS | PASS | PASS |

Crash tests, a *process* crash (SIGKILL; the OS survives, so the WAL contents written before the kill are intact). Separate process running a real server and client; after writing 600 strokes with ~10% erases onto a 1,000-stroke board the process kills itself with SIGKILL: no unload, no flush, no compaction; then the sqlite file is reopened and loaded with no server):

| scenario | recovered / expected strokes | state vector equal | content equal | result |
|---|---|---|---|---|
| log, one row per update (`onChange`), killed before any compaction | 1530 / 1530 | yes | yes | PASS |
| log + count compaction already ran mid-session, then killed | 1530 / 1530 | yes | yes | PASS |
| log, killed inside the compaction transaction before COMMIT (snapshot written, rows deleted, not committed) | 1530 / 1530 (log left intact, snapshot unchanged) | yes | yes | PASS |
| batched log (row per `onStoreDocument`), killed | 1409 / 1530 | no | no | FAIL (loses the unsaved debounce window) |
| stock full rewrite, killed | 1412 / 1530 | no | no | FAIL (loses everything since the last debounced save) |

The two FAILs are the baseline's own durability gap, shown for contrast, not a bug in the log. The per-update log loses nothing that the server had received, in a process crash. An OS crash or power loss is not tested: with `synchronous=NORMAL` the last WAL commits can roll back (see Caveats).

## 2. Hocuspocus specifics (installed 4.8.0; file `node_modules/@hocuspocus/server/dist/hocuspocus-server.esm.js`)

- **Debounce**: defaults `debounce: 2e3`, `maxDebounce: 1e4` (lines 1244-1245). `storeDocumentHooks` (1548-1570) calls `debouncer.debounce(id, fn, debounce, maxDebounce)`. Every update re-arms the timer; once `Date.now() - start >= maxDebounce` it runs immediately (1211). A continuously writing user is therefore saved on the `maxDebounce` clock, not the `debounce` one (that is why the session above saved ~every 500 ms).
- **`onChange` has the update bytes**: `Document.handleUpdate` (line 682) passes the Yjs `update` (v1 bytes) to `onUpdate`, wired at 1502 (registered AFTER `onLoadDocument` finishes, so updates applied while loading from storage are not logged). `handleDocumentUpdate` puts `update`, `transactionOrigin`, `connection`, `context`, `documentName`, `document` in the `onChange` payload (1415-1427). So an extension gets the raw update without hooking Yjs itself. `onChange` also fires for updates from other origins (e.g. server-side `DirectConnection.transact`, redis); only the *store* hooks are skipped by `shouldSkipStoreHooks` (1428), which is true for `redis` origins and `skipStoreHooks` locals. With the redis extension and several servers every server would log the same update; harmless (idempotent) but duplicates.
- **Ordering of `onChange`**: the Yjs `update` event is synchronous, but `this.hooks("onChange", ...)` (1427) is **not awaited**; `hooks()` (1575-1585) chains extension calls as promises, so the extension function runs one microtask later. Calls for successive updates start in update order (microtask FIFO), and my hook does its `INSERT` before any `await`, so rows are in order (`id` autoincrement). An `onChange` that awaits before writing could interleave; do the write first or serialise through a queue. Because the call is un-awaited and the returned promise is dropped, **an exception in `onChange` (e.g. SQLite error) becomes an unhandled rejection** (and `hooks()` rethrows after `console.error`); it cannot back-pressure the client or stop it from being acked.
- **`onStoreDocument` cannot overlap itself for one document**: the body runs inside `document.saveMutex.runExclusive` (1552; mutex created at 501), and the debouncer's `run` awaits the previous `runningExecutions` entry (1202). Even if two runs queue up behind the same previous execution, the mutex serialises them. Different documents do run concurrently. Errors in a store hook are caught and logged, "Document stays in memory" (1563), and the next update retries.
- **Unload with a store pending**: `shouldUnloadDocument` (1587-1589) is false while a store is debounced, executing, or the mutex is locked. On last-client close, if a store is debounced and `unloadImmediately` (default true) the store runs NOW (1397-1400) and the document unloads after it (1558, 1566). On `Server.destroy` `flushPendingStores()` runs the pending stores first (1754). So a graceful close never loses the pending save; a crash loses up to `maxDebounce` (10 s by default) of strokes under the stock store. `onDisconnect` is awaited (1081) before the unload logic, with `clientsCount` already excluding the closing connection (observed 0 for the last client, `hooks` in results.json), so compaction on last disconnect can run there.
- **Gotcha for log stores**: no hook says "update N is durable"; the log extension is the only durability. Also `Y.encodeStateAsUpdate(document)` inside compaction contains everything already applied, including updates whose `onChange` microtask has not run yet, so snapshot-then-delete-rows-up-to-max-id never drops an update (late rows are just redundant, Yjs updates are idempotent).

## 3. Answer (conclusion after the facts)

**Does an incremental store make one doc per board viable at 10k strokes?** On the write side, yes, with a correction on how much. Per save the log hands SQLite 642 B instead of 5.6 MB (0.1 ms instead of ~24 ms), but SQLite physically appends ~12.4 KB of WAL for that row, so the saving on disk is **~460x against the board rewrite (payload 8,800x)**, and only **~23x against one doc per page** (284 KB per save). In the session test the log is not a clear physical win at all: at machine pace one doc per page wrote the fewest bytes on disk (8.9 MB vs 44.5 to 54.8 MB for per-update log variants, 107 MB for the board rewrite); at a human pace it depends on pauses (derived from per-save numbers, not measured sessions, see 1.4): ~14x cheaper than per page on disk only for sparse edits with more than 2 s between strokes (~20 KB vs ~284 KB per stroke including amortised compaction), roughly parity (~1.4x) for continuous writing at ~1 stroke/s (saves run on the 10 s maxDebounce clock, ~10 strokes per save, per page ~28 KB per stroke), and worse than per page for fast writing. The log also gives ~0.5 KB of log per stroke, no data loss in a process crash (SIGKILL, with `synchronous=NORMAL`) for anything the server had received (PASS, including a kill inside a compaction), and correct reload at every size (all PASS). Compaction keeps load at ~36 ms server-side at 10k (uncompacted log replay: 343 ms) and one 10k compaction costs ~53 ms (stop-the-world).

**It does not make the per-page structure pointless; what it leaves unsolved is the read side and the stalls.** Those are board-size costs an update log cannot touch:
- every connect to a board still loads and ships the whole ~5 MB board (open ~81 ms through Hocuspocus at 10k, one page of a per-page layout is ~7 ms per the sync spike), and the server holds all 10k strokes in memory per open board;
- compaction (and every cold load) is stop-the-world for the single Node event loop: ~55 ms at 10k, 1.4 s with `mergeUpdates`; each compaction rewrites ~5 MB (~6.9 MB of WAL), so the policy must scale with board size (bytes or disconnect, not a fixed update count; fixed 500 updates doubled the payload bytes written at 10k);
- one doc per page with a plain full rewrite is already cheap (274 KB payload, 284 KB on disk, 1.2 ms per save at 10k/20 pages) with no log, no compaction policy and no new failure modes, and is the lowest on-disk total in the fast-paced session.

So: the incremental store takes the write-amplification objection off the table (board rewrite -> ~460x less on disk) and makes **one doc per board viable at 10k strokes** if the whole-board open (~5 MB, ~0.1 s locally) and ~55 ms compaction stalls are acceptable. If they are not, or if the simplest design is preferred, the evidence still points at **one doc per page with the stock full-rewrite store**: it is within ~23x of the log on disk per save, ahead of it in the fast-paced session, and the log's physical advantage over it only shows up for sparse edits (more than 2 s between strokes); for continuous writing the two are at parity on disk. The decision now rests on read-side cost and on how often 10k-stroke boards occur, not on write cost. Either choice can later add a log to the doc it uses: an update log is a store detail, not a document-structure decision, so choosing per page now does not close the door.

## 4. Caveats
- WSL2, one shared event loop for server and clients, relative numbers only. Compaction stalls on a dedicated server process would be similar (they are CPU-bound in the server) but ping tails here include client work, and the ping gap cannot by itself attribute a stall to the server (same loop).
- Synthetic strokes, strokes paced ~250x faster than a person (see 1.4 on what that does to full-rewrite totals). Erase/undo is 10% of ops, one update each.
- WAL with `synchronous=NORMAL` (no fsync per commit): the crash tests are process crashes (SIGKILL) only; after an OS crash or power loss the last WAL commits may be lost, for the log and the full rewrite alike. WAL bytes are measured with `wal_autocheckpoint=0` (no checkpoint during a run, so the WAL grows to hundreds of MB per size; a reviewer re-run showed no material effect on load timings), so the later checkpoint writes into the main DB file are not counted; fsyncs and `synchronous=FULL` were not measured. With `synchronous=FULL` or Postgres, per-update appends cost more than 0.1 ms (a batched log, one row per `onStoreDocument`, is then attractive, at the cost of a debounce-sized loss window in a crash).
- One server process, no redis/multi-instance; one writer per board; no tests of concurrent compaction by two servers.
- Compaction ran on the event loop; moving it to a worker thread or running it from a separate process (reading rows only, `mergeUpdates` is slow, so it would load into a `Y.Doc`) was not tried.

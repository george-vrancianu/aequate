# Results: Yjs board under erase/undo churn, and on a low-end tablet (ticket #39)

PROTOTYPE (throwaway). Machine: WSL2, Ryzen 9 5950X, Node 24, Yjs 13.6.x, Hocuspocus 4.x; numbers are relative, not absolute. The tablet section is empty until a human runs [TABLET.md](TABLET.md).

## Part 1: churn

### Method (what was actually done)

- One doc per board (one root map per page, 20 pages) and one doc per page (20 docs), at 1k, 5k, 10k live strokes (3k was not run for churn). Strokes are the sync spike's generator (~530 B packed average).
- Three users, each with their own replica doc (own clientID) and own `Y.UndoManager` (`trackedOrigins` = the user, `captureTimeout: 0`, cap 100), plus a fourth **server replica without an UndoManager** (what Hocuspocus holds). Updates travel through manual queues, with 20% of iterations having two users act concurrently (including both erasing the same stroke).
- One churn iteration: 1 or 2 users erase a random stroke; 35% of the acting users then undo, and half of those redo; then fresh strokes are drawn until the live count is back to N. Churn ratios 0.5x, 1x, 3x are checkpoints of one cumulative run (after 0.5N, N, 3N iterations). At 3x for N=10k: 35,991 erases (deleted items), 28,228 re-draws, 12,652 undos (each restoring a stroke as a new item), 6,353 redos. So "deletions plus re-inserts" is about 3.6N plus about 4.2N.
- Cap model = the sync spike's: trim the undo/redo stack arrays on `stack-item-added` to 100 (for per-page docs, an app-level stack of page ids, trimmed the same way, and the oldest entry of that page's UndoManager stack dropped with it). Extra variants at 5k: no UndoManager, no cap, and "release" (trim and also clear the `keep` flag of dropped entries).
- Tombstones are real: deleted-item count and delete-set size grow in every run (T1). gc=true/false is set on every replica of the run.
- Sizes are exact `Y.encodeStateAsUpdate` bytes (v1; v2 also shown), delete-set size is the exact v1 DS encoding computed from the struct store. Cold load = `applyUpdate` into a fresh `Y.Doc` (median of 5), memory = heap + arrayBuffers delta after forced gc.

### Facts

**1. Server doc (what Hocuspocus stores), 10k live strokes, payload 5.14 MB** (full tables T1 to T7 below):

| churn | gc=true encoded | ratio | gc=false encoded | ratio | deleted items | DS ranges | DS bytes |
|---|---|---|---|---|---|---|---|
| 0x | 5.37 MB | 1.04x | 5.37 MB | 1.04x | 0 | 0 | 1 B |
| 0.5x | 5.49 MB | 1.07x | 9.02 MB | 1.75x | 6,856 | 3,970 | 11.5 KB |
| 1x | 5.63 MB | 1.09x | 12.65 MB | 2.45x | 13,641 | 5,215 | 15.2 KB |
| 3x | 6.06 MB | 1.18x | 27.10 MB | 5.28x | 40,879 | 5,809 | 18.6 KB |

- With gc=true each deleted stroke costs about 17 bytes forever (the Item stays as a content-less tombstone; GC structs were never produced, so nothing merges away). With gc=false each deleted stroke keeps its whole payload (about 520 B). Both layouts behave the same within about 2% (one doc per page is slightly smaller, 5.96 vs 6.06 MB, because per-doc client tables are smaller).
- The delete set is small: 5.8k ranges and 19 KB at 3x churn, growing sublinearly (adjacent deletions coalesce). It is about 0.3% of the doc.
- Re-encoding after a fresh load into a gc=true doc gives the same size as the gc=true server doc; loading a gc=false doc into a gc=true doc strips the content (27.10 MB to 6.06 MB at 10k, 3x). Tombstone items themselves are not removed by reload (6.06 MB stays 6.06 MB).
- Incremental updates are unchanged by churn and by gc: draw about 565 B median (p95 about 915 B), erase 7 B, undo (restores a stroke) about 547 B, redo 7 B (T3). An erase is a 7-byte delete-set-only update.

**2. Cold load and memory (server state into a fresh doc, 10k):**

| state | whole board ms | memory MB (heap + ab) |
|---|---|---|
| fresh, 0x | 14 to 20 | 9.6 |
| 3x churn, gc=true | 55 to 75 | 19.4 |
| 3x churn, author gc=false loaded into gc=true doc | 149 to 199 (first load, includes content strip) | 19.4 |
| 3x churn, gc=false doc loaded into gc=false doc | 153 | 48.2 |

At 5k: 24 ms and 9.7 MB (gc=true, 3x) against 6 to 9 ms and 4.8 MB fresh. One page of a per-page layout at 10k, 3x: 1.6 to 2.7 ms. Churn costs about 3.4 to 5.3 ms per iteration at 10k for three replicas plus relay (T5), so CPU for editing is negligible.

**3. Undo stacks and gc (the client side, user 0 with an UndoManager, gc=true, 10k, 3x):**

- The editing client's encoded state is 15.3 MB against 6.06 MB on the server (payload 5.14 MB): **2.98x payload versus 1.18x**. 17,940 deleted items on the client still hold their content (9.2 MB of payload). The server, without an UndoManager, holds none.
- Cause (from the Yjs source, `UndoManager` and `cleanupTransactions`): an item deleted in a tracked transaction is marked `keep`, and gc only inspects the items of the transaction that deleted them. So content that was kept at deletion time is never collected in that live doc, even after the stack entry is dropped.
- **The cap did not change this.** Retained content is identical with no cap (10,648 stack entries at the end), the spike's cap (100), and the cap plus clearing `keep` on the dropped entries (T6: 8,991 items, 4.61 MB at 5k in all three). Calling `um.clear()` on the whole stack did not reclaim anything in the live doc either (9,295 and 9,094 content-holding items remained). A fresh `applyUpdate` into a gc doc (reload) reclaims all of it (0 content-holding items, 3.06 MB at 5k).
- Without any UndoManager the client equals the server (3.07 MB at 5k).
- The retained amount is proportional to the number of erases by that user during the session (about 520 B per erase), not to the stack depth. Not measured: live-heap of the client replica separately (only the retained payload bytes and the encoded size are); the explanation that the retained items are mostly the user's own erases is inferred from the counts, not isolated.

**4. Correctness after heavy churn** (T7, all 12 runs pass, 0 failures): replicas and server converge (content and state vectors identical); every live stroke equals the bytes originally drawn; an erased stroke is restored by undo with equal content on every replica (also with gc=true, because kept items survive); redo re-erases; a second undo restores again; interleaved concurrent erases by two users undo independently (only own erase is undone); concurrent double-erase of one stroke then undo works; the capped stack holds at most 100; draining up to 300 undos then redos converges. Per-page undo needed one fix: `UndoManager.undo()` can consume several stack entries when earlier ones are no-ops (for instance the stroke was already erased by someone else), so the app-level page stack must only push a redo when `undo()` returned a result.

### Answer to the ticket question

- **Do the spike's conclusions hold: CPU and memory are not the limit up to 10k strokes, the cost is bytes?** CPU: yes. Churn costs a few ms per iteration, a 10k cold load of a 3x-churned server doc is 55 to 75 ms (about 4x a fresh doc, still well under a frame budget on this machine; not yet known on the tablet) and an erase is a 7-byte update. Bytes: yes, and churn adds a second byte cost. Memory: a qualified yes. The server doc is 19 MB against 9.6 MB fresh at 10k, 3x churn. The editing client with an UndoManager is the exception: it holds about 9 MB of dead stroke payload after 3x churn at 10k and the cap does not release it.
- **Do gc plus the cap keep the doc bounded?** gc: partly. With gc=true the server doc stays near the live payload (1.18x at 3x churn) but still grows linearly with every deletion, about 17 B per deleted stroke, with no compaction found short of rebuilding the doc; gc=false is not bounded in any useful sense (5.3x at 3x churn, 27 MB at 10k). The cap: it bounds the stack length (and the memory of the stack objects themselves) but, as measured, **not** the dead content the client retains; only a reload of the doc frees it. One doc per board and one doc per page are indistinguishable here.

### Recommendations (labelled opinion, derived from the above)

1. Keep `doc.gc = true` (the Hocuspocus default) on the server and clients; do not turn it off for any undo or history feature (gc=false costs 5x at 3x churn).
2. Do not rely on the stack cap to free memory in a long editing session. Either reload the client doc (drop and re-fetch it, which loses the undo stack) at natural boundaries, or accept about 520 B of retained payload per erase by that user until reload. At 10k strokes with 3x churn that is about 9 MB, probably acceptable but unmeasured on the tablet.
3. The per-erase tombstone (about 17 B) is small enough that no server-side compaction is needed for v1; if it ever matters, rebuilding a doc from live content (copy strokes into a new doc) is the only reset found, and it invalidates client state.
4. The per-page app-level undo stack needs the "push redo only if undo returned a result" rule.

## Part 2: low-end tablet

### Desktop baseline (headless Chromium 158 on this machine, loopback, `tablet/desktop-baseline.json`)

Not a tablet: this is the reference to compare the tablet numbers against. Times in ms, median of 3 for sync and open, render includes decode and draw to an 800x1200 canvas, apply is per remote stroke update (n about 101: 100 single-stroke adds, then one transaction deleting them again) from beforeAllTransactions to afterAllTransactions including an observer that decodes and draws the stroke. Heap from `performance.memory` with `--enable-precise-memory-info`, not gc-forced, so noisy (the page-layout 10k row is clearly affected by garbage).

| size | layout | sync + open whole board | open one page | apply per stroke med / p95 / max | render one page | render whole board | doc bytes | heap MB after open / after render |
|---|---|---|---|---|---|---|---|---|
| 1k | board | 15.7 | 12.9 | 0.1 / 0.2 / 0.7 | 2.0 | 21.3 | 556,422 | 8.8 / 20.7 |
| 1k | page | 15.5 | 4.2 | 0.1 / 0.2 / 0.3 | 1.0 | 14.6 | 554,091 | 31.3 / 25.2 |
| 3k | board | 24.1 | 27.2 | 0.1 / 0.2 / 0.2 | 2.5 | 44.8 | 1,699,217 | 49.9 / 38.0 |
| 3k | page | 30.4 | 4.9 | 0.1 / 0.2 / 0.3 | 2.0 | 43.6 | 1,691,907 | 65.0 / 40.5 |
| 5k | board | 40.2 | 39.9 | 0.1 / 0.2 / 0.3 | 3.6 | 77.7 | 2,809,622 | 80.3 / 69.5 |
| 5k | page | 50.3 | 6.5 | 0.1 / 0.2 / 0.4 | 3.9 | 69.0 | 2,797,311 | 92.0 / 82.4 |
| 10k | board | 70.9 | 83.8 | 0.1 / 0.2 / 0.5 | 6.6 | 166.2 | 5,647,466 | 165.7 / 142.6 |
| 10k | page | 89.1 | 8.2 | 0.1 / 0.2 / 0.3 | 5.9 | 180.7 | 5,622,655 | 215.6 / 287.0 |

HTTP round trip to the server was 1.3 to 1.7 ms. Open-one-page for the one-doc-per-board layout is the whole-board sync by construction (note the 3x 5k and 10k values equal the whole-board value within noise). The apply time per stroke is far below a frame at every size on desktop; what grows is the whole-board open (bytes) and the full render.

How the page was verified: Playwright (devDependency of this folder only; `chromium-headless-shell` downloaded cleanly) drove the real page against the server on an ephemeral port; the "Copy results as JSON" path reported "copied" (the plain-http fallback to a selected textarea was not exercised, since localhost is a secure context). Server and browser were shut down afterwards; no process left running.

### Tablet results

(Empty. To be filled in by the human from the JSON the page produces; see TABLET.md. iPad: no `performance.memory`, so no heap numbers.)

## Appendix: full churn tables

Generated by `node tables.js` from `results/*.json` (merged in `results.json`).

### T1. Size and tombstones vs churn (server replica, i.e. what Hocuspocus stores; Yjs v1 encoding)

Churn is cumulative within one run: the 0.5x, 1x, 3x rows are the same doc after 0.5N, N, 3N erase iterations. "deleted items" counts deleted Items plus GC structs; "DS ranges" is the number of ranges in the delete set; "DS bytes" its exact v1 encoding. Payload = sum of the packed stroke bytes still live.

| live N | layout | gc | churn | live payload | encoded | encoded / payload | encoded v2 | deleted items | deleted with content kept | DS ranges | DS bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | board | true | 0x | 529.7 KB | 550.7 KB | 1.04x | 548.7 KB | 0 | 0 | 0 | 1 B |
| 1000 | board | true | 0.5x | 531.3 KB | 565.0 KB | 1.06x | 562.8 KB | 710 | 0 | 398 | 1113 B |
| 1000 | board | true | 1x | 522.3 KB | 567.6 KB | 1.09x | 564.3 KB | 1399 | 0 | 509 | 1455 B |
| 1000 | board | true | 3x | 522.2 KB | 614.8 KB | 1.18x | 606.1 KB | 4134 | 0 | 605 | 1810 B |
| 1000 | board | false | 0x | 529.7 KB | 550.7 KB | 1.04x | 548.7 KB | 0 | 0 | 0 | 1 B |
| 1000 | board | false | 0.5x | 531.3 KB | 946.7 KB | 1.78x | 943.9 KB | 710 | 710 | 398 | 1113 B |
| 1000 | board | false | 1x | 522.3 KB | 1.28 MB | 2.51x | 1.28 MB | 1399 | 1399 | 509 | 1455 B |
| 1000 | board | false | 3x | 522.2 KB | 2.74 MB | 5.37x | 2.73 MB | 4134 | 4134 | 605 | 1810 B |
| 1000 | page | true | 0x | 529.7 KB | 548.3 KB | 1.04x | 546.7 KB | 0 | 0 | 0 | 20 B |
| 1000 | page | true | 0.5x | 531.3 KB | 561.3 KB | 1.06x | 559.7 KB | 708 | 0 | 413 | 966 B |
| 1000 | page | true | 1x | 522.3 KB | 562.4 KB | 1.08x | 559.9 KB | 1394 | 0 | 521 | 1182 B |
| 1000 | page | true | 3x | 522.2 KB | 604.0 KB | 1.16x | 597.3 KB | 4115 | 0 | 605 | 1352 B |
| 1000 | page | false | 0x | 529.7 KB | 548.3 KB | 1.04x | 546.7 KB | 0 | 0 | 0 | 20 B |
| 1000 | page | false | 0.5x | 531.3 KB | 942.9 KB | 1.77x | 940.7 KB | 710 | 710 | 413 | 966 B |
| 1000 | page | false | 1x | 522.3 KB | 1.28 MB | 2.50x | 1.27 MB | 1399 | 1399 | 521 | 1182 B |
| 1000 | page | false | 3x | 522.2 KB | 2.73 MB | 5.35x | 2.72 MB | 4134 | 4134 | 605 | 1352 B |
| 5000 | board | true | 0x | 2.56 MB | 2.67 MB | 1.04x | 2.66 MB | 0 | 0 | 0 | 1 B |
| 5000 | board | true | 0.5x | 2.55 MB | 2.71 MB | 1.07x | 2.70 MB | 3373 | 0 | 1977 | 5846 B |
| 5000 | board | true | 1x | 2.54 MB | 2.77 MB | 1.09x | 2.75 MB | 6746 | 0 | 2634 | 7819 B |
| 5000 | board | true | 3x | 2.60 MB | 3.06 MB | 1.18x | 3.01 MB | 20400 | 0 | 2899 | 8692 B |
| 5000 | board | false | 0x | 2.56 MB | 2.67 MB | 1.04x | 2.66 MB | 0 | 0 | 0 | 1 B |
| 5000 | board | false | 0.5x | 2.55 MB | 4.47 MB | 1.75x | 4.45 MB | 3373 | 3373 | 1977 | 5846 B |
| 5000 | board | false | 1x | 2.54 MB | 6.25 MB | 2.46x | 6.23 MB | 6747 | 6747 | 2634 | 7819 B |
| 5000 | board | false | 3x | 2.60 MB | 13.50 MB | 5.19x | 13.46 MB | 20402 | 20402 | 2899 | 8692 B |
| 5000 | page | true | 0x | 2.56 MB | 2.66 MB | 1.04x | 2.64 MB | 0 | 0 | 0 | 20 B |
| 5000 | page | true | 0.5x | 2.55 MB | 2.70 MB | 1.06x | 2.68 MB | 3372 | 0 | 1973 | 4973 B |
| 5000 | page | true | 1x | 2.54 MB | 2.75 MB | 1.08x | 2.72 MB | 6742 | 0 | 2591 | 6391 B |
| 5000 | page | true | 3x | 2.60 MB | 3.01 MB | 1.16x | 2.96 MB | 20382 | 0 | 2879 | 8385 B |
| 5000 | page | false | 0x | 2.56 MB | 2.66 MB | 1.04x | 2.64 MB | 0 | 0 | 0 | 20 B |
| 5000 | page | false | 0.5x | 2.55 MB | 4.45 MB | 1.75x | 4.43 MB | 3373 | 3373 | 1973 | 4973 B |
| 5000 | page | false | 1x | 2.54 MB | 6.23 MB | 2.45x | 6.20 MB | 6747 | 6747 | 2591 | 6391 B |
| 5000 | page | false | 3x | 2.60 MB | 13.45 MB | 5.17x | 13.42 MB | 20402 | 20402 | 2879 | 8385 B |
| 10000 | board | true | 0x | 5.16 MB | 5.37 MB | 1.04x | 5.35 MB | 0 | 0 | 0 | 1 B |
| 10000 | board | true | 0.5x | 5.15 MB | 5.49 MB | 1.07x | 5.46 MB | 6856 | 0 | 3970 | 11806 B |
| 10000 | board | true | 1x | 5.17 MB | 5.63 MB | 1.09x | 5.59 MB | 13641 | 0 | 5215 | 15563 B |
| 10000 | board | true | 3x | 5.14 MB | 6.06 MB | 1.18x | 5.97 MB | 40879 | 0 | 5809 | 19031 B |
| 10000 | board | false | 0x | 5.16 MB | 5.37 MB | 1.04x | 5.35 MB | 0 | 0 | 0 | 1 B |
| 10000 | board | false | 0.5x | 5.15 MB | 9.02 MB | 1.75x | 8.99 MB | 6856 | 6856 | 3970 | 11806 B |
| 10000 | board | false | 1x | 5.17 MB | 12.65 MB | 2.45x | 12.61 MB | 13642 | 13642 | 5215 | 15563 B |
| 10000 | board | false | 3x | 5.14 MB | 27.10 MB | 5.28x | 27.04 MB | 40880 | 40880 | 5809 | 19031 B |
| 10000 | page | true | 0x | 5.16 MB | 5.35 MB | 1.04x | 5.31 MB | 0 | 0 | 0 | 20 B |
| 10000 | page | true | 0.5x | 5.15 MB | 5.45 MB | 1.06x | 5.41 MB | 6854 | 0 | 3963 | 10438 B |
| 10000 | page | true | 1x | 5.17 MB | 5.58 MB | 1.08x | 5.53 MB | 13635 | 0 | 5186 | 13951 B |
| 10000 | page | true | 3x | 5.14 MB | 5.96 MB | 1.16x | 5.87 MB | 40861 | 0 | 5812 | 17284 B |
| 10000 | page | false | 0x | 5.16 MB | 5.35 MB | 1.04x | 5.31 MB | 0 | 0 | 0 | 20 B |
| 10000 | page | false | 0.5x | 5.15 MB | 8.98 MB | 1.75x | 8.94 MB | 6856 | 6856 | 3963 | 10438 B |
| 10000 | page | false | 1x | 5.17 MB | 12.60 MB | 2.44x | 12.55 MB | 13642 | 13642 | 5186 | 13951 B |
| 10000 | page | false | 3x | 5.14 MB | 27.01 MB | 5.26x | 26.94 MB | 40880 | 40880 | 5812 | 17284 B |

### T2. The editing client (user 0, with its UndoManager and the spike cap model) vs the server

| live N | layout | gc | payload | server encoded | client encoded | client / payload | deleted items with content kept (client) | kept payload | items with keep flag | user undo / redo stack |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | board | true | 522.2 KB | 614.8 KB | 1.53 MB | 2.99x | 1810 | 945.3 KB | 1871 | 100 / 0 |
| 1000 | board | false | 522.2 KB | 2.74 MB | 2.74 MB | 5.37x | 4134 | 2.13 MB | 1871 | 100 / 0 |
| 1000 | page | true | 522.2 KB | 604.0 KB | 1.51 MB | 2.97x | 1810 | 945.3 KB | 1871 | 100 / 0 |
| 1000 | page | false | 522.2 KB | 2.73 MB | 2.73 MB | 5.35x | 4134 | 2.13 MB | 1871 | 100 / 0 |
| 5000 | board | true | 2.60 MB | 3.06 MB | 7.68 MB | 2.95x | 8991 | 4.61 MB | 9353 | 100 / 0 |
| 5000 | board | false | 2.60 MB | 13.50 MB | 13.50 MB | 5.19x | 20402 | 10.42 MB | 9353 | 100 / 0 |
| 5000 | page | true | 2.60 MB | 3.01 MB | 7.63 MB | 2.94x | 8991 | 4.61 MB | 9353 | 100 / 0 |
| 5000 | page | false | 2.60 MB | 13.45 MB | 13.45 MB | 5.17x | 20402 | 10.42 MB | 9353 | 100 / 0 |
| 10000 | board | true | 5.14 MB | 6.06 MB | 15.30 MB | 2.98x | 17940 | 9.22 MB | 18653 | 100 / 0 |
| 10000 | board | false | 5.14 MB | 27.10 MB | 27.10 MB | 5.28x | 40880 | 21.01 MB | 18653 | 100 / 0 |
| 10000 | page | true | 5.14 MB | 5.96 MB | 15.20 MB | 2.96x | 17940 | 9.22 MB | 18653 | 100 / 0 |
| 10000 | page | false | 5.14 MB | 27.01 MB | 27.01 MB | 5.26x | 40880 | 21.01 MB | 18653 | 100 / 0 |

### T3. Incremental update sizes during churn (bytes per update, whole run to 3x)

| live N | layout | op | count | median B | p95 B | max B |
|---|---|---|---|---|---|---|
| 1000 | board | draw | 2839 | 570 | 916.0 | 1053 |
| 1000 | board | erase | 3619 | 7 | 7.0 | 7 |
| 1000 | board | undo | 1295 | 551 | 890.0 | 1036 |
| 1000 | board | redo | 669 | 7 | 7.0 | 7 |
| 1000 | page | draw | 2839 | 567 | 912.0 | 1049 |
| 1000 | page | erase | 3619 | 6 | 6.0 | 7 |
| 1000 | page | undo | 1295 | 550 | 888.0 | 1034 |
| 1000 | page | redo | 669 | 6 | 6.0 | 7 |
| 5000 | board | draw | 14084 | 566 | 915.0 | 1116 |
| 5000 | board | erase | 17942 | 7 | 7.0 | 7 |
| 5000 | board | undo | 6318 | 547 | 894.0 | 1063 |
| 5000 | board | redo | 3158 | 7 | 7.0 | 7 |
| 5000 | page | draw | 14084 | 563 | 913.0 | 1113 |
| 5000 | page | erase | 17942 | 7 | 7.0 | 7 |
| 5000 | page | undo | 6318 | 546 | 894.0 | 1063 |
| 5000 | page | redo | 3158 | 7 | 7.0 | 7 |
| 10000 | board | draw | 28228 | 567 | 917.0 | 1128 |
| 10000 | board | erase | 35991 | 7 | 8.0 | 8 |
| 10000 | board | undo | 12652 | 547 | 897.0 | 1109 |
| 10000 | board | redo | 6353 | 7 | 8.0 | 8 |
| 10000 | page | draw | 28228 | 564 | 914.0 | 1125 |
| 10000 | page | erase | 35991 | 7 | 7.0 | 7 |
| 10000 | page | undo | 12652 | 546 | 896.0 | 1109 |
| 10000 | page | redo | 6353 | 7 | 7.0 | 7 |

(gc=false gives identical update sizes: gc does not change what is sent for an op.) Check: 1000/board erase median 7 B, 1000/page erase median 6 B, 5000/board erase median 7 B, 5000/page erase median 7 B, 10000/board erase median 7 B, 10000/page erase median 7 B

### T4. Cold load of the server state into a fresh doc (median of 5; ms) and memory (heap + arrayBuffers delta after gc, MB)

| live N | layout | author gc | churn | loading doc gc | whole board ms | one page ms | memory MB (heap + ab) | re-encoded after load |
|---|---|---|---|---|---|---|---|---|
| 1000 | board | true | 0x | true | 1.8 | 1.3 | 0.4 + 0.5 = 0.9 | 550.7 KB |
| 1000 | board | true | 0x | false | 1.9 | 1.6 | 0.5 + 0.5 = 1.0 | 550.7 KB |
| 1000 | board | true | 3x | true | 4.7 | 4.5 | 1.3 + 0.5 = 1.8 | 614.8 KB |
| 1000 | board | true | 3x | false | 6.3 | 6.9 | 1.4 + 0.5 = 1.9 | 614.8 KB |
| 1000 | board | false | 0x | true | 1.8 | 1.5 | 0.4 + 0.5 = 0.9 | 550.7 KB |
| 1000 | board | false | 0x | false | 2.3 | 1.7 | 0.4 + 0.5 = 0.9 | 550.7 KB |
| 1000 | board | false | 3x | true | 6.7 | 6.6 | 1.2 + 0.5 = 1.7 | 614.8 KB |
| 1000 | board | false | 3x | false | 8.7 | 12.3 | 2.3 + 2.6 = 4.9 | 2.74 MB |
| 1000 | page | true | 0x | true | 3.7 | 0.2 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | true | 0x | false | 3.6 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | true | 3x | true | 6.3 | 0.2 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | true | 3x | false | 5.4 | 0.2 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | false | 0x | true | 3.6 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | false | 0x | false | 2.8 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | false | 3x | true | 9.9 | 0.3 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | false | 3x | false | 7.9 | 0.3 | 2.3 + 2.6 = 4.9 | 2.73 MB |
| 5000 | board | true | 0x | true | 7.9 | 9.0 | 2.3 + 2.6 = 4.9 | 2.67 MB |
| 5000 | board | true | 0x | false | 6.3 | 5.0 | 2.3 + 2.6 = 4.9 | 2.67 MB |
| 5000 | board | true | 3x | true | 24.2 | 23.1 | 7.1 + 2.6 = 9.7 | 3.06 MB |
| 5000 | board | true | 3x | false | 24.3 | 24.4 | 7.1 + 2.6 = 9.7 | 3.06 MB |
| 5000 | board | false | 0x | true | 8.5 | 7.9 | 2.3 + 2.6 = 4.8 | 2.67 MB |
| 5000 | board | false | 0x | false | 6.1 | 8.4 | 2.1 + 2.6 = 4.6 | 2.67 MB |
| 5000 | board | false | 3x | true | 43.1 | 60.0 | 6.6 + 2.6 = 9.2 | 3.06 MB |
| 5000 | board | false | 3x | false | 43.3 | 71.8 | 11.0 + 13.0 = 24.0 | 13.50 MB |
| 5000 | page | true | 0x | true | 9.2 | 0.5 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | true | 0x | false | 10.6 | 0.5 | 2.2 + 2.6 = 4.7 | 2.66 MB |
| 5000 | page | true | 3x | true | 29.1 | 0.9 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | true | 3x | false | 19.4 | 0.9 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | false | 0x | true | 10.5 | 0.5 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | false | 0x | false | 8.1 | 0.4 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | false | 3x | true | 57.4 | 1.2 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | false | 3x | false | 34.7 | 3.9 | 11.1 + 13.0 = 24.1 | 13.45 MB |
| 10000 | board | true | 0x | true | 14.6 | 19.5 | 4.4 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | true | 0x | false | 20.2 | 8.8 | 4.5 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | true | 3x | true | 72.1 | 57.6 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | true | 3x | false | 55.1 | 56.2 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | false | 0x | true | 14.3 | 18.4 | 4.4 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | false | 0x | false | 11.9 | 9.4 | 4.5 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | false | 3x | true | 198.5 | 146.3 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | false | 3x | false | 152.5 | 145.8 | 22.1 + 26.1 = 48.2 | 27.10 MB |
| 10000 | page | true | 0x | true | 13.3 | 1.8 | 4.5 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | true | 0x | false | 25.1 | 0.5 | 4.4 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | true | 3x | true | 75.1 | 2.7 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | true | 3x | false | 57.3 | 1.6 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | false | 0x | true | 14.8 | 2.2 | 4.5 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | false | 0x | false | 21.4 | 0.5 | 4.4 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | false | 3x | true | 149.0 | 12.1 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | false | 3x | false | 129.4 | 3.0 | 22.1 + 26.1 = 48.2 | 27.01 MB |

### T5. Cost of the churn itself and the run

| live N | layout | gc | iterations (3x) | erases | re-draws | undos | redos | ms per iteration (3 replicas + relay) | run wall time (incl. measurements) |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | board | true | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | board | false | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | page | true | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | page | false | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 5000 | board | true | 15000 | 17942 | 14084 | 6318 | 3158 | 1.4 | 23 s |
| 5000 | board | false | 15000 | 17942 | 14084 | 6318 | 3158 | 1.4 | 24 s |
| 5000 | page | true | 15000 | 17942 | 14084 | 6318 | 3158 | 1.5 | 23 s |
| 5000 | page | false | 15000 | 17942 | 14084 | 6318 | 3158 | 1.5 | 24 s |
| 10000 | board | true | 30000 | 35991 | 28228 | 12652 | 6353 | 3.4 | 107 s |
| 10000 | board | false | 30000 | 35991 | 28228 | 12652 | 6353 | 4.1 | 134 s |
| 10000 | page | true | 30000 | 35991 | 28228 | 12652 | 6353 | 5.3 | 162 s |
| 10000 | page | false | 30000 | 35991 | 28228 | 12652 | 6353 | 4.4 | 139 s |

### T6. Undo retention experiment (5k live, gc=true, 3x churn): what keeps tombstone content alive

Variants: **noum** = no UndoManager (pure erase); **none** = UndoManagers, no cap (stacks grow); **splice** = the sync spike cap (trim the stack arrays only); **release** = trim and also clear the `keep` flag of the dropped entries. "Server" = replica without UndoManager.

| layout | variant | payload | server encoded | client encoded | client: deleted items with content | their payload | undo stack | client encoded after um.clear() | client content-holding deleted items after um.clear() | after reload into gc doc: content-holding / re-encoded |
|---|---|---|---|---|---|---|---|---|---|---|
| board | none | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 10648 | 7.84 MB | 9295 | 0 / 3.06 MB |
| board | noum | 2.58 MB | 3.07 MB | 3.07 MB | 0 | 0.0 KB | 0 |  |  |  |
| board | release | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 100 | 7.73 MB | 9094 | 0 / 3.06 MB |
| board | splice | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 100 | 7.73 MB | 9094 | 0 / 3.06 MB |
| page | none | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 10648 | 7.79 MB | 9295 | 0 / 3.01 MB |
| page | noum | 2.58 MB | 3.02 MB | 3.02 MB | 0 | 0.0 KB | 0 |  |  |  |
| page | release | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 100 | 7.68 MB | 9091 | 0 / 3.01 MB |
| page | splice | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 100 | 7.68 MB | 9091 | 0 / 3.01 MB |

### T7. Correctness checks (every run)

| check | 1k board gc=true | 1k board gc=false | 1k page gc=true | 1k page gc=false | 5k board gc=true | 5k board gc=false | 5k page gc=true | 5k page gc=false | 10k board gc=true | 10k board gc=false | 10k page gc=true | 10k page gc=false |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| convergence: N user replicas + server have identical content after churn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| convergence: identical state vectors | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| integrity: every live stroke equals the bytes originally drawn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| cold load of server state: content identical | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| erase removed the stroke on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| undo of an erase after heavy churn restores the stroke (content equal) on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| redo erases it again on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| second undo restores it again (content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| state converged after the undo/redo round | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| interleaved: X undo restores only X erase (a back, b still gone, content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| interleaved: Y undo then restores b (content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| double erase of one stroke by two users: X undo restores it | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| double erase: Y undo afterwards keeps convergence | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| undo stack bounded by cap N | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| drain: N consecutive undos by X (stack capped) run without error and converge | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| drain: N redos (the N undos plus older redo entries) converge | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| final integrity: every live stroke equals the bytes originally drawn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |


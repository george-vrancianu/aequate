# Results: Yjs board under erase/undo churn, and on a low-end tablet (ticket #39)

PROTOTYPE (throwaway). Machine: WSL2, Ryzen 9 5950X, Node 24, Yjs 13.6.x, Hocuspocus 4.x; numbers are relative, not absolute. Tablet numbers: one iPad 9th generation run (iPadOS 26.5, Chrome for iOS, so WebKit) over home Wi-Fi, see Part 2.

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
| fresh, 0x | 12 to 20 | 9.6 |
| 3x churn, gc=true | 46 to 75 | 19.4 |
| 3x churn, author gc=false loaded into gc=true doc | 98 to 199 (each load strips the content) | 19.4 |
| 3x churn, gc=false doc loaded into gc=false doc | 96 to 153 | 48.2 |

At 5k: 18 to 29 ms and 9.7 MB (gc=true, 3x) against 6 to 9 ms and 4.8 MB fresh. One page of a per-page layout at 10k, 3x: 1.6 to 2.9 ms. Churn costs about 3.0 to 5.3 ms per iteration at 10k for three replicas plus relay (T5; this is harness cost for four replicas, not an editing-client figure).

Timings vary run to run (the table gives the range over the original run, the reviewer's re-run and the fixer's re-run, which share seeds and so have identical byte numbers). Bytes and counts were identical in all three runs; memory figures agreed within about 1 MB.

Per item, what churn costs the server doc at 10k, 3x (facts): encoded bytes +17 B per deleted stroke (5.37 MB fresh to 6.06 MB, 0.69 MB over 40,879 tombstones); heap after load goes from 9.6 to 19.4 MB, about 250 B of heap per tombstone (40,879 tombstones, +9.8 MB); cold load goes from 12 to 20 ms to 46 to 75 ms, about 4x. The heap and load costs are per item, not per encoded byte, and are what a weak tablet will feel; they have not been measured on one.

**3. Undo stacks and gc (the client side, user 0 with an UndoManager, gc=true, 10k, 3x):**

- The editing client's encoded state is 15.3 MB against 6.06 MB on the server (payload 5.14 MB): **2.98x payload versus 1.18x**. 17,940 deleted items on the client still hold their content (9.2 MB of payload). The server, without an UndoManager, holds none.
- Cause (from the Yjs source, `UndoManager` and `cleanupTransactions`): an item deleted in a tracked transaction is marked `keep`, and gc only inspects the items of the transaction that deleted them. So content that was kept at deletion time is never collected in that live doc, even after the stack entry is dropped.
- **The cap did not change this.** Retained content is identical with no cap (10,648 stack entries at the end), the spike's cap (100), and the cap plus clearing `keep` on the dropped entries (T6: 8,991 items, 4.61 MB at 5k in all three). Calling `um.clear()` on the whole stack did not reclaim anything in the live doc either: the content-holding count is identical just before and just after the clear (9,296 / 9,095 / 9,092). Those counts are higher than the 8,991 at the 3x checkpoint only because the final correctness checks ran more erases and undos before the clear; `clear()` itself changed nothing. A fresh `applyUpdate` into a gc doc (reload) reclaims all of it (0 content-holding items, 3.06 MB at 5k).
- Without any UndoManager the client equals the server (3.07 MB at 5k).
- Attribution, measured (T6b, 5k, gc=true, items still holding content on user 0's replica): 93.8 to 94.0% were deleted in user 0's own tracked transactions (own erases, redo re-erases, undone draws); 562 items (6.0 to 6.2%) were deleted by other users. The 6% is explained by Yjs `redoItem`, which also calls `keepItem(redoneItem, true)`: a stroke that this user restored by undo stays `keep` while live, so a later erase of it, by anyone including a remote user, retains its content. So the retained amount grows with the number of items deleted by that user's tracked transactions (about 520 B per such item) plus restored strokes erased later by anyone, not with the stack depth. Not measured: the live heap of the client replica separately (only retained payload bytes and encoded size are).
- Mechanism, checked in the Yjs source: in `cleanupTransactions` `afterTransaction` (and with it the UndoManager's `keepItem(item, true)`) runs before `tryGcDeleteSet`, which only looks at that transaction's delete set; `clearUndoManagerStackItem` only resets `keep`. So the cap, the release variant and `um.clear()` cannot reclaim content in a live doc, and a reload can.

**4. Correctness after heavy churn** (T7, all 12 runs pass, 0 failures; the checks were extended in the fix round and every run re-run): in the churn loop, every undo by an acting user (and each undo+redo) is asserted individually after the flush: the right stroke is present (or gone after redo) with equal bytes on all 4 replicas (1,188 asserted ops at 1k, skipped where another user erased the same stroke concurrently); a three-user interleave is checked too. Replicas and server converge (content and state vectors identical); every live stroke equals the bytes originally drawn; an erased stroke is restored by undo with equal content on every replica (also with gc=true, because kept items survive); redo re-erases; a second undo restores again; interleaved concurrent erases by two users undo independently (only own erase is undone); concurrent double-erase of one stroke then undo works; the capped stack holds at most 100; draining up to 300 undos then redos converges. Per-page undo needed one fix: `UndoManager.undo()` can consume several stack entries when earlier ones are no-ops (for instance the stroke was already erased by someone else), so the app-level page stack must only push a redo when `undo()` returned a result.

### Answer to the ticket question

- **Do the spike's conclusions hold: CPU and memory are not the limit up to 10k strokes, the cost is bytes?** CPU: yes. Churn costs a few ms per iteration, a 10k cold load of a 3x-churned server doc is 46 to 75 ms on this desktop (about 4x a fresh doc), a one-off cost of roughly 3 to 4.5 frames at 16.7 ms that will be several times larger on a weak tablet (not measured there), while applying one remote stroke is about 0.1 ms, the per-frame number, and an erase is a 7-byte update. Bytes: yes for the wire and encoded size (about 17 B per deleted stroke), but the per-tombstone cost that remains is per item: about 250 B of heap and about 4x on cold load after 3x churn at 10k. Memory: a qualified yes. The server doc is 19 MB against 9.6 MB fresh at 10k, 3x churn. The editing client with an UndoManager is the exception: it holds about 9 MB of dead stroke payload after 3x churn at 10k and the cap does not release it.
- **Do gc plus the cap keep the doc bounded?** gc: partly. With gc=true the server doc stays near the live payload (1.18x at 3x churn) but still grows linearly with every deletion, about 17 B per deleted stroke, with no compaction found short of rebuilding the doc; gc=false is not bounded in any useful sense (5.3x at 3x churn, 27 MB at 10k). The cap: it bounds the stack length (and the memory of the stack objects themselves) but, as measured, **not** the dead content the client retains; only a reload of the doc frees it. One doc per board and one doc per page are indistinguishable here.

### Recommendations (labelled opinion, derived from the above)

1. Keep `doc.gc = true` (the Hocuspocus default) on the server and clients; do not turn it off for any undo or history feature (gc=false costs 5x at 3x churn).
2. Do not rely on the stack cap to free memory in a long editing session. Either reload the client doc (drop and re-fetch it, which loses the undo stack) at natural boundaries, or accept about 520 B of retained payload per item deleted by that user's tracked transactions (plus restored strokes erased later by anyone) until reload. At 10k strokes with 3x churn that is about 9 MB, probably acceptable but unmeasured on the tablet.
3. The encoded size of a tombstone (about 17 B) is small, but its heap (about 250 B) and load cost (cold load about 4x at 3x churn) are per item and have not been measured on the tablet. Opinion: no server-side compaction for v1, revisit after the tablet numbers; if it ever matters, rebuilding a doc from live content (copy strokes into a new doc) is the only reset found, and it invalidates client state.
4. The per-page app-level undo stack needs the "push redo only if undo returned a result" rule.

## Part 2: low-end tablet

### Desktop baseline (headless Chromium 158 on this machine, loopback, `tablet/desktop-baseline.json`)

Not a tablet: this is the reference to compare the tablet numbers against. Times in ms, median of 3 for sync and open, render includes decode and draw to an 800x1200 canvas, apply is per remote stroke update (n about 101: 100 single-stroke adds, then one transaction deleting them again) from beforeAllTransactions to afterAllTransactions including an observer that decodes and draws the stroke. Heap from `performance.memory` with `--enable-precise-memory-info` (the verify run passes `?precise` so the JSON records `preciseMemory: true`), not gc-forced, so noisy (the page-layout 10k row is clearly affected by garbage). On a real tablet over plain http that flag is not set: the value is bucketed and can be stale (a 1k board read 9.5 MB at all four points in one check), so the page marks tablet heap values "(coarse)" and records `preciseMemory: false`; treat tablet heap as unavailable.

| size | layout | sync + open whole board | open one page | apply per stroke med / p95 / max | render one page | render whole board | doc bytes | heap MB after open / after render |
|---|---|---|---|---|---|---|---|---|
| 1k | board | 14.9 | 13 | 0.1 / 0.2 / 0.8 | 1 | 18.9 | 556,422 | 8.2 / 16.7 |
| 1k | page | 17.5 | 4 | 0.1 / 0.2 / 0.3 | 0.7 | 13.6 | 554,091 | 26.3 / 28.6 |
| 3k | board | 25.8 | 28.7 | 0.1 / 0.2 / 0.3 | 1.9 | 41.9 | 1,699,218 | 29.5 / 33.1 |
| 3k | page | 31.8 | 5.2 | 0.1 / 0.2 / 0.2 | 2.1 | 42.8 | 1,691,906 | 43.5 / 40.4 |
| 5k | board | 43.2 | 38.9 | 0.1 / 0.2 / 0.3 | 3 | 65.9 | 2,809,622 | 80.8 / 69.5 |
| 5k | page | 48.5 | 5.8 | 0.1 / 0.2 / 0.3 | 4 | 68.6 | 2,797,312 | 92 / 82.3 |
| 10k | board | 77.3 | 76.8 | 0.1 / 0.2 / 0.3 | 6 | 157.2 | 5,647,466 | 165.7 / 142.6 |
| 10k | page | 78 | 7.7 | 0.1 / 0.2 / 0.3 | 5.9 | 142.5 | 5,622,656 | 215.6 / 287.3 |

HTTP round trip to the server was 1.2 to 1.6 ms. Open-one-page for the one-doc-per-board layout is the whole-board sync by construction (so those two columns agree for the board layout; at 10k the 76.8 ms against 77.3 ms here is noise). The apply time per stroke is far below a frame at every size on desktop; what grows is the whole-board open (bytes) and the full render.

How the page was verified: Playwright (devDependency of this folder only; `chromium-headless-shell` downloaded cleanly) drove the real page against the server on an ephemeral port; the "Copy results as JSON" path reported "copied". The plain-http fallback was exercised separately by the reviewer over the LAN IP (secure context false, no clipboard API): `execCommand` copied, and with `execCommand` forced to fail the page showed the "use the iPad Copy bubble" message with the text selected. This was not run on a real tablet. Server and browser were shut down afterwards; no process left running.

### Tablet results

iPad, iPadOS 26.5, Chrome for iOS 156 (`CriOS`, so WebKit underneath, same engine as Safari), 810x1080 CSS px at 2x, `hardwareConcurrency` 4, home Wi-Fi to the Hocuspocus server on this PC (mirrored WSL2). One run of all 4 sizes x 2 layouts on 2026-11-09. Raw JSON: `tablet/ipad.json`. iPad 9th generation (2021, A13 Bionic, 3 GB RAM), Wi-Fi probably 5 GHz (from memory, not checked); battery state not recorded. No heap numbers (iOS exposes no `performance.memory`). WebKit clamps `performance.now()` to 1 ms, so the apply column reads 0 or 1: it means "under about 1 ms", not a measured value.

Times in ms, median of 3, same definitions as the desktop table. In brackets: ratio to the desktop baseline. The desktop ran over loopback, so the sync and open ratios mix device CPU with Wi-Fi latency and bandwidth; the render ratio is device only.

| size | layout | sync + open whole board | open one page | apply per stroke med / p95 / max | render one page | render whole board | doc bytes | HTTP RTT |
|---|---|---|---|---|---|---|---|---|
| 1k | board | 136 (9.1x) | 144 (11.1x) | 1 / 1 / 3 | 6 | 23 (1.2x) | 556,422 | 4 |
| 1k | page | 221 (12.6x) | 54 (13.5x) | 0 / 1 / 1 | 6 | 29 (2.1x) | 554,091 | 5.5 |
| 3k | board | 236 (9.1x) | 246 (8.6x) | 0 / 1 / 1 | 12 | 49 (1.2x) | 1,699,218 | 7 |
| 3k | page | 412 (13.0x) | 44 (8.5x) | 0 / 1 / 1 | 11 | 55 (1.3x) | 1,691,908 | 8 |
| 5k | board | 332 (7.7x) | 328 (8.4x) | 0 / 1 / 1 | 16 | 87 (1.3x) | 2,809,622 | 8 |
| 5k | page | 399 (8.2x) | 54 (9.3x) | 0 / 1 / 1 | 15 | 76 (1.1x) | 2,797,310 | 7 |
| 10k | board | 874 (11.3x) | 590 (7.7x) | 0 / 1 / 1 | 29 | 147 (0.9x) | 5,647,466 | 7 |
| 10k | page | 564 (7.2x) | 74 (9.6x) | 0 / 1 / 1 | 28 | 149 (1.0x) | 5,622,656 | 6.5 |

Facts from the table:

- **Live collaboration is not the limit on the iPad.** Applying one remote stroke (Yjs plus decode and draw) stays under about 1 ms at every size, worst case 3 ms (1k board, first update). That is well inside a 16.7 ms frame.
- **Rendering matches the desktop.** Drawing all 10k strokes (1.75 M points) takes about 150 ms on both. That is likely because the desktop baseline is headless Chromium drawing in software, so this compares rendering paths, not CPUs. One page (500 strokes at 10k) draws in 28 to 29 ms, about 2 frames.
- **Opening the board is the cost, and it grows with bytes.** With one doc per board, opening any page means syncing the whole board: 136 ms at 1k up to 590 to 874 ms at 10k (5.6 MB). The first 10k run took 1,446 ms. With one doc per page, opening one page takes 44 to 74 ms at every size, so it stays flat. Syncing the whole board as 20 docs is slower than one doc at 1k and 3k (221 vs 136, 412 vs 236), similar at 5k, and faster at 10k (564 vs 874). The 10k board number is noisy (runs 1,446 / 874 / 629).
- Encoded doc bytes match the desktop exactly, or within a few bytes of `/stream` tombstone drift. Wi-Fi RTT was 4 to 8 ms.

Not measured on the tablet: a churned doc. On desktop, a 3x-churned 10k doc loads cold about 4x slower than a fresh one (Part 1). The page has no churn mode, so nobody knows whether that 4x holds on the iPad. If it did, a churned 10k one-doc-per-board open would land in the seconds. That is an extrapolation, not a measurement.

Answer for the tablet half of the ticket: the spike's conclusion holds on this iPad. Per-stroke CPU is negligible, and the cost that grows is bytes, felt as open time. A 10k board opens in under a second as one doc. As one doc per page, the first page opens in under 100 ms.


## Appendix: full churn tables

Generated by `node tables.js` from `results/*.json` (merged in `results.json`); identical to `results-tables.md`.

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
| 1000 | board | true | 0x | true | 2.1 | 1.4 | 0.4 + 0.5 = 0.9 | 550.7 KB |
| 1000 | board | true | 0x | false | 2.4 | 1.8 | 0.5 + 0.5 = 1.0 | 550.7 KB |
| 1000 | board | true | 3x | true | 4.3 | 3.5 | 1.3 + 0.5 = 1.8 | 614.8 KB |
| 1000 | board | true | 3x | false | 4.8 | 6.3 | 1.5 + 0.5 = 2.0 | 614.8 KB |
| 1000 | board | false | 0x | true | 1.7 | 1.4 | 0.4 + 0.5 = 0.9 | 550.7 KB |
| 1000 | board | false | 0x | false | 1.8 | 1.6 | 0.5 + 0.5 = 1.0 | 550.7 KB |
| 1000 | board | false | 3x | true | 7.0 | 5.5 | 1.2 + 0.5 = 1.7 | 614.8 KB |
| 1000 | board | false | 3x | false | 7.6 | 10.5 | 2.3 + 2.6 = 4.9 | 2.74 MB |
| 1000 | page | true | 0x | true | 3.1 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | true | 0x | false | 3.3 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | true | 3x | true | 5.4 | 0.2 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | true | 3x | false | 4.9 | 0.2 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | false | 0x | true | 2.7 | 0.2 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | false | 0x | false | 2.9 | 0.1 | 0.5 + 0.5 = 1.0 | 548.3 KB |
| 1000 | page | false | 3x | true | 8.8 | 0.3 | 1.5 + 0.5 = 2.0 | 604.0 KB |
| 1000 | page | false | 3x | false | 6.6 | 0.3 | 2.3 + 2.6 = 4.9 | 2.73 MB |
| 5000 | board | true | 0x | true | 6.4 | 9.4 | 2.3 + 2.6 = 4.8 | 2.67 MB |
| 5000 | board | true | 0x | false | 6.1 | 4.9 | 2.2 + 2.6 = 4.8 | 2.67 MB |
| 5000 | board | true | 3x | true | 21.3 | 22.6 | 7.1 + 2.6 = 9.7 | 3.06 MB |
| 5000 | board | true | 3x | false | 24.7 | 23.9 | 7.1 + 2.6 = 9.7 | 3.06 MB |
| 5000 | board | false | 0x | true | 7.2 | 7.6 | 2.3 + 2.6 = 4.9 | 2.67 MB |
| 5000 | board | false | 0x | false | 5.9 | 5.0 | 2.3 + 2.6 = 4.9 | 2.67 MB |
| 5000 | board | false | 3x | true | 51.6 | 72.8 | 7.7 + 2.6 = 10.3 | 3.06 MB |
| 5000 | board | false | 3x | false | 45.1 | 67.4 | 10.5 + 13.0 = 23.5 | 13.50 MB |
| 5000 | page | true | 0x | true | 9.2 | 0.6 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | true | 0x | false | 9.0 | 0.4 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | true | 3x | true | 27.3 | 0.9 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | true | 3x | false | 18.4 | 0.8 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | false | 0x | true | 9.4 | 0.5 | 2.3 + 2.6 = 4.8 | 2.66 MB |
| 5000 | page | false | 0x | false | 8.7 | 0.4 | 2.2 + 2.6 = 4.7 | 2.66 MB |
| 5000 | page | false | 3x | true | 52.8 | 1.2 | 7.2 + 2.6 = 9.8 | 3.01 MB |
| 5000 | page | false | 3x | false | 33.9 | 3.6 | 11.1 + 13.0 = 24.1 | 13.45 MB |
| 10000 | board | true | 0x | true | 13.8 | 19.0 | 4.3 + 5.2 = 9.4 | 5.37 MB |
| 10000 | board | true | 0x | false | 17.8 | 8.7 | 4.3 + 5.2 = 9.5 | 5.37 MB |
| 10000 | board | true | 3x | true | 64.2 | 63.0 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | true | 3x | false | 58.0 | 59.4 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | false | 0x | true | 14.1 | 19.3 | 4.4 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | false | 0x | false | 19.6 | 9.3 | 4.5 + 5.2 = 9.6 | 5.37 MB |
| 10000 | board | false | 3x | true | 133.4 | 106.9 | 14.3 + 5.1 = 19.4 | 6.06 MB |
| 10000 | board | false | 3x | false | 95.8 | 107.2 | 22.1 + 26.1 = 48.2 | 27.10 MB |
| 10000 | page | true | 0x | true | 12.4 | 1.6 | 4.5 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | true | 0x | false | 20.0 | 0.5 | 4.4 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | true | 3x | true | 49.1 | 2.0 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | true | 3x | false | 42.4 | 1.6 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | false | 0x | true | 13.0 | 1.8 | 4.5 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | false | 0x | false | 22.3 | 0.6 | 4.4 + 5.2 = 9.6 | 5.35 MB |
| 10000 | page | false | 3x | true | 97.9 | 2.9 | 14.3 + 5.1 = 19.4 | 5.96 MB |
| 10000 | page | false | 3x | false | 110.8 | 2.4 | 22.1 + 26.1 = 48.2 | 27.01 MB |

### T5. Cost of the churn itself and the run

| live N | layout | gc | iterations (3x) | erases | re-draws | undos | redos | ms per iteration (3 replicas + relay) | run wall time (incl. measurements) |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | board | true | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | board | false | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | page | true | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 1000 | page | false | 3000 | 3619 | 2839 | 1295 | 669 | 0.4 | 2 s |
| 5000 | board | true | 15000 | 17942 | 14084 | 6318 | 3158 | 1.2 | 21 s |
| 5000 | board | false | 15000 | 17942 | 14084 | 6318 | 3158 | 1.2 | 22 s |
| 5000 | page | true | 15000 | 17942 | 14084 | 6318 | 3158 | 1.3 | 22 s |
| 5000 | page | false | 15000 | 17942 | 14084 | 6318 | 3158 | 1.3 | 22 s |
| 10000 | board | true | 30000 | 35991 | 28228 | 12652 | 6353 | 3.0 | 94 s |
| 10000 | board | false | 30000 | 35991 | 28228 | 12652 | 6353 | 3.0 | 100 s |
| 10000 | page | true | 30000 | 35991 | 28228 | 12652 | 6353 | 3.5 | 107 s |
| 10000 | page | false | 30000 | 35991 | 28228 | 12652 | 6353 | 3.3 | 105 s |

### T6. Undo retention experiment (5k live, gc=true, 3x churn): what keeps tombstone content alive

Variants: **noum** = no UndoManager (pure erase); **none** = UndoManagers, no cap (stacks grow); **splice** = the sync spike cap (trim the stack arrays only); **release** = trim and also clear the `keep` flag of the dropped entries. "Server" = replica without UndoManager.

| layout | variant | payload | server encoded | client encoded | client: deleted items with content | their payload | undo stack | content-holding deleted items just before um.clear() (after the final checks) | client encoded after um.clear() | client content-holding deleted items after um.clear() | after reload into gc doc: content-holding / re-encoded |
|---|---|---|---|---|---|---|---|---|---|---|---|
| board | none | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 10648 | 9296 | 7.84 MB | 9296 | 0 / 3.06 MB |
| board | noum | 2.58 MB | 3.07 MB | 3.07 MB | 0 | 0.0 KB | 0 |  |  |  |  |
| board | release | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 100 | 9095 | 7.73 MB | 9095 | 0 / 3.06 MB |
| board | splice | 2.60 MB | 3.06 MB | 7.68 MB | 8991 | 4.61 MB | 100 | 9095 | 7.73 MB | 9095 | 0 / 3.06 MB |
| page | none | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 10648 | 9296 | 7.79 MB | 9296 | 0 / 3.01 MB |
| page | noum | 2.58 MB | 3.02 MB | 3.02 MB | 0 | 0.0 KB | 0 |  |  |  |  |
| page | release | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 100 | 9092 | 7.68 MB | 9092 | 0 / 3.01 MB |
| page | splice | 2.60 MB | 3.01 MB | 7.63 MB | 8991 | 4.61 MB | 100 | 9092 | 7.68 MB | 9092 | 0 / 3.01 MB |

The "3x" columns are the 3x checkpoint. The "before/after um.clear()" columns are taken after the final correctness checks (extra erases, up to 300 undos and redos), which is why they differ from the 3x column; compare after-clear with before-clear, not with 3x.

#### T6b. Who deleted the retained items (user 0 replica, gc=true, 5k, at the end of the run after the final checks, measured in the harness)

| layout | variant | retained items (content held) | deleted in user 0 tracked transactions (erase, redo, undone draw) | other | other share | all items user 0 deleted in tracked transactions |
|---|---|---|---|---|---|---|
| board | none | 9296 | 8734 | 562 | 6.0% | 8734 |
| board | release | 9095 | 8533 | 562 | 6.2% | 8533 |
| board | splice | 9095 | 8533 | 562 | 6.2% | 8533 |
| page | none | 9296 | 8734 | 562 | 6.0% | 8734 |
| page | release | 9092 | 8530 | 562 | 6.2% | 8530 |
| page | splice | 9092 | 8530 | 562 | 6.2% | 8530 |

### T7. Correctness checks (every run)

| check | 1k board gc=true | 1k board gc=false | 1k page gc=true | 1k page gc=false | 5k board gc=true | 5k board gc=false | 5k page gc=true | 5k page gc=false | 10k board gc=true | 10k board gc=false | 10k page gc=true | 10k page gc=false |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| convergence: N user replicas + server have identical content after churn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| convergence: identical state vectors | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| integrity: every live stroke equals the bytes originally drawn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| cold load of server state: content identical | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| churn loop: each of N interleaved undo/redo ops by the acting users left the right stroke present/absent with equal bytes on all N replicas | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| erase removed the stroke on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| undo of an erase after heavy churn restores the stroke (content equal) on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| redo erases it again on every replica | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| second undo restores it again (content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| state converged after the undo/redo round | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| interleaved: X undo restores only X erase (a back, b still gone, content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| interleaved: Y undo then restores b (content equal) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| double erase of one stroke by two users: X undo restores it | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| double erase: Y undo afterwards keeps convergence and the stroke stays present | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| three-user interleave: all three erased | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| three-user interleave: Z undo restores only c | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| three-user interleave: X undo restores only a (b still gone) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| three-user interleave: Z redo re-erases only c | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| three-user interleave: Y undo restores b; a back, c gone, converged | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| undo stack bounded by cap N | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| drain: N consecutive undos by X (stack capped) run without error and converge | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| drain: N redos (the N undos plus older redo entries) converge | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| final integrity: every live stroke equals the bytes originally drawn | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |


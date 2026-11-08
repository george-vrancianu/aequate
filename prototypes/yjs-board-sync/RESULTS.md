# RESULTS: Yjs board with thousands of strokes (PROTOTYPE, ticket #16)

Throwaway spike; see README.md. Terms follow GLOSSARY.md (board, page, stroke). Facts first, recommendation last.

## Setup and caveats

- Machine: WSL2 (kernel 6.18.33.2-microsoft-standard-WSL2) on AMD Ryzen 9 5950X (16 cores / 32 threads), 31 GB RAM, Node v24.21.0.
  Yjs 13.6.33, @hocuspocus/server and provider 4.8.0, ws 8.22, SQLite via node:sqlite.
- Numbers are relative, not absolute: a fast desktop CPU, loopback network, no other clients. A school tablet or Chromebook will be several times slower on CPU, and real Wi-Fi dominates transfer time.
- Strokes are synthetic (seeded RNG, 42): 50-300 points each (random-walk curve), x/y at 0.1 px and pressure packed as delta zigzag varints into one Uint8Array per stroke (about 540 bytes on average). Stored as `strokes: Y.Map<id, Uint8Array>`, ids 10 characters, one transaction per stroke (written once at pen-up). Strokes are spread evenly over pages in drawing order.
- Layout A uses one root Y.Map per page (`strokes:0`, `strokes:1`, ...). B uses `pages: Y.Map<pageId, Y.Doc>`; for B and C "size" and "load" are summed over all documents, "open one page" for B is root doc + that subdoc.
- Timings are the median of 7 repetitions after one discarded warm-up, each on a fresh Y.Doc, with a gc before every repetition. Memory is the delta of V8 heapUsed plus off-heap ArrayBuffers (Yjs copies each binary stroke into its own Uint8Array, which lives off-heap) after gc in a fresh child process (`--expose-gc`, heap capped at 4 GB); the baseline is taken before the update files are read and the files are freed before measuring. The whole run took about 66 s, host memory used peaked at about 15 GB (baseline 14 GB at start).
- Not measured: erase/tombstone growth, awareness, real network, more than one Hocuspocus client per doc, devices slower than this machine. The Hocuspocus per-save tables add 10 extra strokes from the same generator and take the median of their update sizes; stroke length varies from 50 to 300 points, so that median differs from the pure-Yjs median over all strokes (for example 737 vs 571 bytes at 10k) and the write amplification ratios are approximate. The tables are from the final run; a second full run varied by up to about 15% on timings, and not at all on byte counts.

## Headline facts

- A 10,000-stroke board is 5.6 MB as a Yjs update (v1); the packed payload alone is 5.4 MB, so Yjs overhead is about 4.5%. The v2 encoding saves only about 0.4% on this data (strokes are opaque binary).
- One pen-up stroke is a roughly 570 byte update at any board size (about 30 bytes over the packed stroke). Update size does not grow with the board.
- Decoding the whole 10k board: about 15 ms apply (v1) plus about 12 ms to unpack every stroke; memory held about 10 MB (5 MB V8 heap plus 5 MB off-heap stroke payloads). CPU and memory are not the constraint at this scale on this machine; the 5.6 MB transfer and the 5.6 MB whole-doc rewrite per Hocuspocus save are.
- The stock Hocuspocus Database-extension pattern (which this prototype reproduces in its `onStoreDocument`) rewrites the whole document on every save: 5.6 MB written (about 7,700 times the 737 byte stroke update) and about 13 ms of server time per save at 10k strokes in one doc. With 20 separate page documents it is 276 KB and 0.7 ms.
- Layout B cannot be served by Hocuspocus: subdocument contents never reach the server or other clients (concrete test below).
- Per-user undo passes every check in A, B and C. A has one UndoManager across all pages; B and C need one UndoManager per page document plus an app-level stack for cross-page order.

## Measurements

### Undo correctness (two clients, per-origin UndoManager, cap)

| check | A | B | C |
|---|---|---|---|
| A undo x2 removes only A last two strokes (a4,a3), before sync | PASS | PASS | PASS |
| after sync B still has all of B strokes; B view equals A view | PASS | PASS | PASS |
| B undo removes only b4, all A strokes remain | PASS | PASS | PASS |
| A redo brings back a3 (not a4) in both docs | PASS | PASS | PASS |
| A second redo brings back a4; B stroke b4 stays undone | PASS | PASS | PASS |
| new stroke after undo clears A redo stack | PASS | PASS | PASS |
| undo stack capped at 5 after 12 strokes (stack length) | PASS | PASS | PASS |
| cap drops the oldest: only a8..a12 undoable, a1..a7 stay; B strokes untouched | PASS | PASS | PASS |
| redo stack holds exactly the 5 capped entries after 12 undo attempts (redo entries come from the capped undo stack, so the redo trim cannot trigger separately) | PASS | PASS | PASS |
| full redo restores the 5 undone strokes | PASS | PASS | PASS |
| A undo of a stroke B already erased does not throw, does not resurrect it, docs converge | PASS | PASS | PASS |
| B undo of its erase restores A stroke a2 in both docs | PASS | PASS | PASS |
| random run (25 seeds x 300 ops: draw/erase own/erase other's/undo/redo, delayed delivery, cap 8): undo never removed the other user's strokes | PASS | PASS | PASS |
| random run: both clients converge (identical state vectors and stroke bytes) after final exchange | PASS | PASS | PASS |
| B: UndoManager on the ROOT doc scope does not see subdoc edits (undoStack stays 0); needs one UndoManager per subdoc | n/a | PASS | n/a |
| B: UndoManager scoped to the subdoc map works for that page | n/a | PASS | n/a |

- A: One UndoManager spans all pages natively; undo order across pages is automatic.
- B: No single UndoManager spans several Y.Docs (an UndoManager binds to one doc: typeScope[0].doc). Cross-page undo order needs an app-level stack of page ids on top of one UndoManager per page (done in this test; global ordering and the cap are then app responsibilities).
- C: No single UndoManager spans several Y.Docs (an UndoManager binds to one doc: typeScope[0].doc). Cross-page undo order needs an app-level stack of page ids on top of one UndoManager per page (done in this test; global ordering and the cap are then app responsibilities).

### Encoded size in bytes (Yjs update as stored/sent; B and C = sum over all docs)

| strokes | pages | raw packed payload | A v1 B | A v2 B | B v1 B | B v2 B | C v1 B | C v2 B | B root doc v1 B |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | 1 | 530912 | 555919 | 553936 | 553949 | 551977 | 553919 | 551936 | 30 |
| 1000 | 5 | 530912 | 555919 | 553936 | 554073 | 552151 | 553947 | 552022 | 126 |
| 1000 | 20 | 530912 | 556419 | 553438 | 554538 | 552813 | 554032 | 552332 | 506 |
| 3000 | 1 | 1622708 | 1697715 | 1691732 | 1691745 | 1685773 | 1691715 | 1685732 | 30 |
| 3000 | 5 | 1622708 | 1697715 | 1691732 | 1691869 | 1685947 | 1691743 | 1685818 | 126 |
| 3000 | 20 | 1622708 | 1699215 | 1690234 | 1692354 | 1686629 | 1691848 | 1686148 | 506 |
| 5000 | 1 | 2682112 | 2807119 | 2797136 | 2797149 | 2787177 | 2797119 | 2787136 | 30 |
| 5000 | 5 | 2682112 | 2807119 | 2797136 | 2797273 | 2787361 | 2797147 | 2787232 | 126 |
| 5000 | 20 | 2682112 | 2809619 | 2794638 | 2797758 | 2788033 | 2797252 | 2787552 | 506 |
| 10000 | 1 | 5392456 | 5642463 | 5622480 | 5622493 | 5602521 | 5622463 | 5602480 | 30 |
| 10000 | 5 | 5392456 | 5642463 | 5622480 | 5622617 | 5602705 | 5622491 | 5602576 | 126 |
| 10000 | 20 | 5392456 | 5647463 | 5617482 | 5623102 | 5603377 | 5622596 | 5602896 | 506 |

### Update size per stroke (bytes of the update emitted by one pen-up transaction; median / p95 over all strokes of the build)

| strokes | pages | avg packed stroke B | A | B | C |
|---|---|---|---|---|---|
| 1000 | 1 | 531 | 554.5 / 922 | 552.5 / 920 | 552.5 / 920 |
| 1000 | 5 | 531 | 554.5 / 922 | 551.5 / 919 | 551.5 / 919 |
| 1000 | 20 | 531 | 554.5 / 922 | 551.5 / 919 | 551.5 / 919 |
| 3000 | 1 | 541 | 572 / 920 | 570 / 918 | 570 / 918 |
| 3000 | 5 | 541 | 572 / 920 | 570 / 918 | 570 / 918 |
| 3000 | 20 | 541 | 572 / 921 | 569 / 918 | 569 / 918 |
| 5000 | 1 | 536 | 564 / 918 | 562 / 916 | 562 / 916 |
| 5000 | 5 | 536 | 564 / 918 | 562 / 916 | 562 / 916 |
| 5000 | 20 | 536 | 564.5 / 918 | 562 / 915 | 562 / 915 |
| 10000 | 1 | 539 | 570 / 917 | 568 / 915 | 568 / 915 |
| 10000 | 5 | 539 | 570 / 917 | 568 / 915 | 568 / 915 |
| 10000 | 20 | 539 | 571 / 918 | 568 / 915 | 568 / 915 |

### Cold load, whole board (ms, median of 7 fresh docs; apply = decode + integrate the stored update, read = unpack every stroke)

| strokes | pages | A apply v1 | A apply v2 | A read | B apply v1 | B apply v2 | B read | C apply v1 | C apply v2 | C read |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | 1 | 2.74 | 1.90 | 1.18 | 2.81 | 2.01 | 1.20 | 3.31 | 2.42 | 1.26 |
| 1000 | 5 | 2.74 | 1.91 | 1.34 | 3.09 | 2.20 | 1.42 | 3.93 | 2.81 | 1.29 |
| 1000 | 20 | 2.88 | 1.90 | 1.17 | 3.00 | 2.25 | 1.20 | 4.46 | 3.97 | 1.27 |
| 3000 | 1 | 6.47 | 4.50 | 3.55 | 6.22 | 4.43 | 3.61 | 7.69 | 4.95 | 3.56 |
| 3000 | 5 | 6.27 | 4.36 | 3.71 | 6.29 | 4.48 | 3.67 | 7.88 | 5.83 | 3.63 |
| 3000 | 20 | 6.34 | 4.82 | 3.70 | 7.02 | 4.48 | 3.66 | 9.12 | 7.56 | 4.17 |
| 5000 | 1 | 9.32 | 5.94 | 6.34 | 10.5 | 6.57 | 6.30 | 11.7 | 6.79 | 6.31 |
| 5000 | 5 | 9.37 | 6.10 | 6.21 | 8.85 | 6.04 | 6.41 | 11.2 | 8.30 | 6.30 |
| 5000 | 20 | 9.79 | 6.04 | 6.33 | 9.18 | 6.14 | 6.24 | 11.9 | 10.6 | 6.63 |
| 10000 | 1 | 15.7 | 9.66 | 12.0 | 17.1 | 9.87 | 12.1 | 17.1 | 11.9 | 12.2 |
| 10000 | 5 | 15.8 | 8.78 | 12.1 | 14.6 | 11.0 | 12.4 | 19.4 | 12.5 | 12.8 |
| 10000 | 20 | 15.0 | 8.03 | 12.1 | 13.7 | 8.74 | 12.2 | 18.0 | 14.0 | 12.3 |

### Open a single page (ms, median; A must load the whole board, B = root doc + that subdoc, C = that doc only)

| strokes | pages | A apply | A read page | B apply | B read page | C apply | C read page |
|---|---|---|---|---|---|---|---|
| 1000 | 1 | 2.64 | 1.22 | 2.54 | 1.21 | 2.53 | 1.23 |
| 1000 | 5 | 2.71 | 0.24 | 0.88 | 0.33 | 0.70 | 0.28 |
| 1000 | 20 | 2.49 | 0.07 | 0.47 | 0.07 | 0.27 | 0.10 |
| 3000 | 1 | 5.56 | 3.54 | 6.15 | 3.53 | 5.83 | 3.57 |
| 3000 | 5 | 5.64 | 0.72 | 1.62 | 0.71 | 1.51 | 0.69 |
| 3000 | 20 | 5.56 | 0.19 | 0.70 | 0.19 | 0.57 | 0.23 |
| 5000 | 1 | 9.03 | 5.85 | 10.2 | 5.83 | 9.23 | 6.17 |
| 5000 | 5 | 7.80 | 1.20 | 2.39 | 1.24 | 2.28 | 1.18 |
| 5000 | 20 | 9.02 | 0.33 | 0.96 | 0.38 | 0.78 | 0.36 |
| 10000 | 1 | 16.5 | 12.0 | 16.5 | 12.0 | 17.4 | 11.7 |
| 10000 | 5 | 15.1 | 2.46 | 4.05 | 2.48 | 4.27 | 2.51 |
| 10000 | 20 | 15.6 | 0.70 | 1.64 | 0.63 | 1.06 | 0.63 |

### Memory (MB held after gc in a fresh child process: V8 heap / off-heap ArrayBuffers (stroke payload copies) / total; baseline taken before the update files were read, files freed before measuring)

| strokes | pages | A whole board | A one page | B whole board | B one page | C whole board | C one page |
|---|---|---|---|---|---|---|---|
| 1000 | 1 | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** |
| 1000 | 5 | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.3 / 0.1 / **0.4** | 0.7 / 0.5 / **1.2** | 0.3 / 0.1 / **0.4** |
| 1000 | 20 | 0.7 / 0.5 / **1.2** | 0.7 / 0.5 / **1.2** | 0.8 / 0.5 / **1.3** | 0.3 / 0.0 / **0.3** | 0.8 / 0.5 / **1.3** | 0.2 / 0.0 / **0.2** |
| 3000 | 1 | 1.6 / 1.5 / **3.1** | 1.7 / 1.5 / **3.3** | 1.7 / 1.5 / **3.3** | 1.7 / 1.5 / **3.3** | 1.7 / 1.5 / **3.3** | 1.7 / 1.5 / **3.2** |
| 3000 | 5 | 1.7 / 1.5 / **3.2** | 1.8 / 1.5 / **3.3** | 1.7 / 1.5 / **3.2** | 0.5 / 0.3 / **0.8** | 1.7 / 1.5 / **3.2** | 0.5 / 0.3 / **0.8** |
| 3000 | 20 | 1.8 / 1.5 / **3.3** | 1.8 / 1.5 / **3.3** | 1.8 / 1.5 / **3.3** | 0.3 / 0.1 / **0.4** | 1.7 / 1.5 / **3.3** | 0.3 / 0.1 / **0.3** |
| 5000 | 1 | 2.6 / 2.6 / **5.2** | 2.6 / 2.6 / **5.2** | 2.7 / 2.6 / **5.2** | 2.7 / 2.6 / **5.2** | 2.6 / 2.6 / **5.2** | 2.6 / 2.6 / **5.2** |
| 5000 | 5 | 2.5 / 2.6 / **5.1** | 2.5 / 2.6 / **5.1** | 2.4 / 2.6 / **5.0** | 0.7 / 0.5 / **1.2** | 2.4 / 2.6 / **5.0** | 0.7 / 0.5 / **1.2** |
| 5000 | 20 | 2.4 / 2.6 / **5.0** | 2.4 / 2.6 / **5.0** | 2.6 / 2.6 / **5.1** | 0.4 / 0.1 / **0.5** | 2.6 / 2.6 / **5.1** | 0.3 / 0.1 / **0.4** |
| 10000 | 1 | 5.0 / 5.1 / **10.2** | 5.0 / 5.1 / **10.2** | 5.1 / 5.1 / **10.2** | 5.0 / 5.1 / **10.2** | 5.0 / 5.1 / **10.2** | 5.0 / 5.1 / **10.2** |
| 10000 | 5 | 4.8 / 5.1 / **9.9** | 4.8 / 5.1 / **9.9** | 4.6 / 5.1 / **9.8** | 1.2 / 1.0 / **2.2** | 4.6 / 5.1 / **9.8** | 1.2 / 1.0 / **2.2** |
| 10000 | 20 | 4.8 / 5.1 / **9.9** | 4.8 / 5.1 / **9.9** | 4.7 / 5.1 / **9.9** | 0.5 / 0.2 / **0.7** | 4.7 / 5.1 / **9.8** | 0.4 / 0.2 / **0.7** |

### Hocuspocus over local WebSocket: fresh client sync

Time from constructing the provider to the first `synced`, server loading the doc from SQLite each rep (median of 7). Board of A uses 5 page maps; C uses separate documents.

| strokes | layout | pages | what is synced | client sync ms | of which server load ms | strokes received |
|---|---|---|---|---|---|---|
| 1000 | A | 5 | whole board (one doc) | 11.7 | 2.53 | 1000 |
| 1000 | C | 5 | one page of 5 (one doc) | 5.13 | 0.49 | 200 |
| 1000 | C | 20 | one page of 20 (one doc) | 3.58 | 0.22 | 50 |
| 1000 | C | 20 | all 20 pages (20 docs, one socket) | 19.4 | 2.69 | 1000 |
| 3000 | A | 5 | whole board (one doc) | 24.4 | 6.24 | 3000 |
| 3000 | C | 5 | one page of 5 (one doc) | 7.26 | 1.22 | 600 |
| 3000 | C | 20 | one page of 20 (one doc) | 4.35 | 0.41 | 150 |
| 3000 | C | 20 | all 20 pages (20 docs, one socket) | 30.1 | 5.43 | 3000 |
| 5000 | A | 5 | whole board (one doc) | 33.2 | 9.34 | 5000 |
| 5000 | C | 5 | one page of 5 (one doc) | 10.2 | 2.20 | 1000 |
| 5000 | C | 20 | one page of 20 (one doc) | 5.05 | 0.69 | 250 |
| 5000 | C | 20 | all 20 pages (20 docs, one socket) | 54.7 | 8.33 | 5000 |
| 10000 | A | 5 | whole board (one doc) | 73.8 | 19.8 | 10000 |
| 10000 | C | 5 | one page of 5 (one doc) | 14.4 | 3.80 | 2000 |
| 10000 | C | 20 | one page of 20 (one doc) | 7.09 | 1.04 | 500 |
| 10000 | C | 20 | all 20 pages (20 docs, one socket) | 96.2 | 16.0 | 10000 |

### Hocuspocus: per-save cost after adding one stroke (SQLite whole-doc upsert)

onStoreDocument = `encodeStateAsUpdate` of the whole doc + write. "Stroke to stored" includes the configured 20 ms server debounce.

| strokes | layout | pages | doc | bytes written per save | bytes of the stroke update | write amplification | encode ms | sqlite write ms | onStoreDocument ms | stroke to stored ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | A | 5 | whole board (one doc) | 559053 | 526 | 1063x | 0.70 | 0.66 | 1.60 | 22.7 |
| 1000 | C | 5 | one page of 5 | 111334 | 524 | 212x | 0.21 | 0.23 | 0.44 | 20.8 |
| 1000 | C | 20 | one page of 20 | 31496 | 524 | 60x | 0.10 | 0.16 | 0.26 | 21.2 |
| 3000 | A | 5 | whole board (one doc) | 1701921 | 668.5 | 2546x | 1.82 | 2.51 | 4.31 | 24.8 |
| 3000 | C | 5 | one page of 5 | 333595 | 666.5 | 501x | 0.44 | 0.39 | 0.84 | 21.3 |
| 3000 | C | 20 | one page of 20 | 84174 | 666.5 | 126x | 0.16 | 0.20 | 0.37 | 21.4 |
| 5000 | A | 5 | whole board (one doc) | 2810137 | 603.5 | 4656x | 3.49 | 4.86 | 8.53 | 29.2 |
| 5000 | C | 5 | one page of 5 | 556924 | 601.5 | 926x | 0.70 | 0.57 | 1.30 | 22.4 |
| 5000 | C | 20 | one page of 20 | 139856 | 601.5 | 233x | 0.23 | 0.27 | 0.50 | 21.4 |
| 10000 | A | 5 | whole board (one doc) | 5646957 | 737.5 | 7657x | 5.55 | 7.01 | 12.7 | 34.3 |
| 10000 | C | 5 | one page of 5 | 1127433 | 734.5 | 1535x | 1.20 | 1.12 | 2.35 | 22.8 |
| 10000 | C | 20 | one page of 20 | 276205 | 735.5 | 376x | 0.39 | 0.34 | 0.74 | 21.7 |

### Hocuspocus: layout B (subdocuments)

```json
{
 "strokesWrittenToSubdoc": 100,
 "client2SeesSubdocInRootMap": true,
 "client2SubdocStrokes": 0,
 "client2SubdocStrokesAfterLoad": 0,
 "serverStoredRootDocBytes": 33,
 "subdocBytesNeverSentToServer": 57053,
 "client2SubdocStrokesWithItsOwnProviderPerSubdoc": 100
}
```

Notes on the tables:

- Hocuspocus layout B test: a client wrote 100 strokes into a subdocument inside the board document and the server stored a 33 byte root document. A second client sees the subdocument entry (the guid) but 0 strokes, also after `subdoc.load()`. The 57,053 bytes of subdocument content never left the first client. Only when each subdocument gets its own `HocuspocusProvider` with its own document name (the guid) do the 100 strokes arrive, and that is layout C with an extra index document.
- Hocuspocus "of which server load ms" is the extension's SQLite read plus `applyUpdate` into the server-side document. The rest of the client sync time is transfer, decode on the client and the sync protocol round trips.
- Sync of "all 20 pages" in C (20 documents multiplexed on one socket) is slower than one A document of the same strokes (96 ms vs 74 ms at 10k): per-document protocol and server-load overhead adds up. C wins only when pages are opened on demand.
- Stroke to stored includes the 20 ms debounce configured on the server; the real production debounce would be longer.

## Recommendation

Input for the grilling "Decide sync server, board document structure, and API/auth stack". This follows from the numbers above; the numbers are relative to a fast machine.

1. Rule out B (subdocument per page) for Hocuspocus. Hocuspocus does not sync subdocuments, so the only working form is one provider per subdocument, which is layout C plus an index document and more lifecycle to manage. At the pure-Yjs level B performs the same as C (size, load, memory all within noise), so it has no advantage to justify the extra moving parts. Also, a root-doc UndoManager does not see subdocument edits.
2. Layout A (one Y.Doc per board) is sufficient on size, load and memory up to 10k strokes. A 10k board is 5.6 MB, about 15 ms to apply, about 10 MB held in memory (heap plus off-heap payloads); 3k strokes is 1.7 MB. Per-user undo across pages comes for free with one UndoManager over all page maps, and one document means one auth check, one permission/read-only decision (the glossary's shared board and per-student private board each map to one document), one persistence unit, and atomic multi-page operations (for example moving a selection between pages in one transaction).
3. The cost of A is not CPU, it is bytes: opening any page transfers the whole board (5.6 MB at 10k strokes, about 2 s at 20 Mbit/s, not measured), and the stock Database-extension pattern rewrites the whole document on every save (5.6 MB, about 13 ms per save at 10k). Mitigations that keep A: a long `debounce`/`maxDebounce` on onStoreDocument; a custom store that appends the incremental `update` from `onChange` (the payload carries it) and compacts periodically instead of rewriting; capping stroke size. The incremental-log idea was not tested in this spike.
4. Layout C (one Hocuspocus document per page) is the escape hatch if boards routinely pass roughly 5k-10k strokes or weak devices/Wi-Fi make a whole-board first load too slow. It cuts open-a-page sync from 74 ms to 7 ms and per-save writes from 5.6 MB to 276 KB at 10k strokes over 20 pages (about 20x less, in proportion to the page count), and it gives page-level load on demand. Its costs: undo needs an app-level stack of page ids over one UndoManager per page (tested and works, but the cap and the global order are then app code, and an undo cannot span pages that are not loaded), no atomic cross-page operations (moving ink between pages is two transactions in two documents), one authorization and one read-only decision per page document, N websocket documents to open when a student views all pages (96 ms vs 74 ms for 10k strokes), and a board-level index (page list and order) that has to live somewhere, in the database or an index document.
5. Suggested path (default: A unless the grill establishes that 10k-stroke boards are normal): start with A, with each page as its own root map and strokes as `id -> packed bytes` so a later split into C is a mechanical copy per page and the stroke format stays the same. Treat the typical stroke count per board as the open question for the grill: if a lesson board is typically under about 3k strokes (under 2 MB), A has no real downside; if boards of 10k strokes are normal, choose C up front, because migrating live boards later is the expensive part.
6. Independent of layout: write each stroke once at pen-up as one packed value (about 570 bytes per update, 4.5% overhead), keep live preview out of the document (awareness), and keep the UndoManager `trackedOrigins` per user with a stack cap (implemented here by trimming `undoStack`/`redoStack` on `stack-item-added`; the cap check passes). Note that the cap drops the oldest entry silently; the UI should treat undo depth as limited.

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

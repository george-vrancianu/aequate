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
| redo stack also capped; full redo restores the 5 undone strokes | PASS | PASS | PASS |
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
| 1000 | 1 | 2.73 | 1.85 | 1.36 | 2.64 | 2.02 | 1.19 | 3.02 | 2.33 | 1.19 |
| 1000 | 5 | 2.62 | 1.76 | 1.21 | 2.69 | 1.92 | 1.15 | 3.37 | 2.69 | 1.22 |
| 1000 | 20 | 2.61 | 1.81 | 1.20 | 2.98 | 2.35 | 1.22 | 4.55 | 4.18 | 1.27 |
| 3000 | 1 | 6.88 | 5.02 | 3.87 | 6.13 | 4.25 | 3.70 | 7.53 | 6.04 | 4.08 |
| 3000 | 5 | 6.19 | 4.32 | 3.69 | 6.18 | 4.11 | 3.77 | 7.71 | 5.72 | 3.66 |
| 3000 | 20 | 6.32 | 4.50 | 3.67 | 6.89 | 4.68 | 3.65 | 9.33 | 7.55 | 3.95 |
| 5000 | 1 | 9.88 | 6.25 | 6.15 | 10.0 | 6.09 | 6.32 | 11.3 | 7.96 | 5.97 |
| 5000 | 5 | 9.48 | 6.16 | 6.30 | 8.53 | 5.91 | 6.25 | 11.5 | 8.15 | 6.24 |
| 5000 | 20 | 9.69 | 5.84 | 6.65 | 9.26 | 6.11 | 6.23 | 11.1 | 9.39 | 7.00 |
| 10000 | 1 | 16.3 | 9.74 | 12.0 | 16.2 | 9.02 | 11.9 | 18.4 | 9.67 | 12.1 |
| 10000 | 5 | 15.2 | 9.05 | 12.2 | 14.3 | 10.1 | 12.3 | 16.9 | 10.5 | 12.9 |
| 10000 | 20 | 15.3 | 8.17 | 12.0 | 14.3 | 8.24 | 12.4 | 17.9 | 13.5 | 12.4 |

### Open a single page (ms, median; A must load the whole board, B = root doc + that subdoc, C = that doc only)

| strokes | pages | A apply | A read page | B apply | B read page | C apply | C read page |
|---|---|---|---|---|---|---|---|
| 1000 | 1 | 2.46 | 1.16 | 2.77 | 1.18 | 2.52 | 1.24 |
| 1000 | 5 | 2.55 | 0.25 | 0.71 | 0.23 | 0.61 | 0.26 |
| 1000 | 20 | 2.51 | 0.07 | 0.55 | 0.07 | 0.28 | 0.09 |
| 3000 | 1 | 6.07 | 3.64 | 6.29 | 3.65 | 6.06 | 3.79 |
| 3000 | 5 | 5.87 | 0.72 | 1.75 | 0.69 | 1.73 | 0.73 |
| 3000 | 20 | 6.39 | 0.19 | 0.75 | 0.23 | 0.56 | 0.20 |
| 5000 | 1 | 9.16 | 5.88 | 8.91 | 5.79 | 9.19 | 6.02 |
| 5000 | 5 | 9.09 | 1.25 | 2.50 | 1.18 | 2.31 | 1.22 |
| 5000 | 20 | 8.23 | 0.32 | 1.04 | 0.34 | 0.79 | 0.31 |
| 10000 | 1 | 16.8 | 11.5 | 16.3 | 11.5 | 17.4 | 11.7 |
| 10000 | 5 | 15.2 | 2.46 | 4.33 | 2.51 | 4.14 | 2.51 |
| 10000 | 20 | 14.7 | 0.66 | 1.67 | 0.67 | 1.14 | 0.64 |

### Memory (heap used delta after gc, fresh child process; MB)

| strokes | pages | A whole board | A one page | B whole board | B one page | C whole board | C one page |
|---|---|---|---|---|---|---|---|
| 1000 | 1 | 0.7 | 0.7 | 0.7 | 0.7 | 0.7 | 0.7 |
| 1000 | 5 | 0.7 | 0.7 | 0.7 | 0.3 | 0.7 | 0.3 |
| 1000 | 20 | 0.7 | 0.7 | 0.8 | 0.3 | 0.8 | 0.2 |
| 3000 | 1 | 1.7 | 1.7 | 1.6 | 1.7 | 1.6 | 1.6 |
| 3000 | 5 | 1.6 | 1.8 | 1.7 | 0.5 | 1.7 | 0.7 |
| 3000 | 20 | 1.7 | 1.8 | 1.7 | 0.3 | 1.7 | 0.3 |
| 5000 | 1 | 2.6 | 2.6 | 2.7 | 2.7 | 2.6 | 2.6 |
| 5000 | 5 | 2.5 | 2.5 | 2.4 | 0.7 | 2.4 | 0.7 |
| 5000 | 20 | 2.5 | 2.5 | 2.6 | 0.4 | 2.6 | 0.3 |
| 10000 | 1 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| 10000 | 5 | 4.8 | 4.8 | 4.6 | 1.2 | 4.6 | 1.2 |
| 10000 | 20 | 4.8 | 4.8 | 4.7 | 0.5 | 4.7 | 0.4 |

### Hocuspocus over local WebSocket: fresh client sync

Time from constructing the provider to the first `synced`, server loading the doc from SQLite each rep (median of 7). Board of A uses 5 page maps; C uses separate documents.

| strokes | layout | pages | what is synced | client sync ms | of which server load ms | strokes received |
|---|---|---|---|---|---|---|
| 1000 | A | 5 | whole board (one doc) | 12.4 | 2.04 | 1000 |
| 1000 | C | 5 | one page of 5 (one doc) | 4.97 | 0.51 | 200 |
| 1000 | C | 20 | one page of 20 (one doc) | 3.74 | 0.21 | 50 |
| 1000 | C | 20 | all 20 pages (20 docs, one socket) | 20.2 | 2.77 | 1000 |
| 3000 | A | 5 | whole board (one doc) | 19.0 | 5.36 | 3000 |
| 3000 | C | 5 | one page of 5 (one doc) | 6.89 | 1.22 | 600 |
| 3000 | C | 20 | one page of 20 (one doc) | 4.44 | 0.39 | 150 |
| 3000 | C | 20 | all 20 pages (20 docs, one socket) | 36.6 | 5.72 | 3000 |
| 5000 | A | 5 | whole board (one doc) | 32.9 | 9.28 | 5000 |
| 5000 | C | 5 | one page of 5 (one doc) | 9.64 | 2.09 | 1000 |
| 5000 | C | 20 | one page of 20 (one doc) | 4.91 | 0.62 | 250 |
| 5000 | C | 20 | all 20 pages (20 docs, one socket) | 39.7 | 8.78 | 5000 |
| 10000 | A | 5 | whole board (one doc) | 71.3 | 19.0 | 10000 |
| 10000 | C | 5 | one page of 5 (one doc) | 12.9 | 3.25 | 2000 |
| 10000 | C | 20 | one page of 20 (one doc) | 6.27 | 1.05 | 500 |
| 10000 | C | 20 | all 20 pages (20 docs, one socket) | 98.9 | 16.2 | 10000 |

### Hocuspocus: per-save cost after adding one stroke (SQLite whole-doc upsert)

onStoreDocument = `encodeStateAsUpdate` of the whole doc + write. "Stroke to stored" includes the configured 20 ms server debounce.

| strokes | layout | pages | doc | bytes written per save | bytes of the stroke update | write amplification | encode ms | sqlite write ms | onStoreDocument ms | stroke to stored ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | A | 5 | whole board (one doc) | 559478 | 704.5 | 794x | 0.72 | 0.71 | 1.44 | 22.6 |
| 1000 | C | 5 | one page of 5 | 111759 | 702.5 | 159x | 0.20 | 0.23 | 0.44 | 21.5 |
| 1000 | C | 20 | one page of 20 | 31921 | 702.5 | 45x | 0.09 | 0.17 | 0.26 | 20.8 |
| 3000 | A | 5 | whole board (one doc) | 1701318.5 | 622 | 2735x | 1.53 | 1.73 | 3.24 | 24.1 |
| 3000 | C | 5 | one page of 5 | 332993.5 | 621 | 536x | 0.49 | 0.41 | 0.92 | 21.9 |
| 3000 | C | 20 | one page of 20 | 83572.5 | 621 | 135x | 0.15 | 0.21 | 0.37 | 21.3 |
| 5000 | A | 5 | whole board (one doc) | 2811029.5 | 665.5 | 4224x | 4.07 | 4.12 | 8.17 | 28.5 |
| 5000 | C | 5 | one page of 5 | 557816.5 | 663.5 | 841x | 0.69 | 0.59 | 1.29 | 22.2 |
| 5000 | C | 20 | one page of 20 | 140748.5 | 663.5 | 212x | 0.17 | 0.27 | 0.45 | 21.5 |
| 10000 | A | 5 | whole board (one doc) | 5645920 | 694.5 | 8129x | 4.34 | 9.42 | 13.8 | 34.5 |
| 10000 | C | 5 | one page of 5 | 1126397 | 692.5 | 1627x | 1.08 | 1.11 | 2.15 | 22.8 |
| 10000 | C | 20 | one page of 20 | 275168 | 692.5 | 397x | 0.39 | 0.39 | 0.79 | 21.7 |

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

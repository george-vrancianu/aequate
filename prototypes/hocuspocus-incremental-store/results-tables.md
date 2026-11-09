### Single added stroke: bytes written per save (steady state)

| strokes | store | update bytes | payload bytes per save | on-disk (WAL) bytes per save | save ms (encode+write) |
|---|---|---|---|---|---|
| 1000 | full rewrite, one doc per board | 443 | 558341 | 572680 | 2.70 |
| 1000 | full rewrite, one doc per page (20 pages) | 441 | 30789 | 41200 | 0.30 |
| 1000 | update log (row per onChange) | 443 | 443 | 12360 | 0.10 |
| 1000 | batched log (row per onStoreDocument) | 443 | 443 | 12360 | 0.10 |
| 3000 | full rewrite, one doc per board | 752 | 1700257 | 1722160 | 7.00 |
| 3000 | full rewrite, one doc per page (20 pages) | 750 | 82515 | 94760 | 0.50 |
| 3000 | update log (row per onChange) | 752 | 752 | 12360 | 0.10 |
| 3000 | batched log (row per onStoreDocument) | 752 | 752 | 12360 | 0.10 |
| 5000 | full rewrite, one doc per board | 831 | 2810409 | 2838680 | 13.80 |
| 5000 | full rewrite, one doc per page (20 pages) | 829 | 140133 | 152440 | 1.00 |
| 5000 | update log (row per onChange) | 831 | 831 | 12360 | 0.20 |
| 5000 | batched log (row per onStoreDocument) | 831 | 831 | 12360 | 0.10 |
| 10000 | full rewrite, one doc per board | 642 | 5644528 | 5697960 | 23.70 |
| 10000 | full rewrite, one doc per page (20 pages) | 640 | 273781 | 284280 | 1.20 |
| 10000 | update log (row per onChange) | 642 | 642 | 12360 | 0.10 |
| 10000 | batched log (row per onStoreDocument) | 642 | 642 | 12360 | 0.10 |

### Load time (Hocuspocus cold open, median of 3; server onLoadDocument ms in brackets)

| strokes | log rows | log MB | live state MB | replay row by row (direct) | mergeUpdates then apply (direct) | open via Hocuspocus, log uncompacted | after compaction (doc) | after compaction (merge) | snapshot + 100-row tail |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | 1100 | 0.54 MB | 0.48 MB | 14.2 ms | 24.3 ms | 61.7 ms (21.5) | 13.8 ms (3.2) | 11.7 ms (2.7) | 14.6 ms (3.0) |
| 3000 | 3300 | 1.65 MB | 1.47 MB | 26.7 ms | 159.6 ms | 149.3 ms (99.5) | 28.9 ms (14.3) | 28.5 ms (13.0) | 29.8 ms (7.1) |
| 5000 | 5500 | 2.73 MB | 2.42 MB | 49.3 ms | 296.3 ms | 215.8 ms (160.1) | 46.8 ms (16.7) | 43.3 ms (14.1) | 46.2 ms (10.5) |
| 10000 | 11000 | 5.49 MB | 4.87 MB | 96.9 ms | 1493.9 ms | 394.2 ms (342.7) | 81.3 ms (36.2) | 93.4 ms (40.9) | 76.2 ms (22.4) |

### Compaction of a whole N-stroke log (+10% erases), on a live server doc

| strokes | mode | rows merged | compaction ms (blocks event loop) | snapshot size | max gap between ping arrivals during compaction | calm gap p50 (ping every 5 ms) |
|---|---|---|---|---|---|---|
| 1000 | encodeStateAsUpdate(live doc) | 1100 | 5.2 | 0.48 MB | 7.9 ms | 5.0 ms |
| 1000 | Y.mergeUpdates(snapshot + rows) | 1100 | 23.5 | 0.53 MB | 27.9 ms | 5.0 ms |
| 3000 | encodeStateAsUpdate(live doc) | 3300 | 12.3 | 1.47 MB | 14.0 ms | 5.0 ms |
| 3000 | Y.mergeUpdates(snapshot + rows) | 3300 | 144.8 | 1.62 MB | 148.4 ms | 4.9 ms |
| 5000 | encodeStateAsUpdate(live doc) | 5500 | 21.7 | 2.42 MB | 24.9 ms | 5.1 ms |
| 5000 | Y.mergeUpdates(snapshot + rows) | 5500 | 374.3 | 2.68 MB | 376.8 ms | 5.0 ms |
| 10000 | encodeStateAsUpdate(live doc) | 11000 | 53.0 | 4.87 MB | 58.3 ms | 5.0 ms |
| 10000 | Y.mergeUpdates(snapshot + rows) | 11000 | 1437.3 | 5.38 MB | 1444.7 ms | 4.9 ms |

### Session: 2000 strokes (+~10% erase/undo), two sessions with disconnect/reconnect. Totals over both sessions

| strokes on board | store | saves/appends | payload bytes (incl. compaction) | payload bytes per stroke | on-disk WAL bytes (incl. compaction) | WAL bytes per stroke | median payload / WAL bytes per write | write ms p50 / p99 / max | compactions (ms) | log left after s1 / s2 (rows, KB) | ping RTT p99 / max (ms) | ping gap p99 / max (ms) | max ping gap in compaction window (ms) | reload == live |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | full rewrite, doc per board | 18 | 19.19 MB | 9.8 KB | 19.50 MB | 10.0 KB | 1097 KB / 1114 KB | 6.55 / 13.45 / 13.45 | - | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 7.5 | 7.4 / 15.9 | - / - | true / true |
| 1000 | full rewrite, doc per page | 20 | 3.88 MB | 2.0 KB | 4.14 MB | 2.1 KB | 211 KB / 225 KB | 1.27 / 2.88 / 2.88 | - | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 2.5 | 6.2 / 7.1 | - / - | true / true |
| 1000 | log + compact @500 updates | 2208 | 5.44 MB | 2.8 KB | 35.25 MB | 18 KB | 0.5 KB / 12 KB | 0.09 / 0.19 / 5.40 | count 3.6, count 4.3, count 6.3, count 6.6 | 121, 57 KB / 208, 108 KB | 1.3 / 8.9 | 6.3 / 13.7 | 9.1 / 13.7 | true / true |
| 1000 | log + compact @512 KiB | 2208 | 3.50 MB | 1.8 KB | 34.48 MB | 18 KB | 0.5 KB / 12 KB | 0.09 / 0.20 / 7.95 | bytes 4.8, bytes 6.6 | 117, 55 KB / 213, 111 KB | 1.2 / 7.6 | 6.1 / 13.4 | 8.2 / 11.7 | true / true |
| 1000 | log + compact on last disconnect | 2208 | 3.64 MB | 1.9 KB | 33.93 MB | 17 KB | 0.5 KB / 12 KB | 0.09 / 0.21 / 5.46 | disconnect 5.6, disconnect 7.4 | 0, 0.0 KB / 0, 0.0 KB | 1.3 / 6.1 | 6.1 / 10.9 | - / - | true / true |
| 1000 | batched log + compact on disconnect | 18 | 3.62 MB | 1.9 KB | 4.07 MB | 2.1 KB | 68 KB / 89 KB | 1.08 / 1.57 / 1.57 | disconnect 4.9, disconnect 6.4 | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 1.7 | 5.7 / 6.3 | - / - | true / true |
| 1000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.00 MB | 0.0 KB | 0.0 KB / 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 0.8 / 1.4 | 5.9 / 6.4 | - / - | n/a / n/a |
| 3000 | full rewrite, doc per board | 18 | 38.48 MB | 20 KB | 38.92 MB | 20 KB | 2195 KB / 2221 KB | 10.56 / 11.64 / 11.64 | - | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 11.1 | 6.2 / 16.8 | - / - | true / true |
| 3000 | full rewrite, doc per page | 20 | 4.86 MB | 2.5 KB | 5.10 MB | 2.6 KB | 260 KB / 273 KB | 1.46 / 9.90 / 9.90 | - | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 2.5 | 6.2 / 7.2 | - / - | true / true |
| 3000 | log + compact @500 updates | 2208 | 9.69 MB | 5.0 KB | 39.44 MB | 20 KB | 0.5 KB / 12 KB | 0.08 / 0.17 / 5.01 | count 7.9, count 9.2, count 10.1, count 10.7 | 121, 57 KB / 208, 105 KB | 1.2 / 1.4 | 6.1 / 13.8 | 12.7 / 13.8 | true / true |
| 3000 | log + compact @512 KiB | 2208 | 5.64 MB | 2.9 KB | 37.07 MB | 19 KB | 0.5 KB / 12 KB | 0.09 / 0.20 / 5.08 | bytes 12.1, bytes 12.0 | 70, 33 KB / 164, 80 KB | 1.1 / 13.6 | 6.1 / 18.6 | 18.6 / 14.4 | true / true |
| 3000 | log + compact on last disconnect | 2208 | 5.74 MB | 2.9 KB | 36.60 MB | 19 KB | 0.5 KB / 12 KB | 0.08 / 0.17 / 5.35 | disconnect 12.7, disconnect 13.1 | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 6.1 | 6.1 / 11.0 | - / - | true / true |
| 3000 | batched log + compact on disconnect | 18 | 5.72 MB | 2.9 KB | 6.19 MB | 3.2 KB | 66 KB / 89 KB | 0.97 / 1.45 / 1.45 | disconnect 16.5, disconnect 11.9 | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 2.5 | 5.8 / 6.7 | - / - | true / true |
| 3000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.00 MB | 0.0 KB | 0.0 KB / 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 1.9 | 5.8 / 6.5 | - / - | n/a / n/a |
| 5000 | full rewrite, doc per board | 18 | 57.78 MB | 30 KB | 58.35 MB | 30 KB | 3289 KB / 3321 KB | 15.22 / 16.11 / 16.11 | - | 0, 0.0 KB / 0, 0.0 KB | 1.7 / 17.4 | 7.8 / 21.8 | - / - | true / true |
| 5000 | full rewrite, doc per page | 20 | 5.98 MB | 3.1 KB | 6.26 MB | 3.2 KB | 317 KB / 330 KB | 1.69 / 2.20 / 2.20 | - | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 2.6 | 6.1 / 10.6 | - / - | true / true |
| 5000 | log + compact @500 updates | 2208 | 14.01 MB | 7.2 KB | 44.97 MB | 23 KB | 0.5 KB / 12 KB | 0.11 / 0.27 / 8.32 | count 16.7, count 18.0, count 17.7, count 17.3 | 121, 65 KB / 208, 112 KB | 1.6 / 18.8 | 6.6 / 23.4 | 23.4 / 23.3 | true / true |
| 5000 | log + compact @512 KiB | 2208 | 7.79 MB | 4.0 KB | 39.36 MB | 20 KB | 0.5 KB / 12 KB | 0.09 / 0.21 / 5.94 | bytes 16.1, bytes 17.8 | 106, 57 KB / 206, 111 KB | 1.1 / 18.9 | 6.0 / 22.3 | 20.9 / 22.3 | true / true |
| 5000 | log + compact on last disconnect | 2208 | 7.94 MB | 4.1 KB | 38.85 MB | 20 KB | 0.5 KB / 12 KB | 0.09 / 0.19 / 5.10 | disconnect 19.1, disconnect 18.8 | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 5.7 | 6.2 / 10.5 | - / - | true / true |
| 5000 | batched log + compact on disconnect | 18 | 7.92 MB | 4.1 KB | 8.39 MB | 4.3 KB | 68 KB / 89 KB | 0.94 / 1.51 / 1.51 | disconnect 16.5, disconnect 17.0 | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 2.6 | 5.8 / 7.0 | - / - | true / true |
| 5000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.00 MB | 0.0 KB | 0.0 KB / 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 7.2 | 5.8 / 11.8 | - / - | n/a / n/a |
| 10000 | full rewrite, doc per board | 18 | 106.39 MB | 54 KB | 107.36 MB | 55 KB | 6055 KB / 6110 KB | 28.71 / 32.28 / 32.28 | - | 0, 0.0 KB / 0, 0.0 KB | 1.1 / 26.7 | 10.0 / 37.4 | - / - | true / true |
| 10000 | full rewrite, doc per page | 20 | 8.64 MB | 4.4 KB | 8.92 MB | 4.6 KB | 452 KB / 470 KB | 2.30 / 3.71 / 3.71 | - | 0, 0.0 KB / 0, 0.0 KB | 1.9 / 4.3 | 6.9 / 9.7 | - / - | true / true |
| 10000 | log + compact @500 updates | 2208 | 24.79 MB | 13 KB | 54.83 MB | 28 KB | 0.5 KB / 12 KB | 0.10 / 0.25 / 6.36 | count 29.9, count 25.7, count 34.0, count 32.2 | 121, 59 KB / 208, 109 KB | 1.6 / 26.8 | 6.4 / 38.0 | 34.5 / 38 | true / true |
| 10000 | log + compact @512 KiB | 2208 | 13.18 MB | 6.7 KB | 45.11 MB | 23 KB | 0.5 KB / 12 KB | 0.10 / 0.23 / 8.77 | bytes 28.9, bytes 28.7 | 93, 46 KB / 188, 99 KB | 1.3 / 30.3 | 6.2 / 34.5 | 34.3 / 34.5 | true / true |
| 10000 | log + compact on last disconnect | 2208 | 13.32 MB | 6.8 KB | 44.53 MB | 23 KB | 0.5 KB / 12 KB | 0.10 / 0.20 / 0.40 | disconnect 35.7, disconnect 32.1 | 0, 0.0 KB / 0, 0.0 KB | 1.5 / 2.8 | 6.3 / 7.9 | - / - | true / true |
| 10000 | batched log + compact on disconnect | 18 | 13.30 MB | 6.8 KB | 13.82 MB | 7.1 KB | 66 KB / 89 KB | 1.16 / 2.10 / 2.10 | disconnect 32.0, disconnect 28.5 | 0, 0.0 KB / 0, 0.0 KB | 1.1 / 2.8 | 6.1 / 9.7 | - / - | true / true |
| 10000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.00 MB | 0.0 KB | 0.0 KB / 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 7.8 | 5.7 / 12.5 | - / - | n/a / n/a |

### Log growth over the session (update-log with no compaction until disconnect), rows / KB after every 200 strokes

- 1000 strokes, log + compact on last disconnect: s1 220/109, 438/225, 672/344, 897/458, 1120/568 ; s2 214/110, 429/226, 650/342, 864/452, 1086/567
- 1000 strokes, log + compact @500 updates: s1 220/109, 438/225, 172/88, 397/202, 120/56 ; s2 335/166, 50/26, 271/142, 485/253, 207/108
- 1000 strokes, log + compact @512 KiB: s1 220/109, 438/224, 672/343, 897/457, 116/54 ; s2 331/165, 546/281, 767/397, 981/507, 212/110
- 1000 strokes, batched log + compact on disconnect: s1 1/67, 3/205, 4/274, 6/414, 8/549 ; s2 1/69, 3/203, 4/270, 6/405, 8/540
- 3000 strokes, log + compact on last disconnect: s1 220/107, 438/218, 672/329, 897/437, 1120/543 ; s2 214/113, 429/225, 650/340, 864/447, 1086/558
- 3000 strokes, log + compact @500 updates: s1 220/108, 438/218, 172/82, 397/190, 120/56 ; s2 335/170, 50/28, 271/144, 485/250, 207/104
- 3000 strokes, log + compact @512 KiB: s1 220/108, 438/218, 672/329, 897/438, 69/32 ; s2 284/147, 499/258, 720/374, 934/480, 163/80
- 3000 strokes, batched log + compact on disconnect: s1 1/66, 3/198, 4/264, 6/395, 8/524 ; s2 1/68, 3/203, 4/275, 6/411, 8/540
- 5000 strokes, log + compact on last disconnect: s1 220/112, 438/228, 672/340, 897/448, 1120/568 ; s2 214/115, 429/225, 650/333, 864/447, 1086/566
- 5000 strokes, log + compact @500 updates: s1 220/112, 438/228, 172/83, 397/190, 120/64 ; s2 335/179, 50/26, 271/135, 485/248, 207/111
- 5000 strokes, log + compact @512 KiB: s1 220/112, 438/228, 672/340, 897/448, 105/56 ; s2 320/171, 535/281, 756/390, 970/503, 205/110
- 5000 strokes, batched log + compact on disconnect: s1 1/71, 3/204, 4/274, 6/405, 8/545 ; s2 1/64, 3/201, 4/266, 6/398, 8/539
- 10000 strokes, log + compact on last disconnect: s1 220/109, 438/224, 672/336, 897/446, 1120/558 ; s2 214/112, 429/228, 650/339, 864/449, 1086/564
- 10000 strokes, log + compact @500 updates: s1 220/109, 438/224, 172/82, 397/192, 120/59 ; s2 335/171, 50/26, 271/137, 485/247, 207/109
- 10000 strokes, log + compact @512 KiB: s1 220/109, 438/224, 672/336, 897/446, 92/46 ; s2 307/158, 522/274, 743/385, 957/494, 187/98
- 10000 strokes, batched log + compact on disconnect: s1 1/64, 3/200, 4/267, 6/396, 8/532 ; s2 1/66, 3/202, 4/269, 6/402, 8/537

### Correctness: load experiment

| strokes | log replay == live | mergeUpdates == live | after compaction (doc) == live | after compaction (merge) == live | snapshot+tail == live |
|---|---|---|---|---|---|
| 1000 | PASS | PASS | PASS | PASS | PASS |
| 3000 | PASS | PASS | PASS | PASS | PASS |
| 5000 | PASS | PASS | PASS | PASS | PASS |
| 10000 | PASS | PASS | PASS | PASS | PASS |

### Crash tests (SIGKILL of the server process, then reload from sqlite only; board of 1000 + 600 strokes with ~10% erases)

| scenario | recovered / expected strokes | log rows left | snapshot bytes | state vector equal | content equal | result |
|---|---|---|---|---|---|---|
| log-per-update | 1530 / 1530 | 670 | 555919 | true | true | PASS |
| log-compacted-midway | 1530 / 1530 | 170 | 789820 | true | true | PASS |
| log-batched | 1409 / 1530 | 2 | 555919 | false | false | FAIL |
| full-rewrite | 1412 / 1530 | 0 | - | false | false | FAIL |
| log-kill-inside-compaction | 1530 / 1530 | 670 | 555919 | true | true | PASS |

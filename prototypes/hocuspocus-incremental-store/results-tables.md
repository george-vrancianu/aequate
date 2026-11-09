### Single added stroke: bytes written per save (steady state)

| strokes | store | update bytes | bytes written per save | save ms (encode+write) |
|---|---|---|---|---|
| 1000 | full rewrite, one doc per board | 443 | 558341 | 2.70 |
| 1000 | full rewrite, one doc per page (20 pages) | 441 | 30789 | 0.30 |
| 1000 | update log (row per onChange) | 443 | 443 | 0.10 |
| 1000 | batched log (row per onStoreDocument) | 443 | 443 | 0.10 |
| 3000 | full rewrite, one doc per board | 752 | 1700257 | 11.10 |
| 3000 | full rewrite, one doc per page (20 pages) | 750 | 82515 | 0.50 |
| 3000 | update log (row per onChange) | 752 | 752 | 0.10 |
| 3000 | batched log (row per onStoreDocument) | 752 | 752 | 0.10 |
| 5000 | full rewrite, one doc per board | 831 | 2810409 | 20.90 |
| 5000 | full rewrite, one doc per page (20 pages) | 829 | 140133 | 0.90 |
| 5000 | update log (row per onChange) | 831 | 831 | 0.10 |
| 5000 | batched log (row per onStoreDocument) | 831 | 831 | 0.10 |
| 10000 | full rewrite, one doc per board | 642 | 5644528 | 50.20 |
| 10000 | full rewrite, one doc per page (20 pages) | 640 | 273781 | 1.20 |
| 10000 | update log (row per onChange) | 642 | 642 | 0.10 |
| 10000 | batched log (row per onStoreDocument) | 642 | 642 | 0.10 |

### Load time (Hocuspocus cold open, median of 3; server onLoadDocument ms in brackets)

| strokes | log rows | log MB | live state MB | replay row by row (direct) | mergeUpdates then apply (direct) | open via Hocuspocus, log uncompacted | after compaction (doc) | after compaction (merge) | snapshot + 100-row tail |
|---|---|---|---|---|---|---|---|---|---|
| 1000 | 1100 | 0.54 MB | 0.48 MB | 13.9 ms | 47 ms | 93.6 ms (29.6) | 12.2 ms (2.4) | 9.5 ms (1.9) | 14.6 ms (3.3) |
| 3000 | 3300 | 1.65 MB | 1.47 MB | 29.6 ms | 139.6 ms | 117.8 ms (80.1) | 18.6 ms (5.7) | 20.7 ms (5.7) | 20.9 ms (7.3) |
| 5000 | 5500 | 2.73 MB | 2.42 MB | 39.9 ms | 395.6 ms | 213.1 ms (156.4) | 38.8 ms (12.0) | 35.3 ms (11.1) | 30.6 ms (10.2) |
| 10000 | 11000 | 5.49 MB | 4.87 MB | 105.1 ms | 1517.5 ms | 442.1 ms (381.0) | 92.7 ms (23.6) | 76.7 ms (26.3) | 84.1 ms (25.3) |

### Compaction of a whole N-stroke log (+10% erases), on a live server doc

| strokes | mode | rows merged | compaction ms (blocks event loop) | snapshot size | max gap between ping arrivals during compaction | calm gap p50 (ping every 5 ms) |
|---|---|---|---|---|---|---|
| 1000 | encodeStateAsUpdate(live doc) | 1100 | 35.8 | 0.48 MB | 41.4 ms | 5.4 ms |
| 1000 | Y.mergeUpdates(snapshot + rows) | 1100 | 20.2 | 0.53 MB | 25.5 ms | 5.1 ms |
| 3000 | encodeStateAsUpdate(live doc) | 3300 | 46.1 | 1.47 MB | 50.8 ms | 4.9 ms |
| 3000 | Y.mergeUpdates(snapshot + rows) | 3300 | 163.1 | 1.62 MB | 168.3 ms | 4.8 ms |
| 5000 | encodeStateAsUpdate(live doc) | 5500 | 52.5 | 2.42 MB | 56.1 ms | 5.0 ms |
| 5000 | Y.mergeUpdates(snapshot + rows) | 5500 | 394.1 | 2.68 MB | 398.3 ms | 4.8 ms |
| 10000 | encodeStateAsUpdate(live doc) | 11000 | 86.2 | 4.87 MB | 90.0 ms | 5.2 ms |
| 10000 | Y.mergeUpdates(snapshot + rows) | 11000 | 1490.7 | 5.38 MB | 1495.5 ms | 4.9 ms |

### Session: 2000 strokes (+~10% erase/undo), two sessions with disconnect/reconnect. Totals over both sessions

| strokes on board | store | saves/appends | bytes written (incl. compaction) | bytes per stroke | median bytes per write | write ms p50 / p99 / max | compactions (ms) | log left after s1 / s2 (rows, KB) | ping RTT p99 / max (ms) | ping gap p99 / max (ms) | max ping gap in compaction window (ms) | reload == live |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | full rewrite, doc per board | 18 | 19.16 MB | 9.8 KB | 1095 KB | 17.87 / 33.46 / 33.46 | - | 0, 0.0 KB / 0, 0.0 KB | 1.4 / 34.5 | 7.1 / 38.6 | - / - | true / true |
| 1000 | full rewrite, doc per page | 20 | 3.89 MB | 2.0 KB | 212 KB | 1.03 / 15.81 / 15.81 | - | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 4.8 | 5.8 / 19.0 | - / - | true / true |
| 1000 | log + compact @500 updates | 2208 | 5.44 MB | 2.8 KB | 0.5 KB | 0.08 / 0.23 / 21.37 | count 2.9, count 27.7, count 30.1, count 31.5 | 121, 57 KB / 208, 108 KB | 1.4 / 34.1 | 6.3 / 41.8 | 38.8 / 41.8 | true / true |
| 1000 | log + compact @512 KiB | 2208 | 3.50 MB | 1.8 KB | 0.5 KB | 0.09 / 0.33 / 26.08 | bytes 6.3, bytes 6.8 | 117, 55 KB / 213, 111 KB | 2.0 / 29.3 | 6.8 / 35.2 | 9.6 / 8.1 | true / true |
| 1000 | log + compact on last disconnect | 2208 | 3.64 MB | 1.9 KB | 0.5 KB | 0.08 / 0.21 / 25.04 | disconnect 4.6, disconnect 32.5 | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 26.6 | 5.9 / 50.3 | - / - | true / true |
| 1000 | batched log + compact on disconnect | 18 | 3.62 MB | 1.9 KB | 69 KB | 0.23 / 13.32 / 13.32 | disconnect 4.1, disconnect 34.3 | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 1.9 | 6.0 / 15.6 | - / - | true / true |
| 1000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 0.8 / 5.3 | 5.7 / 9.9 | - / - | n/a / n/a |
| 3000 | full rewrite, doc per board | 18 | 38.47 MB | 20 KB | 2195 KB | 23.36 / 38.84 / 38.84 | - | 0, 0.0 KB / 0, 0.0 KB | 1.3 / 39.3 | 7.5 / 43.7 | - / - | true / true |
| 3000 | full rewrite, doc per page | 20 | 4.86 MB | 2.5 KB | 260 KB | 1.30 / 27.03 / 27.03 | - | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 5.5 | 5.8 / 32.4 | - / - | true / true |
| 3000 | log + compact @500 updates | 2208 | 9.68 MB | 5.0 KB | 0.5 KB | 0.08 / 0.18 / 23.80 | count 33.1, count 31.4, count 34.9, count 34.6 | 121, 57 KB / 208, 105 KB | 1.6 / 32.4 | 5.9 / 44.7 | 42.7 / 44.7 | true / true |
| 3000 | log + compact @512 KiB | 2208 | 5.64 MB | 2.9 KB | 0.5 KB | 0.08 / 0.17 / 21.97 | bytes 34.0, bytes 38.2 | 70, 33 KB / 164, 80 KB | 1.0 / 26.8 | 6.0 / 44.6 | 44.2 / 44.6 | true / true |
| 3000 | log + compact on last disconnect | 2208 | 5.74 MB | 2.9 KB | 0.5 KB | 0.09 / 0.19 / 22.45 | disconnect 35.9, disconnect 42.8 | 0, 0.0 KB / 0, 0.0 KB | 1.2 / 22.6 | 6.1 / 31.5 | - / - | true / true |
| 3000 | batched log + compact on disconnect | 18 | 5.72 MB | 2.9 KB | 64 KB | 0.27 / 13.90 / 13.90 | disconnect 9.0, disconnect 46.1 | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 3.0 | 6.0 / 19.5 | - / - | true / true |
| 3000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 0.9 / 1.9 | 5.9 / 6.4 | - / - | n/a / n/a |
| 5000 | full rewrite, doc per board | 18 | 57.78 MB | 30 KB | 3289 KB | 41.16 / 50.68 / 50.68 | - | 0, 0.0 KB / 0, 0.0 KB | 1.5 / 45.6 | 8.7 / 54.2 | - / - | true / true |
| 5000 | full rewrite, doc per page | 20 | 5.96 MB | 3.1 KB | 315 KB | 1.63 / 30.61 / 30.61 | - | 0, 0.0 KB / 0, 0.0 KB | 1.5 / 2.7 | 6.3 / 33.5 | - / - | true / true |
| 5000 | log + compact @500 updates | 2208 | 14.01 MB | 7.2 KB | 0.5 KB | 0.08 / 0.19 / 63.47 | count 14.2, count 46.1, count 42.0, count 44.8 | 121, 65 KB / 208, 112 KB | 1.5 / 46.0 | 6.2 / 91.2 | 56.9 / 52.2 | true / true |
| 5000 | log + compact @512 KiB | 2208 | 7.79 MB | 4.0 KB | 0.5 KB | 0.08 / 0.19 / 21.48 | bytes 42.1, bytes 44.1 | 106, 57 KB / 206, 111 KB | 1.3 / 48.3 | 6.2 / 52.6 | 52.6 / 49.6 | true / true |
| 5000 | log + compact on last disconnect | 2208 | 7.94 MB | 4.1 KB | 0.5 KB | 0.08 / 0.18 / 26.11 | disconnect 33.2, disconnect 49.8 | 0, 0.0 KB / 0, 0.0 KB | 1.8 / 27.2 | 6.1 / 32.0 | - / - | true / true |
| 5000 | batched log + compact on disconnect | 18 | 7.92 MB | 4.1 KB | 65 KB | 0.28 / 14.68 / 14.68 | disconnect 37.6, disconnect 45.3 | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 17.3 | 6.0 / 22.0 | - / - | true / true |
| 5000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 1.0 / 9.3 | 5.9 / 13.6 | - / - | n/a / n/a |
| 10000 | full rewrite, doc per board | 18 | 106.37 MB | 54 KB | 6055 KB | 63.19 / 81.93 / 81.93 | - | 0, 0.0 KB / 0, 0.0 KB | 1.7 / 74.0 | 11.3 / 87.4 | - / - | true / true |
| 10000 | full rewrite, doc per page | 20 | 8.66 MB | 4.4 KB | 454 KB | 1.87 / 26.71 / 26.71 | - | 0, 0.0 KB / 0, 0.0 KB | 2.3 / 3.6 | 6.8 / 28.2 | - / - | true / true |
| 10000 | log + compact @500 updates | 2208 | 24.79 MB | 13 KB | 0.5 KB | 0.09 / 0.22 / 22.41 | count 58.1, count 46.9, count 56.0, count 73.5 | 121, 59 KB / 208, 109 KB | 1.5 / 23.1 | 6.3 / 84.3 | 66.9 / 84.3 | true / true |
| 10000 | log + compact @512 KiB | 2208 | 13.18 MB | 6.7 KB | 0.5 KB | 0.11 / 0.43 / 22.19 | bytes 65.7, bytes 53.7 | 93, 46 KB / 188, 99 KB | 2.5 / 22.6 | 6.6 / 76.0 | 76 / 64.2 | true / true |
| 10000 | log + compact on last disconnect | 2208 | 13.32 MB | 6.8 KB | 0.5 KB | 0.08 / 0.20 / 22.33 | disconnect 71.2, disconnect 75.7 | 0, 0.0 KB / 0, 0.0 KB | 1.4 / 27.7 | 6.2 / 32.1 | - / - | true / true |
| 10000 | batched log + compact on disconnect | 18 | 13.30 MB | 6.8 KB | 66 KB | 0.28 / 14.46 / 14.46 | disconnect 64.3, disconnect 61.7 | 0, 0.0 KB / 0, 0.0 KB | 1.6 / 17.0 | 6.8 / 21.6 | - / - | true / true |
| 10000 | no storage (ping baseline) | 0 | 0.00 MB | 0.0 KB | 0.0 KB | - | - | 0, 0.0 KB / 0, 0.0 KB | 1.7 / 5.9 | 6.5 / 10.1 | - / - | n/a / n/a |

### Log growth over the session (update-log with no compaction until disconnect), rows / KB after every 200 strokes

- 1000 strokes, log + compact on last disconnect: s1 220/109, 438/225, 672/344, 897/458, 1120/568 ; s2 214/110, 429/226, 650/342, 864/452, 1086/567
- 1000 strokes, log + compact @500 updates: s1 220/109, 438/224, 172/88, 397/201, 120/56 ; s2 335/166, 50/26, 271/142, 485/253, 207/108
- 1000 strokes, log + compact @512 KiB: s1 220/109, 438/224, 672/343, 897/457, 116/54 ; s2 331/165, 546/281, 767/397, 981/507, 212/110
- 1000 strokes, batched log + compact on disconnect: s1 1/68, 3/206, 4/276, 6/415, 8/549 ; s2 1/70, 3/204, 4/273, 6/410, 8/547
- 3000 strokes, log + compact on last disconnect: s1 220/108, 438/218, 672/329, 897/438, 1120/544 ; s2 214/113, 429/225, 650/340, 864/447, 1086/558
- 3000 strokes, log + compact @500 updates: s1 220/108, 438/218, 172/82, 397/190, 120/56 ; s2 335/170, 50/28, 271/143, 485/250, 207/104
- 3000 strokes, log + compact @512 KiB: s1 220/108, 438/218, 672/329, 897/438, 69/32 ; s2 284/147, 499/258, 720/374, 934/480, 163/80
- 3000 strokes, batched log + compact on disconnect: s1 1/66, 3/195, 4/258, 6/386, 8/513 ; s2 1/68, 3/200, 4/270, 6/402, 8/528
- 5000 strokes, log + compact on last disconnect: s1 220/112, 438/228, 672/340, 897/448, 1120/568 ; s2 214/115, 429/225, 650/333, 864/447, 1086/566
- 5000 strokes, log + compact @500 updates: s1 220/112, 438/228, 172/83, 397/190, 120/64 ; s2 335/179, 50/26, 271/135, 485/248, 207/111
- 5000 strokes, log + compact @512 KiB: s1 220/112, 438/228, 672/340, 897/448, 105/56 ; s2 320/171, 535/281, 756/390, 970/503, 205/110
- 5000 strokes, batched log + compact on disconnect: s1 1/70, 3/204, 4/272, 6/404, 8/541 ; s2 1/64, 3/201, 4/265, 6/392, 8/529
- 10000 strokes, log + compact on last disconnect: s1 220/109, 438/224, 672/336, 897/446, 1120/558 ; s2 214/112, 429/228, 650/339, 864/449, 1086/564
- 10000 strokes, log + compact @500 updates: s1 220/109, 438/224, 172/82, 397/192, 120/59 ; s2 335/171, 50/26, 271/137, 485/247, 207/109
- 10000 strokes, log + compact @512 KiB: s1 220/109, 438/224, 672/336, 897/446, 92/46 ; s2 307/158, 522/274, 743/385, 957/494, 187/98
- 10000 strokes, batched log + compact on disconnect: s1 1/62, 3/196, 5/327, 6/392, 8/524 ; s2 1/64, 3/203, 4/269, 6/400, 8/534

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
| log-compacted-midway | 1530 / 1530 | 170 | 789822 | true | true | PASS |
| log-batched | 1411 / 1530 | 2 | 555919 | false | false | FAIL |
| full-rewrite | 1413 / 1530 | 0 | - | false | false | FAIL |
| log-kill-inside-compaction | 1530 / 1530 | 670 | 555919 | true | true | PASS |

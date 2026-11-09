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


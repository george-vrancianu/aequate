# PROTOTYPE (throwaway): incremental Hocuspocus store, update log plus compaction

Ticket #38. Not production code. Do not import from it. Results: see RESULTS.md.

    npm install
    npm run bench            # all sizes (1k/3k/5k/10k) + crash tests, about 10 minutes
    npm run bench -- 3000    # one size only (then crash tests)

Each size runs in its own `node --max-old-space-size=4096` process, one at a time; the orchestrator waits while `free -g` shows more than 18 GB used.
A real Hocuspocus server (ephemeral port, loopback) and real HocuspocusProvider clients are started inside the benchmark and shut down at the end.
SQLite (`node:sqlite`) lives in `.tmp-wipe-me/run-*/PROTOTYPE-wipe-me.sqlite` and is deleted at the end. Needs Node 24.
Outputs: results.json (raw), results-tables.md (generated tables). Files: store.js (stores), bench.js, crash.js, common.js, report.js, lib.js (copied from ../yjs-board-sync).

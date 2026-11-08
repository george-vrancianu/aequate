# PROTOTYPE: Yjs board sync spike (throwaway, ticket #16)

Throwaway code that answers one question: how should a board's ink be laid out in Yjs documents?
Do not build on it. Results and the recommendation are in [RESULTS.md](RESULTS.md).

Three layouts are compared with strokes written once at pen-up (packed binary, one transaction per stroke):

- A: one Y.Doc per board (one Y.Map of strokes per page)
- B: one Y.Doc per board, one Yjs subdocument per page
- C: one Y.Doc (one Hocuspocus document) per page

## Run

    npm install && npm start

Needs Node 24. Takes about 1-2 minutes. It runs the undo checks, the pure-Yjs benchmark (each measurement in its own
child process, heap capped at 4 GB), and a Hocuspocus server on an ephemeral loopback port that is shut down at the end.
Nothing is left running. It writes `results.json` and `results-tables.md` (RESULTS.md embeds a copy of those tables plus
hand-written analysis). Parts alone: `npm run undo`, `npm run hocuspocus`.

Yjs is pinned to 13.6.x. The SQLite file used by the Hocuspocus part is a temp file, deleted at the end.

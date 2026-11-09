# Yjs with Hocuspocus: one document per page plus a board document

Board data is kept in Yjs and synced through Hocuspocus, pinned at 4.x on Yjs 13.6.x. Each page of a board is its own Hocuspocus document (`board:<id>:page:<id>`), holding that page's strokes as `strokeId → packed bytes`. Each board also has one small document (`board:<id>`) for the page list, the worked solutions with their steps, goal changes and level changes, and the active worked solution. Server-computed data (verdicts, recognition results, hint usage) lives in Postgres, keyed by step id. The stock Hocuspocus store rewrites a document on each save. We chose one document per page because the sync spike and the incremental-store spike found the cost of a large board is bytes, not CPU. Per page, a save at 10k strokes writes about 284 KB and opening a page takes about 7 ms. One document per board writes 5.6 MB per save with the stock store, and even with an update log it still loads the whole board (about 5 MB, 81 ms) to open any page and needs compaction. The board document exists because worked solutions belong to the board, not to a page, and must work offline like the ink.

## Considered Options

- **One document per board with an incremental update-log store.** Viable at 10k strokes (642 B per save), but opening any page loads the whole board, and it adds a compaction policy that pauses for about 55 ms. The update log stays available as a store detail for either layout.
- **One document per board, one subdocument per page.** Hocuspocus does not sync subdocuments.
- **y-websocket.** Minimal. Auth hooks, read-only connections and per-connection messaging would be ours to write.
- **Worked solutions in Postgres only.** Steps can be confirmed offline (#21), so they need the same local-first sync as the ink.

## Consequences

- Undo is per user, kept as an app-level stack over one UndoManager per page, because no single UndoManager spans documents. The sync spike showed this works.
- Hocuspocus's `onAuthenticate` loads the session from its cookie and opens a document only for the board's owner or the holder of an active grant (ADR 0006), read-only for grants. Revoking a grant or purging an account closes open connections.
- The server stack follows from this:
  - one Node/TypeScript service running Fastify (REST with JSON, TypeBox schemas producing OpenAPI and shared types) and Hocuspocus in the same process;
  - our own session auth, after the Lucia guide: argon2id, sessions in Postgres, an `HttpOnly`/`SameSite=Lax`/`Secure` cookie, an origin check on requests that change state, rate-limited login, 30-day sliding sessions;
  - Postgres through Kysely, with migrations as plain SQL files, and Yjs states as `bytea`;
  - the CAS as a separate Python FastAPI service with a pool of worker processes that can be killed on timeout, called over internal HTTP, with parse and check caches in Postgres;
  - no message broker and no object storage in v1.
- Offline, the app works on its local Yjs data whatever the state of the session. On reconnect with an expired session it asks for a login and then syncs. Local data is tied to the user id, and logging out offers to wipe it from the device.
- Pending the churn and low-end tablet spike (#39): whether Yjs garbage collection stays on (on for now), the undo cap (200 entries per user for now) and any limit on strokes per page (none for now).

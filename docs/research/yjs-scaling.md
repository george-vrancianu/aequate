# Yjs at thousands of strokes: document limits, subdocs, persistence

Research for issue #6 (part of #1). Feeds the sync spike and the sync-server / document-structure decision.
Checked on 2026-10-08 against Yjs 13.6.33 (latest release; `main` is already `@y/y` 14.0.0-rc), Hocuspocus 4.7.0, `@y/websocket-server`, tldraw `main`, and Excalidraw `main`.

## Question

Does a single Yjs document stay manageable at thousands of ink strokes with per-user undo, or should boards chunk per page? Which sync server (Hocuspocus or y-websocket) suits Postgres persistence, auth, and presence? What do tldraw and Excalidraw do?

## 1. Document size and update encoding

- Changes are encoded as "binary encoded (highly compressed) document updates". Updates are commutative, associative and idempotent. Peers sync by exchanging state vectors and sending only the missing diff. Source: https://docs.yjs.dev/api/document-updates
- `Y.mergeUpdates` merges several updates into one smaller update without loading a `Y.Doc`. But it "only merges document updates and doesn't garbage-collect deleted content". To shrink a document you must load it into a `Y.Doc` and re-encode it. Source: https://docs.yjs.dev/api/document-updates
- The README says Yjs is "well suited for even large documents". It also admits that text CRDTs "only grow in size"; Yjs reduces that growth but does not remove it. Source: https://github.com/yjs/yjs/blob/main/README.md
- Benchmarks (Yjs 13.6.11): a real editing trace of about 260k operations encodes to 160 KB, parses in 39 ms and uses about 3.2 MB of heap. The same trace replayed 100 times (about 26M operations) encodes to 16 MB, parses in 2.6 s and uses about 327 MB of heap. Source: https://github.com/dmonad/crdt-benchmarks
  - Those numbers come from character-level text editing, which is the worst case for per-item metadata. A stroke document has far fewer items (one per stroke), each with a large binary payload. So the encoded size should be dominated by point data, not CRDT metadata. **This is an inference and the spike must measure it.**
- Rough sizing (inference): tldraw stores draw paths as a Float32 first point plus Float16 deltas, i.e. 6 bytes per (x, y, pressure) point (https://github.com/tldraw/tldraw/blob/main/packages/tlschema/src/shapes/TLDrawShape.ts). A 200-point stroke is therefore about 1.2 KB, and 5,000 strokes are about 6 MB of payload. With naive JSON `{x,y,p}` objects the same board would be roughly 5 to 10 times larger.

## 2. Update log growth and garbage collection

- `Y.Doc` options include `gc` (default `true`) and `gcFilter` ("Return false to keep the Item"). Source: https://github.com/yjs/yjs/blob/main/src/utils/Doc.js
- GC runs during transaction cleanup: deleted items are replaced with `ItemDeleted`/`GC` structs ("This is where content is actually remove from the Yjs Doc"), and adjacent structs are merged. Source: https://github.com/yjs/yjs/blob/main/src/utils/Transaction.js
- Tombstones themselves cannot be collected while order must be preserved, but their *content* can be dropped. When a whole type is deleted, all its children become `GC` structs. Source: https://github.com/yjs/yjs/blob/main/README.md
- Set `gc = false` only if you need snapshots or version history. y-websocket-server says "disable gc when using snapshots!" Source: https://github.com/yjs/y-websocket-server/blob/main/src/utils.js
- **Implication for strokes:** an erased stroke leaves a small tombstone, but its point payload is freed (with `gc` on). The document grows with the number of strokes ever created, not with the points in deleted strokes.
- **Server-side update log:** if you store each incremental update in Postgres, the log grows with every transaction. `mergeUpdates` compacts it, but deleted content only goes away when you periodically load the document into a `Y.Doc` and write back `encodeStateAsUpdate`. Source: https://docs.yjs.dev/api/document-updates

## 3. Y.Map / Y.Array vs subdocuments

- **Y.Map retains overwritten values.** Per y-utility, Y.Map "needs to retain all key values that were created in history to resolve potential conflicts". Benchmark: 100k writes over 10 keys give 525 KB with Y.Map, but 271 bytes with `YKeyValue` (built on Y.Array). Y.Map's size scales with the number of operations, not the number of keys. Source: https://github.com/yjs/y-utility
  - So do not stream in-progress points into a Y.Map key, and do not repeatedly overwrite a stroke record while the pen moves. Write the stroke once at pen-up, and send the live preview over awareness instead (section 6).
- Y.Array "uses a linked list of Arrays that is split when necessary". Consecutive inserts from the same client merge into one struct. Source: https://github.com/yjs/yjs/blob/main/README.md
- **Subdocuments** are Y.Docs nested in a parent. They stay empty until `load()` is called, and `destroy()` frees their memory, which enables lazy loading of pages. "It is up to the providers to sync subdocuments", "Not all providers support subdocuments yet", and official providers treat them as separate entities. Source: https://docs.yjs.dev/api/subdocuments
- **Hocuspocus does not support subdocuments:** "We're currently evaluating feedback for subdocuments, but haven't implemented support yet." Source: https://tiptap.dev/docs/hocuspocus/guides/multi-subdocuments
- Hocuspocus does **multiplex many separate documents over one WebSocket**. `HocuspocusProviderWebsocket` keeps a `providerMap` "of attached providers keyed by documentName". Source: https://github.com/ueberdosis/hocuspocus/blob/main/packages/provider/src/HocuspocusProviderWebsocket.ts
  - So with Hocuspocus, "chunk per page" means one top-level document per page (for example `board:<id>:page:<n>`) plus a small board-index document. It does not mean Yjs subdocs.

## 4. UndoManager scoping per user

- An UndoManager is created over a scope of shared types. By default it tracks "all local changes that don't specify a transaction origin" (`trackedOrigins = new Set([null])`). It merges edits within `captureTimeout` (500 ms by default), and `stopCapturing()` forces a step boundary. Source: https://docs.yjs.dev/api/undo-manager
- Remote updates are applied with the provider as the transaction origin, so they are not tracked. Each client's own UndoManager is therefore per-user by construction. Remote attribute changes are never overwritten by default (`ignoreRemoteAttributeChanges`). Source: https://github.com/yjs/yjs/blob/main/src/utils/UndoManager.js
- **Cost:** the UndoManager calls `keepItem(item, true)` on deleted items in scope ("make sure that deleted structs are not gc'd"). Items the user could still restore keep their content in memory until the stack item is dropped. The `keep` flag is not persisted. Source: https://github.com/yjs/yjs/blob/main/src/utils/UndoManager.js
  - Cap the stack size (clear old stack items) so a long lesson does not pin every erased stroke.
- An UndoManager belongs to one `Y.Doc`. If pages are separate documents, undo is per page. This is acceptable, arguably expected, on a whiteboard.

## 5. Hocuspocus vs y-websocket: Postgres persistence and auth

| | Hocuspocus (MIT) | `@y/websocket-server` (MIT) |
|---|---|---|
| Persistence | `extension-database` with `fetch`/`store` callbacks. `store` receives `Buffer.from(Y.encodeStateAsUpdate(document))`, i.e. the **full document state** each time ([source](https://github.com/ueberdosis/hocuspocus/blob/main/packages/extension-database/src/Database.ts)). `onStoreDocument` is debounced: `debounce` 2000 ms, `maxDebounce` 10000 ms ([config](https://tiptap.dev/docs/hocuspocus/server/configuration)). There is no first-party Postgres extension; the docs show SQLite and name Postgres as an option ([docs](https://tiptap.dev/docs/hocuspocus/server/extensions/database)). Packages also include `extension-sqlite`, `extension-s3`, `extension-redis`, `extension-throttle` and `extension-webhook` ([repo](https://github.com/ueberdosis/hocuspocus/tree/main/packages)). | `setPersistence({bindState, writeState})`, which you implement yourself. `writeState` is called only when the last connection closes ([source](https://github.com/yjs/y-websocket-server/blob/main/src/utils.js)). "Documents live in memory by default". "If you need durable, production-grade persistence, use YHub or Hocuspocus instead of rolling your own" ([README](https://github.com/yjs/y-websocket-server)). |
| Auth | `onAuthenticate` gets the client `token` and can set `connection.readOnly = true`. `onTokenSync` re-validates the token mid-session. `beforeHandleMessage` can reject messages ([hooks](https://tiptap.dev/docs/hocuspocus/server/hooks)). | Only a comment in the `upgrade` handler: "You may check auth of request here" ([source](https://github.com/yjs/y-websocket-server/blob/main/src/server.js)). Permanent rejection is done by closing with codes 4400-4499 ([y-websocket README](https://github.com/yjs/y-websocket)). There is no read-only mode. |
| Awareness | Built in. Hooks: `onAwarenessUpdate`, plus `beforeHandleAwareness` to inspect or rewrite inbound presence ([hooks](https://tiptap.dev/docs/hocuspocus/server/hooks)). Provider: `setAwarenessField` ([source](https://github.com/ueberdosis/hocuspocus/blob/main/packages/provider/src/HocuspocusProvider.ts)). | Relays awareness and cleans up a client's states on disconnect ([source](https://github.com/yjs/y-websocket-server/blob/main/src/utils.js)). |
| Scaling | `extension-redis` syncs updates and awareness across instances. It "does not persist data", and "all messages will be handled on all instances" ([docs](https://tiptap.dev/docs/hocuspocus/server/extensions/redis)). | "can't be scaled easily"; the README points to @y/hub instead ([README](https://github.com/yjs/y-websocket)). |
| Targeted messages | `Connection.sendStateless(payload)` sends to one connection ([source](https://github.com/ueberdosis/hocuspocus/blob/main/packages/server/src/Connection.ts)). This is relevant to the "verdicts only to tutor sockets" rule. | None. |

Note: Hocuspocus writes a full snapshot every ≤10 s while a board is active. At a multi-MB stroke document that is a multi-MB Postgres `UPDATE` every 10 s per active board. That is fine for a few concurrent lessons, but it is also an argument for per-page documents, which keep each snapshot small.

## 6. Awareness (multi-cursor presence)

- Awareness is a separate, state-based CRDT for presence and cursors. It is "not stored in the Yjs document, as it doesn't need to be persisted". Source: https://docs.yjs.dev/getting-started/adding-awareness
- `outdatedTimeout = 30000`: a client's state is removed if it has not been renewed within 30 s. Source: https://github.com/yjs/y-protocols/blob/master/src/awareness.js
- Awareness is the natural channel for **in-progress strokes**: broadcast the live points as awareness state while the pen is down, and commit a single immutable stroke to the document at pen-up. This avoids Y.Map overwrite growth (section 3). It is an inference; check awareness throughput in the spike.

## 7. What tldraw and Excalidraw do

**tldraw**
- A freehand stroke is one `draw` shape record. Its `segments[].path` is a "Delta-encoded base64 path data" string: the first point as Float32, then Float16 deltas, 6 bytes per point. Source: https://github.com/tldraw/tldraw/blob/main/packages/tlschema/src/shapes/TLDrawShape.ts
- tldraw sync is not Yjs. `TLSyncRoom` is "the authoritative source for all document state and handles conflict resolution" (https://github.com/tldraw/tldraw/blob/main/packages/sync-core/src/lib/TLSyncRoom.ts). One `TLSocketRoom` exists per document (https://tldraw.dev/docs/sync).
- Persistence is a per-record table: `documents(id, state BLOB, lastChangedClock)` plus a `tombstones(id, clock)` table with pruning. Source: https://github.com/tldraw/tldraw/blob/main/packages/sync-core/src/lib/SQLiteSyncStorage.ts
- All pages live in one store/room.
- Undo is local: the history interceptor ignores any change whose source is not `'user'`. Source: https://github.com/tldraw/tldraw/blob/main/packages/editor/src/lib/editor/managers/HistoryManager/HistoryManager.ts

**Excalidraw**
- A freehand stroke is one `freedraw` element with `points: LocalPoint[]`, `pressures: number[]` and `simulatePressure`. Source: https://github.com/excalidraw/excalidraw/blob/master/packages/element/src/types.ts
- Sync is not a CRDT. Each element carries `version` and `versionNonce`, and reconciliation keeps the higher version, using the lower nonce as tie-break (https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/data/reconcile.ts). The server "relays end-to-end encrypted messages ... but does no centralized coordination" (https://plus.excalidraw.com/blog/building-excalidraw-p2p-collaboration-feature).
- Persistence: excalidraw.com stores the whole element array as JSON, encrypted, in Firebase. Source: https://github.com/excalidraw/excalidraw/blob/master/excalidraw-app/data/firebase.ts
- Undo: early collaboration cleared the undo stack on remote updates. Current history records only "local durable increment[s]". Source: https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/history.ts

Both tools use the same core pattern: **one record per stroke, immutable or last-writer-wins per record, with points packed inside the record**, a whole board in one room, and local-only undo.

## Answer

Yes: a single Yjs document should stay manageable at thousands of strokes, provided each stroke is stored as one immutable entry with packed points. Do not use per-point CRDT items or repeatedly overwritten Y.Map keys.

- The document then grows with the number of strokes ever drawn. GC drops the payload of erased strokes and leaves only small tombstones. The size is dominated by point data: about 6 MB for 5,000 strokes at 6 bytes per point, which is within what Yjs handles (benchmarks show 16 MB documents parsing in about 2.6 s).
- Per-user undo comes free: each client's UndoManager tracks only local-origin transactions. Its stack must be capped, because it pins erased strokes against GC.
- Use Hocuspocus over y-websocket. It has real auth hooks with read-only connections, debounced persistence hooks, Redis scaling, awareness hooks, and per-connection stateless messages for tutor-only verdicts. y-websocket-server itself tells you to use Hocuspocus or YHub for durable persistence.
- Hocuspocus does not support Yjs subdocuments. Chunking, if needed, means one Hocuspocus document per page, multiplexed over one socket. Since Hocuspocus stores the full document state on every debounced save, per-page documents are the cheap insurance for long multi-page lessons.
- tldraw and Excalidraw both keep one record per stroke with packed points, store the whole board in one room, and use local-only undo.

## Recommendation for the sync spike

Try first: **Hocuspocus plus one Yjs document per page**, with a small board-index document listing the pages.
- Store strokes in a `Y.Array<Y.Map>` or y-utility `YKeyValue` keyed by stroke id.
- Store each stroke's points as a single packed `Uint8Array`: Float32 first point plus Float16 or Int16 deltas for x, y and pressure.
- Write each stroke once at pen-up, and send the in-progress stroke via awareness.
- Run one UndoManager per page document, with `captureTimeout: 0` or `stopCapturing()` per stroke.
- Persist through `extension-database` into a Postgres `bytea` column.
- Keep the single-document-per-board variant as the comparison.

Measure, for 1,000 / 5,000 / 20,000 strokes (a mix of 50 to 500 points each, with about 20% erased):
1. Encoded document size, plus the size after reload and re-encode, with `gc` on.
2. Cold load time on an iPad and a Surface: fetch, `applyUpdate`, first render.
3. Client and server heap.
4. Postgres write size and latency per `onStoreDocument` at the 2 s / 10 s debounce.
5. Pen-up-to-remote-render latency with 6 clients.
6. Awareness bandwidth while streaming in-progress strokes at 60 Hz.
7. Undo correctness when two users draw and erase concurrently, and memory growth with an uncapped vs capped undo stack.

If the single-document variant stays under about 1 s cold load and about 5 MB per snapshot at 5,000 strokes, per-page chunking is optional. Otherwise adopt it.

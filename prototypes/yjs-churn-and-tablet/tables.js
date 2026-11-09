// PROTOTYPE (throwaway): render results/*.json into Markdown tables (results-tables.md).
import fs from 'node:fs'
const all = fs.readdirSync('results').filter((f) => f.endsWith('.json') && f !== 'quick.json').map((f) => JSON.parse(fs.readFileSync('results/' + f)))
const main = all.filter((r) => r.cfg.name.startsWith('main-')).sort((a, b) => a.cfg.N - b.cfg.N || a.cfg.layout.localeCompare(b.cfg.layout) || (b.cfg.gc - a.cfg.gc))
const ret = all.filter((r) => r.cfg.name.startsWith('retain-'))
const kb = (n) => (n / 1024 >= 1024 ? (n / 1048576).toFixed(2) + ' MB' : (n / 1024).toFixed(1) + ' KB')
const f1 = (n) => (n == null ? 'n/a' : Number(n).toFixed(1))
const mb = (n) => (n / 1048576).toFixed(1)
let md = ''
const T = (head, rows) => { md += '| ' + head.join(' | ') + ' |\n|' + head.map(() => '---').join('|') + '|\n' + rows.map((r) => '| ' + r.join(' | ') + ' |\n').join('') + '\n' }

md += '### T1. Size and tombstones vs churn (server replica, i.e. what Hocuspocus stores; Yjs v1 encoding)\n\n'
md += 'Churn is cumulative within one run: the 0.5x, 1x, 3x rows are the same doc after 0.5N, N, 3N erase iterations. "deleted items" counts deleted Items plus GC structs; "DS ranges" is the number of ranges in the delete set; "DS bytes" its exact v1 encoding. Payload = sum of the packed stroke bytes still live.\n\n'
{
  const rows = []
  for (const r of main) for (const c of r.rows) rows.push([r.cfg.N, r.cfg.layout, r.cfg.gc, c.label, kb(c.livePayloadBytes), kb(c.encodedServerV1), c.overheadServer.toFixed(2) + 'x', kb(c.encodedServerV2), c.serverStats.deletedTotal, c.serverStats.retainedDeleted, c.serverStats.dsRanges, c.serverStats.dsBytesV1 + ' B'])
  T(['live N', 'layout', 'gc', 'churn', 'live payload', 'encoded', 'encoded / payload', 'encoded v2', 'deleted items', 'deleted with content kept', 'DS ranges', 'DS bytes'], rows)
}
md += '### T2. The editing client (user 0, with its UndoManager and the spike cap model) vs the server\n\n'
{
  const rows = []
  for (const r of main) { const c = r.rows[3]; rows.push([r.cfg.N, r.cfg.layout, r.cfg.gc, kb(c.livePayloadBytes), kb(c.encodedServerV1), kb(c.encodedClientV1), c.overheadClient.toFixed(2) + 'x', c.clientStats.retainedDeleted, kb(c.clientStats.retainedBytes), c.clientStats.keepFlagged, c.userStack.undo + ' / ' + c.userStack.redo]) }
  T(['live N', 'layout', 'gc', 'payload', 'server encoded', 'client encoded', 'client / payload', 'deleted items with content kept (client)', 'kept payload', 'items with keep flag', 'user undo / redo stack'], rows)
}
md += '### T3. Incremental update sizes during churn (bytes per update, whole run to 3x)\n\n'
{
  const rows = []
  for (const r of main.filter((r) => r.cfg.gc)) { const u = r.rows[3].updateBytes; for (const k of ['draw', 'erase', 'undo', 'redo']) if (u[k].n) rows.push([r.cfg.N, r.cfg.layout, k, u[k].n, u[k].median, f1(u[k].p95), u[k].max]) }
  T(['live N', 'layout', 'op', 'count', 'median B', 'p95 B', 'max B'], rows)
  const g = main.filter((r) => !r.cfg.gc)
  md += '(gc=false gives identical update sizes: gc does not change what is sent for an op.) Check: ' + g.map((r) => `${r.cfg.N}/${r.cfg.layout} erase median ${r.rows[3].updateBytes.erase.median} B`).join(', ') + '\n\n'
}
md += '### T4. Cold load of the server state into a fresh doc (median of 5; ms) and memory (heap + arrayBuffers delta after gc, MB)\n\n'
{
  const rows = []
  for (const r of main) for (const ci of [0, 3]) { const c = r.rows[ci]; for (const g of ['gcTrue', 'gcFalse']) { const l = c.coldLoad[g]; rows.push([r.cfg.N, r.cfg.layout, r.cfg.gc, c.label, g === 'gcTrue' ? 'true' : 'false', f1(l.wholeBoardMs), f1(l.onePageMs), mb(l.mem.heap) + ' + ' + mb(l.mem.ab) + ' = ' + mb(l.mem.total), kb(l.reEncodedBytes)]) } }
  T(['live N', 'layout', 'author gc', 'churn', 'loading doc gc', 'whole board ms', 'one page ms', 'memory MB (heap + ab)', 're-encoded after load'], rows)
}
md += '### T5. Cost of the churn itself and the run\n\n'
{
  const rows = main.map((r) => { const c = r.rows[3]; return [r.cfg.N, r.cfg.layout, r.cfg.gc, c.ops.iterations, c.ops.erases, c.ops.redraws, c.ops.undos, c.ops.redos, f1(c.churnMsPerIter), r.wallSeconds.toFixed(0) + ' s'] })
  T(['live N', 'layout', 'gc', 'iterations (3x)', 'erases', 're-draws', 'undos', 'redos', 'ms per iteration (3 replicas + relay)', 'run wall time (incl. measurements)'], rows)
}
md += '### T6. Undo retention experiment (5k live, gc=true, 3x churn): what keeps tombstone content alive\n\n'
md += 'Variants: **noum** = no UndoManager (pure erase); **none** = UndoManagers, no cap (stacks grow); **splice** = the sync spike cap (trim the stack arrays only); **release** = trim and also clear the `keep` flag of the dropped entries. "Server" = replica without UndoManager.\n\n'
{
  const mains = main.filter((r) => r.cfg.N === 5000 && r.cfg.gc).map((r) => ({ ...r, cfg: { ...r.cfg, cap: 'splice' } }))
  const rows = []
  for (const r of [...ret, ...mains.filter((m) => !ret.some((x) => x.cfg.layout === m.cfg.layout && x.cfg.cap === 'splice'))].sort((a, b) => a.cfg.layout.localeCompare(b.cfg.layout) || a.cfg.cap.localeCompare(b.cfg.cap))) {
    const c = r.rows[3], rt = r.retention
    rows.push([r.cfg.layout, r.cfg.cap, kb(c.livePayloadBytes), kb(c.encodedServerV1), kb(c.encodedClientV1), c.clientStats.retainedDeleted, kb(c.clientStats.retainedBytes), c.userStack.undo, rt?.beforeClear ? rt.beforeClear.clientStats.retainedDeleted : '', rt?.afterClear ? kb(rt.afterClear.encodedClientV1) : '', rt?.afterClear ? rt.afterClear.clientStats.retainedDeleted : '', rt?.afterReloadGcTrue ? rt.afterReloadGcTrue.stats.retainedDeleted + ' / ' + kb(rt.afterReloadGcTrue.encodedV1) : ''])
  }
  T(['layout', 'variant', 'payload', 'server encoded', 'client encoded', 'client: deleted items with content', 'their payload', 'undo stack', 'content-holding deleted items just before um.clear() (after the final checks)', 'client encoded after um.clear()', 'client content-holding deleted items after um.clear()', 'after reload into gc doc: content-holding / re-encoded'], rows)
}
md += 'The "3x" columns are the 3x checkpoint. The "before/after um.clear()" columns are taken after the final correctness checks (extra erases, up to 300 undos and redos), which is why they differ from the 3x column; compare after-clear with before-clear, not with 3x.\n\n'
md += '#### T6b. Who deleted the retained items (user 0 replica, gc=true, 5k, 3x churn, measured in the harness)\n\n'
{
  const rows = ret.filter((r) => r.retention?.attribution).map((r) => { const a = r.retention.attribution, t = a.retainedFromOwn + a.retainedFromOthers; return [r.cfg.layout, r.cfg.cap, t, a.retainedFromOwn, a.retainedFromOthers, t ? (100 * a.retainedFromOthers / t).toFixed(1) + '%' : '', a.user0TrackedDeletions] })
  T(['layout', 'variant', 'retained items (content held)', 'deleted in user 0 tracked transactions (erase, redo, undone draw)', 'other', 'other share', 'all items user 0 deleted in tracked transactions'], rows)
}
md += '### T7. Correctness checks (every run)\n\n'
{
  const names = [...new Set(main.flatMap((r) => r.checks.map((c) => c.name.replace(/\d+/g, 'N'))))]
  const rows = names.map((n) => [n, ...main.map((r) => { const cs = r.checks.filter((c) => c.name.replace(/\d+/g, 'N') === n); return cs.length ? (cs.every((c) => c.pass) ? 'PASS' : 'FAIL') : '-' })])
  T(['check', ...main.map((r) => `${r.cfg.N / 1000}k ${r.cfg.layout} gc=${r.cfg.gc}`)], rows)
}
fs.writeFileSync('results-tables.md', md)
console.log(md)

// PROTOTYPE (throwaway): results.json -> results-tables.md
import fs from 'node:fs'
const R = JSON.parse(fs.readFileSync(new URL('./results.json', import.meta.url)))
const kb = (b) => (b / 1024).toFixed(b < 10240 ? 1 : 0) + ' KB'
const mb = (b) => (b / 1048576).toFixed(2) + ' MB'
const f = (x, d = 1) => (x == null ? '-' : (+x).toFixed(d))
const out = []
const sizes = Object.keys(R.sizes)
out.push('### Single added stroke: bytes written per save (steady state)\n', '| strokes | store | update bytes | payload bytes per save | on-disk (WAL) bytes per save | save ms (encode+write) |', '|---|---|---|---|---|---|')
const label = { full: 'full rewrite, one doc per board', pg: 'full rewrite, one doc per page (20 pages)', ld: 'update log (row per onChange)', lt: 'batched log (row per onStoreDocument)' }
for (const N of sizes) for (const s of R.sizes[N].singleSave) out.push(`| ${N} | ${label[s.kind]} | ${s.updateBytes} | ${s.bytesWrittenPerSave} | ${s.walBytesPerSave} | ${f(s.saveMs, 2)} |`)
out.push('', '### Load time (Hocuspocus cold open, median of 3; server onLoadDocument ms in brackets)\n', '| strokes | log rows | log MB | live state MB | replay row by row (direct) | mergeUpdates then apply (direct) | open via Hocuspocus, log uncompacted | after compaction (doc) | after compaction (merge) | snapshot + 100-row tail |', '|---|---|---|---|---|---|---|---|---|---|')
for (const N of sizes) { const L = R.sizes[N].load; const d = L.compact_doc, m = L.compact_merge
  out.push(`| ${N} | ${L.rows.rows} | ${mb(L.rows.bytes)} | ${mb(L.liveStateBytes)} | ${L.replayDirectMs} ms | ${L.mergeThenApplyDirectMs} ms | ${f(L.hocuspocusOpenBeforeCompaction.clientOpenMs)} ms (${f(L.hocuspocusOpenBeforeCompaction.serverLoadMs)}) | ${f(d.hocuspocusOpen.clientOpenMs)} ms (${f(d.hocuspocusOpen.serverLoadMs)}) | ${f(m.hocuspocusOpen.clientOpenMs)} ms (${f(m.hocuspocusOpen.serverLoadMs)}) | ${f(d.hocuspocusOpenSnapshotPlusTail.clientOpenMs)} ms (${f(d.hocuspocusOpenSnapshotPlusTail.serverLoadMs)}) |`) }
out.push('', '### Compaction of a whole N-stroke log (+10% erases), on a live server doc\n', '| strokes | mode | rows merged | compaction ms (blocks event loop) | snapshot size | max gap between ping arrivals during compaction | calm gap p50 (ping every 5 ms) |', '|---|---|---|---|---|---|---|')
for (const N of sizes) for (const m of ['doc', 'merge']) { const c = R.sizes[N].load['compact_' + m]; out.push(`| ${N} | ${m === 'doc' ? 'encodeStateAsUpdate(live doc)' : 'Y.mergeUpdates(snapshot + rows)'} | ${c.rowsMerged} | ${f(c.compactMs)} | ${mb(c.snapshotBytes)} | ${f(c.pingGapMaxDuringCompactionMs)} ms | ${f(c.pingGapCalmP50Ms)} ms |`) }
out.push('', '### Session: 2000 strokes (+~10% erase/undo), two sessions with disconnect/reconnect. Totals over both sessions\n', '| strokes on board | store | saves/appends | payload bytes (incl. compaction) | payload bytes per stroke | on-disk WAL bytes (incl. compaction) | WAL bytes per stroke | median payload / WAL bytes per write | write ms p50 / p99 / max | compactions (ms) | log left after s1 / s2 (rows, KB) | ping RTT p99 / max (ms) | ping gap p99 / max (ms) | max ping gap in compaction window (ms) | reload == live |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
const names = { full: 'full rewrite, doc per board', pg: 'full rewrite, doc per page', lc: `log + compact @${R.meta.COUNT} updates`, lb: `log + compact @${R.meta.BYTES / 1024} KiB`, ld: 'log + compact on last disconnect', lt: 'batched log + compact on disconnect', none: 'no storage (ping baseline)' }
for (const N of sizes) for (const v of R.sizes[N].sessions) {
  const [a, b] = v.sessions
  const saves = a.saves + b.saves, wm = (k) => f(Math.max(a.writeMs?.[k] ?? 0, b.writeMs?.[k] ?? 0), 2)
  const comps = [...a.compactions, ...b.compactions]
  out.push(`| ${N} | ${names[v.kind]} | ${saves} | ${mb(v.totalBytesWritten)} | ${kb(v.totalBytesPerStroke)} | ${mb(v.totalWalBytes)} | ${kb(v.totalWalBytesPerStroke)} | ${kb((a.bytesPerSaveMedian + b.bytesPerSaveMedian) / 2)} / ${kb((a.walBytesPerSaveMedian + b.walBytesPerSaveMedian) / 2)} | ${v.kind === 'none' ? '-' : `${wm('p50')} / ${wm('p99')} / ${wm('max')}`} | ${comps.length ? comps.map((c) => `${c.trigger} ${f(c.ms)}`).join(', ') : '-'} | ${a.logLeftAfterSession.rows}, ${kb(a.logLeftAfterSession.bytes)} / ${b.logLeftAfterSession.rows}, ${kb(b.logLeftAfterSession.bytes)} | ${f(Math.max(a.pingMs.p99, b.pingMs.p99))} / ${f(Math.max(a.pingMs.max, b.pingMs.max))} | ${f(Math.max(a.pingGapMs.p99, b.pingGapMs.p99))} / ${f(Math.max(a.pingGapMs.max, b.pingGapMs.max))} | ${a.pingMaxDuringCompactionMs ?? '-'} / ${b.pingMaxDuringCompactionMs ?? '-'} | ${a.correct_reloadFromStorageEqualsLive} / ${b.correct_reloadFromStorageEqualsLive} |`)
}
out.push('', '### Log growth over the session (update-log with no compaction until disconnect), rows / KB after every 200 strokes\n')
for (const N of sizes) for (const k of ['ld', 'lc', 'lb', 'lt']) { const v = R.sizes[N].sessions.find((s) => s.kind === k); out.push(`- ${N} strokes, ${names[k]}: s1 ` + v.sessions[0].growthSeries.filter((_, i) => i % 2 === 1).map((g) => `${g.logRows}/${Math.round(g.logBytes / 1024)}`).join(', ') + ' ; s2 ' + v.sessions[1].growthSeries.filter((_, i) => i % 2 === 1).map((g) => `${g.logRows}/${Math.round(g.logBytes / 1024)}`).join(', ')) }
out.push('', '### Correctness: load experiment\n', '| strokes | log replay == live | mergeUpdates == live | after compaction (doc) == live | after compaction (merge) == live | snapshot+tail == live |', '|---|---|---|---|---|---|')
const pf = (b) => (b === true ? 'PASS' : 'FAIL')
for (const N of sizes) { const L = R.sizes[N].load; out.push(`| ${N} | ${pf(L.correct_replayEqualsLive)} | ${pf(L.correct_mergeEqualsLive)} | ${pf(L.compact_doc.correct_equalsLive)} | ${pf(L.compact_merge.correct_equalsLive)} | ${pf(L.compact_doc.correct_snapshotPlusTailEqualsLive)} |`) }
out.push('', '### Crash tests (SIGKILL of the server process, then reload from sqlite only; board of 1000 + 600 strokes with ~10% erases)\n', '| scenario | recovered / expected strokes | log rows left | snapshot bytes | state vector equal | content equal | result |', '|---|---|---|---|---|---|---|')
for (const c of R.crash) out.push(`| ${c.mode} | ${c.recoveredStrokes} / ${c.expectedStrokes} | ${c.logRowsLeft} | ${c.snapshotBytes ?? '-'} | ${c.svEqual} | ${c.contentEqual} | ${c.result} |`)
fs.writeFileSync(new URL('./results-tables.md', import.meta.url), out.join('\n') + '\n')
console.log('wrote results-tables.md')

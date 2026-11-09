// PROTOTYPE (throwaway): Hocuspocus on 0.0.0.0 that also serves the measurement page and a few control endpoints.
//   npm run tablet            (PORT=8787 by default; override with PORT=1234 or --port 1234; PORT=0 = ephemeral)
// Boards live only in memory (held open through direct connections); restart the server to wipe them.
import { Server } from '@hocuspocus/server'
import os from 'node:os'
import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { build } from './build.js'
import { genStrokes, genStroke, pack, mulberry32, pageOf } from '../lib.js'

const dir = path.dirname(fileURLToPath(import.meta.url))
const PAGES = 20
export const docName = (size, layout, p) => (layout === 'board' ? `t-${size}-board` : `t-${size}-page-${p}`)

export async function startServer({ port = 8787, quiet = false } = {}) {
  await build()
  const held = new Map() // key -> {conns:[{conn,name}], size, layout}
  const strokeCache = new Map()
  const getStrokes = (n) => { if (!strokeCache.has(n)) strokeCache.set(n, genStrokes(n)); return strokeCache.get(n) }
  const mapOf = (doc, layout, p) => doc.getMap(layout === 'board' ? 'strokes:' + p : 'strokes')
  const json = (res, code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(obj)) }

  async function seed(size, layout) {
    const key = size + '/' + layout
    if (held.has(key)) return { key, already: true, ms: 0 }
    const t0 = Date.now()
    const strokes = getStrokes(size)
    const names = layout === 'board' ? [docName(size, 'board')] : Array.from({ length: PAGES }, (_, p) => docName(size, 'page', p))
    const entry = { size, layout, conns: [] }
    for (const name of names) entry.conns.push({ name, conn: await hocus.openDirectConnection(name, {}) })
    for (let d = 0; d < names.length; d++) {
      await entry.conns[d].conn.transact((doc) => {
        strokes.forEach((s, i) => { const p = pageOf(i, size, PAGES); if (layout === 'board' || p === d) mapOf(doc, layout, p).set(s.id, s.packed) })
      })
    }
    held.set(key, entry)
    return { key, already: false, ms: Date.now() - t0, docs: names.length }
  }

  async function stream(size, layout, count, intervalMs) {
    const entry = held.get(size + '/' + layout)
    if (!entry) throw new Error('not seeded: ' + size + '/' + layout)
    const c = layout === 'board' ? entry.conns[0] : entry.conns[0] // page 0 doc (or the board doc)
    const rng = mulberry32(Date.now() & 0xffff)
    const ids = []
    for (let i = 0; i < count; i++) {
      const id = 'live' + Date.now().toString(36) + i
      const packed = pack(genStroke(rng))
      await c.conn.transact((doc) => mapOf(doc, layout, 0).set(id, packed))
      ids.push(id)
      await new Promise((r) => setTimeout(r, intervalMs))
    }
    // clean up so the seeded board keeps its size (leaves `count` tombstones in that doc)
    await new Promise((r) => setTimeout(r, 300))
    await c.conn.transact((doc) => { const m = mapOf(doc, layout, 0); ids.forEach((id) => m.delete(id)) })
    return { sent: ids.length }
  }

  const routes = {
    async '/seed'(q) { return seed(+q.get('size'), q.get('layout')) },
    async '/stream'(q) { return stream(+q.get('size'), q.get('layout'), +(q.get('count') || 100), +(q.get('interval') || 30)) },
    async '/status'() { return { seeded: [...held.keys()], pages: PAGES } },
    async '/ping'() { return { t: Date.now() } },
    async '/reset'() { for (const e of held.values()) for (const c of e.conns) await c.conn.disconnect(); held.clear(); return { ok: true } },
  }
  const staticFiles = { '/': ['index.html', 'text/html; charset=utf-8'], '/index.html': ['index.html', 'text/html; charset=utf-8'], '/client.js': ['client.js', 'text/javascript; charset=utf-8'] }

  const server = new Server({
    address: '0.0.0.0', port, quiet: true, stopOnSignals: false,
    extensions: [{
      extensionName: 'TabletRoutes',
      async onRequest({ request, response }) {
        const u = new URL(request.url, 'http://x')
        try {
          if (staticFiles[u.pathname]) {
            const [f, type] = staticFiles[u.pathname]
            response.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' }); response.end(fs.readFileSync(path.join(dir, 'dist', f)))
          } else if (routes[u.pathname]) json(response, 200, await routes[u.pathname](u.searchParams))
          else { response.writeHead(404); response.end('not found') }
        } catch (e) { json(response, 500, { error: String(e.message || e) }) }
        throw null // response already sent: stop Hocuspocus from writing its welcome text
      },
    }],
  })
  const hocus = await server.listen(port)
  const actual = server.address.port
  return { port: actual, hocus, async close() { for (const e of held.values()) for (const c of e.conns) await c.conn.disconnect().catch(() => {}); await server.destroy() } }
}

function lanAddresses() {
  const out = []
  for (const [name, list] of Object.entries(os.networkInterfaces())) for (const a of list || []) if (a.family === 'IPv4' && !a.internal) out.push({ name, address: a.address })
  return out
}

if (import.meta.url === 'file://' + process.argv[1]) {
  const argPort = process.argv.indexOf('--port')
  const port = Number(argPort > 0 ? process.argv[argPort + 1] : process.env.PORT ?? 8787)
  const s = await startServer({ port })
  const P = s.port
  const isWsl = /microsoft/i.test(fs.readFileSync('/proc/version', 'utf8').toString())
  const addrs = lanAddresses()
  console.log('\nPROTOTYPE tablet benchmark server (in-memory, throwaway). Ctrl+C to stop.')
  console.log(`Listening on 0.0.0.0:${P}`)
  if (!isWsl) {
    console.log('Open on the tablet (same Wi-Fi):')
    addrs.forEach((a) => console.log(`  http://${a.address}:${P}/   (${a.name})`))
  } else {
    const wslIp = addrs.find((a) => a.name === 'eth0')?.address ?? addrs[0]?.address ?? '<WSL-IP>'
    let winIp = '<WINDOWS-LAN-IP>'
    try {
      const o = execSync(`powershell.exe -NoProfile -Command "(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1).IPv4Address.IPAddress"`, { timeout: 8000, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()
      if (/^\d+\.\d+\.\d+\.\d+$/.test(o)) winIp = o
    } catch {}
    console.log(`WSL2 detected. WSL IP: ${wslIp}   Windows LAN IP: ${winIp}${winIp.startsWith('<') ? '  (could not detect: run ipconfig in Windows, use the Wi-Fi IPv4 address)' : ''}`)
    console.log('Open on the tablet (same Wi-Fi) AFTER the Windows port proxy and firewall rule below exist:')
    console.log(`  http://${winIp}:${P}/`)
    console.log(`(Inside WSL / Windows this machine only: http://localhost:${P}/  or  http://${wslIp}:${P}/)`)
    console.log('\nWSL2 is NATed, so the tablet cannot reach it directly. In an ADMIN PowerShell on Windows run:')
    console.log(`  netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=${P} connectaddress=${wslIp} connectport=${P}`)
    console.log(`  New-NetFirewallRule -DisplayName "aequate-proto-${P}" -Direction Inbound -Action Allow -Protocol TCP -LocalPort ${P}`)
    console.log('  (or: netsh advfirewall firewall add rule name="aequate-proto-' + P + '" dir=in action=allow protocol=TCP localport=' + P + ')')
    console.log('The WSL IP changes on every WSL restart: if it does, delete and re-add the portproxy. Cleanup afterwards:')
    console.log(`  netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=${P}`)
    console.log(`  Remove-NetFirewallRule -DisplayName "aequate-proto-${P}"`)
    console.log('  (or: netsh advfirewall firewall delete rule name="aequate-proto-' + P + '")')
    console.log('Check: netsh interface portproxy show v4tov4')
    console.log('If Windows still blocks it, the Wi-Fi profile may be "Public": set it to Private, or allow the rule on all profiles (the rule above applies to all).')
  }
  const stop = async () => { await s.close(); process.exit(0) }
  process.on('SIGINT', stop); process.on('SIGTERM', stop)
}

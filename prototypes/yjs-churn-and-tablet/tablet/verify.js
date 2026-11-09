// PROTOTYPE (throwaway): short-lived local verification. Starts the server on an EPHEMERAL port, drives headless Chromium
// through the real page (desktop baseline), writes tablet/desktop-baseline.json, shuts everything down.
//   node tablet/verify.js [sizes, e.g. 1000,3000]    default: 1000,3000,5000,10000
import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { startServer } from './server.js'

const dir = path.dirname(fileURLToPath(import.meta.url))
const sizes = (process.argv[2] || '1000,3000,5000,10000').split(',').map(Number)
const s = await startServer({ port: 0 })
console.log('server on ephemeral port', s.port)
const browser = await chromium.launch({ headless: true, args: ['--enable-precise-memory-info'] })
try {
  const page = await browser.newPage({ viewport: { width: 1024, height: 1400 } })
  page.on('console', (m) => { if (m.type() === 'error') console.log('[page error]', m.text()) })
  page.on('pageerror', (e) => console.log('[pageerror]', e.message))
  await page.goto(`http://127.0.0.1:${s.port}/`)
  for (const n of sizes) for (const lay of ['board', 'page']) {
    const t = Date.now()
    await page.evaluate(([n, lay]) => window.__run(n, lay), [n, lay])
    console.log(`${n} ${lay} done in ${Date.now() - t} ms`)
  }
  // exercise the UI buttons too: the JSON box is filled and the copy button reports a status
  await page.click('#copy')
  await page.waitForTimeout(500)
  const status = await page.textContent('#copystatus')
  const json = JSON.parse(await page.inputValue('#json'))
  console.log('copy status:', status, '| table rows:', await page.locator('#tbl tr').count())
  json.verification = { headless: true, browser: browser.version(), note: 'desktop baseline on the same machine, loopback, not a tablet' }
  fs.writeFileSync(path.join(dir, process.argv[3] || 'desktop-baseline.json'), JSON.stringify(json, null, 1))
} finally {
  await browser.close()
  await s.close()
}
console.log('stopped')
setTimeout(() => process.exit(0), 200)

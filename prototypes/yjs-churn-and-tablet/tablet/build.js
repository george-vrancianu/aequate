// PROTOTYPE (throwaway): bundle the browser page with esbuild. Low target so an old iPad Safari can parse it.
import * as esbuild from 'esbuild'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const dir = path.dirname(fileURLToPath(import.meta.url))
export async function build() {
  fs.mkdirSync(path.join(dir, 'dist'), { recursive: true })
  await esbuild.build({
    entryPoints: [path.join(dir, 'client.js')], bundle: true, outfile: path.join(dir, 'dist', 'client.js'),
    format: 'iife', target: ['safari12', 'chrome70'], minify: true, sourcemap: false, logLevel: 'warning',
    define: { 'process.env.NODE_ENV': '"production"' },
  })
  fs.copyFileSync(path.join(dir, 'index.html'), path.join(dir, 'dist', 'index.html'))
}
if (import.meta.url === 'file://' + process.argv[1]) { await build(); console.log('built tablet/dist') }

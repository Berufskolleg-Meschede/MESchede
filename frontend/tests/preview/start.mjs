import { createServer } from 'node:http'
import { spawn } from 'node:child_process'
import { PreviewError, PreviewOrderStore } from './store.mts'

const store = new PreviewOrderStore()
const server = createServer(async (request, response) => {
  const url = new URL(request.url, 'http://127.0.0.1:18030')
  try {
    let data
    if (request.method === 'GET' && url.pathname === '/health') { data = { preview: true } }
    else if (request.method === 'GET' && url.pathname === '/orders/overview') { data = store.overview() }
    else if (request.method === 'POST' && url.pathname === '/orders/preview/reset') { store.reset(); data = { reset: true } }
    else if (request.method === 'POST' && /^\/orders\/runs\/[^/]+\/reviews$/.test(url.pathname)) {
      let body = ''
      for await (const chunk of request) {
        body += chunk
        if (body.length > 20000) { throw new PreviewError(413, 'Die Testanfrage ist zu groß.') }
      }
      data = store.review(url.pathname.split('/')[3], JSON.parse(body))
    } else if (request.method === 'GET' && /^\/(productionorder|deliveryorder)(\/|$)/.test(url.pathname)) {
      const kind = url.pathname.startsWith('/productionorder') ? 'production' : 'delivery'
      const id = decodeURIComponent(url.pathname.split('/').slice(2).join('/'))
      data = id ? store.detail(kind, id) : store.page(kind, url.searchParams)
    } else { throw new PreviewError(404, 'Die Vorschau unterstützt ausschließlich Auftragsansichten und Testbewertungen.') }
    response.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' })
    response.end(JSON.stringify(data))
  } catch (error) {
    response.writeHead(error instanceof PreviewError ? error.status : 400, { 'Content-Type': 'application/json' })
    response.end(JSON.stringify({ detail: error instanceof Error ? error.message : 'Ungültige Testanfrage.' }))
  }
})

let frontend
let stopping = false
function stop() {
  if (stopping) { return }
  stopping = true
  frontend?.kill('SIGTERM')
  server.close()
}
server.once('error', error => { console.error(error.message); process.exitCode = 1; stop() })
server.listen(18030, '127.0.0.1', () => {
  frontend = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3030'], {
    cwd: process.cwd(), stdio: 'inherit', env: { ...process.env, NODE_ENV: 'development', MES_PREVIEW_MODE: 'true', MES_BACKEND_URL: 'http://127.0.0.1:18030' },
  })
  frontend.once('error', error => { console.error(error.message); process.exitCode = 1; stop() })
  frontend.once('exit', code => { if (!stopping && code) { process.exitCode = code }; stop() })
  console.log('Testdaten-Vorschau: http://127.0.0.1:3030 — ausschließlich temporäre simulierte Daten.')
})
for (const signal of ['SIGINT', 'SIGTERM']) { process.on(signal, stop) }

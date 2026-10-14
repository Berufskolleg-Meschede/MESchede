import type { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'

const ALLOWED_PATHS = new Set(['productionorder', 'deliveryorder', 'orders'])

/** Leitet Auftragsrequests an eine serverseitig konfigurierte Backendadresse weiter. */
async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params
  if (!ALLOWED_PATHS.has(path[0]) || path.some(segment => segment === '..' || segment === '.')) {
    return Response.json({ detail: 'Diese Schnittstelle ist nicht verfügbar.' }, { status: 404 })
  }

  const base = (process.env.MES_BACKEND_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
  const isOrderList = path.length === 1 && (path[0] === 'productionorder' || path[0] === 'deliveryorder')
  const trailingSlash = isOrderList || request.nextUrl.pathname.endsWith('/') ? '/' : ''
  const url = `${base}/${path.map(encodeURIComponent).join('/')}${trailingSlash}${request.nextUrl.search}`
  try {
    const upstream = await fetch(url, {
      method: request.method,
      headers: { 'Content-Type': 'application/json' },
      body: request.method === 'POST' ? await request.text() : undefined,
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    })
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { 'Content-Type': upstream.headers.get('Content-Type') ?? 'application/json', 'Cache-Control': 'no-store' },
    })
  } catch {
    return Response.json({ detail: 'Das MES-Backend ist nicht erreichbar. Bitte erneut versuchen.' }, { status: 503 })
  }
}

export const GET = forward
export const POST = forward

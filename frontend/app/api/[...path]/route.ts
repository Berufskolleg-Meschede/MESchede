type RouteContext = {
  params: Promise<{ path: string[] }>
}

export const dynamic = 'force-dynamic'

async function proxyBackendRequest(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? 'http://localhost:8000'
  const requestUrl = new URL(request.url)
  // Next.js normalisiert eingehende Pfade ohne abschließenden Slash, bevor dieser Handler
  // läuft. Die Backend-Router erwarten ihn aber auf der Ressourcenwurzel (z.B. /settings/,
  // /storage/) und würden sonst per 308 auf eine absolute Backend-URL umleiten, der der
  // Browser cross-origin folgt (CORS-Fehler). Collection-Routen bestehen hier immer aus genau
  // einem Pfadsegment; Einzelressourcen (/storage/5, /storage/status) aus mehreren.
  const trailingSlash = path.length === 1 ? '/' : ''
  const targetUrl = new URL(`/${path.map(encodeURIComponent).join('/')}${trailingSlash}`, backendUrl)
  targetUrl.search = requestUrl.search

  const headers = new Headers(request.headers)
  headers.delete('host')
  headers.delete('connection')
  headers.delete('content-length')

  const body = ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer()
  const backendResponse = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
    cache: 'no-store',
    redirect: 'manual',
  })

  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: backendResponse.headers,
  })
}

export const GET = proxyBackendRequest
export const HEAD = proxyBackendRequest
export const POST = proxyBackendRequest
export const PATCH = proxyBackendRequest
export const PUT = proxyBackendRequest
export const DELETE = proxyBackendRequest

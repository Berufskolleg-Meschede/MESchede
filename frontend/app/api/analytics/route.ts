import { NextRequest } from 'next/server'

export async function GET(request: NextRequest): Promise<Response> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? 'http://localhost:8000'
  const target = new URL(`/analytics/${request.nextUrl.search}`, backendUrl)
  try {
    const result = await fetch(target, { cache: 'no-store' })
    return new Response(result.body, {
      status: result.status,
      headers: { 'content-type': result.headers.get('content-type') ?? 'application/json' },
    })
  } catch {
    return Response.json({ detail: 'Backend nicht erreichbar.' }, { status: 503 })
  }
}

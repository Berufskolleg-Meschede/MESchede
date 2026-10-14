import { createServer } from 'node:http'

// Ausschließlich lokale HTTP-Transportfixture; keine Produktions- oder PLC-Verbindung.
const server = createServer(async (request, response) => {
  const url = new URL(request.url, 'http://127.0.0.1:18029')
  let body = ''
  for await (const chunk of request) { body += chunk }
  response.setHeader('Content-Type', 'application/json')
  response.statusCode = Number(url.searchParams.get('response_status') ?? 200)
  response.end(JSON.stringify({ path: url.pathname, search: url.search, method: request.method, body: body ? JSON.parse(body) : null }))
})
server.listen(18029, '127.0.0.1')
process.on('SIGTERM', () => server.close())

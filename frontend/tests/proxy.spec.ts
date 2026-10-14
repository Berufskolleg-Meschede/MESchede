import { test, expect } from '@playwright/test'

test('Proxy erhält Pfad, Query, Reviewinhalt und Konfliktstatus', async ({ request }) => {
  const list = await request.get('/api/mes/productionorder/?search=Produkt%2042&offset=50')
  expect(list.status()).toBe(200)
  const received = await list.json()
  expect(received).toMatchObject({ path: '/productionorder/', method: 'GET' })
  expect(new URLSearchParams(received.search).get('search')).toBe('Produkt 42')
  expect(new URLSearchParams(received.search).get('offset')).toBe('50')
  const body = { request_id: 'test-request', expected_version: 3, outcome: 'unknown', good_quantity: null }
  const review = await request.post('/api/mes/orders/runs/test-run/reviews?response_status=409', { data: body })
  expect(review.status()).toBe(409)
  expect(await review.json()).toMatchObject({ path: '/orders/runs/test-run/reviews', method: 'POST', body })
  expect(review.headers()['cache-control']).toBe('no-store')
  expect((await request.get('/api/mes/unrelated')).status()).toBe(404)
})

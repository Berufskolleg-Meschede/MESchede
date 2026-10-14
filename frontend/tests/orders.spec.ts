import { test, expect } from '@playwright/test'
import { pageData, overview } from './order-fixtures'
import type { RunReview } from '../lib/types'

for (const [kind, title] of [['production', 'Fertigungsaufträge'], ['delivery', 'Lieferaufträge']] as const) {
  test(`${kind}: getrennte Queues und Prüfung nach Reload`, async ({ page }, testInfo) => {
    const data = pageData(kind)
    const prefix = kind === 'production' ? 'productionorder' : 'deliveryorder'
    await page.route(`**/api/mes/${prefix}/**`, route => route.fulfill({ json: data }))
    await page.goto(kind === 'production' ? '/production-orders' : '/delivery-orders')
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Wartende MES-Aufträge' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Produktqueue dieses Laufs' })).toBeVisible()
    await expect(page.getByText('Laufprüfung erforderlich · neue Starts gesperrt')).toBeVisible()
    await page.reload()
    await expect(page.getByRole('button', { name: 'Lauf prüfen', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Neuer Auftrag' })).toHaveCount(0)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    await page.screenshot({ path: testInfo.outputPath(`${kind}.png`), fullPage: true })
  })
}

test('Dashboard kombiniert beide Bereiche und bleibt lesend', async ({ page }, testInfo) => {
  await page.route('**/api/mes/orders/overview', route => route.fulfill({ json: overview() }))
  await page.goto('/dashboard')
  await expect(page.getByRole('heading', { name: 'Betriebsübersicht' })).toBeVisible()
  await expect(page.getByText('Testdaten-Vorschau · simulierte Aufträge')).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Lieferung #0001 prüfen' })).toHaveAttribute('href', '/delivery-orders#run-delivery-1')
  await expect(page.getByRole('button', { name: /prüfen|speichern|Neuer Auftrag/i })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Fertigungsaufträge' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Lieferaufträge' })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('dashboard.png'), fullPage: true })
})

test('Tastaturprüfung speichert unbekannte Mengen ohne Notiz', async ({ page }, testInfo) => {
  const data = pageData('production')
  let saved: RunReview | undefined
  await page.route('**/api/mes/productionorder/**', route => route.fulfill({ json: data }))
  await page.route('**/api/mes/orders/runs/*/reviews', async route => {
    saved = route.request().postDataJSON()
    data.active[0].review_required = false
    data.active[0].has_manual_review = true
    data.active[0].run_phase = 'completed'
    data.active[0].status = 'completed'
    data.reviews = []
    await route.fulfill({ json: { ...saved, run_id: data.active[0].run_id } })
  })
  await page.goto('/production-orders')
  const trigger = page.getByRole('button', { name: 'Lauf prüfen', exact: true })
  await trigger.focus()
  await page.keyboard.press('Enter')
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByLabel('Erfolgreiche Einheiten')).toHaveValue('')
  await dialog.screenshot({ path: testInfo.outputPath('review.png') })
  await dialog.getByRole('radio', { name: 'Abgeschlossen', exact: true }).focus()
  await page.keyboard.press('Space')
  await dialog.getByRole('button', { name: 'Bewertung speichern' }).focus()
  await page.keyboard.press('Enter')
  await expect(dialog).toHaveCount(0)
  expect(saved).toMatchObject({ outcome: 'completed', good_quantity: null, error_quantity: null, expected_version: 2 })
  expect(Object.keys(saved!)).toEqual(expect.arrayContaining(['request_id']))
  expect(Object.keys(saved!)).not.toContain('note')
  await expect(page.getByText('Manuell bewertet')).toBeVisible()
})

test('Versionskonflikt erhält Eingaben und verlangt explizite Aktualisierung', async ({ page }) => {
  const data = pageData('production')
  const bodies: RunReview[] = []
  await page.route('**/api/mes/productionorder/**', route => {
    const detail = !new URL(route.request().url()).pathname.endsWith('/')
    return route.fulfill({ json: detail ? { ...data.active[0], version: 3 } : data })
  })
  await page.route('**/api/mes/orders/runs/*/reviews', route => {
    bodies.push(route.request().postDataJSON())
    return route.fulfill(bodies.length === 1 ? { status: 409, json: { detail: 'Der Lauf wurde inzwischen geändert.' } } : { json: bodies[1] })
  })
  await page.goto('/production-orders')
  await page.getByRole('button', { name: 'Lauf prüfen', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Erfolgreiche Einheiten').fill('1')
  await dialog.getByRole('button', { name: 'Bewertung speichern' }).click()
  await expect(dialog.getByRole('button', { name: 'Bewertung speichern' })).toBeDisabled()
  await expect(dialog.getByLabel('Erfolgreiche Einheiten')).toHaveValue('1')
  await dialog.getByRole('button', { name: 'Aktuelle Laufdaten übernehmen' }).click()
  await dialog.getByRole('button', { name: 'Bewertung speichern' }).click()
  await expect(dialog).toHaveCount(0)
  expect(bodies.map(body => body.expected_version)).toEqual([2,3])
  expect(bodies[0].request_id).not.toBe(bodies[1].request_id)
})

test('unsichere Speicherantwort wird mit derselben Anfrage-ID wiederholt', async ({ page }) => {
  const data = pageData('delivery')
  const bodies: RunReview[] = []
  await page.route('**/api/mes/deliveryorder/**', route => route.fulfill({ json: data }))
  await page.route('**/api/mes/orders/runs/*/reviews', route => {
    bodies.push(route.request().postDataJSON())
    return route.fulfill(bodies.length === 1 ? { status: 503, json: { detail: 'Antwort verloren' } } : { json: bodies[1] })
  })
  await page.goto('/delivery-orders')
  await page.getByRole('button', { name: 'Lauf prüfen', exact: true }).click()
  const save = page.getByRole('dialog').getByRole('button', { name: 'Bewertung speichern' })
  await save.click()
  await expect(page.getByText('Antwort verloren')).toBeVisible()
  await save.click()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  expect(bodies[0]).toEqual(bodies[1])
})

test('API-Ausfall erhält letzte Daten und kennzeichnet deren Veraltung', async ({ page }) => {
  const data = pageData('production')
  data.stale_after_s = 0.1
  data.source = { ...data.source, last_success_at: new Date(Date.now() - 2000).toISOString() }
  let failed = false
  await page.route('**/api/mes/productionorder/**', route => failed
    ? route.fulfill({ status: 503, json: { detail: 'Backend nicht erreichbar' } }) : route.fulfill({ json: data }))
  await page.goto('/production-orders')
  await expect(page.getByText('Daten veraltet', { exact: true })).toBeVisible()
  failed = true
  await expect(page.getByText(/Die letzten Daten bleiben sichtbar/)).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Produktqueue dieses Laufs' })).toBeVisible()
})

test('Erstausfall zeigt keine erfundenen Aufträge', async ({ page }) => {
  await page.route('**/api/mes/**', route => route.fulfill({ status: 503, json: { detail: 'Backend nicht erreichbar' } }))
  await page.goto('/delivery-orders')
  await expect(page.getByText('Backend nicht erreichbar')).toBeVisible()
  await expect(page.getByRole('button', { name: /Details zu Auftrag/ })).toHaveCount(0)
})

test('Suche und Status senden echte Backendfilter', async ({ page }) => {
  const data = pageData('production')
  const queries: URL[] = []
  await page.route('**/api/mes/productionorder/**', route => {
    const url = new URL(route.request().url())
    queries.push(url)
    return route.fulfill({ json: { ...data, orders: [], filtered_total: 0 } })
  })
  await page.goto('/production-orders')
  await page.getByLabel('Aufträge suchen').fill('Produkt 42')
  await page.getByLabel('Status', { exact: true }).selectOption('completed')
  await expect.poll(() => queries.some(url => url.searchParams.get('search') === 'Produkt 42' && url.searchParams.get('status') === 'completed')).toBe(true)
  await expect(page.getByText('Keine Aufträge für diese Suche gefunden.')).toBeVisible()
})


test('ungültige Gesamtmenge bleibt im Dialog und sendet keine Bewertung', async ({ page }) => {
  let requests = 0
  await page.route('**/api/mes/productionorder/**', route => route.fulfill({ json: pageData('production') }))
  await page.route('**/api/mes/orders/runs/*/reviews', route => {
    requests += 1
    return route.fulfill({ json: {} })
  })
  await page.goto('/production-orders')
  await page.getByRole('button', { name: 'Lauf prüfen', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Erfolgreiche Einheiten').fill('2')
  await dialog.getByLabel('Fehlgeschlagene Einheiten').fill('2')
  await dialog.getByRole('button', { name: 'Bewertung speichern' }).click()
  await expect(dialog.getByRole('alert')).toContainText('überschreitet die Sollmenge')
  await expect(dialog.getByLabel('Erfolgreiche Einheiten')).toHaveAttribute('aria-invalid', 'true')
  expect(requests).toBe(0)
})

import { test, expect, type Page } from '@playwright/test'
import { order, pageData } from './order-fixtures'
import { orderDraft, orderPayload, sameOrder } from '../lib/order-input'
import type { OrderDetailView, OrderInputContext, OrderPayload, OrderType } from '../lib/types'

test.use({ timezoneId: 'America/New_York' })

/** Diese Produkte und Antworten sind ausschließlich synthetische Browserfixtures. */
function inputContext(): OrderInputContext {
  return { available: true, suggested_order_id: '10', suggested_plc_order_number: 20,
    start_date: '2026-10-14', start_time: '08:30:00', plant_timezone: 'Europe/Berlin',
    products: [{ product_id: 1, product_text: 'Testprodukt A' }, { product_id: 42, product_text: 'Testprodukt B' }],
    capacity: 33, observed_at: new Date().toISOString(), error: null, refresh_interval_s: 0.2, stale_after_s: 10 }
}

function detailFor(type: OrderType, payload: OrderPayload): OrderDetailView {
  return { ...order(type, payload.order_id), plc_order_number: payload.mes_auftrag.kopf.Auftragsnummer,
    planned_quantity: payload.mes_auftrag.inhalt.Produktqueue.length, mes_auftrag: payload.mes_auftrag,
    units: payload.mes_auftrag.inhalt.Produktqueue.map((unit, index) => ({ index, product_id: unit.ProduktID,
      product_text: unit.Produkttext, serial_number: unit.Seriennummer, sequence_number: unit.Sequenznummer,
      result: null, raw_status: null, error_code: null })), refresh_interval_s: 0.2, stale_after_s: 10 }
}

async function arrange(page: Page, type: OrderType = 'production') {
  const state: { mode: 'success' | 'lost' | 'missing' | 'check-failure' | 'different' | 'incomplete' | 'reject' | 'hold'
    context: OrderInputContext; stored: OrderDetailView | null; posts: OrderPayload[]; events: string[]; release: () => void } = {
    mode: 'success', context: inputContext(), stored: null, posts: [], events: [], release: () => {},
  }
  await page.route('**/api/mes/orders/input-context?**', route => route.fulfill({ json: {
    ...state.context, observed_at: state.context.available ? new Date().toISOString() : state.context.observed_at,
  } }))
  const prefix = type === 'production' ? 'productionorder' : 'deliveryorder'
  await page.route(`**/api/mes/${prefix}/**`, async route => {
    const request = route.request()
    if (request.method() === 'POST') {
      state.events.push('POST')
      const payload: OrderPayload = request.postDataJSON()
      state.posts.push(payload)
      if (state.mode === 'reject') { return route.fulfill({ status: 409, json: { detail: 'Die PLC-Auftragsnummer ist bereits vergeben.' } }) }
      if (state.mode === 'missing' || state.mode === 'check-failure') { return route.abort('failed') }
      state.stored = detailFor(type, payload)
      if (state.mode === 'different') { state.stored.mes_auftrag = { ...payload.mes_auftrag, kopf: { ...payload.mes_auftrag.kopf, Parameter1: 9 } } }
      if (state.mode === 'incomplete') { delete (state.stored.mes_auftrag.kopf as Partial<OrderPayload['mes_auftrag']['kopf']>).Parameter1 }
      if (state.mode === 'lost' || state.mode === 'different' || state.mode === 'incomplete') { return route.abort('failed') }
      if (state.mode === 'hold') { await new Promise<void>(resolve => { state.release = resolve }) }
      return route.fulfill({ status: 202, json: { queued: true, order_id: payload.order_id,
        order_ref: state.stored.order_ref, run_id: state.stored.run_id, queue_size: 1, accepted_sequence: 10 } })
    }
    const path = new URL(request.url()).pathname
    if (path.endsWith(`/${prefix}/`)) {
      const data = pageData(type)
      if (state.stored) { data.orders = [state.stored]; data.total = 1; data.filtered_total = 1 }
      return route.fulfill({ json: data })
    }
    state.events.push('GET detail')
    if (state.mode === 'check-failure') { return route.fulfill({ status: 503, json: { detail: 'Synthetischer Abgleichausfall' } }) }
    return state.stored ? route.fulfill({ json: state.stored }) : route.fulfill({ status: 404, json: { detail: 'Nicht vorhanden' } })
  })
  await page.goto(type === 'production' ? '/production-orders' : '/delivery-orders')
  return state
}

async function openAndFill(page: Page, mixed = false) {
  await page.getByRole('button', { name: 'Neuer Auftrag', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByLabel('Auftrag-ID', { exact: true })).toHaveValue('10')
  await dialog.getByLabel('Produkt 1', { exact: true }).click()
  await page.getByRole('option', { name: 'Testprodukt A · ID 1', exact: true }).click()
  await dialog.getByLabel('Menge 1 (Stk.)', { exact: true }).fill('2')
  await dialog.getByLabel('Seriennummer ab', { exact: true }).fill('100')
  if (mixed) {
    await dialog.getByRole('button', { name: 'Produkt hinzufügen' }).click()
    await dialog.getByLabel('Produkt 2', { exact: true }).click()
    await page.getByRole('option', { name: 'Testprodukt B · ID 42', exact: true }).click()
    await dialog.getByLabel('Menge 2 (Stk.)', { exact: true }).fill('3')
  }
  return dialog
}

for (const type of ['production', 'delivery'] as const) {
  test(`${type}: gemischter Auftrag wird geprüft und angenommen`, async ({ page }, testInfo) => {
    const state = await arrange(page, type)
    await page.getByLabel('Aufträge suchen').fill('Alte Suche')
    await page.getByLabel('Status', { exact: true }).selectOption('completed')
    const dialog = await openAndFill(page, true)
    await dialog.getByLabel('Auftrag-ID', { exact: true }).fill('UI-Auftrag A')
    await dialog.getByLabel('PLC-Auftragsnummer', { exact: true }).fill('88')
    await dialog.getByLabel('Startdatum', { exact: true }).fill('2026-10-15')
    await dialog.getByLabel('Startzeit', { exact: true }).fill('09:15:30')
    await dialog.getByText('Weitere Angaben', { exact: true }).click()
    await dialog.getByLabel('Priorität', { exact: true }).fill('2')
    await dialog.getByLabel('Parameter 1', { exact: true }).fill('7')
    await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
    await expect(dialog.getByRole('heading', { name: 'Auftrag prüfen', exact: true })).toBeVisible()
    expect(state.posts).toHaveLength(0)
    await expect(dialog.getByText('100 bis 104', { exact: true })).toBeVisible()
    expect(await dialog.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true)
    await page.screenshot({ path: testInfo.outputPath(`manual-${type}-review.png`), fullPage: true })
    await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
    await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
    await expect(page.getByLabel('Aufträge suchen')).toHaveValue('UI-Auftrag A')
    await expect(page.getByLabel('Status', { exact: true })).toHaveValue('all')
    expect(state.posts).toHaveLength(1)
    const body = state.posts[0]
    expect(body.order_id).toBe('UI-Auftrag A')
    expect(body.mes_auftrag.kopf).toMatchObject({ Auftragsnummer: 88, Kundennummer: 0,
      Startdatum: '2026-10-15', Startzeit: '09:15:30', Prioritaet: 2, Parameter0: 0, Parameter1: 7 })
    expect(body.mes_auftrag.inhalt.Produktqueue.map(unit => [unit.ProduktID, unit.Seriennummer])).toEqual([
      [1, 100], [1, 101], [42, 102], [42, 103], [42, 104],
    ])
    await expect(page.getByText('Die Annahme bestätigt noch keinen PLC-Start.', { exact: false })).toBeVisible()
    await page.getByRole('button', { name: 'Auftragsdetails anzeigen' }).click()
    await expect(page.getByRole('dialog').getByText('Wartend', { exact: true })).toBeVisible()
    state.stored!.run_phase = 'running'
    state.stored!.status = 'in_progress'
    state.stored!.started_at = new Date().toISOString()
    await expect(page.getByRole('dialog').getByText('Lauf bestätigt', { exact: true })).toBeVisible()
  })
}

test('Ungültige Menge und Seriennummernüberlauf bleiben vor dem POST sichtbar', async ({ page }) => {
  const state = await arrange(page)
  const dialog = await openAndFill(page)
  await dialog.getByLabel('Menge 1 (Stk.)', { exact: true }).fill('1.5')
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await expect(dialog.getByLabel('Menge 1 (Stk.)', { exact: true })).toBeFocused()
  await expect(dialog.getByText('Bitte eine ganze Zahl zwischen 1 und 33 eingeben.', { exact: true })).toBeVisible()
  await dialog.getByLabel('Menge 1 (Stk.)', { exact: true }).fill('2')
  await dialog.getByLabel('Seriennummer ab', { exact: true }).fill('65535')
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await expect(dialog.getByText(/Seriennummernbereich überschreitet/)).toBeVisible()
  expect(state.posts).toHaveLength(0)
})

test('Doppelklick und Escape während des Sendens verändern keinen Request', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'hold'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).dblclick()
  await expect(dialog.getByRole('button', { name: 'Sendet…', exact: true })).toBeDisabled()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeVisible()
  expect(state.posts).toHaveLength(1)
  state.release()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
})

test('Verlorene Antwort wird ohne zweiten POST aus gespeichertem Inhalt aufgeklärt', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'lost'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
  expect(state.events).toEqual(['POST', 'GET detail'])
  expect(state.posts).toHaveLength(1)
})

test('Detailausfall erhält bestätigte Annahme und letzte Fakten ohne neuen POST', async ({ page }) => {
  const state = await arrange(page)
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Auftragsdetails anzeigen' }).click()
  await expect(page.getByRole('dialog').getByText('Wartend', { exact: true })).toBeVisible()
  state.mode = 'check-failure'
  await expect(page.getByRole('dialog').getByText('Synthetischer Abgleichausfall', { exact: true })).toBeVisible()
  await expect(page.getByRole('dialog').getByText('Wartend', { exact: true })).toBeVisible()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
  expect(state.posts).toHaveLength(1)
})

test('Nach 404 wiederholt die UI exakt denselben Inhalt nach vorherigem GET', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'missing'
  const dialog = await openAndFill(page, true)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByRole('button', { name: 'Denselben Auftrag erneut senden' })).toBeVisible()
  state.mode = 'success'
  await dialog.getByRole('button', { name: 'Denselben Auftrag erneut senden' }).click()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toBeVisible()
  expect(state.posts[1]).toEqual(state.posts[0])
  expect(state.events).toEqual(['POST', 'GET detail', 'POST'])
})

test('Abgleichausfall und Reload erzeugen keinen weiteren POST', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'check-failure'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByText(/Annahme ist noch unklar/)).toBeVisible()
  await expect(dialog.getByRole('button', { name: /erneut senden/ })).toHaveCount(0)
  await page.reload()
  await expect(page.getByRole('dialog').getByText(/Annahme ist noch unklar/)).toBeVisible()
  expect(state.posts).toHaveLength(1)
  expect(state.events).toEqual(['POST', 'GET detail', 'GET detail'])
})

test('Abweichender gespeicherter Kopfwert wird nicht als Annahme übernommen', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'different'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByText(/andere Daten gespeichert/)).toBeVisible()
  await expect(page.getByText('Auftrag angenommen', { exact: true })).toHaveCount(0)
  await expect(dialog.getByRole('button', { name: /erneut senden/ })).toHaveCount(0)
  await dialog.getByRole('button', { name: 'Entwurf korrigieren', exact: true }).click()
  await expect(dialog.getByLabel('Auftrag-ID', { exact: true })).toHaveValue('10')
  expect(state.posts).toHaveLength(1)
})

test('Belegter Konflikt erhält bearbeitbare Eingaben', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'reject'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByText('Die PLC-Auftragsnummer ist bereits vergeben.', { exact: true })).toBeVisible()
  await expect(dialog.getByLabel('Seriennummer ab', { exact: true })).toHaveValue('100')
  await expect(dialog.getByLabel('PLC-Auftragsnummer', { exact: true })).toBeEnabled()
})

test('Unvollständiger Detailinhalt bleibt unklar und gibt keinen neuen Entwurf frei', async ({ page }) => {
  const state = await arrange(page)
  state.mode = 'incomplete'
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByText(/Annahme ist noch unklar/)).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Entwurf korrigieren', exact: true })).toHaveCount(0)
  await expect(dialog.getByRole('button', { name: /erneut senden/ })).toHaveCount(0)
  expect(state.posts).toHaveLength(1)
})

test('Während ausbleibender Aktualisierung sperren veraltete Katalogdaten den Prüfschritt', async ({ page }) => {
  const state = await arrange(page)
  state.context.refresh_interval_s = 5
  state.context.stale_after_s = 0.1
  await page.getByRole('button', { name: 'Neuer Auftrag', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByText('Die Produktdaten sind veraltet. Bitte erneut laden.', { exact: true })).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' })).toBeDisabled()
  expect(state.posts).toHaveLength(0)
})

test('Unbekannter Katalog sperrt die Erfassung ohne Ersatzprodukte', async ({ page }) => {
  const state = await arrange(page)
  state.context = { ...state.context, available: false, products: [], capacity: null, error: 'Produktkatalog nicht verfügbar.' }
  await page.getByRole('button', { name: 'Neuer Auftrag', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByText('Produktkatalog nicht verfügbar.', { exact: true })).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' })).toBeDisabled()
  expect(state.posts).toHaveLength(0)
})

test('Produktabgleich lädt den SPS-Katalog ohne einen Auftrag zu senden', async ({ page }) => {
  const state = await arrange(page)
  let syncs = 0
  await page.route('**/api/mes/orders/catalog/sync?**', async route => {
    expect(route.request().method()).toBe('POST')
    syncs += 1
    state.context = { ...inputContext(), products: [{ product_id: 7, product_text: 'Neu abgeglichen' }] }
    await route.fulfill({ json: state.context })
  })
  await page.getByRole('button', { name: 'Neuer Auftrag', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: 'Produktdaten abgleichen', exact: true }).click()
  await dialog.getByLabel('Produkt 1', { exact: true }).click()
  await expect(page.getByRole('option', { name: 'Neu abgeglichen · ID 7', exact: true })).toBeVisible()
  expect(syncs).toBe(1)
  expect(state.posts).toHaveLength(0)
})

test('Speicherfehler verhindert den ersten POST', async ({ page }) => {
  await page.addInitScript(() => { Storage.prototype.setItem = () => { throw new Error('Synthetischer Speicherfehler') } })
  const state = await arrange(page)
  const dialog = await openAndFill(page)
  await dialog.getByRole('button', { name: 'Zusammenfassung anzeigen' }).click()
  await dialog.getByRole('button', { name: 'Auftrag annehmen', exact: true }).click()
  await expect(dialog.getByText(/Es wurde nichts gesendet/)).toBeVisible()
  expect(state.posts).toHaveLength(0)
})

test('Enter im Erfassungsschritt bestätigt keinen Auftrag und Abbrechen stellt Fokus wieder her', async ({ page }) => {
  const state = await arrange(page)
  const dialog = await openAndFill(page)
  await dialog.getByLabel('Auftrag-ID', { exact: true }).press('Enter')
  await expect(dialog.getByRole('heading', { name: 'Auftrag prüfen', exact: true })).toBeVisible()
  expect(state.posts).toHaveLength(0)
  await dialog.getByRole('button', { name: 'Abbrechen', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Neuer Auftrag', exact: true })).toBeFocused()
})

test('Queueaufbau und kompletter Inhaltsvergleich beachten alle wirksamen Werte', () => {
  const context = inputContext()
  const draft = orderDraft(context)
  draft.rows = [{ key: 0, product: '1', quantity: '2' }, { key: 1, product: '42', quantity: '1' }]
  draft.serial_start = '65533'
  const result = orderPayload(draft, context)
  expect(result.errors).toEqual({})
  expect(result.payload!.mes_auftrag.inhalt.Produktqueue.map(unit => unit.Seriennummer)).toEqual([65533, 65534, 65535])
  const detail = detailFor('production', result.payload!)
  expect(sameOrder(result.payload!, detail)).toBe(true)
  detail.mes_auftrag = { ...detail.mes_auftrag, kopf: { ...detail.mes_auftrag.kopf, Kundennummer: 7 } }
  expect(sameOrder(result.payload!, detail)).toBe(false)
})

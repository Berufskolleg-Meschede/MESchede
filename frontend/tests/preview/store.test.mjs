import { test } from 'node:test'
import assert from 'node:assert/strict'
import { PreviewOrderStore } from './store.mts'

function request(store, changes = {}) {
  const run = store.overview().reviews[0]
  return { runId: run.run_id, body: { request_id: crypto.randomUUID(), expected_version: run.version, outcome: 'completed', good_quantity: 2, error_quantity: 1, ...changes } }
}

test('Vorschau besitzt einen reservierten Lauf und typspezifische FIFO-Ansichten', () => {
  const store = new PreviewOrderStore()
  const overview = store.overview()
  assert.equal(overview.active.length,1)
  assert.equal(overview.combined.total,6)
  assert.deepEqual(overview.waiting.map(item => item.queue_position),[1,2,3])
  assert.equal(overview.waiting[0].order_type,'delivery')
  assert.ok(store.page('production',new URLSearchParams()).orders.every(item => item.order_type === 'production'))
  assert.equal(store.page('delivery',new URLSearchParams()).reviews[0].order_type,'production')
})

test('Bewertung ist idempotent und überschreibt keine neue Version', () => {
  const store = new PreviewOrderStore()
  const { runId,body } = request(store)
  const first = store.review(runId,body)
  assert.deepEqual(store.review(runId,body),first)
  assert.equal(store.overview().active[0].version,body.expected_version+1)
  assert.equal(store.overview().active[0].processed_quantity,3)
  assert.equal(store.overview().active[0].units.filter(unit => unit.result !== null).length,2)
  assert.throws(() => store.review(runId,{ ...body,request_id:crypto.randomUUID() }),{ status:409 })
  assert.equal(store.overview().dispatch.blocked,true)
})

test('Unklar und widersprüchliche Mengen bleiben erkennbar', () => {
  const store = new PreviewOrderStore()
  const { runId,body } = request(store,{ outcome:'unknown',good_quantity:null,error_quantity:null })
  store.review(runId,body)
  assert.equal(store.overview().reviews.length,1)
  assert.equal(store.overview().active[0].good_quantity,1)
  const changed = { ...body,request_id:crypto.randomUUID(),expected_version:store.overview().active[0].version,good_quantity:0 }
  assert.throws(() => store.review(runId,changed),{ status:422 })
  assert.throws(() => store.review(runId,{ ...changed,good_quantity:2,error_quantity:3 }),{ status:422 })
})

test('Zurücksetzen entfernt Bewertungen und alte Laufreferenzen', () => {
  const store = new PreviewOrderStore()
  const { runId,body } = request(store)
  store.review(runId,body)
  store.reset()
  assert.equal(store.overview().reviews.length,1)
  assert.equal(store.overview().active[0].version,1)
  assert.notEqual(store.overview().active[0].run_id,runId)
  assert.throws(() => store.review(runId,body),{ status:404 })
})

test('Suche und Status werden vor der Pagination kombiniert', () => {
  const store = new PreviewOrderStore()
  const page = store.page('production',new URLSearchParams({ search:' DEMO-P-1003 ',status:'pending',limit:'1' }))
  assert.equal(page.filtered_total,1)
  assert.equal(page.orders[0].order_id,'DEMO-P-1003')
  assert.equal(page.summary.total,3)
})

import type { OrderInputContext, OrderPayload, OrderDetailView } from './types'

export interface ProductRow { key: number; product: string; quantity: string }
export interface OrderDraft {
  order_id: string; plc_number: string; serial_start: string; start_date: string; start_time: string
  customer: string; priority: string; parameter_zero: string; parameter_one: string; rows: ProductRow[]
}
export type InputErrors = Record<string, string>

/** Initialisiert nur einen neuen Entwurf; erneutes Laden überschreibt keine Eingaben. */
export function orderDraft(context: OrderInputContext): OrderDraft {
  return {
    order_id: context.suggested_order_id ?? '', plc_number: context.suggested_plc_order_number?.toString() ?? '',
    serial_start: '0', start_date: context.start_date, start_time: context.start_time,
    customer: '', priority: '1', parameter_zero: '0', parameter_one: '0',
    rows: [{ key: 0, product: '', quantity: '1' }],
  }
}

/** Prüft ganze Eingaben und baut dieselbe Queue deterministisch in sichtbarer Reihenfolge. */
export function orderPayload(draft: OrderDraft, context: OrderInputContext): { payload: OrderPayload | null; errors: InputErrors } {
  const errors: InputErrors = {}
  function integer(key: string, value: string, min: number, max: number) {
    const number = Number(value)
    if (!/^\d+$/.test(value) || !Number.isSafeInteger(number) || number < min || number > max) {
      errors[key] = `Bitte eine ganze Zahl zwischen ${min} und ${max} eingeben.`
    }
    return number
  }
  const id = draft.order_id.trim()
  if (!id || id.length > 200) { errors.order_id = 'Bitte eine Auftrag-ID mit 1 bis 200 Zeichen eingeben.' }
  if (['.', '..', 'queue-status'].includes(id)) { errors.order_id = 'Diese Auftrag-ID ist reserviert. Bitte eine andere ID wählen.' }
  const number = integer('plc_number', draft.plc_number, 0, 65535)
  const serial = integer('serial_start', draft.serial_start, 0, 65535)
  const customer = integer('customer', draft.customer || '0', 0, 65535)
  const priority = integer('priority', draft.priority, 0, 2)
  const parameterZero = integer('parameter_zero', draft.parameter_zero, 0, 255)
  const parameterOne = integer('parameter_one', draft.parameter_one, 0, 255)
  const date = new Date(`${draft.start_date}T00:00:00Z`)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(draft.start_date) || !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== draft.start_date || draft.start_date < '1990-01-01' || draft.start_date > '2168-12-31') {
    errors.start_date = 'Bitte ein gültiges Datum zwischen 01.01.1990 und 31.12.2168 eingeben.'
  }
  if (!/^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$/.test(draft.start_time)) {
    errors.start_time = 'Bitte eine lokale Uhrzeit ohne Zeitzonenoffset eingeben.'
  }
  const quantities = draft.rows.map((row, index) => integer(`quantity.${index}`, row.quantity, 1, context.capacity ?? 255))
  draft.rows.forEach((row, index) => {
    if (!context.products.some(item => String(item.product_id) === row.product)) {
      errors[`product.${index}`] = 'Bitte ein verfügbares Produkt auswählen.'
    }
  })
  const total = quantities.reduce((sum, value) => sum + value, 0)
  if (!draft.rows.length || !context.available || context.capacity === null || total > context.capacity) {
    errors.products = context.error ?? `Die Gesamtmenge darf höchstens ${context.capacity ?? 0} Stück betragen.`
  }
  if (serial + total - 1 > 65535) { errors.serial_start = 'Der Seriennummernbereich überschreitet 65535. Bitte die Startnummer oder Menge ändern.' }
  if (Object.keys(errors).length) { return { payload: null, errors } }
  const queue: OrderPayload['mes_auftrag']['inhalt']['Produktqueue'] = []
  draft.rows.forEach((row, index) => {
    const product = context.products.find(item => String(item.product_id) === row.product)!
    for (let unit = 0; unit < quantities[index]; unit++) {
      queue.push({ ProduktID: product.product_id, Produkttext: product.product_text,
        Seriennummer: serial + queue.length, Sequenznummer: 0, Takt: 0 })
    }
  })
  return { errors, payload: { order_id: id, mes_auftrag: {
    kopf: { Auftragsnummer: number, Kundennummer: customer, Startdatum: draft.start_date,
      Startzeit: draft.start_time.length === 5 ? `${draft.start_time}:00` : draft.start_time,
      Prioritaet: priority, Parameter0: parameterZero, Parameter1: parameterOne },
    inhalt: { SeriennummerStart: serial, Produktqueue: queue },
  } } }
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) { return `[${value.map(canonical).join(',')}]` }
  if (value !== null && typeof value === 'object') {
    return `{${Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`).join(',')}}`
  }
  return JSON.stringify(value)
}

/** Vergleicht alle gespeicherten Kopfdaten und Einheiten, einschließlich ihrer Reihenfolge. */
export function sameOrder(payload: OrderPayload, detail: OrderDetailView): boolean {
  return detail.order_id === payload.order_id && canonical(detail.mes_auftrag) === canonical(payload.mes_auftrag)
}

/** Ein unvollständiger Detailvertrag ist kein Nachweis für einen abweichenden gespeicherten Auftrag. */
export function completeOrderInput(value: unknown): boolean {
  if (!value || typeof value !== 'object') { return false }
  const input = value as Partial<OrderPayload['mes_auftrag']>
  const head = input.kopf
  const content = input.inhalt
  if (!head || !content || !Array.isArray(content.Produktqueue) || !content.Produktqueue.length) { return false }
  const numbers = [head.Auftragsnummer, head.Kundennummer, head.Prioritaet, head.Parameter0, head.Parameter1, content.SeriennummerStart]
  return numbers.every(Number.isSafeInteger) && typeof head.Startdatum === 'string' && typeof head.Startzeit === 'string' &&
    content.Produktqueue.every(unit => unit && typeof unit.Produkttext === 'string' &&
      [unit.ProduktID, unit.Seriennummer, unit.Sequenznummer, unit.Takt].every(Number.isSafeInteger))
}

/** Ordnet Backend-Payloadpfade den Feldern und expandierten Produktzeilen zu. */
export function inputFieldErrors(fields: { loc: (string | number)[]; msg: string }[], draft: OrderDraft): InputErrors {
  const mapping: Record<string, string> = { order_id: 'order_id', Auftragsnummer: 'plc_number',
    SeriennummerStart: 'serial_start', Startdatum: 'start_date', Startzeit: 'start_time', Kundennummer: 'customer',
    Prioritaet: 'priority', Parameter0: 'parameter_zero', Parameter1: 'parameter_one' }
  const errors: InputErrors = {}
  for (const field of fields) {
    const queueAt = field.loc.indexOf('Produktqueue')
    let key = mapping[String(field.loc.at(-1))] ?? 'products'
    if (queueAt >= 0 && typeof field.loc[queueAt + 1] === 'number') {
      const unit = Number(field.loc[queueAt + 1])
      let end = 0
      const row = draft.rows.findIndex(item => { end += Number(item.quantity); return unit < end })
      key = `product.${Math.max(0, row)}`
    }
    errors[key] = field.msg.startsWith('Value error, ') ? field.msg.slice(13) :
      /[äöüß]|Bitte|Produkt|Start/.test(field.msg) ? field.msg : 'Dieser Wert ist ungültig. Bitte die Eingabe prüfen.'
  }
  return errors
}

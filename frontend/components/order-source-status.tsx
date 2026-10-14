import type { SourceStatus } from '@/lib/types'
import { timestamp } from '@/lib/order-format'

export function OrderSourceStatus({ source, staleAfter, checkedAt, label = 'Steuerungsrückmeldungen' }: {
  source: SourceStatus; staleAfter: number; checkedAt: number; label?: string
}) {
  const old = source.last_success_at !== null && checkedAt - Date.parse(source.last_success_at) > staleAfter * 1000
  const text = source.connection_status === 'disconnected' ? 'Verbindung unterbrochen' :
    source.freshness === 'unknown' ? 'Noch keine bestätigten Daten' :
    old || source.freshness === 'stale' ? 'Daten veraltet' : 'Daten aktuell'

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
      <p>{label}: <span className="text-foreground">{text}</span></p>
      <p>Letzte Rückmeldung: {timestamp(source.last_success_at)}</p>
    </div>
  )
}

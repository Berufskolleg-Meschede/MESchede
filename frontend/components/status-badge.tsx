import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

const STATUS: Record<string, { dot: string; label: string }> = {
  pending: { dot: 'bg-status-waiting', label: 'Ausstehend' },
  in_progress: { dot: 'bg-status-running', label: 'In Bearbeitung' },
  error: { dot: 'bg-destructive', label: 'Fehler' },
  completed: { dot: 'bg-status-success', label: 'Abgeschlossen' },
  online: { dot: 'bg-status-success', label: 'Online' },
  offline: { dot: 'bg-muted-foreground', label: 'Offline' },
  review_required: { dot: 'bg-status-waiting', label: 'Prüfung erforderlich' },
  good: { dot: 'bg-status-success', label: 'Erfolgreich' },
  failed: { dot: 'bg-destructive', label: 'Fehlgeschlagen' },
  unknown: { dot: 'bg-muted-foreground', label: 'Unbekannt' },
}

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS[status] ?? { dot: 'bg-muted-foreground', label: status }
  return (
    <Badge variant="status">
      <span aria-hidden="true" className={cn('size-1.5 shrink-0 rounded-full', config.dot)} />
      {config.label}
    </Badge>
  )
}

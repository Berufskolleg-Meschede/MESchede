import { cn } from '@/lib/utils'

const STATUS: Record<string, { dot: string; label: string }> = {
  pending: { dot: 'bg-[#c7b485]', label: 'Ausstehend' },
  in_progress: { dot: 'bg-[#92afbc]', label: 'In Bearbeitung' },
  error: { dot: 'bg-[#e79b93]', label: 'Fehler' },
  completed: { dot: 'bg-[#9eb5a1]', label: 'Abgeschlossen' },
  online: { dot: 'bg-[#9eb5a1]', label: 'Online' },
  offline: { dot: 'bg-[#939c95]', label: 'Offline' },
}

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS[status] ?? { dot: 'bg-muted-foreground', label: status }
  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap text-xs text-foreground">
      <span aria-hidden="true" className={cn('size-1.5 shrink-0 rounded-full', config.dot)} />
      {config.label}
    </span>
  )
}

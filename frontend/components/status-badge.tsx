import { cn } from '@/lib/utils'

interface StatusConfig {
  dot: string
  text: string
  bg: string
  border: string
  glow?: string
  pulse?: boolean
  label: string
}

const STATUS: Record<string, StatusConfig> = {
  pending: {
    dot: 'bg-amber-400',
    text: 'text-amber-300',
    bg: 'bg-amber-500/8',
    border: 'border-amber-500/20',
    label: 'Ausstehend',
  },
  in_progress: {
    dot: 'bg-cyan-400',
    text: 'text-cyan-300',
    bg: 'bg-cyan-500/8',
    border: 'border-cyan-500/20',
    glow: 'shadow-[0_0_8px_rgba(34,211,238,0.45)]',
    pulse: true,
    label: 'In Bearbeitung',
  },
  error: {
    dot: 'bg-red-400',
    text: 'text-red-300',
    bg: 'bg-red-500/8',
    border: 'border-red-500/20',
    glow: 'shadow-[0_0_6px_rgba(248,113,113,0.4)]',
    label: 'Fehler',
  },
  completed: {
    dot: 'bg-emerald-400',
    text: 'text-emerald-300',
    bg: 'bg-emerald-500/8',
    border: 'border-emerald-500/20',
    label: 'Abgeschlossen',
  },
  online: {
    dot: 'bg-emerald-400',
    text: 'text-emerald-300',
    bg: 'bg-emerald-500/8',
    border: 'border-emerald-500/20',
    glow: 'shadow-[0_0_8px_rgba(52,211,153,0.4)]',
    pulse: true,
    label: 'Online',
  },
  offline: {
    dot: 'bg-zinc-500',
    text: 'text-zinc-400',
    bg: 'bg-zinc-500/8',
    border: 'border-zinc-500/20',
    label: 'Offline',
  },
}

export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS[status] ?? {
    dot: 'bg-zinc-500',
    text: 'text-zinc-400',
    bg: 'bg-zinc-500/8',
    border: 'border-zinc-500/20',
    label: status,
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs border font-mono',
        cfg.bg,
        cfg.border,
        cfg.text,
        cfg.glow
      )}
    >
      <span
        className={cn('w-1.5 h-1.5 rounded-full shrink-0', cfg.dot, cfg.pulse && 'led-pulse')}
      />
      {cfg.label}
    </span>
  )
}

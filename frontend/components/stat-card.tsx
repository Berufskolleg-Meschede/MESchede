import { cn } from '@/lib/utils'

type Accent = 'orange' | 'blue' | 'green' | 'red' | 'amber'

interface StatCardProps {
  label: string
  value: string | number
  accent?: Accent
  delay?: number
}

const ACCENT: Record<Accent, { stripe: string; value: string }> = {
  orange: { stripe: 'bg-orange-400', value: 'text-orange-300' },
  blue:   { stripe: 'bg-blue-400',   value: 'text-blue-300' },
  green:  { stripe: 'bg-emerald-400', value: 'text-emerald-300' },
  red:    { stripe: 'bg-red-400',    value: 'text-red-300' },
  amber:  { stripe: 'bg-amber-400',  value: 'text-amber-300' },
}

export function StatCard({ label, value, accent = 'orange', delay = 0 }: StatCardProps) {
  const a = ACCENT[accent]
  return (
    <div
      className="relative bg-card border border-border rounded-lg p-5 overflow-hidden animate-card"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Left accent stripe */}
      <div className={cn('absolute left-0 top-4 bottom-4 w-0.5 rounded-r-full', a.stripe)} />

      <p className="text-muted-foreground text-[10px] uppercase tracking-[0.15em] font-mono pl-3">
        {label}
      </p>
      <p className={cn('font-display text-5xl font-bold leading-none mt-2 pl-3', a.value)}>
        {value}
      </p>
    </div>
  )
}

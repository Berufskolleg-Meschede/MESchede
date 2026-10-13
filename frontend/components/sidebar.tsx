'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Factory, Truck, ChartLine, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/dashboard', label: 'Übersicht', icon: LayoutDashboard },
  { href: '/production-orders', label: 'Fertigungsaufträge', icon: Factory },
  { href: '/delivery-orders', label: 'Lieferaufträge', icon: Truck },
  { href: '/settings', label: 'Einstellungen', icon: Settings },
  { href: '/analytics', label: 'Analysen', icon: ChartLine },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="flex shrink-0 flex-col border-b border-sidebar-border bg-sidebar md:w-60 md:border-r md:border-b-0">
      <div className="px-5 py-6 md:py-7">
        <p className="text-lg font-semibold tracking-tight">MESchede<span className="ml-2 text-xs font-normal text-muted-foreground">MES</span></p>
        <p className="mt-1 text-xs text-muted-foreground">Berufskolleg Meschede</p>
      </div>
      <nav aria-label="Hauptnavigation" className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-1 md:flex-col md:justify-start">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href)
          return (
            <Link key={href} href={href} aria-current={active ? 'page' : undefined}
              className={cn('flex shrink-0 items-center gap-3 rounded-sm px-3 py-2.5 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring',
                active ? 'bg-sidebar-accent font-medium text-foreground' : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground')}>
              <Icon size={16} strokeWidth={1.5} aria-hidden="true" />{label}
            </Link>
          )
        })}
      </nav>
      <div className="hidden border-t border-sidebar-border px-5 py-4 text-xs text-muted-foreground md:block">
        Fertigungssteuerung
      </div>
    </aside>
  )
}

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Factory, Truck } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/production-orders', label: 'Produktion', icon: Factory },
  { href: '/delivery-orders', label: 'Lieferung', icon: Truck },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-56 flex flex-col shrink-0 bg-sidebar border-r border-sidebar-border">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-sidebar-border">
        <p className="font-display text-2xl font-bold tracking-tight text-foreground leading-none">
          MES<span className="text-primary">chede</span>
        </p>
        <p className="text-muted-foreground text-[10px] uppercase tracking-[0.2em] mt-1.5 font-mono">
          Fertigungssteuerung
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'relative flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-150',
                active
                  ? 'text-primary bg-primary/8 font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/60'
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-primary rounded-r-full" />
              )}
              <Icon size={16} strokeWidth={active ? 2 : 1.5} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-sidebar-border">
        <p className="text-muted-foreground text-[10px] uppercase tracking-[0.15em] font-mono">
          BK Meschede
        </p>
      </div>
    </aside>
  )
}

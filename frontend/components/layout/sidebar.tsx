"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  LayoutGrid,
  Box,
  TrendingUp,
  BarChart3,
  Package,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

const NAVIGATION_ITEMS = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutGrid,
  },
  {
    label: "Production Orders",
    href: "/production-orders",
    icon: Box,
  },
  {
    label: "Delivery Orders",
    href: "/delivery-orders",
    icon: TrendingUp,
  },
  {
    label: "Inventory",
    href: "/inventory",
    icon: BarChart3,
  },
  {
    label: "Articles",
    href: "/articles",
    icon: Package,
  },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = React.useState(false)
  const pathname = usePathname()

  return (
    <div className={cn(
      "bg-sidebar border-r border-sidebar-border transition-all duration-300 flex flex-col",
      collapsed ? "w-20" : "w-64"
    )}>
      {/* Header */}
      <div className="h-16 border-b border-sidebar-border flex items-center justify-between px-4">
        {!collapsed && <h2 className="font-bold text-sidebar-foreground">Navigation</h2>}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAVIGATION_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))

          return (
            <Link key={item.href} href={item.href}>
              <Button
                variant={isActive ? "default" : "ghost"}
                className={cn(
                  "w-full justify-start gap-3 font-normal",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Button>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-border p-4">
        <p className="text-xs text-sidebar-foreground/60">
          {!collapsed && "Version 1.0"}
        </p>
      </div>
    </div>
  )
}

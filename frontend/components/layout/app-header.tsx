"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"

export function AppHeader() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <header className="border-b border-border bg-card h-16 flex items-center justify-between px-6">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-bold text-foreground">MES</h1>
        <span className="text-sm text-muted-foreground">Manufacturing Execution System</span>
      </div>

      {mounted && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun data-icon="inline-start" /> : <Moon data-icon="inline-start" />}
        </Button>
      )}
    </header>
  )
}

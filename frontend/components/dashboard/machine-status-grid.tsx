"use client"

import * as React from "react"
import { Card } from "@/components/ui/card"
import { StatusDot } from "@/components/ui/status-badge"

// Mock machine data for now
const MOCK_MACHINES = [
  { id: 1, name: "Press Machine A", status: "ONLINE" as const },
  { id: 2, name: "CNC Machine B", status: "ONLINE" as const },
  { id: 3, name: "Conveyor C", status: "OFFLINE" as const },
  { id: 4, name: "Assembly Robot D", status: "ONLINE" as const },
]

export function MachineStatusGrid() {
  return (
    <Card className="p-6 border border-border">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
        Machine Status
      </h3>

      <div className="grid grid-cols-2 gap-4">
        {MOCK_MACHINES.map((machine) => (
          <div
            key={machine.id}
            className="flex items-center gap-3 p-3 border border-border hover:bg-muted/50 transition-colors"
          >
            <StatusDot status={machine.status} size="md" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">{machine.name}</p>
              <p className="text-xs text-muted-foreground">
                {machine.status === "ONLINE" ? "Connected" : "Disconnected"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

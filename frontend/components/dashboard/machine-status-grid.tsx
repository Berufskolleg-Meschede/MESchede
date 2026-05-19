"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
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
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wide">Machine Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {MOCK_MACHINES.map((machine) => (
            <div key={machine.id} className="flex items-center gap-3 p-3 rounded-md">
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
      </CardContent>
    </Card>
  )
}

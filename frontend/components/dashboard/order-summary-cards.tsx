"use client"

import * as React from "react"
import { Card } from "@/components/ui/card"
import { useOrderStats } from "@/hooks/use-orders"

export function OrderSummaryCards() {
  const stats = useOrderStats()

  const cards = [
    {
      label: "Production Orders",
      value: stats.production.total,
      subItems: [
        { label: "Pending", value: stats.production.pending, color: "text-amber-400" },
        { label: "In Progress", value: stats.production.inProgress, color: "text-blue-400" },
        { label: "Completed", value: stats.production.completed, color: "text-green-400" },
      ],
    },
    {
      label: "Delivery Orders",
      value: stats.delivery.total,
      subItems: [
        { label: "Pending", value: stats.delivery.pending, color: "text-amber-400" },
        { label: "In Progress", value: stats.delivery.inProgress, color: "text-blue-400" },
        { label: "Completed", value: stats.delivery.completed, color: "text-green-400" },
      ],
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {cards.map((card) => (
        <Card key={card.label} className="p-6 border border-border">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            {card.label}
          </h3>
          <div className="mt-4 mb-6">
            <p className="text-4xl font-bold text-foreground">{card.value}</p>
          </div>
          <div className="grid grid-cols-3 gap-4 text-xs">
            {card.subItems.map((item) => (
              <div key={item.label}>
                <p className="text-muted-foreground">{item.label}</p>
                <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  )
}

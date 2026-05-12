"use client"

import * as React from "react"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useInventoryAlerts } from "@/hooks/use-orders"
import { AlertCircle } from "lucide-react"

export function InventoryAlerts() {
  const alerts = useInventoryAlerts(50)

  return (
    <Card className="p-6 border border-border">
      <div className="flex items-center gap-2 mb-4">
        <AlertCircle className="h-5 w-5 text-amber-500" />
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Low Stock Alerts
        </h3>
      </div>

      {alerts.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4">All inventory levels are adequate.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
                Article
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
                Current Qty
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
                Threshold
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow
                key={alert.article.id}
                className="border-border hover:bg-muted/50 bg-red-950/20"
              >
                <TableCell className="text-sm font-medium text-foreground">
                  {alert.article.name}
                </TableCell>
                <TableCell className="text-sm font-mono text-red-400">
                  {alert.currentQty}
                </TableCell>
                <TableCell className="text-sm font-mono text-muted-foreground">
                  {alert.threshold}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  )
}

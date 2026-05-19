"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle />
          <CardTitle className="text-sm uppercase tracking-wide">Low Stock Alerts</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
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
              <TableRow key={alert.article.id} className="border-border hover:bg-transparent">
                <TableCell className="text-sm font-medium text-foreground">
                  {alert.article.name}
                </TableCell>
                <TableCell className="text-sm">
                  <Badge variant="destructive" className="font-mono">{alert.currentQty}</Badge>
                </TableCell>
                <TableCell className="text-sm font-mono text-muted-foreground">
                  {alert.threshold}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        )}
      </CardContent>
    </Card>
  )
}

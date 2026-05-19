"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { StatusBadge } from "@/components/ui/status-badge"
import { useRecentOrders } from "@/hooks/use-orders"

export function RecentOrders() {
  const orders = useRecentOrders(10)

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wide">Recent Orders</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Type
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Article
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Qty
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Status
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground text-right">
              Time
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id} className="border-border">
              <TableCell className="text-xs font-mono text-muted-foreground">
                {order.type === "production" ? "PROD" : "DELV"}
              </TableCell>
              <TableCell className="text-sm text-foreground">{order.article}</TableCell>
              <TableCell className="text-sm font-mono text-foreground">{order.quantity}</TableCell>
              <TableCell>
                <StatusBadge status={order.status} />
              </TableCell>
              <TableCell className="text-xs text-muted-foreground text-right">
                {formatDate(order.createdAt)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      </CardContent>
    </Card>
  )
}

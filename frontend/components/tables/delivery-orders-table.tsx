"use client"

import * as React from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { StatusBadge } from "@/components/ui/status-badge"
import { Button } from "@/components/ui/button"
import { Trash2, Edit } from "lucide-react"
import { useDeliveryOrders } from "@/hooks/use-orders"

export function DeliveryOrdersTable() {
  const { data: orders, isLoading } = useDeliveryOrders()

  if (isLoading) {
    return <div className="text-center py-8 text-muted-foreground">Loading orders...</div>
  }

  return (
    <div className="border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-b border-border hover:bg-transparent bg-muted/20">
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Order ID
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Article ID
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Quantity
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Status
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Created
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase text-muted-foreground">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id} className="border-b border-border hover:bg-muted/50">
              <TableCell className="text-sm font-mono text-foreground font-semibold">
                #{order.id}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">{order.article_id}</TableCell>
              <TableCell className="text-sm font-mono text-foreground">{order.quantity}</TableCell>
              <TableCell>
                <StatusBadge status={order.status} />
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {order.created_at ? new Date(order.created_at).toLocaleDateString() : "-"}
              </TableCell>
              <TableCell className="flex gap-2">
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-red-400">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {orders.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">No delivery orders found.</div>
      )}
    </div>
  )
}

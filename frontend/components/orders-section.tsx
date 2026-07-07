'use client'

import { useState, useEffect } from 'react'
import {
  Plus, MoreHorizontal, Pencil, Trash2,
  Clock, Activity, AlertCircle, CheckCircle2,
} from 'lucide-react'
import { api } from '@/lib/api'
import type { ProductionOrder, DeliveryOrder, Article, OrderFormData, OrderStatus } from '@/lib/types'
import { StatusBadge } from './status-badge'
import { StatCard } from './stat-card'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type Order = ProductionOrder | DeliveryOrder

interface OrdersSectionProps {
  type: 'production' | 'delivery'
  title: string
}

const ORDER_STATUSES: OrderStatus[] = ['pending', 'in_progress', 'error', 'completed']

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: 'Ausstehend',
  in_progress: 'In Bearbeitung',
  error: 'Fehler',
  completed: 'Abgeschlossen',
}

export function OrdersSection({ type, title }: OrdersSectionProps) {
  const [orders, setOrders] = useState<Order[]>([])
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingOrder, setEditingOrder] = useState<Order | null>(null)
  const [form, setForm] = useState<OrderFormData>({
    quantity: 1,
    status: 'pending',
    article_id: 0,
  })

  const ordersApi = type === 'production' ? api.productionOrders : api.deliveryOrders

  useEffect(() => {
    setLoading(true)
    Promise.all([ordersApi.list(), api.articles.list()]).then(
      ([ordersData, articlesData]) => {
        setOrders(ordersData)
        setArticles(articlesData)
        if (articlesData.length > 0) {
          setForm(f => ({ ...f, article_id: articlesData[0].id }))
        }
        setLoading(false)
      }
    )
  }, [type])

  const openCreate = () => {
    setEditingOrder(null)
    setForm({ quantity: 1, status: 'pending', article_id: articles[0]?.id ?? 0 })
    setDialogOpen(true)
  }

  const openEdit = (order: Order) => {
    setEditingOrder(order)
    setForm({ quantity: order.quantity, status: order.status, article_id: order.article_id })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    if (editingOrder) {
      const updated = await ordersApi.update(editingOrder.id, form)
      setOrders(prev => prev.map(o => (o.id === editingOrder.id ? updated : o)))
    } else {
      const created = await ordersApi.create(form)
      setOrders(prev => [...prev, created])
    }
    setDialogOpen(false)
  }

  const handleDelete = async (id: number) => {
    await ordersApi.delete(id)
    setOrders(prev => prev.filter(o => o.id !== id))
  }

  const counts = {
    pending: orders.filter(o => o.status === 'pending').length,
    in_progress: orders.filter(o => o.status === 'in_progress').length,
    error: orders.filter(o => o.status === 'error').length,
    completed: orders.filter(o => o.status === 'completed').length,
  }

  return (
    <div className="p-8 space-y-8 max-w-5xl">
      {/* Header */}
      <div className="flex items-end justify-between animate-card">
        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-foreground">
            {title}
          </h1>
          <p className="text-muted-foreground text-sm font-mono mt-1">
            {orders.length} Aufträge gesamt
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-primary text-primary-foreground hover:bg-primary/85 gap-1.5 font-medium"
        >
          <Plus size={15} />
          Neuer Auftrag
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Ausstehend"    value={counts.pending}    accent="amber"  delay={50} />
        <StatCard label="In Bearbeitung" value={counts.in_progress} accent="blue" delay={100} />
        <StatCard label="Fehler"         value={counts.error}       accent="red"  delay={150} />
        <StatCard label="Abgeschlossen"  value={counts.completed}   accent="green" delay={200} />
      </div>

      {/* Table */}
      <div
        className="bg-card border border-border rounded-lg overflow-hidden animate-card"
        style={{ animationDelay: '250ms' }}
      >
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-muted-foreground text-[10px] uppercase tracking-[0.12em] font-mono w-20">
                ID
              </TableHead>
              <TableHead className="text-muted-foreground text-[10px] uppercase tracking-[0.12em] font-mono">
                Artikel
              </TableHead>
              <TableHead className="text-muted-foreground text-[10px] uppercase tracking-[0.12em] font-mono w-28">
                Menge
              </TableHead>
              <TableHead className="text-muted-foreground text-[10px] uppercase tracking-[0.12em] font-mono w-40">
                Status
              </TableHead>
              <TableHead className="text-right w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-14 font-mono text-sm">
                  Lade Aufträge…
                </TableCell>
              </TableRow>
            ) : orders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-14 font-mono text-sm">
                  Keine Aufträge vorhanden — erstelle einen neuen Auftrag.
                </TableCell>
              </TableRow>
            ) : (
              orders.map((order, i) => (
                <TableRow
                  key={order.id}
                  className="border-border hover:bg-secondary/40 animate-row"
                  style={{ animationDelay: `${300 + i * 35}ms` }}
                >
                  <TableCell>
                    <span className="font-mono text-[10px] text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                      #{String(order.id).padStart(4, '0')}
                    </span>
                  </TableCell>
                  <TableCell className="text-foreground text-sm">
                    {order.article?.name ?? `Artikel #${order.article_id}`}
                  </TableCell>
                  <TableCell className="font-mono text-sm text-foreground">
                    {order.quantity}
                    <span className="text-muted-foreground text-xs ml-1">Stk.</span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={order.status} />
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-secondary"
                        >
                          <MoreHorizontal size={14} />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent
                        align="end"
                        className="bg-popover border-border text-sm"
                      >
                        <DropdownMenuItem
                          onClick={() => openEdit(order)}
                          className="cursor-pointer gap-2"
                        >
                          <Pencil size={13} />
                          Bearbeiten
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(order.id)}
                          className="text-destructive cursor-pointer gap-2 focus:text-destructive"
                        >
                          <Trash2 size={13} />
                          Löschen
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create / Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-popover border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-display text-2xl font-bold tracking-tight">
              {editingOrder ? 'Auftrag bearbeiten' : 'Neuer Auftrag'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 py-2">
            <div className="space-y-1.5">
              <Label className="text-[10px] uppercase tracking-[0.12em] font-mono text-muted-foreground">
                Artikel
              </Label>
              <Select
                value={String(form.article_id)}
                onValueChange={v => setForm(f => ({ ...f, article_id: Number(v) }))}
              >
                <SelectTrigger className="bg-secondary border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-popover border-border">
                  {articles.map(a => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-[10px] uppercase tracking-[0.12em] font-mono text-muted-foreground">
                Menge
              </Label>
              <Input
                type="number"
                min={1}
                value={form.quantity}
                onChange={e => setForm(f => ({ ...f, quantity: Number(e.target.value) }))}
                className="bg-secondary border-border font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-[10px] uppercase tracking-[0.12em] font-mono text-muted-foreground">
                Status
              </Label>
              <Select
                value={form.status}
                onValueChange={v => setForm(f => ({ ...f, status: v as OrderStatus }))}
              >
                <SelectTrigger className="bg-secondary border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-popover border-border">
                  {ORDER_STATUSES.map(s => (
                    <SelectItem key={s} value={s}>
                      {STATUS_LABELS[s]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="mt-2">
            <Button
              variant="ghost"
              onClick={() => setDialogOpen(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              Abbrechen
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-primary text-primary-foreground hover:bg-primary/85 font-medium"
            >
              {editingOrder ? 'Speichern' : 'Erstellen'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

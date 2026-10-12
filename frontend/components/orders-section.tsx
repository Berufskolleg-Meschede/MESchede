'use client'

import { useState, useEffect } from 'react'
import {
  Plus, MoreHorizontal, Pencil, Trash2, Search,
} from 'lucide-react'
import { api } from '@/lib/api'
import type { ProductionOrder, DeliveryOrder, Article, OrderFormData, OrderStatus } from '@/lib/types'
import { StatusBadge } from './status-badge'
import { StatCard } from './stat-card'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
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
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<OrderStatus | 'all'>('all')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingOrder, setEditingOrder] = useState<Order | null>(null)
  const [form, setForm] = useState<OrderFormData>({
    quantity: 1,
    status: 'pending',
    article_id: 0,
  })

  const ordersApi = type === 'production' ? api.productionOrders : api.deliveryOrders

  useEffect(() => {
    let cancelled = false
    Promise.all([ordersApi.list(), api.articles.list()]).then(
      ([ordersData, articlesData]) => {
        if (cancelled) return
        setOrders(ordersData)
        setArticles(articlesData)
        if (articlesData.length > 0) {
          setForm(f => ({ ...f, article_id: articlesData[0].id }))
        }
        setLoading(false)
      }
    ).catch(() => {
      if (!cancelled) {
        setError('Aufträge konnten nicht geladen werden. Bitte lade die Seite erneut.')
        setLoading(false)
      }
    })
    return () => { cancelled = true }
  }, [ordersApi])

  const openCreate = () => {
    setEditingOrder(null)
    setForm({ quantity: 1, status: 'pending', article_id: articles[0]?.id ?? 0 })
    setError('')
    setDialogOpen(true)
  }

  const openEdit = (order: Order) => {
    setEditingOrder(order)
    setForm({ quantity: order.quantity, status: order.status, article_id: order.article_id })
    setError('')
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    if (!Number.isInteger(form.quantity) || form.quantity < 1 || !articles.some(article => article.id === form.article_id)) {
      setError('Bitte wähle einen Artikel und eine ganze Menge größer als 0.')
      return
    }
    setSaving(true)
    setError('')
    try {
      if (editingOrder) {
        const updated = await ordersApi.update(editingOrder.id, form)
        setOrders(previous => previous.map(order => order.id === editingOrder.id ? updated : order))
      } else {
        const created = await ordersApi.create(form)
        setOrders(previous => [...previous, created])
      }
      setDialogOpen(false)
    } catch {
      setError('Der Auftrag konnte nicht gespeichert werden. Bitte versuche es erneut.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await ordersApi.delete(id)
      setOrders(previous => previous.filter(order => order.id !== id))
    } catch {
      setError('Der Auftrag konnte nicht gelöscht werden. Bitte versuche es erneut.')
    }
  }

  const query = search.trim().toLocaleLowerCase('de-DE')
  const visibleOrders = orders.filter(order => {
    const name = order.article?.name ?? articles.find(article => article.id === order.article_id)?.name ?? ''
    return (statusFilter === 'all' || order.status === statusFilter)
      && `${name} ${order.id} ${String(order.id).padStart(4, '0')} ${order.article_id}`.toLocaleLowerCase('de-DE').includes(query)
  })

  const counts = {
    pending: orders.filter(o => o.status === 'pending').length,
    in_progress: orders.filter(o => o.status === 'in_progress').length,
    error: orders.filter(o => o.status === 'error').length,
    completed: orders.filter(o => o.status === 'completed').length,
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          <p className="text-muted-foreground text-sm mt-1.5">
            {orders.length} Aufträge gesamt
          </p>
        </div>
        <Button
          onClick={openCreate}
          disabled={loading || articles.length === 0}
          className="bg-primary text-primary-foreground hover:bg-primary/85 gap-1.5 font-medium"
        >
          <Plus size={15} />
          Neuer Auftrag
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-4">
        <StatCard label="Ausstehend"    value={counts.pending} />
        <StatCard label="In Bearbeitung" value={counts.in_progress} />
        <StatCard label="Fehler"         value={counts.error} />
        <StatCard label="Abgeschlossen"  value={counts.completed} />
      </div>

      {error && !dialogOpen && <p role="alert" className="rounded-sm border border-destructive/40 p-3 text-sm text-destructive">{error}</p>}

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-full sm:max-w-sm">
          <Label htmlFor="order-search" className="mb-2 text-xs text-muted-foreground">Aufträge suchen</Label>
          <div className="relative">
            <Search aria-hidden="true" size={15} className="pointer-events-none absolute left-3 top-3 text-muted-foreground" />
            <Input id="order-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Artikel oder Auftragsnummer" className="h-10 bg-card pl-9" />
          </div>
        </div>
        <div>
          <Label htmlFor="status-filter" className="mb-2 text-xs text-muted-foreground">Status</Label>
          <select id="status-filter" value={statusFilter} onChange={event => setStatusFilter(event.target.value as OrderStatus | 'all')} className="h-10 rounded-sm border border-input bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <option value="all">Alle Status</option>
            {ORDER_STATUSES.map(status => <option key={status} value={status}>{STATUS_LABELS[status]}</option>)}
          </select>
        </div>
        <p aria-live="polite" className="pb-2 text-xs text-muted-foreground sm:ml-auto">{loading ? 'Lade Aufträge…' : `${visibleOrders.length} von ${orders.length} Aufträgen`}</p>
      </div>

      {/* Table */}
      <div
        className="bg-card border border-border rounded-sm overflow-hidden"
      >
        <Table>
          <TableHeader>
            <TableRow className="border-border bg-secondary/35 hover:bg-secondary/35">
              <TableHead className="text-muted-foreground text-xs font-medium w-24 px-5">
                ID
              </TableHead>
              <TableHead className="text-muted-foreground text-xs font-medium">
                Artikel
              </TableHead>
              <TableHead className="text-muted-foreground text-xs font-medium w-28 text-right">
                Menge
              </TableHead>
              <TableHead className="text-muted-foreground text-xs font-medium w-40">
                Status
              </TableHead>
              <TableHead className="text-right w-16"><span className="sr-only">Aktionen</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-12 text-sm">
                  Lade Aufträge…
                </TableCell>
              </TableRow>
            ) : visibleOrders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-12 text-sm">
                  {orders.length === 0 ? 'Keine Aufträge vorhanden.' : 'Keine Aufträge für diese Suche gefunden.'}
                </TableCell>
              </TableRow>
            ) : (
              visibleOrders.map(order => (
                <TableRow
                  key={order.id}
                  className="border-border hover:bg-secondary/40"
                >
                  <TableCell className="px-5 py-3.5">
                    <span className="font-mono text-xs text-muted-foreground">
                      #{String(order.id).padStart(4, '0')}
                    </span>
                  </TableCell>
                  <TableCell className="text-foreground text-sm">
                    {order.article?.name ?? `Artikel #${order.article_id}`}
                  </TableCell>
                  <TableCell className="text-sm tabular-nums text-foreground text-right">
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
                          aria-label={`Aktionen für Auftrag ${order.id}`}
                          className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-secondary"
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
            <DialogTitle className="text-lg font-semibold">
              {editingOrder ? 'Auftrag bearbeiten' : 'Neuer Auftrag'}
            </DialogTitle>
            <DialogDescription>Artikel, Menge und Status des Auftrags festlegen.</DialogDescription>
          </DialogHeader>

          <form id="order-form" onSubmit={event => { event.preventDefault(); void handleSubmit() }} className="space-y-5 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="order-article" className="text-sm text-foreground">
                Artikel
              </Label>
              <Select
                value={String(form.article_id)}
                onValueChange={v => setForm(f => ({ ...f, article_id: Number(v) }))}
              >
                <SelectTrigger id="order-article" className="w-full bg-background border-input">
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
              <Label htmlFor="order-quantity" className="text-sm text-foreground">
                Menge
              </Label>
              <Input
                id="order-quantity"
                required
                step={1}
                type="number"
                min={1}
                value={form.quantity}
                onChange={e => setForm(f => ({ ...f, quantity: Number(e.target.value) }))}
                className="bg-background border-input tabular-nums"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="order-status" className="text-sm text-foreground">
                Status
              </Label>
              <Select
                value={form.status}
                onValueChange={v => setForm(f => ({ ...f, status: v as OrderStatus }))}
              >
                <SelectTrigger id="order-status" className="w-full bg-background border-input">
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
            {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          </form>

          <DialogFooter className="mt-2">
            <Button
              variant="ghost"
              onClick={() => setDialogOpen(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              Abbrechen
            </Button>
            <Button
              type="submit"
              form="order-form"
              disabled={saving || articles.length === 0}
              className="bg-primary text-primary-foreground hover:bg-primary/85 font-medium"
            >
              {saving ? 'Speichert…' : editingOrder ? 'Speichern' : 'Erstellen'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

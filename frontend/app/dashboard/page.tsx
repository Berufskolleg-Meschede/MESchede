'use client'

import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { api } from '@/lib/api'
import type { ProductionOrder, DeliveryOrder, Machine } from '@/lib/types'
import { StatCard } from '@/components/stat-card'
import { StatusBadge } from '@/components/status-badge'
import { cn } from '@/lib/utils'

// ── Colour tokens shared between chart cells and legend ───────────────────────
const STATUS_COLORS: Record<string, string> = {
  pending:     'hsl(45 90% 55%)',
  in_progress: 'hsl(190 90% 55%)',
  error:       'hsl(0 80% 65%)',
  completed:   'hsl(150 65% 55%)',
}

const STATUS_LABELS: Record<string, string> = {
  pending:     'Ausstehend',
  in_progress: 'In Bearbeitung',
  error:       'Fehler',
  completed:   'Abgeschlossen',
}

// ── Custom tooltips ───────────────────────────────────────────────────────────

function StatusTooltip({ active, payload }: { active?: boolean; payload?: { payload: { status: string; count: number } }[] }) {
  if (!active || !payload?.length) return null
  const { status, count } = payload[0].payload
  return (
    <div className="bg-popover border border-border rounded px-3 py-1.5 shadow-lg">
      <span className="text-muted-foreground text-xs font-mono">
        {STATUS_LABELS[status] ?? status}:{' '}
      </span>
      <span className="text-foreground text-xs font-mono font-semibold">{count}</span>
    </div>
  )
}

function VolumeTooltip({ active, payload }: { active?: boolean; payload?: { payload: { name: string; quantity: number } }[] }) {
  if (!active || !payload?.length) return null
  const { name, quantity } = payload[0].payload
  return (
    <div className="bg-popover border border-border rounded px-3 py-1.5 shadow-lg max-w-52">
      <p className="text-muted-foreground text-[10px] font-mono truncate">{name}</p>
      <p className="text-foreground text-xs font-mono font-semibold">{quantity} Stk.</p>
    </div>
  )
}

// ── Custom axis tick for truncated article names ──────────────────────────────

function ArticleTick({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) {
  if (!payload) return null
  const raw = payload.value
  const label = raw.length > 16 ? raw.slice(0, 15) + '…' : raw
  return (
    <text
      x={x}
      y={y}
      dy={4}
      textAnchor="end"
      fill="#71717a"
      fontSize={10}
      fontFamily="var(--font-geist-mono)"
    >
      {label}
    </text>
  )
}

function NumericTick({ x, y, payload }: { x?: number; y?: number; payload?: { value: number } }) {
  if (!payload) return null
  return (
    <text
      x={x}
      y={y}
      dy={-4}
      textAnchor="middle"
      fill="#52525b"
      fontSize={9}
      fontFamily="var(--font-geist-mono)"
    >
      {payload.value}
    </text>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [productionOrders, setProductionOrders] = useState<ProductionOrder[]>([])
  const [deliveryOrders, setDeliveryOrders] = useState<DeliveryOrder[]>([])
  const [machines, setMachines] = useState<Machine[]>([])

  useEffect(() => {
    Promise.all([
      api.productionOrders.list(),
      api.deliveryOrders.list(),
      api.machines.list(),
    ]).then(([prod, del, mach]) => {
      setProductionOrders(prod)
      setDeliveryOrders(del)
      setMachines(mach)
    })
  }, [])

  const allOrders = [...productionOrders, ...deliveryOrders]
  const totalOrders = allOrders.length
  const inProgress = allOrders.filter(o => o.status === 'in_progress').length
  const completed  = allOrders.filter(o => o.status === 'completed').length
  const onlineCount = machines.filter(m => m.status === 'online').length

  // Donut data — all order statuses combined
  const statusData = (['pending', 'in_progress', 'error', 'completed'] as const)
    .map(status => ({ status, count: allOrders.filter(o => o.status === status).length }))
    .filter(d => d.count > 0)

  // Horizontal bar data — total units produced per article
  const articleVolume = productionOrders.reduce<Record<string, number>>((acc, order) => {
    const name = order.article?.name ?? `Artikel #${order.article_id}`
    acc[name] = (acc[name] ?? 0) + order.quantity
    return acc
  }, {})

  const volumeData = Object.entries(articleVolume)
    .map(([name, quantity]) => ({ name, quantity }))
    .sort((a, b) => b.quantity - a.quantity)

  const barHeight = Math.max(volumeData.length * 36, 120)

  return (
    <div className="p-8 space-y-8 max-w-5xl">

      {/* Header */}
      <div className="animate-card">
        <h1 className="font-display text-4xl font-bold tracking-tight text-foreground">
          Dashboard
        </h1>
        <p className="text-muted-foreground text-sm font-mono mt-1">
          Fertigungsübersicht —{' '}
          {new Date().toLocaleDateString('de-DE', {
            weekday: 'long', day: 'numeric', month: 'long',
          })}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Fertigungsaufträge" value={productionOrders.length} accent="orange" delay={50} />
        <StatCard label="Lieferaufträge"      value={deliveryOrders.length}   accent="blue"   delay={100} />
        <StatCard label="In Bearbeitung"      value={inProgress}              accent="amber"  delay={150} />
        <StatCard label="Abgeschlossen"       value={completed}               accent="green"  delay={200} />
      </div>

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Donut — status breakdown */}
        <div
          className="bg-card border border-border rounded-lg p-6 animate-card"
          style={{ animationDelay: '250ms' }}
        >
          <p className="text-muted-foreground text-[10px] uppercase tracking-[0.18em] font-mono">
            Auftragsstatus
          </p>
          <p className="font-display text-xl font-bold text-foreground mt-0.5 mb-5">
            Alle Aufträge
          </p>

          {totalOrders === 0 ? (
            <div className="h-44 flex items-center justify-center">
              <p className="text-muted-foreground text-xs font-mono">Keine Daten</p>
            </div>
          ) : (
            <>
              {/* Chart + centre label overlay */}
              <div className="relative h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      dataKey="count"
                      nameKey="status"
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={76}
                      strokeWidth={0}
                      paddingAngle={2}
                    >
                      {statusData.map(entry => (
                        <Cell
                          key={entry.status}
                          fill={STATUS_COLORS[entry.status] ?? '#71717a'}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<StatusTooltip />} />
                  </PieChart>
                </ResponsiveContainer>

                {/* Centre total */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="font-display text-4xl font-bold text-foreground leading-none">
                    {totalOrders}
                  </span>
                  <span className="text-muted-foreground text-[10px] font-mono uppercase tracking-widest mt-1">
                    Gesamt
                  </span>
                </div>
              </div>

              {/* Legend */}
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 mt-5">
                {statusData.map(({ status, count }) => (
                  <div key={status} className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: STATUS_COLORS[status] }}
                    />
                    <span className="text-muted-foreground text-xs font-mono flex-1 truncate">
                      {STATUS_LABELS[status]}
                    </span>
                    <span className="text-foreground text-xs font-mono tabular-nums">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Horizontal bar — volume per article */}
        <div
          className="bg-card border border-border rounded-lg p-6 animate-card"
          style={{ animationDelay: '300ms' }}
        >
          <p className="text-muted-foreground text-[10px] uppercase tracking-[0.18em] font-mono">
            Produktionsvolumen
          </p>
          <p className="font-display text-xl font-bold text-foreground mt-0.5 mb-5">
            Stück je Artikel
          </p>

          {volumeData.length === 0 ? (
            <div className="h-44 flex items-center justify-center">
              <p className="text-muted-foreground text-xs font-mono">Keine Daten</p>
            </div>
          ) : (
            <div style={{ height: barHeight }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={volumeData}
                  layout="vertical"
                  margin={{ left: 0, right: 24, top: 4, bottom: 4 }}
                >
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%"   stopColor="hsl(35 90% 55%)" stopOpacity={1} />
                      <stop offset="100%" stopColor="hsl(35 90% 68%)" stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={118}
                    tick={<ArticleTick />}
                    axisLine={false}
                    tickLine={false}
                  />
                  <XAxis
                    type="number"
                    tick={<NumericTick />}
                    axisLine={false}
                    tickLine={false}
                    tickCount={4}
                  />
                  <Tooltip content={<VolumeTooltip />} />
                  <Bar
                    dataKey="quantity"
                    fill="url(#barGrad)"
                    radius={[0, 3, 3, 0]}
                    barSize={14}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* ── Machines ── */}
      <section>
        <h2 className="text-muted-foreground text-[10px] uppercase tracking-[0.2em] font-mono mb-4">
          Maschinen — {onlineCount}/{machines.length} Online
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {machines.map((machine, i) => (
            <div
              key={machine.id}
              className={cn(
                'bg-card border border-border rounded-lg p-4 animate-card',
                machine.status === 'online' && 'border-emerald-500/15'
              )}
              style={{ animationDelay: `${400 + i * 50}ms` }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-muted-foreground font-mono text-[10px]">
                  M-{String(machine.id).padStart(2, '0')}
                </span>
                <StatusBadge status={machine.status} />
              </div>
              <p className="text-foreground text-sm font-medium leading-tight">
                {machine.name}
              </p>
              <p className="text-muted-foreground text-xs font-mono mt-0.5">
                {machine.type}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

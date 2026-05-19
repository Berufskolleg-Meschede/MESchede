"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { OrderStatus, MachineStatus } from "@/lib/types"

type StatusKind = OrderStatus | MachineStatus

// Map statuses to shadcn Badge variants (semantic usage)
const BADGE_VARIANT: Record<StatusKind, string> = {
  PENDING: "secondary",
  IN_PROGRESS: "outline",
  COMPLETED: "default",
  ERROR: "destructive",
  OFFLINE: "secondary",
  ONLINE: "default",
}

const LABEL: Record<StatusKind, string> = {
  PENDING: "Pending",
  IN_PROGRESS: "In Progress",
  COMPLETED: "Completed",
  ERROR: "Error",
  OFFLINE: "Offline",
  ONLINE: "Online",
}

interface StatusBadgeProps {
  status: StatusKind
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const variant = (BADGE_VARIANT[status] as any) || "secondary"
  const label = LABEL[status] || String(status)

  return (
    <Badge variant={variant} className={className}>
      {label}
    </Badge>
  )
}

interface StatusDotProps {
  status: StatusKind
  size?: "sm" | "md" | "lg"
}

const DOT_CLASS: Record<StatusKind, string> = {
  PENDING: "bg-amber-500",
  IN_PROGRESS: "bg-blue-500",
  COMPLETED: "bg-green-500",
  ERROR: "bg-red-500",
  OFFLINE: "bg-gray-500",
  ONLINE: "bg-green-500",
}

export function StatusDot({ status, size = "md" }: StatusDotProps) {
  const sz = size === "sm" ? "w-2 h-2" : size === "lg" ? "w-4 h-4" : "w-3 h-3"
  const color = DOT_CLASS[status] || DOT_CLASS.PENDING
  return <div className={`${sz} ${color}`} aria-hidden />
}

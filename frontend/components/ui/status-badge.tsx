"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { OrderStatus, MachineStatus } from "@/lib/types"

const STATUS_CONFIG: Record<OrderStatus | MachineStatus, { color: string; label: string }> = {
  PENDING: { color: "bg-amber-900 text-amber-200 border-amber-700", label: "Pending" },
  IN_PROGRESS: { color: "bg-blue-900 text-blue-200 border-blue-700", label: "In Progress" },
  COMPLETED: { color: "bg-green-900 text-green-200 border-green-700", label: "Completed" },
  ERROR: { color: "bg-red-900 text-red-200 border-red-700", label: "Error" },
  OFFLINE: { color: "bg-gray-700 text-gray-200 border-gray-600", label: "Offline" },
  ONLINE: { color: "bg-green-900 text-green-200 border-green-700", label: "Online" },
}

interface StatusBadgeProps {
  status: OrderStatus | MachineStatus
  variant?: "default" | "outline"
  className?: string
}

export function StatusBadge({ status, variant = "default", className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING
  
  return (
    <Badge
      variant={variant as any}
      className={`${config.color} border font-semibold ${className || ""}`}
    >
      {config.label}
    </Badge>
  )
}

/**
 * Colored dot indicator for status
 */
interface StatusDotProps {
  status: OrderStatus | MachineStatus
  size?: "sm" | "md" | "lg"
}

const DOT_SIZES = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
}

const DOT_COLORS = {
  PENDING: "bg-amber-500",
  IN_PROGRESS: "bg-blue-500",
  COMPLETED: "bg-green-500",
  ERROR: "bg-red-500",
  OFFLINE: "bg-gray-500",
  ONLINE: "bg-green-500",
}

export function StatusDot({ status, size = "md" }: StatusDotProps) {
  return (
    <div
      className={`${DOT_SIZES[size]} ${DOT_COLORS[status] || DOT_COLORS.PENDING} rounded-none`}
      aria-label={status}
    />
  )
}

import { AppLayout } from "@/components/layout/app-layout"
import { OrderSummaryCards } from "@/components/dashboard/order-summary-cards"
import { InventoryAlerts } from "@/components/dashboard/inventory-alerts"
import { MachineStatusGrid } from "@/components/dashboard/machine-status-grid"
import { RecentOrders } from "@/components/dashboard/recent-orders"

export default function Home() {
  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Real-time overview of production, delivery, and inventory status
          </p>
        </div>

        {/* Order Summary Cards */}
        <OrderSummaryCards />

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Inventory Alerts */}
          <InventoryAlerts />

          {/* Machine Status */}
          <MachineStatusGrid />
        </div>

        {/* Recent Orders */}
        <RecentOrders />
      </div>
    </AppLayout>
  )
}

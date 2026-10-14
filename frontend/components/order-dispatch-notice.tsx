import Link from 'next/link'
import type { DispatchStatus, OrderRunView } from '@/lib/types'
import { orderLabel } from '@/lib/order-format'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

export function OrderDispatchNotice({ dispatch, reviews }: { dispatch: DispatchStatus; reviews: OrderRunView[] }) {
  if (!dispatch.reason && reviews.length === 0) { return null }
  return (
    <Alert className="rounded-sm">
      <AlertTitle>{reviews.length > 0 ? 'Laufprüfung erforderlich · neue Starts gesperrt' : 'Neue Starts gesperrt'}</AlertTitle>
      <AlertDescription>
        <p>{reviews.length > 0 ? 'Prüfe den Ausgang der offenen Läufe. Die Sperre gilt für Produktion und Lieferung.' : dispatch.reason}</p>
        {reviews.length > 0 && <div className="flex flex-wrap gap-4">
          {reviews.map(order => <Link key={order.run_id}
            href={`/${order.order_type === 'production' ? 'production-orders' : 'delivery-orders'}#run-${order.run_id}`}
            className="underline underline-offset-4">
            {order.order_type === 'production' ? 'Fertigung' : 'Lieferung'} {orderLabel(order.order_id)} prüfen
          </Link>)}
        </div>}
      </AlertDescription>
    </Alert>
  )
}

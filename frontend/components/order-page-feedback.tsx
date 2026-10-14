import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export function OrderPageFeedback({ error, loading, hasData, reload }: {
  error: string | null; loading: boolean; hasData: boolean; reload: () => void
}) {
  return <>
    {error && <Alert variant="destructive" className="rounded-sm"><AlertDescription>
      <p>{error}{hasData && ' Die letzten Daten bleiben sichtbar.'}</p>
      <Button variant="outline" onClick={reload}>Erneut laden</Button>
    </AlertDescription></Alert>}
    {loading && <div role="status" aria-label="Lade Auftragsdaten"><Skeleton className="h-24 w-full rounded-sm" /></div>}
  </>
}

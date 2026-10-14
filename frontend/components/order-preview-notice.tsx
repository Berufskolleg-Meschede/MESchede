'use client'

import { useState } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

/** Kennzeichnet den expliziten Entwicklungswrapper auf allen bestehenden Seiten. */
export function OrderPreviewNotice() {
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function reset() {
    setResetting(true)
    setError(null)
    try {
      const response = await fetch('/api/mes/orders/preview/reset', { method: 'POST' })
      if (!response.ok) { throw new Error('Die Testdaten konnten nicht zurückgesetzt werden.') }
      window.location.reload()
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Die Testdaten sind nicht erreichbar.')
      setResetting(false)
    }
  }

  return <div className="px-5 pt-5 md:px-8 lg:px-10">
    <Alert className="rounded-sm">
      <AlertTitle>Testdaten-Vorschau · simulierte Aufträge</AlertTitle>
      <AlertDescription>
        <p>Auch Rückmeldungen und Mengen sind simuliert. Bewertungen ändern nur den temporären Vorschauzustand. Es besteht keine PLC- oder Produktionsdatenbank-Verbindung.</p>
        <Button variant="outline" size="sm" disabled={resetting} onClick={() => void reset()}>{resetting ? 'Setzt zurück…' : 'Testdaten zurücksetzen'}</Button>
        {error && <p role="alert">{error}</p>}
      </AlertDescription>
    </Alert>
  </div>
}

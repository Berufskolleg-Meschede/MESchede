'use client'

import { useCallback, useEffect, useState } from 'react'

/** Lädt Snapshots nacheinander und bewahrt letzte Daten bei einem Quellenfehler. */
export function useOrderSnapshot<T extends { refresh_interval_s: number }>(
  key: string,
  load: (signal: AbortSignal) => Promise<T>,
) {
  const [state, setState] = useState<{ key: string; data: T | null; error: string | null; checkedAt: number }>({
    key: '', data: null, error: null, checkedAt: 0,
  })
  const [revision, setRevision] = useState(0)
  const reload = useCallback(() => setRevision(value => value + 1), [])

  useEffect(() => {
    let active = true
    let timer: ReturnType<typeof setTimeout>
    let controller: AbortController
    let interval = 2000

    async function refresh() {
      controller = new AbortController()
      try {
        const data = await load(controller.signal)
        if (!active) { return }
        interval = Math.max(250, data.refresh_interval_s * 1000)
        setState({ key, data, error: null, checkedAt: Date.now() })
      } catch (error) {
        if (!active || controller.signal.aborted) { return }
        const message = error instanceof Error ? error.message : 'Die Auftragsdaten sind nicht erreichbar.'
        setState(previous => ({ key, data: previous.key === key ? previous.data : null, error: message, checkedAt: Date.now() }))
      } finally {
        if (active) { timer = setTimeout(refresh, interval) }
      }
    }

    void refresh()
    return () => {
      active = false
      clearTimeout(timer)
      controller?.abort()
    }
  }, [key, load, revision])

  const current = state.key === key
  return { data: current ? state.data : null, error: current ? state.error : null,
    loading: !current || state.data === null && state.error === null, checkedAt: state.checkedAt, reload }
}

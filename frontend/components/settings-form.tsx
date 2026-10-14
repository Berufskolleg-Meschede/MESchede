'use client'

import { useEffect, useState } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api'
import { ApiValidationError } from '@/lib/types'
import type { Settings } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NodeTreeEditor } from '@/components/node-tree-editor'

const EMPTY_SETTINGS: Settings = {
  opcua_node_production_order: '',
  opcua_node_delivery_order: '',
  polling_interval_ms: 500,
  opcua_node_kopf: '',
  opcua_node_inhalt: '',
  opcua_node_feedback: '',
  opcua_node_auftragssteuerung: '',
  opcua_node_status: '',
  opcua_node_produktqueue_pattern: '',
}

export function SettingsForm() {
  const [settings, setSettings] = useState<Settings>(EMPTY_SETTINGS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedAt, setSavedAt] = useState<Date | null>(null)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    let cancelled = false
    api.settings.get().then(data => {
      if (cancelled) return
      setSettings(data)
      setLoading(false)
    }).catch(() => {
      if (!cancelled) {
        setError('Einstellungen konnten nicht geladen werden. Bitte lade die Seite erneut.')
        setLoading(false)
      }
    })
    return () => { cancelled = true }
  }, [])

  const handleSubmit = async () => {
    setSaving(true)
    setError('')
    setFieldErrors({})
    setSavedAt(null)
    try {
      const updated = await api.settings.update(settings)
      setSettings(updated)
      setSavedAt(new Date())
    } catch (err) {
      if (err instanceof ApiValidationError) {
        setFieldErrors(err.fieldErrors)
        setError(
          Object.keys(err.fieldErrors).length > 0
            ? 'Bitte korrigiere die markierten Felder.'
            : err.message
        )
      } else {
        setError('Die Einstellungen konnten nicht gespeichert werden. Bitte versuche es erneut.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-5 md:p-8 lg:p-10">
      <div className="border-b border-border pb-5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Einstellungen
        </h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          OPC-UA-Zielnodes und Abfrageintervall für die Anlagenanbindung.
        </p>
      </div>

      {loading ? (
        <p aria-live="polite" className="text-sm text-muted-foreground">Lade Einstellungen…</p>
      ) : (
        <>
          {error && (
            <p role="alert" className="rounded-sm border border-destructive/40 p-3 text-sm text-destructive">
              {error}
            </p>
          )}

          {savedAt && !saving && !error && (
            <p role="status" className="flex items-center gap-2 rounded-sm border border-emerald-600/40 p-3 text-sm text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 size={15} aria-hidden="true" />
              Einstellungen übernommen um {savedAt.toLocaleTimeString('de-DE')}
            </p>
          )}

          <form
            onSubmit={event => { event.preventDefault(); void handleSubmit() }}
            className="space-y-5"
          >
            <div className="space-y-1.5">
              <Label htmlFor="settings-production-node" className="text-sm text-foreground">
                Zielnode Produktionsaufträge
              </Label>
              <Input
                id="settings-production-node"
                value={settings.opcua_node_production_order}
                onChange={e => setSettings(s => ({ ...s, opcua_node_production_order: e.target.value }))}
                aria-invalid={!!fieldErrors.opcua_node_production_order}
                className="bg-background border-input"
              />
              {fieldErrors.opcua_node_production_order && (
                <p role="alert" className="text-xs text-destructive">
                  {fieldErrors.opcua_node_production_order}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="settings-delivery-node" className="text-sm text-foreground">
                Zielnode Lieferaufträge
              </Label>
              <Input
                id="settings-delivery-node"
                value={settings.opcua_node_delivery_order}
                onChange={e => setSettings(s => ({ ...s, opcua_node_delivery_order: e.target.value }))}
                aria-invalid={!!fieldErrors.opcua_node_delivery_order}
                className="bg-background border-input"
              />
              {fieldErrors.opcua_node_delivery_order && (
                <p role="alert" className="text-xs text-destructive">
                  {fieldErrors.opcua_node_delivery_order}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="settings-interval" className="text-sm text-foreground">
                Abfrageintervall (Millisekunden)
              </Label>
              <Input
                id="settings-interval"
                type="number"
                step={1}
                min={100}
                max={10000}
                value={settings.polling_interval_ms}
                onChange={e => setSettings(s => ({ ...s, polling_interval_ms: Number(e.target.value) }))}
                aria-invalid={!!fieldErrors.polling_interval_ms}
                className="bg-background border-input tabular-nums"
              />
              {fieldErrors.polling_interval_ms && (
                <p role="alert" className="text-xs text-destructive">
                  {fieldErrors.polling_interval_ms}
                </p>
              )}
            </div>

            <div className="border-t border-border pt-5">
              <NodeTreeEditor
                settings={settings}
                fieldErrors={fieldErrors}
                onChange={(key, value) => setSettings(s => ({ ...s, [key]: value }))}
              />
            </div>

            <Button
              type="submit"
              disabled={saving}
              className="bg-primary text-primary-foreground hover:bg-primary/85 font-medium"
            >
              {saving ? 'Speichert…' : 'Speichern'}
            </Button>
          </form>
        </>
      )}
    </div>
  )
}

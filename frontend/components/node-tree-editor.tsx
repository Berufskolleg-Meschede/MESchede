'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Settings } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface TreeNodeDef {
  key: keyof Settings
  label: string
  description: string
  children?: TreeNodeDef[]
}

const NODE_TREE: TreeNodeDef[] = [
  {
    key: 'opcua_node_kopf',
    label: 'Kopf',
    description: 'Auftragskopfdaten: Auftragsnummer, Priorität, Startzeit und die Auftragssteuerung.',
    children: [
      {
        key: 'opcua_node_auftragssteuerung',
        label: 'Auftragssteuerung_MES',
        description: 'Startet den Auftrag bzw. quittiert dessen Abschluss (0 = Leerlauf, 1 = Start).',
      },
    ],
  },
  {
    key: 'opcua_node_inhalt',
    label: 'Inhalt',
    description: 'Die zu fertigenden bzw. zu kommissionierenden Produkte dieses Auftrags.',
    children: [
      {
        key: 'opcua_node_produktqueue_pattern',
        label: 'Produktqueue',
        description: 'Namensmuster für die einzelnen Produktplätze; muss den Platzhalter {index} enthalten.',
      },
    ],
  },
  {
    key: 'opcua_node_feedback',
    label: 'Feedback',
    description: 'Rückmeldungen der Anlage zum aktuellen Status des Auftrags.',
    children: [
      {
        key: 'opcua_node_status',
        label: 'StatusMES',
        description: 'Statuscode der Anlage (0 = bereit, 1 = läuft, 5 = fertig).',
      },
    ],
  },
  {
    key: 'opcua_node_lager_gehaeuse',
    label: 'LagerGehaeuse',
    description: 'Gehäuselager: Gesamtzahl sowie Stückzahlen rot/silber/schwarz.',
  },
  {
    key: 'opcua_node_magazin_deckel_1',
    label: 'MagazinDeckel_1',
    description: 'Deckelmagazin 1 (blau): aktuelle Stückzahl.',
  },
  {
    key: 'opcua_node_magazin_deckel_2',
    label: 'MagazinDeckel_2',
    description: 'Deckelmagazin 2 (grün): aktuelle Stückzahl.',
  },
  {
    key: 'opcua_node_lager_produkte',
    label: 'LagerProdukte',
    description: 'Hochregallager: Gesamtzahl sowie Stückzahlen je Produkt und Farbe.',
  },
]

interface NodeTreeEditorProps {
  settings: Settings
  onChange: (key: keyof Settings, value: string) => void
  fieldErrors: Record<string, string>
}

function TreeRow({
  node, depth, settings, onChange, fieldErrors,
}: NodeTreeEditorProps & { node: TreeNodeDef; depth: number }) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = !!node.children?.length
  const inputId = `node-tree-${node.key}`
  const error = fieldErrors[node.key as string]

  return (
    <li className="relative">
      <div className="flex flex-wrap items-start gap-3 py-2.5" style={{ paddingLeft: depth * 20 }}>
        {hasChildren ? (
          <button
            type="button"
            onClick={() => setExpanded(e => !e)}
            aria-expanded={expanded}
            aria-label={expanded ? `${node.label} einklappen` : `${node.label} ausklappen`}
            className="mt-1.5 shrink-0 text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        ) : (
          <span className="mt-1.5 shrink-0 text-muted-foreground" aria-hidden="true">
            └
          </span>
        )}

        <div className="min-w-0 flex-1 space-y-1.5">
          <Label htmlFor={inputId} className="text-sm font-medium text-foreground">
            {node.label}
          </Label>
          <p className="text-xs text-muted-foreground">{node.description}</p>
          <Input
            id={inputId}
            value={settings[node.key] as string}
            onChange={e => onChange(node.key, e.target.value)}
            aria-invalid={!!error}
            className="max-w-sm bg-background border-input font-mono text-sm"
          />
          {error && (
            <p role="alert" className="text-xs text-destructive">
              {error}
            </p>
          )}
        </div>
      </div>

      {hasChildren && expanded && (
        <ul className={cn('ml-[9px] border-l border-border')}>
          {node.children!.map(child => (
            <TreeRow
              key={child.key as string}
              node={child}
              depth={depth + 1}
              settings={settings}
              onChange={onChange}
              fieldErrors={fieldErrors}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export function NodeTreeEditor({ settings, onChange, fieldErrors }: NodeTreeEditorProps) {
  return (
    <div className="space-y-2">
      <div>
        <h2 className="text-sm font-medium text-foreground">Knotenstruktur</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Struktur der Kindknoten unterhalb des Produktions- bzw. Lieferauftrags-Zielnodes sowie
          die Lagerknoten für die Lagerbestandsseite. Die Struktur selbst ist fest vorgegeben; nur
          die Browse-Namen sind editierbar, falls sich die Anlagenkonfiguration ändert.
        </p>
      </div>
      <ul>
        {NODE_TREE.map(node => (
          <TreeRow
            key={node.key as string}
            node={node}
            depth={0}
            settings={settings}
            onChange={onChange}
            fieldErrors={fieldErrors}
          />
        ))}
      </ul>
    </div>
  )
}

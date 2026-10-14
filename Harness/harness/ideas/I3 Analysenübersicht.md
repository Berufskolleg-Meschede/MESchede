# Analysenübersicht

## Meta

- **Typ:** Idee
- **State:** Assessed
- **Geltungsbereich:** Backend (OPC-UA-Rückmeldung, PostgreSQL, Analytics-API), Frontend (Analysenseite)

## Zweck

Die Produktionsleitung soll tatsächliche Ergebnisse und beobachtete Laufzeiten von Produktions- und Lieferaufträgen nachvollziehen.

## Kontext

Die vorhandenen Worker lesen `Feedback.StatusMES` mit den bestätigten Zuständen `0` (bereit), `1` (gestartet) und `5` (abgeschlossen). Sie lesen keine Gut- oder Fehlmengen. Die eingehenden `Produktqueue`-Felder sind bislang Auftragsdaten, kein bestätigtes Ergebnisformat. Die Produktionsaufträge und Lieferaufträge werden durch Worker angenommen, aber Laufbeobachtungen werden bisher nicht dauerhaft gespeichert.

## Quellen

- Benutzeranforderung vom 13.10.2026
- `backend/app/workers/plc_handshake.py`
- `backend/app/workers/production_queue.py`
- `backend/app/workers/delivery_queue.py`
- `backend/app/clients/opc_ua_client.py`
- `docs/opc-ua-integration.md`
- `docs/issues/projektwoche/analytics.md`

Die Felder und die Semantik für Gut-/Fehlergebnisse sind in der verfügbaren PLC-Dokumentation nicht belegt.

## Inhalt

### Ursprünglicher Prompt

Die Produktionsleitung soll produzierte Mengen und Laufdauern nachvollziehen können. Benötigt werden eine Analysenübersicht mit Zeitraum- und Auftragsartfilter, Soll- und tatsächliche Mengen je Lauf, gute und fehlerhafte Einheiten, beobachtete Start-/Endzeiten sowie persistente OPC-UA-Ergebnisse. Wiederholtes Abfragen darf Produkte nicht doppelt zählen; Sollmengen sind keine tatsächliche Produktion. Produktions- und Liefermengen sind getrennt, fehlende Daten unbekannt.

### Kritische Bewertung

#### 1. Welche tatsächlichen Produktionsrückmeldungen stehen zur Verfügung?

**Antwort:** Die Dokumentation bestätigt nur `StatusMES` für Start und Abschluss. Felder für Produktresultat, Gutmenge oder Fehlmenge sind nicht beschrieben. Der Benutzer hat bestätigt, dass die Ergebnisfelder noch unbekannt sind.

#### 2. Welches beobachtbare Verhalten wird erwartet?

**Antwort:** Pro Produktions- oder Lieferlauf sollen Planmenge, bestätigte Resultatmengen und beobachtete Zeitpunkte getrennt sichtbar sein. Die Laufdauer folgt ausschließlich aus beobachtetem Start und Ende; ein noch laufender Wert ist vorläufig. Filter schränken die gespeicherten Läufe ein.

#### 3. Welche Risiken und Randfälle gelten?

**Antwort:** Sollmengen dürfen nie als Ist-Menge gezählt werden. Ein kurz laufender Auftrag kann schon bei der ersten Abfrage Status `5` melden; dann darf kein Startzeitpunkt erfunden werden. Wiederholte Statusabfragen aktualisieren dieselbe Auftragsidentität. Lieferläufe bleiben in einer separaten Kategorie. Der unbekannte Ergebnisvertrag verhindert eine korrekte Zuordnung von Gut- und Fehlmengen.

### Entscheidung

Assessed. Persistenz von Auftragsannahme und beobachteten PLC-Zuständen sowie eine Analyseoberfläche lassen sich mit belegten Daten umsetzen. Tatsächliche Gut-/Fehlmengen bleiben unbekannt, bis die Steuerungsgruppe Feldnamen und Semantik bestätigt. Keine Sollmenge wird als Produktion ausgegeben.

### Abgeleitete Specs

- Noch keine; die Rückmeldefelder sind fachlich nicht bestätigt.

## Beziehungen

- **Voraussetzung:** `harness/_idea.md`
- **Ergänzt:** `harness/_uiux.md`
- **Ergebnis:** `backend/app/routers/analytics_router.py`, persistente Laufdaten und `/analytics`-Oberfläche

## Offene Punkte

- OPC-UA-Node/Feld und Semantik für Gut-/Fehlteile sowie die Identität einer bearbeiteten Produkteinheit bestätigen.
- Bestätigen, ob `order_id` pro Auftragsart im betrachteten MES-Betrieb eindeutig ist.
- Migrationsreihenfolge mit der parallelen Lagerbestandsänderung abstimmen.

## Pflege

- **Aktualisierung:** Nach Bestätigung des PLC-Ergebnisvertrags und nach Änderung der Analyseregeln.
- **Ablösung:** Durch eine ausgereifte Feature-Spezifikation und spätere Fehler-Specs.

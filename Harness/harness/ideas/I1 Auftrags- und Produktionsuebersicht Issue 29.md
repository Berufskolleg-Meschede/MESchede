# Auftrags- und Produktionsübersicht

## Meta

- **Typ:** Idee
- **State:** Specified
- **Geltungsbereich:** GitHub Issue #29; Live-Übersicht, PLC-Rückmeldungen, persistente Auftragsdaten und Wiederaufnahme.

## Zweck

Issue #29 gemeinsam zu einer prüfbaren Feature-Spezifikation ausarbeiten. Der Implementierungsplan folgt erst nach der fachlichen Klärung.

## Kontext

Issue #29 fordert getrennte Ansichten für aktive Produktions- und Lieferaufträge, wartende MES-Aufträge und Produkteinheiten des aktiven Auftrags. PLC-Rückmeldungen sollen eindeutig zugeordnet, relevante Status-/Laufdaten in PostgreSQL gespeichert und regelmäßig in einer deutschsprachigen Oberfläche angezeigt werden. Daten und wartende Aufträge müssen einen Neustart überstehen. Mehrfach gelesene Resultate dürfen keine doppelten Mengen erzeugen. Verbindungsprobleme und veraltete beziehungsweise unbekannte Daten müssen sichtbar bleiben.

Der aktuelle Dashboard-Code lädt Daten einmalig beim Öffnen und verwendet über `USE_MOCK = true` Demo-Daten. Die Frontend-Auftragstypen enthalten ID, Artikel, Sollmenge und Status, aber keine bearbeitete Menge oder Produktresultate. Die vorhandenen Datenbank-Auftragsmodelle enthalten ebenfalls noch keine Laufdaten oder Produktresultate.

Die POST-Endpunkte nehmen PLC-nahe Payloads mit `order_id` und `mes_auftrag` in prozesslokale Warteschlangen auf. Die Worker speichern die angenommenen Aufträge und ihre Ergebnisse in diesem Ablauf nicht in PostgreSQL. Die Worker-Diagnosen liefern aktuelle beziehungsweise zuletzt bearbeitete IDs und Fehler, aber keine vollständige Auftrags- oder Produkthistorie.

Der bestehende gemeinsame Handshake liest `StatusMES` beziehungsweise `Status_MES`: Idle `0`, gestartet `1`, fertig `5`; anschließend quittiert er den Abschluss und wartet auf Idle. Dieses implementierte Verhalten ist ein Ausgangspunkt, kein in dieser Sitzung erhobener Nachweis für die vollständige fachliche Status- und Ergebniszuordnung an der Anlage. Seriennummern, Sequenznummern und numerische PLC-Auftragsnummern existieren im Eingabemodell; ihre Eignung als eindeutige Rückmeldeidentität ist noch zu klären.

## Quellen

- Benutzerauftrag zur gemeinsamen Spezifikation mit Harness, anschließend Implementierungsplan, und Erstellung eines neuen Branches; korrigiert auf Issue #29.
- [GitHub Issue #29: Auftrags- und Produktionsübersicht](https://github.com/Berufskolleg-Meschede/MESchede/issues/29); beim Abruf offen, ohne Kommentare.
- `../../../docs/issues/projektwoche/overview.md`
- `../../../frontend/app/dashboard/page.tsx`
- `../../../frontend/lib/api.ts`
- `../../../frontend/lib/types.ts`
- `../../../frontend/app/production-orders/page.tsx`
- `../../../frontend/app/delivery-orders/page.tsx`
- `../../../frontend/components/orders-section.tsx`
- `../../../docs/issues/projektwoche/manual.md` (Abgrenzung zur manuellen Auftragsannahme aus Issue #30)
- `../../../backend/app/models/production_order.py`
- `../../../backend/app/models/delivery_order.py`
- `../../../backend/app/models/mes_auftrag.py`
- `../../../backend/app/clients/opc_ua_client.py`
- `../../../backend/app/routers/productionorders_router.py`
- `../../../backend/app/routers/deliveryorders_router.py`
- `../../../backend/app/workers/production_queue.py`
- `../../../backend/app/workers/delivery_queue.py`
- `../../../backend/app/workers/plc_handshake.py`
- `../../../backend/app/workers/diagnostics.py`
- `../../../docs/opc-ua-integration.md`
- `../_uiux.md`
- Vorhandene Tests unter `../../../backend/tests/`; in dieser Spezifikationsphase nicht ausgeführt. Kein Anlagenlauf in dieser Sitzung.

## Inhalt

### Ursprünglicher Prompt

Sinngemäß: Feature für GitHub Issue zunächst gemeinsam als Spezifikation für spec-driven development ausarbeiten, Fragen stellen und diskutieren; anschließend einen Implementierungsplan erstellen. Harness verwenden und einen neuen Branch erstellen. Die ursprünglich genannte Issue-Nummer #12 wurde vom Benutzer auf #29 korrigiert. Die hierzu zuvor gestellten Fragen sind überholt.

### Kritische Bewertung

#### 1. Welche operativen Aufgaben und Ansichten umfasst die zentrale Übersicht?

**Antwort:** Vom Benutzer bestätigt: Produktion und Lieferung erhalten getrennte Seiten. Das Dashboard bleibt ein separates, ausschließlich lesendes Modul und kombiniert Zusammenfassungen beider Bereiche. Die bestehenden Routen `/production-orders`, `/delivery-orders` und `/dashboard` bieten dafür bereits die passende Grundstruktur. Präzisierung: manuelles Auslösen gehört zu einem separaten Issue und wird später bearbeitet. Diese Arbeit ergänzt Übersicht und Wiederaufnahme; die genaue Reviewaktion wird gemeinsam ausgearbeitet. Neue Pause-, Abbruch- oder Wiederholungssteuerung wird daraus nicht abgeleitet.

#### 2. Welche bestätigten Rückmeldungen definieren fachlichen Status, bearbeitete Menge und Produktresultat?

**Antwort:** Vom Benutzer bestätigt: erfolgreiche und fehlgeschlagene Einheiten im MES zählen und anhand der PLC-Statusrückmeldungen verifizieren. Bearbeitete Einheiten umfassen beide Ergebnisarten; erfolgreiche und fehlerhafte Mengen bleiben getrennt sichtbar. Der aktuelle Handshake kennt Auftragsfeedback `0`, `1` und `5`, belegt aber noch nicht den vollständigen Produktresultatvertrag. Finale Produktsignale und stabile Identitätsfelder müssen bestätigt werden. Wiederholtes Lesen derselben finalen Produkteinheit darf keine weitere Einheit zählen; fehlende Ergebnisse dürfen nicht aus Sollmengen oder angenommenen Starts abgeleitet werden.

#### 3. Wie werden Datenverlust, Doppelzählung und Doppelstart bei wiederholten Rückmeldungen, Ausfällen und Neustarts vermieden?

**Antwort:** Vom Benutzer bestätigt: zuerst mit der PLC abgleichen; bei weiter unklarer Ausführung manuelle Prüfung verlangen. Ein laufender Produktions- oder Lieferlauf muss dauerhaft erkennbar sein. Nach Neustart beziehungsweise Herunterfahren soll beim nächsten Öffnen der Anwendung der Prüfbedarf sichtbar sein. Unklare Läufe dürfen nicht automatisch erneut gestartet werden. Die globale Sperre gilt für beide Auftragsarten bis zur erforderlichen Prüfung. Das Review enthält Information über den Lauf und bekannte Mengen; eine Erklärung ist nicht erforderlich. Wiederholt gelesene beziehungsweise manuell erfasste Resultate dürfen nicht doppelt zählen. Die vorhandenen prozesslokalen Queues erfüllen diese Garantie noch nicht. Die Spec definiert Identitäts-/Nachweisregeln; konkrete PLC-Felder werden vor Live-Abnahme verifiziert.

Zusätzlich vom Benutzer entschieden: Produktion und Kommissionierung sollen im MES nicht gleichzeitig laufen. Diese Projektregel wird übernommen; sie ist kein Nachweis, dass die PLC physisch keinen Parallelbetrieb unterstützt. Der aktuelle Code besitzt zwei unabhängige Worker; eine gemeinsame Regel zur Vergabe des nächsten Laufs fehlt in diesem Ablauf.

Nach Beratung hat der Benutzer die globale Sperre, das Review ohne erforderliche Erklärung und eine gemeinsame FIFO-Reihenfolge bestätigt. Der älteste dauerhaft angenommene Auftrag startet zuerst; Produktions-/Lieferpriorität ist irrelevant. Die Entscheidungsvorlage `../decisions/issue-29-recovery.md` wird durch die verlinkte Feature-Spezifikation abgelöst.

### Entscheidung

Die drei kritischen Fragen sind beantwortet; Umfang, Mengenregeln, globale Sperre, Review und gemeinsame Reihenfolge sind ausreichend abgegrenzt. Die Idee ist `Specified` und in die vom Benutzer bestätigte Feature-Spezifikation überführt. Konkrete PLC-Signale werden nicht erfunden: fehlende Nachweise bleiben unbekannt und verhindern die zugehörige Live-Abnahme. Der Implementierungsplan konkretisiert OOP-Verantwortlichkeiten, DTOs, Persistenz, gemeinsame Startvergabe und die Wiederverwendung der bestehenden Auftragsseiten. Noch keine Anwendungscodeänderung.

### Abgeleitete Specs

- [Issue #29 – Auftrags- und Produktionsübersicht](../../../docs/specs/issue-29-order-production-overview.md)

## Beziehungen

- **Voraussetzung:** `../_idea.md`, `../_template.md`
- **Ergänzt:** `../../../docs/issues/projektwoche/overview.md`, `../../../docs/opc-ua-integration.md`, `../decisions/issue-29-recovery.md`
- **Ergebnis:** `../../../docs/specs/issue-29-order-production-overview.md`
- **Implementierungsplan:** `../../../docs/plans/issue-29-order-production-overview.md`

## Offene Punkte

- PLC-Verifikation für eindeutige Korrelation, Produktresultate, Endsignale und Bereitschaft; siehe verpflichtende Nachweisliste in der Spec.
- Prüfung der technischen Entwurfsentscheidungen bei Umsetzung, insbesondere Pollinglast und Wiederaufnahme bei verlorenem Ausführungsnachweis.
- Verfügbare Projektgeräte für UI-Abnahme.

## Pflege

- **Aktualisierung:** Nach fachlichen Antworten und beim Abgleich der gemeinsamen Spezifikation.
- **Ablösung:** Fachlicher Inhalt ist in die verlinkte Feature-Spezifikation überführt; State `Specified`.

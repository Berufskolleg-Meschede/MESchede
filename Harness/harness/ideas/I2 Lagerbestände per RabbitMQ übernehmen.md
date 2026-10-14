# Lagerbestände per RabbitMQ übernehmen

## Meta

- **Typ:** Idee
- **State:** Assessed
- **Geltungsbereich:** Backend (RabbitMQ, PostgreSQL, Storage-API), Frontend (Lagerbestandsseite)

## Zweck

Eingehende Lagerbestände sollen dauerhaft gespeichert und mit Herkunftsstatus im MES angezeigt werden.

## Kontext

Bestätigte gute Produkteinheiten aus Produktions- und Lieferaufträgen werden zusätzlich als relative Lagerbewegungen auf der Ausgangsqueue `storage` veröffentlicht: Produktion `+1`, Auslieferung `-1`. Die Nachricht enthält `product_id` und `quantity_delta`; ihre dauerhafte AMQP-`message_id` erlaubt Empfängern die Deduplizierung. Eine persistente Outbox hält Ereignisse bei Broker-Ausfällen zur erneuten Zustellung bereit. Der eingehende Consumer bleibt davon getrennt, deaktiviert bis eine eigene Eingangsqueue konfiguriert ist. Das eingehende Vertragsformat und der Stale-Grenzwert sind weiterhin nicht bestätigt.

## Quellen

- Prompt des Benutzers vom 13.10.2026
- Ergänzung des Benutzers vom 14.10.2026: bestätigte Produktion als `+1`, Auslieferung als `-1`
- `backend/app/clients/rabbitmq/base.py`
- `backend/app/models/storage.py`
- `backend/app/routers/storage_router.py`
- `frontend/app/inventory/page.tsx`
- `README.md` (RabbitMQ-Integration)

Nicht belegt sind Eingangsqueue, Snapshot-/Delta-Nachrichtenformat und Aktualitätsgrenze.

## Inhalt

### Ursprünglicher Prompt

Aktuelle Lagerbestände aus dem vorhandenen RabbitMQ-Projekt sollen im MES sichtbar sein. Das Backend soll Bestandsnachrichten validieren und in PostgreSQL übernehmen. Produkt/Artikel, verfügbarer Bestand und letzte Aktualisierung sollen in der Oberfläche erscheinen. Snapshot und Änderung sind zu unterscheiden; doppelte oder ungültige Nachrichten dürfen Bestände nicht verfälschen. Bei Broker-Ausfall bleiben letzte Bestände erhalten und werden als veraltet gekennzeichnet; unbekannte Bestände sind nicht null.

### Kritische Bewertung

#### 1. Welcher Ist-Zustand liegt vor und wie grenzt sich die Änderung ab?

**Antwort:** Der Publisher schreibt bestätigte gute Produkteinheiten aus Produktionsaufträgen als `+1` und aus Lieferaufträgen als `-1` auf `storage`. Die Veröffentlichung wird dauerhaft vorgemerkt und im bestehenden Auftragsworker wiederholt, bis RabbitMQ sie bestätigt. Fehlgeschlagene Einheiten sowie nicht produktbezogene manuelle Mengenbewertungen erzeugen kein Ereignis. Die eingehende Queue bleibt separat; `storage` darf nicht als Eingangsqueue verwendet werden. Der genaue Empfangsvertrag der Lager-/ERP-Gruppe ist weiterhin offen.

#### 2. Welches beobachtbare Verhalten wird erwartet und welchen Nutzen erzeugt es?

**Antwort:** Erfolgreich produzierte Einheiten erhöhen und erfolgreich ausgelieferte Einheiten verringern den ERP-seitigen Bestand jeweils um eins. Eingehende, gültige ERP-Nachrichten sollen den MES-Bestand dauerhaft ändern. Die Oberfläche zeigt Artikel, bekannte Menge, letzten Aktualisierungszeitpunkt sowie unbekannte und veraltete Zustände. Nach Backend-Neustart bleiben zuletzt gespeicherte Mengen und noch nicht veröffentlichte Ausgangsereignisse erhalten.

#### 3. Welche Auswirkungen, Randfälle und Regressionsrisiken müssen berücksichtigt werden?

**Antwort:** Die Lager-/ERP-Gruppe muss Eingangsqueue und Routing, JSON-Beispiele für Snapshot und Änderung, Zeitstempel und Aktualitätsgrenze bestätigen. Der Ausgangsvertrag ist auf relative Einheitenbewegungen festgelegt; Empfänger müssen die AMQP-`message_id` zur Deduplizierung wiederholter Zustellungen berücksichtigen. Der Consumer bleibt deaktiviert, solange keine separate Eingangsqueue konfiguriert ist.

### Entscheidung

Assessed. Die ausgehende Richtung ist fachlich festgelegt und implementiert. Die Idee bleibt wegen des noch offenen eingehenden Vertrags und der Aktualitätsgrenze `Assessed`; diese Punkte müssen vor dem Aktivieren des Consumers mit der Lager-/ERP-Gruppe bestätigt werden.

### Abgeleitete Specs

- Keine Bugfix-Spec: Es handelt sich um ein neues Feature.

## Beziehungen

- **Voraussetzung:** `harness/_idea.md`
- **Ergänzt:** `harness/_uiux.md`, `harness/_unittest.md`
- **Ergebnis:** `backend/app/workers/storage_consumer.py`, `backend/app/services/storage_outbox.py`, Storage-API und Lagerbestandsseite

## Offene Punkte

- Bestätigung des Vertragsentwurfs in `README.md` durch die Lager-/ERP-Gruppe.
- Bestätigung des Standardwerts für `STORAGE_STALE_AFTER_SECONDS`.

## Pflege

- **Aktualisierung:** Nach Bestätigung des Nachrichtenvertrags und bei Änderungen an Consumer oder Storage-API.
- **Ablösung:** Durch eine aktualisierte Feature-Dokumentation oder Bugfix-Specs bei fehlerhaftem Verhalten.

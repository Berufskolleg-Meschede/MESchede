# Lagerbestände per RabbitMQ übernehmen

## Meta

- **Typ:** Idee
- **State:** Assessed
- **Geltungsbereich:** Backend (RabbitMQ, PostgreSQL, Storage-API), Frontend (Lagerbestandsseite)

## Zweck

Eingehende Lagerbestände sollen dauerhaft gespeichert und mit Herkunftsstatus im MES angezeigt werden.

## Kontext

Der bestehende RabbitMQ-Client veröffentlicht MES-Änderungen mit `product_id` und `quantity_delta` auf der Queue `storage`. Ein Consumer für eingehende Bestände ist nicht vorhanden. Das Storage-Modell speichert bisher Menge und Artikel-ID; die vorhandene Lagerseite verwendet Mockdaten. Der bestätigte Eingangskontrakt der Lager-/ERP-Gruppe liegt noch nicht vor.

## Quellen

- Prompt des Benutzers vom 13.10.2026
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

**Antwort:** Der Code enthält nur einen Publisher für ausgehende Änderungsereignisse auf `storage`. Ein Consumer fehlt. Diese Queue darf nicht ungeprüft als Eingang verwendet werden, da dadurch Nachrichten für ERP-Konsumenten abgefangen werden könnten. Das Backend besitzt Storage-CRUD; die UI nutzt derzeit Mockdaten.

#### 2. Welches beobachtbare Verhalten wird erwartet und welchen Nutzen erzeugt es?

**Antwort:** Gültige Eingangsnachrichten sollen den Artikelbestand dauerhaft ändern. Die Oberfläche zeigt Artikel, bekannte Menge, letzten Aktualisierungszeitpunkt sowie unbekannte und veraltete Zustände. Nach Backend-Neustart bleiben zuletzt gespeicherte Mengen verfügbar.

#### 3. Welche Auswirkungen, Randfälle und Regressionsrisiken müssen berücksichtigt werden?

**Antwort:** Die Lager-/ERP-Gruppe muss Eingangsqueue und Routing, JSON-Beispiele für Snapshot und Änderung, eindeutige Ereignisidentität, Reihenfolge/Zeitstempel und Aktualitätsgrenze bestätigen. Ohne diese Angaben kann der Consumer nur mit einem ausdrücklich als Entwurf markierten Vertrag arbeiten. Der Consumer bleibt deaktiviert, solange keine separate Eingangsqueue konfiguriert ist.

### Entscheidung

Assessed. Der Benutzer hat die Umsetzung ausdrücklich beauftragt. Die Anwendungserwartungen sind vorbereitet; der Nachrichtenvertrag und die Aktualitätsgrenze bleiben fachlich offen und müssen vor realem Brokerbetrieb mit der Lager-/ERP-Gruppe bestätigt werden.

### Abgeleitete Specs

- Keine Bugfix-Spec: Es handelt sich um ein neues Feature.

## Beziehungen

- **Voraussetzung:** `harness/_idea.md`
- **Ergänzt:** `harness/_uiux.md`, `harness/_unittest.md`
- **Ergebnis:** `backend/app/workers/storage_consumer.py`, Storage-API und Lagerbestandsseite

## Offene Punkte

- Bestätigung des Vertragsentwurfs in `README.md` durch die Lager-/ERP-Gruppe.
- Bestätigung des Standardwerts für `STORAGE_STALE_AFTER_SECONDS`.

## Pflege

- **Aktualisierung:** Nach Bestätigung des Nachrichtenvertrags und bei Änderungen an Consumer oder Storage-API.
- **Ablösung:** Durch eine aktualisierte Feature-Dokumentation oder Bugfix-Specs bei fehlerhaftem Verhalten.

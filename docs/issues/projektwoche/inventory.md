# Lagerbestandsübersicht

<!-- meschede-projektwoche-v2:INVENTORY -->
## Ziel

Aktuelle Lagerbestände aus dem vorhandenen RabbitMQ-Projekt sind im MES sichtbar.

## Anforderungen

- Vorhandene RabbitMQ-Anbindung prüfen und wiederverwenden; Nachrichtenformat und Bestandsverantwortung mit der Lager-/ERP-Gruppe abstimmen.
- Bestandsnachrichten im Backend lesen, validieren und in PostgreSQL übernehmen.
- Produkt bzw. Artikel, verfügbaren Bestand und letzte Aktualisierung in der Oberfläche anzeigen.
- Snapshot- und Änderungsnachrichten korrekt unterscheiden; doppelte Zustellung darf Bestände nicht verfälschen.
- Bei Broker-Ausfall letzte bekannte Bestände erhalten und als veraltet kennzeichnen. Noch unbekannte Bestände sind nicht 0.

## Akzeptanzkriterien

- [ ] Eine gültige RabbitMQ-Nachricht verändert den richtigen Bestand in der UI.
- [ ] Doppelte oder ungültige Nachrichten erzeugen keine falschen Mengen.
- [ ] Verbindungsprobleme und fehlende Daten sind erkennbar.
- [ ] Letzte Bestände bleiben nach Backend-Neustart verfügbar.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Bestände, Artikel/Produkte und Aktualitäts-/Verbindungsanzeige in die Übersicht einbauen.
- [ ] **Person 2 – Backend:** RabbitMQ-Consumer wiederverwenden/ergänzen; Validierung, persistente Bestände und Lese-API bereitstellen.
- [ ] **Person 3 – Anbindung und Prüfung:** Nachrichtenvertrag und RabbitMQ-Zugang mit der Lagergruppe klären; Updates, Duplikate und Ausfälle gemeinsam prüfen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Queue, welcher Routing-Key und welches Nachrichtenformat werden verwendet?
- Sind die Nachrichten vollständige Bestände oder Änderungen?
- Wie wird festgestellt, ob ein ereignisbasiert übermittelter Bestand noch aktuell ist?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:INVENTORY:links-complete -->

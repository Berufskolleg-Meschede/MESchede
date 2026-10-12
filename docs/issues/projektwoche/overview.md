# Auftrags- und Produktionsübersicht

<!-- meschede-projektwoche-v2:OVERVIEW -->
## Ziel

Eine zentrale Ansicht zeigt den aktuellen Produktions- und Kommissionierstatus sowie die wartenden Aufträge und Produktqueue.

## Anforderungen

- Aktive Produktions- und Lieferaufträge getrennt mit ID, Status, Sollmenge und bearbeiteter Menge anzeigen.
- Produktqueue der Steuerung mit Produktinformationen, Serien-/Sequenznummer, Ergebnis und Fehlercode anzeigen, soweit diese Werte verfügbar sind.
- Wartende MES-Aufträge getrennt von den Produkteinheiten des aktiven Auftrags darstellen.
- Rückmeldungen per OPC UA lesen, den passenden Aufträgen zuordnen und relevante Status-/Laufdaten in PostgreSQL speichern.
- Fachliche Auftragsstatus und die tatsächlichen Start-/Endsignale zu Beginn an der Anlage prüfen. Ein einzelner Rohwert oder ein angenommenes POST gilt nicht ohne Nachweis als Abschluss.
- Daten regelmäßig aktualisieren; Verbindungsprobleme, letzte Aktualisierung und unbekannte/veraltete Daten sichtbar machen.
- Gemeinsame API-Datenfelder und Statusbegriffe für die Oberflächen abstimmen; reale Daten anbinden.
- Deutschsprachige, verständliche Darstellung mit Lade-, Leer- und Fehlerzuständen; Status zusätzlich zur Farbe als Text. Demo-Daten nur sichtbar gekennzeichnet.
- Nach Neustart bleiben Daten und wartende Aufträge erhalten; möglicherweise bereits gestartete Aufträge werden vor erneutem Schreiben abgeglichen.

## Akzeptanzkriterien

- [ ] Ein realer Auftrag lässt sich von der Annahme bis zur passenden Steuerungsrückmeldung im Browser verfolgen.
- [ ] Produktion, Kommissionierung, wartende Aufträge und Produktqueue sind unterscheidbar.
- [ ] Mehrfach gelesene Resultate erzeugen keine doppelten Mengen.
- [ ] Ein Verbindungsabbruch wird als Quellenproblem dargestellt und nicht als erfolgreicher Abschluss.
- [ ] Die Oberfläche ist auf den Projektgeräten verständlich und per Tastatur bedienbar.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Dashboard, aktive Aufträge, Warteschlangen und Produktqueue mit den vereinbarten Datenbeispielen darstellen.
- [ ] **Person 2 – Backend:** Gemeinsame DTOs/API, OPC-UA-Reader, Aggregation, persistente Status-/Laufdaten und Wiederaufnahme umsetzen.
- [ ] **Person 3 – Anbindung und Prüfung:** OPC-UA-Nodes und Start-/Endsignale praktisch prüfen, reale Beispielrückmeldungen liefern und den Datenfluss abnehmen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche PLC-Rückmeldungen und Statuswerte sind tatsächlich verfügbar?
- Dürfen Produktion und Kommissionierung parallel laufen?
- Was genau bedeutet der Lieferabschluss in der Fabriksimulation? Er bestätigt keine Zustellung beim Kunden.
- Wie werden fachliche Auftrag-ID und numerische PLC-Auftragsnummer eindeutig verbunden?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:OVERVIEW:links-complete -->

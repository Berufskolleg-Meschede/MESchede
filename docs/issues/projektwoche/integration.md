# Integration, Tests und Projektdokumentation

<!-- meschede-projektwoche-v2:INTEGRATION -->
## Ziel

Die Themen sind am echten System gemeinsam geprüft, dokumentiert und anhand eines Beispielablaufs vorführbar.

## Anforderungen

- Schnittstellen und Datenfluss mit ERP-, Webshop-, Lager- und Steuerungsgruppe abstimmen und im NAS-Netzwerk prüfen.
- Je einen Produktions- und Lieferauftrag vom manuellen bzw. externen Aufruf bis zur Rückmeldung im Browser testen.
- Mengen, Laufdauer, Lagerupdates und Konfigurationsänderungen mit erwarteten Werten vergleichen.
- Wiederholung, Verbindungsabbruch und Neustart prüfen; relevante Befunde korrigieren und nachtesten.
- Durchführung, Entscheidungen, Schwierigkeiten und Ergebnisse während der Woche dokumentieren.
- Architektur, API-Verträge, tatsächliche OPC-UA-Nodes, Einstellungen und Bedienung beschreiben.
- Beispielablauf für die Präsentation vorbereiten und gemeinsam proben.

## Akzeptanzkriterien

- [ ] Erwartete und tatsächliche Ergebnisse der Kernabläufe sind dokumentiert.
- [ ] Produktions- und Lieferauftrag, Analysen und Lagerdaten sind am realen System nachvollziehbar.
- [ ] Ausfälle und Neustarts erzeugen keine unbemerkten Doppelstarts oder erfundenen Ergebnisse.
- [ ] Dokumentation beschreibt den tatsächlich erreichten Stand; nicht geprüfte Fälle bleiben erkennbar offen.
- [ ] Die Vorführung wurde gemeinsam geprobt.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** UI-Abläufe prüfen, zugeordnete Fehler korrigieren, die eigenen Ergebnisse dokumentieren und Demo mit vorbereiten.
- [ ] **Person 2 – Backend:** API-/Datenverträge und Backend-Nachweise prüfen, die eigenen Ergebnisse dokumentieren und Demo mit vorbereiten.
- [ ] **Person 3 – Anbindung und Prüfung:** Gesamtdurchläufe, NAS-/Ausfall-/Neustarttests koordinieren, Schnittstellen abstimmen und die gemeinsame Dokumentation zusammenführen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Testaufträge und Anlagenzeiten stehen für die gemeinsame Prüfung zur Verfügung?
- Welche Nachweise und Aufteilung braucht die Projektarbeit?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:INTEGRATION:links-complete -->

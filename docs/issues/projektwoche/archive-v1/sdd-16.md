# [SDD-16] End-to-End-Abnahme mit realen Aufträgen, Ausfällen und Neustart durchführen

<!-- meschede-projektwoche-v1:SDD-16 -->
## Ziel

Die MVP-Anforderungen sind anhand reproduzierbarer Testfälle vom Auftrag bis zur Browserrückmeldung belegt.

## Einordnung

- Bereich: Integration; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05, REQ-06, REQ-07, REQ-08, REQ-09.
- Abhängigkeiten: SDD-14, SDD-15
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: Backend-Tests, NAS-Setup, MVP-Seiten, neues Abnahmeprotokoll

## Umsetzung

- Testmatrix aus REQ-IDs mit Erwartung/Istwert/Nachweis erstellen; je einen Produktions- und Lieferauftrag ausführen.
- Soll/Ist, Produktresultate, Laufdauer und Lagerupdate prüfen; identischen Request und wiederholte Polls testen.
- OPC-UA-/RabbitMQ-Ausfall, ungültige Node-/Intervalle und aktiven Konfigurationswechsel prüfen.
- Backend-/Containerneustart kontrolliert testen: History/Settings bleiben, wartende Aufträge bleiben, übertragene Aufträge werden abgeglichen.
- Unklare Rückmeldungen und kurze Läufe prüfen; bei bestätigter Parallelität beide Slots gleichzeitig abnehmen.

## Akzeptanzkriterien

- [ ] Jede REQ-ID hat ein dokumentiertes Prüfergebnis mit erwarteten und tatsächlichen Werten.
- [ ] Ein echter Produktions- und Lieferlauf wird bis zur passenden Abschlussrückmeldung im Frontend nachvollzogen.
- [ ] Retry/Repeated polling führt weder zu doppeltem PLC-Start noch doppelten Ergebnissen.
- [ ] Ausfälle erzeugen unknown/stale statt falschem Abschluss und blockieren andere Datenquellen nicht.
- [ ] History, Settings und Wiederaufnahme erfüllen den dokumentierten Neustartvertrag; Befunde werden an SDD-17 übergeben.

## Nachweis und Review

Abnahmeprotokoll mit Testdaten, Screenshots/Logs und Lauf-IDs; passende automatisierte Backendprüfungen ergänzen. Nicht ausgeführte Live-Fälle ausdrücklich offen lassen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

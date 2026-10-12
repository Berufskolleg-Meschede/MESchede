# [SDD-05] OPC-UA-Status und Produktqueue lesen und persistente Läufe aktualisieren

<!-- meschede-projektwoche-v1:SDD-05 -->
## Ziel

Ein Backend-Reader liefert korrelierte Rückmeldungen für Produktion und Lieferung mit nachvollziehbarer Aktualität.

## Einordnung

- Bereich: Backend; Schätzung: 8 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-06.
- Abhängigkeiten: SDD-02, SDD-04
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `backend/app/clients/opc_ua_client.py`, beide Queue-Worker, `backend/app/main.py`, `backend/tests/`

## Umsetzung

- Reader für Kopf/Auftragssteuerung, Auftragsnummer und Produktqueue nach bestätigtem Nodevertrag ergänzen.
- Auftragsstatus und Laufzeitpunkte durch verifizierte Übergänge aktualisieren; Start-/Endeereignisse einmal erfassen.
- Queueeinheiten nach Lauf/Identität upserten; alte/leere Slots ausschließen; Produktfehler vom Auftrags-/Verbindungsfehler trennen.
- Blockierende Bibliotheksaufrufe außerhalb des Eventloops ausführen; Client-/Workerzugriffe koordinieren und Backend-Lifecycle sauber beenden.
- Timeout/Reconnect mit letztem Datensatz, unknown/stale und nachvollziehbarer Diagnose behandeln; Polling aus aktiver Settingsversion beziehen.

## Akzeptanzkriterien

- [ ] Beide Slottypen liefern Auftrag, Rohwert, Produktresultate und letzten erfolgreichen Lesezeitpunkt.
- [ ] Fremde/veraltete PLC-Aufträge werden nicht dem aktuellen MES-Lauf zugeschlagen.
- [ ] Repeated polling verändert Mengen und Start-/Endzeit nicht mehrfach.
- [ ] Kurzlauf, unbekannter Rohwert, Timeout und Reconnect erzeugen nachvollziehbare Zustände; keine fingierten Abschlüsse.
- [ ] Eine externe Störung blockiert API und anderen Slot nicht; konfigurierte Abfrageintervalle wirken.

## Nachweis und Review

Vorhandene OPC-UA-Tests erweitern: reale Vertragsfixtures für Übergänge, kurzer Lauf, doppelte Resultate und Abbruch. Einen echten Lauf anhand der gespeicherten Rückmeldungen prüfen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#12: OPC UA Services implementieren](https://github.com/Berufskolleg-Meschede/MESchede/issues/12): Bestehende OPC-UA-Anbindung weiterverwenden; dieses Ticket ergänzt Reader, Rückmeldungsaggregation und persistente Laufzustände.

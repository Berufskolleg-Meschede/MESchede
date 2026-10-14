# [SDD-02] OPC-UA-Spike: Nodes, Rückmeldungen und Start-/Ende-Handshake prüfen

<!-- meschede-projektwoche-v1:SDD-02 -->
## Ziel

Mit der tatsächlichen Fabriksimulation nachweisen, welche Signale den passenden Auftrag starten und abschließen und welche Produktresultate gelesen werden können.

## Einordnung

- Bereich: Analyse; Schätzung: 5 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-05, REQ-06, REQ-07.
- Abhängigkeiten: Keine; kann sofort beginnen.
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `backend/app/clients/opc_ua_client.py`, `backend/app/workers/production_queue.py`, `backend/app/workers/delivery_queue.py`, alte OPC-UA-Designnotiz

## Umsetzung

- Für Produktions- und Kommissionierslot NodeIds/Namespace, BrowseNames, Datentypen und Zugriffsrechte erfassen.
- Beispielauftrag je Art durchführen; Rohwerte, IDs, Übergänge und Zeitpunkte für frei, Start, aktiv, Ende und Fehler protokollieren.
- Queuekapazität, Arrayindexierung, Produktstatus/Fehlercode, Serien-/Sequenzidentität und Zurücksetzen alter Einträge prüfen.
- Kurzen Lauf, Verbindungsabbruch, Timeout und bereits aktiven Auftrag berücksichtigen; Regel gegen unbeabsichtigte Wiederholung ableiten.
- Parallelität beider Slots und Bedeutung des Lieferabschlusses prüfen; zulässige Pollinggrenzen und Mengenlimits in SDD-01 übernehmen.

## Akzeptanzkriterien

- [ ] Eine geprüfte Node-/Datentyp-Tabelle und Rückmeldungsbeispiele für beide Arten liegen vor.
- [ ] Ein einzelner Rohwert 0 gilt nur dann als Abschluss, wenn korrelierter Ablauf diesen Schluss belegt; unklare Fälle werden unknown.
- [ ] Start wird nach vollständigen gültigen Auftragsfeldern geschrieben; PLC-Auftragsnummer ist kollisionsfrei zuordenbar.
- [ ] Queue-Resultatmapping und zulässige Parallelität sind bestätigt oder ausdrücklich als Blocker dokumentiert.

## Nachweis und Review

Kurzes Versuchprotokoll mit Erwartung, Istwert und Schlussfolgerung. Kontrollierte Testaufträge mit der betreuenden Anlagen-Gruppe abstimmen; Protokoll enthält keine Zugangsdaten.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#12: OPC UA Services implementieren](https://github.com/Berufskolleg-Meschede/MESchede/issues/12): Bestehende Anbindung und Schreibwege als Grundlage prüfen; hier werden Rückmeldungen und Handshake praktisch verifiziert.

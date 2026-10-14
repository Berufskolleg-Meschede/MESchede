# [SDD-08] Persistente und validierte Konfigurations-API bereitstellen

<!-- meschede-projektwoche-v1:SDD-08 -->
## Ziel

OPC-UA-Zielnodes und Abfrageintervall können reproduzierbar geändert werden, ohne einen laufenden Auftrag umzuleiten.

## Einordnung

- Bereich: Backend; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-07.
- Abhängigkeiten: SDD-01, SDD-02
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: neue Settings-Modelle/Migration/Router; `backend/app/main.py`, OPC-UA-Client und Worker

## Umsetzung

- GET/PUT /settings/ mit persistierter und aktiver Version implementieren; bestehende Umgebung als dokumentierte initiale Defaults verwenden.
- NodeId/Namespace, Pflichtfelder, Datentyp-/Zugriffsanforderungen und bestätigte Intervallgrenzen serverseitig prüfen.
- Einstellungen atomar speichern; konkurrierende Versionsänderung zurückweisen; Verbindungsprüfung mit Timeout.
- Änderungen an Zielnodes bei aktiven/unklaren Aufträgen nach dokumentierter Regel verschieben oder mit 409 ablehnen; keine Umleitung.
- Keine Secrets im GET, in Fehlermeldungen oder Logs ausgeben; bestätigtes vorhandenes Admin-Zugangsmodell berücksichtigen.

## Akzeptanzkriterien

- [ ] Gültige Werte sind nach API-/Backend-Neustart vorhanden und werden vom Reader/Worker tatsächlich verwendet.
- [ ] Leere/ungültige NodeIds und nicht zugelassene Intervalle erzeugen Feldfehler ohne Teiländerung.
- [ ] Ein aktiver Auftrag verwendet bis zur Klärung/Beendigung die ursprünglichen Nodes.
- [ ] Gespeicherte/aktive Version ist sichtbar oder Änderung wird mit verständlichem 409 abgelehnt.
- [ ] Ungültige oder unerreichbare Konfiguration wird nicht still als geprüft bestätigt.

## Nachweis und Review

Settings-Integrationstests für Persistenz, atomare Validierung, Versionskonflikt und aktiven Auftrag; gültigen Nodewechsel am Testsystem belegen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

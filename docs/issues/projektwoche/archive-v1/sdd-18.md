# [SDD-18] Projektdokumentation, Schnittstellen und Betriebsanleitung fertigstellen

<!-- meschede-projektwoche-v1:SDD-18 -->
## Ziel

Durchführung und Ergebnis der Projektwoche sind nachvollziehbar dokumentiert; die Software kann übernommen werden.

## Einordnung

- Bereich: Dokumentation; Schätzung: 24 Teamstunden.
- Anforderungen: REQ-09.
- Abhängigkeiten: Keine; kann sofort beginnen.
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `docs/specs/`, neue Schnittstellen-/Betriebs-/Abnahmedokumentation, `README.md`

## Umsetzung

- Ab Tag 1 gemeinsam dokumentieren: Entscheidungen, Datenfluss, Arbeitsaufteilung, Probleme und tatsächliche Ergebnisse (18 h).
- Software/Schnittstellen dokumentieren: drei Container, externe Dienste, Node-Tabelle, API-Verträge, Konfiguration und UI-Bedienung (4 h).
- Text, Querverweise, Quellen und Soll/Ist-Nachweise prüfen; fertigstellen (2 h).
- Annahmen, bestätigte Fakten und nicht getestete Fälle trennen; Zugangsdaten und private Kontaktdaten nicht ins Repository übernehmen.

## Akzeptanzkriterien

- [ ] Datenfluss ERP/Webshop → MES → OPC UA → Rückmeldung sowie RabbitMQ → Lageransicht ist nachvollziehbar.
- [ ] Betriebsanleitung erklärt NAS-Start, Konfiguration, Migration, Logs und Neustartverhalten.
- [ ] UI und Auswertung sind beschrieben; Messauflösung und Kommissionier-/Auslieferungsgrenze korrekt benannt.
- [ ] Endfassung enthält die tatsächlich verwendeten Nodes/APIs und erwartete/tatsächliche Testergebnisse.
- [ ] Dokumentation ist im Team gegengelesen; finale Abnahme-/Fehlerergebnisse aus SDD-16/17 sind eingearbeitet.

## Nachweis und Review

Fortlaufend bearbeiten; Abschluss nach SDD-16/17. Arbeit teilen, jede Person dokumentiert eigene Entscheidungen. 24 h sind bereits im 120-h-Teamumfang enthalten.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#14: create readme file for overview](https://github.com/Berufskolleg-Meschede/MESchede/issues/14): Geschlossenes Grundlagen-Ticket; vorhandene Architekturübersicht aktualisieren und um Ergebnisse der Projektwoche erweitern.

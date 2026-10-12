# [SDD-10] Live-Übersicht für Produktion, Kommissionierung, Produktqueue und Lager bauen

<!-- meschede-projektwoche-v1:SDD-10 -->
## Ziel

Die Produktionsleitung erkennt auf einer Seite, welcher Auftrag läuft, was bearbeitet wurde und wie aktuell die angezeigten Daten sind.

## Einordnung

- Bereich: Frontend; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-04, REQ-08.
- Abhängigkeiten: SDD-09
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `frontend/app/dashboard/page.tsx`, vorhandene Dashboard-/Stat-/Status-Komponenten

## Umsetzung

- Zwei getrennte aktive Slots mit ID, Status, Soll/Ist, gut/fehlerhaft und Laufdauer zeigen; eine reale Maschine darstellen.
- OPC-UA-Produktqueue mit bestätigten Feldern anzeigen; wartende MES-Aufträge ausdrücklich davon getrennt darstellen.
- Letzte Lagerdaten und Verbindungs-/Aktualitätsanzeige je Quelle integrieren.
- Polling über gemeinsamen API-Client mit Cleanup; Laden, leer, Fehler, unknown und stale behandeln.

## Akzeptanzkriterien

- [ ] Produktion und Kommissionierung sind getrennt und zeitgleich darstellbar, soweit die Anlage dies bestätigt.
- [ ] Keine Aktivität zeigt einen Leerzustand; unbekannter Status wird nicht als frei/fertig ausgegeben.
- [ ] Produktqueue und wartende Auftragsqueue sind unterschiedlich benannt; Werte passen zum DTO-Fixture.
- [ ] Ausfall einer Quelle erhält andere Anzeigen und kennzeichnet letzte Werte mit Zeitpunkt.
- [ ] Nach Integration mit SDD-07 erscheinen reale Rückmeldungen ohne Seitenneuladen.

## Nachweis und Review

UI-Prüfung mit aktiven, leeren und teilweise ausgefallenen Fixtures; nach SDD-07/15 echten Auftrag am NAS beobachten. Typecheck/Lint/Build.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

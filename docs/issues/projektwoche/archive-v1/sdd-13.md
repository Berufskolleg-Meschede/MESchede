# [SDD-13] Konfigurationsansicht für Zielnodes und Abfrageintervalle erstellen

<!-- meschede-projektwoche-v1:SDD-13 -->
## Ziel

Administratoren können die bestätigten MES-Einstellungen lesen und mit nachvollziehbarem Ergebnis speichern.

## Einordnung

- Bereich: Frontend; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-07, REQ-08.
- Abhängigkeiten: SDD-09
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: neue `frontend/app/settings/page.tsx`, gemeinsamer API-Client, vorhandene Formular-Komponenten

## Umsetzung

- GET /settings/ anzeigen; Felder für Produktions-/Liefernode und PLC-Intervall in ms; OPC-UA-Endpunkt nur gemäß Vertrag.
- Feldvalidierung und serverseitige Fehler zusammenführen; Speichern ausstehend/erfolgreich/fehlgeschlagen anzeigen.
- Gespeicherte/aktive Version bzw. 409 bei laufendem Auftrag erklären; konkurrierende Änderungen nicht still überschreiben.
- UI-Refresh und PLC-Abfrageintervall getrennt benennen; bestätigten Admin-Zugang berücksichtigen.

## Akzeptanzkriterien

- [ ] Gültige Werte werden gespeichert, neu geladen und bleiben nach Backend-Neustart sichtbar.
- [ ] Ungültiger Node/Intervall zeigt Feldfehler; keine erfolgreiche Meldung ohne Backendbestätigung.
- [ ] Bei aktivem Auftrag erklärt die UI die spätere Aktivierung oder Zurückweisung und zeigt keine falsche aktive Version.
- [ ] Keine Credentials erscheinen im Formular/Response; Tastatur und Labels funktionieren.
- [ ] Nach SDD-08/15 lässt sich ein erlaubter Wechsel am Testsystem nachvollziehen.

## Nachweis und Review

Fixtures für GET, erfolgreichen PUT, 422, 409, Timeout und Versionskonflikt; mit SDD-08 Persistenz und aktive Werte kontrollieren.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

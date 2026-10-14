# [SDD-17] Priorisierte Befunde aus Integration und Abnahme beheben

<!-- meschede-projektwoche-v1:SDD-17 -->
## Ziel

Die für den MVP relevanten Fehler aus der Abnahme sind korrigiert und erneut nachgewiesen.

## Einordnung

- Bereich: Integration; Schätzung: 4 Teamstunden.
- Anforderungen: REQ-09.
- Abhängigkeiten: SDD-16
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: betroffene Dateien gemäß Abnahmebefund; `docs/specs/projektwoche-mes-ui.md` und Abnahmeprotokoll

## Umsetzung

- Befunde nach falschem Start/Zählung/Datenverlust, blockiertem Kernablauf und UI-Problemen priorisieren.
- Konkrete Reproduktion, erwartetes Verhalten und minimale Korrektur je Befund dokumentieren.
- Relevante Tests und Abnahmeschritte erneut ausführen; Spec bei tatsächlich geänderter Fachentscheidung aktualisieren.
- Reicht der 4-Stunden-Puffer nicht, zusätzliche Fehler separat schätzen und Umfang mit dem Team neu planen.

## Akzeptanzkriterien

- [ ] Jeder bearbeitete Fehler hat Reproduktion und erfolgreichen Nachtest.
- [ ] Keine bekannten unbeabsichtigten Doppelstarts, Doppelzählungen oder Datenverluste werden als erledigt ausgegeben.
- [ ] Betroffene Typecheck/Lint/Build-/Backendprüfungen sind erfolgreich.
- [ ] Übrige Befunde sind sichtbar mit Priorität/Zuständigkeit erfasst; kein pauschaler Haken ohne Nachweis.

## Nachweis und Review

Vorher/Nachher im Abnahmeprotokoll, kleine Review-PRs und gezielter Regressionstest. Ticketbudget ist ein Puffer, keine Garantie für unbekannte Fehler.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

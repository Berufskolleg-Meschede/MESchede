# [SDD-14] Gemeinsame UI-Zustände, Navigation und Browserdarstellung prüfen

<!-- meschede-projektwoche-v1:SDD-14 -->
## Ziel

Alle MVP-Seiten sind auf den Projektgeräten verständlich und bei Fehlern weiterhin bedienbar.

## Einordnung

- Bereich: Frontend; Schätzung: 4 Teamstunden.
- Anforderungen: REQ-08.
- Abhängigkeiten: SDD-10, SDD-11, SDD-12, SDD-13
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: bestehende Layouts/Sidebars/Status-Badges, alle MVP-Seiten

## Umsetzung

- Deutschsprachige Navigation und konsistente Begriffe/Statusdarstellung fertigstellen.
- Laden, leer, Fehler, stale und unbekannt über alle Seiten prüfen; Fokus-/Tastaturabläufe und Feldlabels korrigieren.
- Bei 1280 px und 768 px Browserbreite Tabellen, Dialoge und Navigation prüfen; horizontales Scrollen gezielt ermöglichen.
- Demo-Markierung kontrollieren; Polling auf Unmount beenden und keine mehrfachen Hintergrundabfragen erzeugen.

## Akzeptanzkriterien

- [ ] Alle fünf MVP-Ansichten sind erreichbar und verwenden dieselben Statusbegriffe.
- [ ] Status ist ohne Farbe verständlich; Dialoge/Formulare vollständig per Tastatur bedienbar.
- [ ] Bei beiden Prüfbrowserbreiten werden zentrale Informationen und Speichern/Absenden nicht abgeschnitten.
- [ ] Fehler-/Leerzustand sind unterscheidbar; stale Werte tragen einen Zeitpunkt; Demo ist sichtbar gekennzeichnet.
- [ ] Typecheck, Lint und Produktionsbuild sind abschließend geprüft.

## Nachweis und Review

Kurzes UI-Prüfprotokoll mit den beiden Browserbreiten, Keyboard-Flow und repräsentativen Fehlerzuständen; sinnvolle Screenshots für Dokumentation.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

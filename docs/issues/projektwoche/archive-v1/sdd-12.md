# [SDD-12] Auswertung für tatsächliche Mengen und beobachtete Laufdauer erstellen

<!-- meschede-projektwoche-v1:SDD-12 -->
## Ziel

Die Analyse zeigt nachvollziehbare Produktionsresultate und Laufzeiten statt summierter Bestellmengen.

## Einordnung

- Bereich: Frontend; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-06, REQ-08.
- Abhängigkeiten: SDD-09
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: neue `frontend/app/analytics/page.tsx`, bestehende Chart-/Tabellen-Komponenten, Dashboard-Mengenberechnung

## Umsetzung

- Zeitraum-/Artfilter und Lauf-Tabelle mit Soll, bearbeitet, gut, fehlerhaft, Start, Ende und Dauer implementieren.
- Produktions- und Liefermengen getrennt darstellen; alle Summen aus Analytics-DTO statt geplanter quantity berechnen.
- UTC-Zeiten in Europe/Berlin darstellen; laufende Dauer vorläufig und fehlende Dauer unbekannt markieren.
- Messauflösung/Polling erklären; leere Daten, API-Ausfall und Aktualität behandeln; optional kleines Soll/Ist-Diagramm ohne Erweiterung zu OEE.

## Akzeptanzkriterien

- [ ] Fixture Soll=10, gut=7, Fehler=2 zeigt bearbeitet=9; keine geplanten 10 als Istproduktion.
- [ ] Kommissionierte Einheiten erhöhen den Produktionszähler nicht.
- [ ] Dauer stimmt mit bestätigten Start-/Endzeiten überein; bei fehlenden Zeitpunkten keine 0-Erfindung.
- [ ] Zeitraumgrenzen und Sommer-/Winterzeit folgen dem bestätigten Vertrag.
- [ ] Filter wirken und eine leere Auswahl zeigt Keine Daten; nach SDD-07 historische Läufe aus PostgreSQL sichtbar.

## Nachweis und Review

Ergebnisfixtures mit ungefüllten Slots, laufendem Lauf, zwei Arten und Zeitgrenzen prüfen; echte Laufdaten mit SDD-16 abgleichen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

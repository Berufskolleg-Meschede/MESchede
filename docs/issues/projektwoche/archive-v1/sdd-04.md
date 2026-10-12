# [SDD-04] Aufträge, Läufe und Produktresultate in PostgreSQL persistieren

<!-- meschede-projektwoche-v1:SDD-04 -->
## Ziel

Status und Auswertung überleben Neustarts; dieselben Aufträge/Produkte werden nicht mehrfach gezählt oder unkontrolliert erneut gestartet.

## Einordnung

- Bereich: Backend; Schätzung: 4 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-05, REQ-06.
- Abhängigkeiten: SDD-01, SDD-02
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `backend/app/models/`, `backend/app/db/`, `backend/alembic/versions/`, beide Queue-Worker

## Umsetzung

- Alembic-Migration für Auftrag, Lauf und Produktresultat erstellen; fachliche ID/Art und numerische PLC-ID separat speichern.
- UTC-Start-/Endzeit, letzter Rohstatus, letzte Beobachtung, Mengen und stabile Resultatidentität aus dem bestätigten Vertrag speichern.
- Eindeutigkeitsbedingungen für Art+ID und Lauf+Einheit sowie sinnvolle Transaktionsgrenzen festlegen.
- Persistierte wartende Aufträge und unklare bereits übertragene Aufträge beim Neustart unterscheiden; Abgleich statt blindem Neustart ermöglichen.

## Akzeptanzkriterien

- [ ] Migration funktioniert auf leerer DB und bestehendem Schema, ohne bestehende machine/user-Daten zu entfernen.
- [ ] Wiederholte Annahme derselben Art/ID und mehrfaches Einlesen desselben Ergebnisses erzeugen keine Duplikate.
- [ ] Gleiche ID mit anderem Payload ist ein Konflikt; gleiche ID unterschiedlicher Auftragsart bleibt unterscheidbar.
- [ ] Nach Neustart bleiben History und Warteschlange erhalten; unklar übertragene Aufträge sind abgleichbar und werden nicht automatisch erneut gestartet.

## Nachweis und Review

DB-Integrationstest für Eindeutigkeit, Resultat-Upsert und Wiederaufnahme; Migration anwenden und erhaltene Daten prüfen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#9: DB-Models komplett definieren](https://github.com/Berufskolleg-Meschede/MESchede/issues/9): Geschlossenes Grundlagen-Ticket; hier geht es um persistente Laufhistorie, Resultate und Wiederaufnahme für die UI.

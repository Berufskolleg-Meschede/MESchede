# Analysenübersicht

<!-- meschede-projektwoche-v2:ANALYTICS -->
## Ziel

Die Produktionsleitung kann produzierte Mengen und die Dauer einzelner Läufe nachvollziehen.

## Anforderungen

- Eine eigene Analysenübersicht mit Zeitraum- und Auftragsartfilter bereitstellen.
- Je Auftrag bzw. Lauf Sollmenge, bearbeitete Menge, gute und fehlerhafte Einheiten zeigen.
- Start, Ende und beobachtete Laufdauer darstellen; laufende Dauer als vorläufig kennzeichnen.
- Tatsächliche Resultate aus den OPC-UA-Rückmeldungen dauerhaft speichern und für die Auswertung bereitstellen.
- Wiederholtes Abfragen darf dieselben Produkte nicht mehrfach zählen. Geplante Mengen sind keine tatsächlich produzierte Menge.
- Produktions- und Liefermengen getrennt darstellen; fehlende Daten als unbekannt kennzeichnen.
- Auf eine einfache Auswertung begrenzen; umfangreiche Stillstandsanalysen sind nicht Teil der Projektwoche.

## Akzeptanzkriterien

- [ ] Ein Lauf mit Soll 10, 7 guten und 2 fehlerhaften Einheiten zeigt 9 bearbeitete Einheiten.
- [ ] Angezeigte Dauer passt zu den gespeicherten Start-/Endbeobachtungen; fehlende Zeiten ergeben keine erfundene Dauer.
- [ ] Filter wirken und gespeicherte Ergebnisse bleiben nach Neustart verfügbar.
- [ ] Lieferaufträge erhöhen den Produktionszähler nicht.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Filter, Ergebnisübersicht und Darstellung von Mengen und Laufdauer bauen.
- [ ] **Person 2 – Backend:** Historische Resultate und Zeitpunkte speichern und über eine gemeinsame Auswertungs-API liefern.
- [ ] **Person 3 – Anbindung und Prüfung:** Rückmeldungsfelder und Zeit-/Mengensemantik klären; erwartete Werte eines echten Laufs mit der Anzeige vergleichen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Tabellen und Diagramme helfen bei der Vorführung?
- Welche Rückmeldungen der Steuerung bestätigen Start, Ende und Produktresultate?
- Wie werden Zeitraumgrenzen und Messauflösung der Laufdauer erklärt?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:ANALYTICS:links-complete -->

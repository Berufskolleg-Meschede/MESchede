# Produktions- und Lieferaufträge manuell starten

<!-- meschede-projektwoche-v2:MANUAL -->
## Ziel

Benutzer können Produktions- und Lieferaufträge aus der MES-Oberfläche auslösen und anschließend verfolgen.

## Anforderungen

- Für beide Auftragsarten ein Formular bzw. einen Dialog mit Auftrag-ID, Produkt(en), Menge und den erforderlichen Auftragsdaten anbieten.
- Eingaben validieren und vor dem Absenden eine verständliche Zusammenfassung anzeigen.
- Vorhandene MES-Auftragsschnittstellen und Worker verwenden; das Backend schreibt in den jeweils passenden OPC-UA-Auftragsslot.
- Ein angenommener Auftrag wird dauerhaft gespeichert. Gleiche Auftragsart und ID mit gleichem Inhalt dürfen keinen zweiten Lauf starten; anderer Inhalt unter derselben ID ist ein Konflikt.
- Während des Absendevorgangs weitere Klicks verhindern; Annahme, bestätigter Start und Fehler unterscheiden.
- Bei unbekanntem Requestergebnis erst prüfen, ob der Auftrag schon angenommen wurde.
- Nach dem Anlegen den Auftrag in der Übersicht und im Detail zugänglich machen.

## Akzeptanzkriterien

- [ ] Ein Produktions- und ein Lieferauftrag lassen sich mit gültigen Testdaten aus der UI auslösen.
- [ ] Ungültige Mengen oder Produktdaten erzeugen verständliche Meldungen.
- [ ] Ein Doppelklick oder Retry erzeugt keinen zweiten Auftrag bzw. unbeabsichtigten zweiten Start.
- [ ] Die UI meldet nach Annahme noch keinen bestätigten PLC-Start.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Formulare und Auftragsdetail, Eingabeprüfung und Annahme-/Fehlerzustände umsetzen.
- [ ] **Person 2 – Backend:** Vorhandene POST-/Workerwege mit Validierung, dauerhafter Annahme und Schutz gegen doppelte Starts anbinden.
- [ ] **Person 3 – Anbindung und Prüfung:** Testdaten und zulässige Werte mit der Steuerungsgruppe abstimmen; beide Auftragsarten, Retry und Rückmeldungen prüfen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Pflichtfelder und Mengenlimits gelten an der Steuerung?
- Woher kommen gültige Produkt-/Artikelinformationen?
- Reicht ein Einzelproduktformular für die Vorführung oder werden gemischte Produktqueues benötigt?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:MANUAL:links-complete -->

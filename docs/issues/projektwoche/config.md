# Konfigurationsoberfläche

<!-- meschede-projektwoche-v2:CONFIG -->
## Ziel

Die MES-Einstellungen lassen sich über eine gemeinsame Oberfläche verwalten.

## Anforderungen

- OPC-UA-Zielnodes für Produktions- und Lieferaufträge anzeigen und ändern.
- Abfrageintervall mit eindeutig angegebener Einheit einstellen; zulässige Grenzen mit der Steuerungsgruppe klären.
- Einstellungen im Backend validieren und in PostgreSQL speichern; nach einem Neustart wieder laden.
- Ungültige Werte und fehlgeschlagenes Speichern verständlich am Feld bzw. als Meldung anzeigen.
- Während eines laufenden Auftrags dürfen neue Zielnodes diesen nicht unbemerkt umleiten. Eine Änderung wird bis zu einem sicheren Zeitpunkt zurückgestellt oder klar zurückgewiesen.
- Laden, Speichern und erfolgreiche Übernahme sind in der Oberfläche erkennbar.

## Akzeptanzkriterien

- [ ] Gültige Nodes und Intervalle lassen sich speichern und nach Neustart wieder anzeigen.
- [ ] Das Backend verwendet die bestätigten Einstellungen tatsächlich.
- [ ] Ungültige Angaben werden ohne Teiländerung zurückgewiesen.
- [ ] Eine Änderung während eines aktiven Auftrags wird nachvollziehbar behandelt.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Formular für Nodes und Intervalle, Laden/Speichern und verständliche Fehlermeldungen bauen.
- [ ] **Person 2 – Backend:** Settings-API, serverseitige Validierung, PostgreSQL-Persistenz und sichere Aktivierung umsetzen.
- [ ] **Person 3 – Anbindung und Prüfung:** Node-/Intervallangaben mit der Steuerungsgruppe klären und Änderungen am laufenden Testsystem prüfen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche konkreten NodeIds und weiteren Einstellungen werden benötigt?
- Welche Intervalle sind an der Anlage sinnvoll und zulässig?
- Wie wird der Zugriff auf die Konfigurationsansicht im vorhandenen Zugangsmodell abgegrenzt?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:CONFIG:links-complete -->

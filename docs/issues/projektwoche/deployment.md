# Docker-Betrieb auf dem Synology NAS

<!-- meschede-projektwoche-v2:DEPLOYMENT -->
## Ziel

Das MES ist als gemeinsames Docker-Projekt auf dem Synology NAS im Netzwerk erreichbar.

## Anforderungen

- Genau drei dauerhaft laufende MES-Container vorsehen: Frontend, Backend und PostgreSQL.
- OPC-UA-Steuerung, RabbitMQ, ERP und Webshop als bestehende externe Projekte/Dienste im Netzwerk anbinden.
- Worker und Consumer innerhalb des Backends betreiben.
- Frontend-Build, Browser-API-Adresse, Ports und Netzwerke für NAS-Betrieb konfigurieren; keine Browseraufrufe an localhost oder Docker-interne Hostnamen.
- PostgreSQL-Daten persistent halten; Start, Healthchecks, Neustart und Migrationen nachvollziehbar regeln.
- Konfigurationsbeispiele ohne echte Zugangsdaten und eine kurze Start-/Betriebsanleitung bereitstellen.
- NAS-Architektur und unterstützte Images vor dem Deployment prüfen.

## Akzeptanzkriterien

- [ ] Im MES-Projekt laufen genau Frontend, Backend und PostgreSQL.
- [ ] Ein weiterer Rechner im LAN erreicht die UI und deren Backend-Daten.
- [ ] Daten bleiben nach Container-Neustart erhalten.
- [ ] Das Team kann das Projekt anhand der Anleitung starten und Logs prüfen.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Frontend-Docker-Build und Browserzugriff auf die gemeinsame API bereitstellen.
- [ ] **Person 2 – Backend:** Backend-/PostgreSQL-Betrieb, Migrationen und persistentes DB-Volume vorbereiten.
- [ ] **Person 3 – Anbindung und Prüfung:** Compose-Projekt auf dem NAS zusammenführen; Netzwerk, Ports, externe Dienste und Start-/Betriebsanleitung prüfen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche NAS-Architektur und Container-Manager-/Docker-Version stehen bereit?
- Welche Hostnamen, Ports und Netzwerke verwenden die vorhandenen Projekte?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:DEPLOYMENT:links-complete -->

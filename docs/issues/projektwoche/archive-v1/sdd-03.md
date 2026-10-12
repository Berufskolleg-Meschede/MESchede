# [SDD-03] MES mit genau drei Docker-Services auf dem Synology NAS betreiben

<!-- meschede-projektwoche-v1:SDD-03 -->
## Ziel

Frontend, Backend und PostgreSQL sind im gemeinsamen Netzwerk reproduzierbar startbar; bestehende externe Projekte bleiben erreichbar.

## Einordnung

- Bereich: NAS; Schätzung: 8 Teamstunden.
- Anforderungen: REQ-01.
- Abhängigkeiten: Keine; kann sofort beginnen.
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `docker-compose.yaml`, `backend/Dockerfile`, `frontend/next.config.mjs`, neuer Frontend-Dockerfile und Betriebsdokumentation

## Umsetzung

- NAS-Bestand, CPU-Architektur, Container-Manager/Docker, Ports, Netzwerke und Zuständigkeiten dokumentieren.
- Frontend-Build ergänzen; Compose für exakt frontend/backend/db fertigstellen. Worker/Consumer im Backend; vorhandenes RabbitMQ extern anbinden.
- Relative Browser-API über Frontend-Weiterleitung oder bestätigten bestehenden NAS-Proxy einrichten; Containerhostname nicht an Browser ausliefern.
- Persistentes PostgreSQL-Volume, Startreihenfolge/Healthchecks, Restart-Verhalten und Migrationsablauf definieren; keine Dev-Source-Bind-Mounts im NAS-Betrieb.
- Beispielumgebung mit Platzhaltern für OPC UA/ERP/RabbitMQ/DB bereitstellen; reale Secrets separat verwalten.

## Akzeptanzkriterien

- [ ] Compose definiert genau drei MES-Services; NAS zeigt sie laufend und ein anderer LAN-Rechner erreicht die UI.
- [ ] Browserrequests treffen das Backend ohne localhost-Fallback oder Docker-DNS im Browser.
- [ ] Daten bleiben nach Container-Neustart erhalten; Images passen zur NAS-Architektur.
- [ ] Externe Verbindungen sind dokumentiert und einzeln geprüft; externer Ausfall löst keinen Backend-Restartloop aus.
- [ ] Ein Teammitglied kann anhand der Anleitung starten, stoppen und Logs prüfen.

## Nachweis und Review

Compose-Konfiguration validieren und auf NAS testen. Erreichbarkeits-, Neustart- und Verbindungsnachweise dokumentieren; keine fiktive Live-Abnahme bei fehlendem NAS-Zugriff.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

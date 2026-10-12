# [SDD-06] RabbitMQ-Lagerdaten konsumieren und aktuelle Bestände bereitstellen

<!-- meschede-projektwoche-v1:SDD-06 -->
## Ziel

Das Backend liest Lagerereignisse aus dem vorhandenen RabbitMQ-Projekt und stellt letzte gültige Bestände mit Aktualität bereit.

## Einordnung

- Bereich: Backend; Schätzung: 4 Teamstunden.
- Anforderungen: REQ-04.
- Abhängigkeiten: SDD-01
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `backend/app/routers/storage_router.py`, `backend/app/main.py`, neuer Consumer/Bestandsservice und Migration

## Umsetzung

- Mit der Lager-Gruppe vHost/Exchange/Queue/Routing, Produktzuordnung, Snapshot/Delta, Ereignisidentität und Nachrichtenschema klären.
- Consumer im Backend-Lifecycle starten und reconnecten; validieren und in PostgreSQL übernehmen; Ack nach erfolgreicher Persistenz.
- Duplikat-/Reihenfolgeverhalten passend zum bestätigten Vertrag implementieren; fehlerhafte Nachrichten nachvollziehbar behandeln.
- GET /storage/ und Detail falls benötigt mit letzter Beobachtung und Quellenstatus bereitstellen; RabbitMQ-Aktualität unabhängig vom PLC-Polling definieren.

## Akzeptanzkriterien

- [ ] Vertragsbeispiele und Snapshot-/Delta-Regel sind dokumentiert; es wurde keine unbekannte Feldstruktur vorausgesetzt.
- [ ] Eine gültige Nachricht verändert den richtigen Bestand; erneute Zustellung zählt ein Delta nicht doppelt.
- [ ] Ungültige Nachricht und Broker-Ausfall löschen letzte Bestände nicht und erscheinen als Quellenproblem.
- [ ] Lagerdaten bleiben nach Backend-Neustart erhalten; initial fehlender Bestand ist unbekannt, nicht 0.
- [ ] Kein zusätzlicher RabbitMQ-Container wird im MES-Compose gestartet.

## Nachweis und Review

Consumer-Test mit gültiger, doppelter und fehlerhafter Nachricht sowie Reconnect; echte Nachricht am NAS gegen GET /storage/ abgleichen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#11: RabbitMQ Funktionalität](https://github.com/Berufskolleg-Meschede/MESchede/issues/11): Geschlossenes Grundlagen-Ticket. Vorhandene Umsetzung zuerst auffinden und wiederverwenden; hier nur fehlende Validierung, persistente Bestände, Aktualität und UI-API ergänzen.

# [SDD-15] ERP, Webshop, RabbitMQ und Feldebene am NAS integrieren

<!-- meschede-projektwoche-v1:SDD-15 -->
## Ziel

Die verteilten Projekte verwenden abgestimmte reale Schnittstellen; manuelle und externe Aufträge folgen demselben MES-Datenfluss.

## Einordnung

- Bereich: Integration; Schätzung: 8 Teamstunden.
- Anforderungen: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05, REQ-07.
- Abhängigkeiten: SDD-03, SDD-07, SDD-08, SDD-09
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `README.md`, NAS-Betriebskonfiguration, Backend-Clients/Router und Frontend-API-Zugriff

## Umsetzung

- Mit anderen Gruppen reale URLs/Pfade, Payloads, Verantwortlichkeiten und Beispielaufträge für ERP/Webshop/Feldebene klären.
- README-Hinweise /inventory, /article und /order praktisch prüfen; keine zweite widersprüchliche Bestandsquelle aufbauen.
- NAS-Netzwerk/Ports und Produktionsumgebung konfigurieren; drei MES-Services mit externen Diensten verbinden.
- Einen externen und einen UI-Auftrag durch dieselben Annahme-/Workerpfade verfolgen; PLC-ID und Rückmeldung korrelieren.
- Konfigurationswechsel und RabbitMQ-Bestandsupdate mit beteiligten Gruppen testen; verbleibende Schnittstellenabweichungen dokumentieren.

## Akzeptanzkriterien

- [ ] Eine geprüfte Schnittstellenmatrix mit Datenquelle/Eigentümer und Beispielpayloads liegt vor.
- [ ] Webshop-/ERP-Auftragsweg bleibt kompatibel; manuelle Aufträge erscheinen im selben Statusmodell.
- [ ] Browser im LAN erreicht echte API-Daten; OPC UA und RabbitMQ sind nachweislich angebunden.
- [ ] Kommissionierabschluss wird fachlich korrekt beschriftet, ohne Kundenzustellung zu behaupten.
- [ ] Abweichungen oder externe Blocker sind mit Zuständigkeit dokumentiert und aus Live-Nachweisen klar ersichtlich.

## Nachweis und Review

Integrationsprotokoll mit Request/Antwortreferenzen, PLC-ID und Browserergebnis ohne Zugangsdaten. Früh einen Durchlauf durchführen, nicht erst zur Präsentation.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

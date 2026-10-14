# Projektwoche: Themenübersicht und Aufgabenverteilung

<!-- meschede-projektwoche-v2:COLLECTION -->
## Ziel der Projektwoche

Die MES-Weboberfläche bündelt Auftragsstatus, Produktion/Kommissionierung, Lagerbestände, manuelle Aufträge, einfache Analysen und Konfiguration. Die Aufgaben sind nach Themen zusammengefasst; jedes Themen-Issue enthält Anforderungen, Akzeptanzkriterien, offene Fragen und Arbeitspakete für drei Personen.

## Themen-Issues

- [ ] [Konfigurationsoberfläche #32](https://github.com/Berufskolleg-Meschede/MESchede/issues/32)
- [ ] [Analysenübersicht #31](https://github.com/Berufskolleg-Meschede/MESchede/issues/31)
- [ ] [Auftrags- und Produktionsübersicht #29](https://github.com/Berufskolleg-Meschede/MESchede/issues/29)
- [ ] [Produktions- und Lieferaufträge manuell starten #30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30)
- [ ] [Lagerbestandsübersicht #25](https://github.com/Berufskolleg-Meschede/MESchede/issues/25)
- [ ] [Docker-Betrieb auf dem Synology NAS #22](https://github.com/Berufskolleg-Meschede/MESchede/issues/22)
- [ ] [Integration, Tests und Projektdokumentation #35](https://github.com/Berufskolleg-Meschede/MESchede/issues/35)

## Aufteilung auf drei Personen

Die Rollen sind ein Vorschlag für die Codeaufteilung. Wer sie übernimmt, legt ihr im Kommentarverlauf fest; GitHub-Assignees können danach gesetzt werden.

| Rolle | Arbeit | Geplante Teamstunden |
|---|---|---:|
| Person 1 – Oberfläche | UI für die Themen, gemeinsame Navigation und Zustände (28 h); Fehlerkorrektur/Nachtests (3 h); eigene Dokumentation (8 h); Demo (1 h) | **40** |
| Person 2 – Backend | APIs, Persistenz, Reader/Consumer und Settings (28 h); gemeinsamer Fach-/Datenvertrag (3 h); eigene Dokumentation (8 h); Demo (1 h) | **40** |
| Person 3 – Anbindung und Integration | NAS/Docker (8 h); OPC-UA-Prüfung und Schnittstellen-/Datenflussklärung (9 h); Integration, Abnahme und Fehlerkorrektur (15 h); eigene Dokumentation (8 h) | **40** |
| **Gesamt** | 3 Personen × 5 Tage × 8 Stunden | **120** |

Die Stunden sind Planungswerte aus dem Projektantrag. Nach der ersten Anlagenprüfung bei Bedarf Arbeit verschieben. Die Arbeitspakete in den Issues sind innerhalb desselben Themas einzeln übernehmbar; ein Themen-Issue ist erst fertig, wenn seine Akzeptanzkriterien gemeinsam erfüllt sind.

## Paralleles Vorgehen

1. Zu Beginn gemeinsam Kernfelder und Beispiele für beide Auftragsarten festlegen. Person 3 prüft die realen OPC-UA-Nodes und Rückmeldungen; Person 2 legt daraus den API-Vertrag fest.
2. Person 1 baut mit abgestimmten Beispieldaten die Oberfläche. Person 2 entwickelt Backend und Datenhaltung. Person 3 bereitet NAS und externe Anbindungen vor.
3. Früh einen echten Auftrag gemeinsam durchlaufen lassen. Weitere Anforderungen, Entscheidungen und Fortschritt im jeweiligen Themen-Issue kommentieren; bestätigte Änderungen in dessen Beschreibung übernehmen.
4. Jede Person prüft und dokumentiert ihre Änderungen. Integration, Abnahme und Vorführung laufen gemeinsam.

## Gemeinsamer Rahmen

- Betrieb auf dem Synology NAS im Netzwerk mit genau drei MES-Containern: Frontend, Backend und PostgreSQL. OPC-UA-Steuerung, RabbitMQ, ERP und Webshop sind vorhandene externe Dienste/Projekte.
- Auftrags- und Produktstatus kommen aus bestätigten OPC-UA-Rückmeldungen; Startbefehle laufen über das MES-Backend. Lagerdaten kommen über RabbitMQ.
- Ein angenommener Auftrag bedeutet noch keinen bestätigten Produktionsstart. Wiederholungen dürfen keinen unbeabsichtigten zweiten Start auslösen.
- Mengen und Laufdauer beruhen auf tatsächlichen Rückmeldungen; geplante Mengen werden getrennt dargestellt. Fehlende/veraltete Daten müssen erkennbar sein.
- Lieferstatus bezeichnet die von der Fabriksimulation bestätigte Kommissionierung/Übergabe; eine Kundenzustellung ist damit nicht belegt.
- Zugangsdaten und reale Node-/Nachrichtenverträge werden mit den beteiligten Gruppen abgestimmt. Umfangreiche Stillstandsanalysen und neue ERP-/Webshop-Funktionen gehören nicht zum MVP.

## Abnahme

- [ ] Produktions- und Lieferauftrag sind vom Aufruf bis zur passenden Rückmeldung in der UI nachvollziehbar.
- [ ] Konfiguration, Analysen und Lageranzeige erfüllen ihre Themen-Anforderungen.
- [ ] Ausfälle, Wiederholungen und Neustart wurden geprüft.
- [ ] Dokumentation ist aktuell und Vorführung geprobt.

Die früheren Detail-Issues #20–#38 wurden in diese Themenstruktur eingeordnet. Zusammengeführte Detailtickets bleiben als Historie geschlossen und verweisen auf ihr aktuelles Themen-Issue. Bestehende Grundlagen-Issues außerhalb dieser Sammlung bleiben als Referenzen erhalten.

<!-- meschede-projektwoche-v2:COLLECTION:links-complete -->

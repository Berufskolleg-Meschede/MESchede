# GitHub-Issue-Sammlung für die Projektwoche

Veröffentlicht auf GitHub: **1 Sammel-Issue und 19 Teil-Issues**, insgesamt **120 Teamstunden**. [Sammlung #19](https://github.com/Berufskolleg-Meschede/MESchede/issues/19) enthält die vollständige Spezifikation und verlinkt alle Aufgaben. Die Teil-Issues #20 bis #38 enthalten Links zur Sammlung und zu ihren Abhängigkeiten. Veröffentlichungsstand: `published.json`.

Die Spezifikation ist unter `../../specs/projektwoche-mes-ui.md` gespeichert und im [Sammel-Issue-Entwurf](sdd-00.md) vollständig enthalten. Jeder Teilentwurf hat Umfang, Abhängigkeiten, REQ-IDs, Akzeptanzkriterien und Prüfhinweise. `backlog.json` ist die maschinenlesbare Quelle. Keine Änderungen am Anwendungscode wurden vorgenommen.

| Issue | Aufgabe | Bereich | Teamstunden | Abhängigkeiten |
|---|---|---|---:|---|
| [SDD-01 #20](https://github.com/Berufskolleg-Meschede/MESchede/issues/20) · [Entwurf](sdd-01.md) | MVP-Spezifikation, API-Verträge und UI-Zustände festlegen | Analyse | 7 | — |
| [SDD-02 #21](https://github.com/Berufskolleg-Meschede/MESchede/issues/21) · [Entwurf](sdd-02.md) | OPC-UA-Spike: Nodes, Rückmeldungen und Start-/Ende-Handshake prüfen | Analyse | 5 | — |
| [SDD-03 #22](https://github.com/Berufskolleg-Meschede/MESchede/issues/22) · [Entwurf](sdd-03.md) | MES mit genau drei Docker-Services auf dem Synology NAS betreiben | NAS | 8 | — |
| [SDD-04 #23](https://github.com/Berufskolleg-Meschede/MESchede/issues/23) · [Entwurf](sdd-04.md) | Aufträge, Läufe und Produktresultate in PostgreSQL persistieren | Backend | 4 | SDD-01, SDD-02 |
| [SDD-05 #24](https://github.com/Berufskolleg-Meschede/MESchede/issues/24) · [Entwurf](sdd-05.md) | OPC-UA-Status und Produktqueue lesen und persistente Läufe aktualisieren | Backend | 8 | SDD-02, SDD-04 |
| [SDD-06 #25](https://github.com/Berufskolleg-Meschede/MESchede/issues/25) · [Entwurf](sdd-06.md) | RabbitMQ-Lagerdaten konsumieren und aktuelle Bestände bereitstellen | Backend | 4 | SDD-01 |
| [SDD-07 #26](https://github.com/Berufskolleg-Meschede/MESchede/issues/26) · [Entwurf](sdd-07.md) | MES-Aggregations-API und dauerhafte manuelle Auftragsannahme umsetzen | Backend | 6 | SDD-01, SDD-04, SDD-05, SDD-06 |
| [SDD-08 #27](https://github.com/Berufskolleg-Meschede/MESchede/issues/27) · [Entwurf](sdd-08.md) | Persistente und validierte Konfigurations-API bereitstellen | Backend | 6 | SDD-01, SDD-02 |
| [SDD-09 #28](https://github.com/Berufskolleg-Meschede/MESchede/issues/28) · [Entwurf](sdd-09.md) | Frontend-Datenvertrag und API-Zugriff vereinheitlichen | Frontend | 2 | SDD-01 |
| [SDD-10 #29](https://github.com/Berufskolleg-Meschede/MESchede/issues/29) · [Entwurf](sdd-10.md) | Live-Übersicht für Produktion, Kommissionierung, Produktqueue und Lager bauen | Frontend | 6 | SDD-09 |
| [SDD-11 #30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30) · [Entwurf](sdd-11.md) | Produktions- und Lieferaufträge anzeigen und manuell auslösen | Frontend | 4 | SDD-09 |
| [SDD-12 #31](https://github.com/Berufskolleg-Meschede/MESchede/issues/31) · [Entwurf](sdd-12.md) | Auswertung für tatsächliche Mengen und beobachtete Laufdauer erstellen | Frontend | 6 | SDD-09 |
| [SDD-13 #32](https://github.com/Berufskolleg-Meschede/MESchede/issues/32) · [Entwurf](sdd-13.md) | Konfigurationsansicht für Zielnodes und Abfrageintervalle erstellen | Frontend | 6 | SDD-09 |
| [SDD-14 #33](https://github.com/Berufskolleg-Meschede/MESchede/issues/33) · [Entwurf](sdd-14.md) | Gemeinsame UI-Zustände, Navigation und Browserdarstellung prüfen | Frontend | 4 | SDD-10, SDD-11, SDD-12, SDD-13 |
| [SDD-15 #34](https://github.com/Berufskolleg-Meschede/MESchede/issues/34) · [Entwurf](sdd-15.md) | ERP, Webshop, RabbitMQ und Feldebene am NAS integrieren | Integration | 8 | SDD-03, SDD-07, SDD-08, SDD-09 |
| [SDD-16 #35](https://github.com/Berufskolleg-Meschede/MESchede/issues/35) · [Entwurf](sdd-16.md) | End-to-End-Abnahme mit realen Aufträgen, Ausfällen und Neustart durchführen | Integration | 6 | SDD-14, SDD-15 |
| [SDD-17 #36](https://github.com/Berufskolleg-Meschede/MESchede/issues/36) · [Entwurf](sdd-17.md) | Priorisierte Befunde aus Integration und Abnahme beheben | Integration | 4 | SDD-16 |
| [SDD-18 #37](https://github.com/Berufskolleg-Meschede/MESchede/issues/37) · [Entwurf](sdd-18.md) | Projektdokumentation, Schnittstellen und Betriebsanleitung fertigstellen | Dokumentation | 24 | — |
| [SDD-19 #38](https://github.com/Berufskolleg-Meschede/MESchede/issues/38) · [Entwurf](sdd-19.md) | Beispielablauf für Präsentation vorbereiten und gemeinsam proben | Präsentation | 2 | SDD-17, SDD-18 |
| | **Gesamt** | | **120** | |

## Import

Der Importer verwendet die vorhandene GitHub CLI und benötigt eine gültige Anmeldung mit Issue-Schreibzugriff. Er erstellt zuerst die Sammlung, dann die Aufgaben und ergänzt echte GitHub-Links zu Sammlung, Aufgaben und Abhängigkeiten. Bereits vorhandene Issues erkennt er an einer eindeutigen Markierung im Body. Wiederaufnahme nach Teilimport erzeugt keine neuen Issues für bereits erkannte IDs. Bereits vollständig verlinkte Issues bleiben bei Wiederholung unverändert, damit Teamänderungen und abgehakte Aufgaben erhalten bleiben. Er verändert nur Issues dieser Sammlung; keine Labels, Meilensteine oder Assignees werden ohne konkrete Zuordnung angelegt.

Vorschau ohne GitHub-Zugriff:

```sh
python3 scripts/import_projektwoche_issues.py
```

Nach Wiederherstellung des Repositoryzugriffs veröffentlichen:

```sh
python3 scripts/import_projektwoche_issues.py --apply
```

Die Befehle werden aus dem Repository-Stamm ausgeführt. Der Import prüft das Zielrepository und liest vorhandene Issues vor dem Schreiben. Issue-Bodies sind auch ohne separat gepushte Spec vollständig verständlich, weil die Sammlung die Spec enthält.

## Verwendung im Team

SDD-01/02 klären den gemeinsamen Vertrag. SDD-03 und Dokumentation starten parallel. Danach Backend/Integration und Frontend anhand der Abhängigkeiten aufteilen; Frontend-Fixtures ermöglichen Arbeit vor der Live-API. Namen/GitHub-Assignees setzt das Team beim Übernehmen der Aufgaben. SDD-18 ist ein gemeinsamer fortlaufender Dokumentationsblock, keine zusätzliche Arbeit außerhalb der 120 Stunden.

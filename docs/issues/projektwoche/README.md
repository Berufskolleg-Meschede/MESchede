# Projektwoche: Themen-Issues

Die GitHub-Sammlung besteht aus **sieben Themen-Issues** und der [gemeinsamen Übersicht #19](https://github.com/Berufskolleg-Meschede/MESchede/issues/19). Jedes Thema enthält Anforderungen, Akzeptanzkriterien, offene Fragen und drei getrennte Arbeitspakete. Absprachen und Fortschritt werden im Kommentarverlauf des jeweiligen Issues festgehalten.

| Thema | Arbeitsfassung |
|---|---|
| [Konfigurationsoberfläche #32](https://github.com/Berufskolleg-Meschede/MESchede/issues/32) | [Lokale Fassung](config.md) |
| [Analysenübersicht #31](https://github.com/Berufskolleg-Meschede/MESchede/issues/31) | [Lokale Fassung](analytics.md) |
| [Auftrags- und Produktionsübersicht #29](https://github.com/Berufskolleg-Meschede/MESchede/issues/29) | [Lokale Fassung](overview.md) |
| [Produktions- und Lieferaufträge manuell starten #30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30) | [Lokale Fassung](manual.md) |
| [Lagerbestandsübersicht #25](https://github.com/Berufskolleg-Meschede/MESchede/issues/25) | [Lokale Fassung](inventory.md) |
| [Docker-Betrieb auf dem Synology NAS #22](https://github.com/Berufskolleg-Meschede/MESchede/issues/22) | [Lokale Fassung](deployment.md) |
| [Integration, Tests und Projektdokumentation #35](https://github.com/Berufskolleg-Meschede/MESchede/issues/35) | [Lokale Fassung](integration.md) |

## Aufteilung auf drei Personen

- **Person 1:** Oberflächen (28 h), Fehlerkorrektur/Nachtests (3 h), eigene Dokumentation (8 h), Demo (1 h): **40 h**.
- **Person 2:** Backend (28 h), Fach-/Datenvertrag (3 h), eigene Dokumentation (8 h), Demo (1 h): **40 h**.
- **Person 3:** NAS/Docker (8 h), OPC-UA-/Schnittstellenklärung (9 h), Integration/Abnahme/Fehlerkorrektur (15 h), eigene Dokumentation (8 h): **40 h**.

Die Rollen können im Team zugeordnet werden. Früh gemeinsame Felder und Beispielwerte vereinbaren; damit kann die Oberfläche parallel zur realen Backend-/Anlagenanbindung entstehen. Jedes Themen-Issue wird erst abgeschlossen, wenn die gemeinsamen Akzeptanzkriterien erfüllt sind. Gesamtumfang: **120 Teamstunden**. Die internen Themenschätzungen im JSON stammen aus der Zusammenführung der alten Budgets; maßgeblich für die Personenplanung ist die obige Verteilung.

## Lokale Daten und Historie

`backlog.json` enthält die aktive Themenstruktur, `published.json` die GitHub-Nummern und die Zuordnung geschlossener Detailtickets. `archive-v1/` bewahrt die frühere 19-Ticket-Struktur sowie den GitHub-Stand vor der Zusammenführung. Die zwölf zusammengeführten Detailtickets wurden wegen dieser Strukturänderung geschlossen, nicht als implementiert bestätigt. Bereits vorhandene Grundlagen-Issues außerhalb der Sammlung wurden nicht verändert.

Die aktuelle [Spezifikation](../../specs/projektwoche-mes-ui.md) beschreibt denselben thematischen Umfang und die Aufgabenverteilung. Am Anwendungscode wurde nichts geändert.

Der vorhandene Importer nutzt nun die aktive Themenstruktur. Vorschau ohne GitHub-Zugriff:

```sh
python3 scripts/import_projektwoche_issues.py
```

`--apply` erkennt die bereits veröffentlichten Themen anhand ihrer Markierungen und lässt vollständig importierte Issues einschließlich späterer Kommentare und Änderungen unverändert.

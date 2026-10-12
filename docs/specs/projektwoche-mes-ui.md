# MESchede: Themen-Spezifikation der Projektwoche

Version 0.2, 09.10.2026. Quellen: MES-Projektantrag_v3.pdf und zusätzliche Nutzeranforderungen. Die Aufgaben sind auf Wunsch thematisch gebündelt und innerhalb jedes Themas auf drei Personen aufteilbar.

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


## Konfigurationsoberfläche

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


## Analysenübersicht

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


## Auftrags- und Produktionsübersicht

<!-- meschede-projektwoche-v2:OVERVIEW -->
## Ziel

Eine zentrale Ansicht zeigt den aktuellen Produktions- und Kommissionierstatus sowie die wartenden Aufträge und Produktqueue.

## Anforderungen

- Aktive Produktions- und Lieferaufträge getrennt mit ID, Status, Sollmenge und bearbeiteter Menge anzeigen.
- Produktqueue der Steuerung mit Produktinformationen, Serien-/Sequenznummer, Ergebnis und Fehlercode anzeigen, soweit diese Werte verfügbar sind.
- Wartende MES-Aufträge getrennt von den Produkteinheiten des aktiven Auftrags darstellen.
- Rückmeldungen per OPC UA lesen, den passenden Aufträgen zuordnen und relevante Status-/Laufdaten in PostgreSQL speichern.
- Fachliche Auftragsstatus und die tatsächlichen Start-/Endsignale zu Beginn an der Anlage prüfen. Ein einzelner Rohwert oder ein angenommenes POST gilt nicht ohne Nachweis als Abschluss.
- Daten regelmäßig aktualisieren; Verbindungsprobleme, letzte Aktualisierung und unbekannte/veraltete Daten sichtbar machen.
- Gemeinsame API-Datenfelder und Statusbegriffe für die Oberflächen abstimmen; reale Daten anbinden.
- Deutschsprachige, verständliche Darstellung mit Lade-, Leer- und Fehlerzuständen; Status zusätzlich zur Farbe als Text. Demo-Daten nur sichtbar gekennzeichnet.
- Nach Neustart bleiben Daten und wartende Aufträge erhalten; möglicherweise bereits gestartete Aufträge werden vor erneutem Schreiben abgeglichen.

## Akzeptanzkriterien

- [ ] Ein realer Auftrag lässt sich von der Annahme bis zur passenden Steuerungsrückmeldung im Browser verfolgen.
- [ ] Produktion, Kommissionierung, wartende Aufträge und Produktqueue sind unterscheidbar.
- [ ] Mehrfach gelesene Resultate erzeugen keine doppelten Mengen.
- [ ] Ein Verbindungsabbruch wird als Quellenproblem dargestellt und nicht als erfolgreicher Abschluss.
- [ ] Die Oberfläche ist auf den Projektgeräten verständlich und per Tastatur bedienbar.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Dashboard, aktive Aufträge, Warteschlangen und Produktqueue mit den vereinbarten Datenbeispielen darstellen.
- [ ] **Person 2 – Backend:** Gemeinsame DTOs/API, OPC-UA-Reader, Aggregation, persistente Status-/Laufdaten und Wiederaufnahme umsetzen.
- [ ] **Person 3 – Anbindung und Prüfung:** OPC-UA-Nodes und Start-/Endsignale praktisch prüfen, reale Beispielrückmeldungen liefern und den Datenfluss abnehmen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche PLC-Rückmeldungen und Statuswerte sind tatsächlich verfügbar?
- Dürfen Produktion und Kommissionierung parallel laufen?
- Was genau bedeutet der Lieferabschluss in der Fabriksimulation? Er bestätigt keine Zustellung beim Kunden.
- Wie werden fachliche Auftrag-ID und numerische PLC-Auftragsnummer eindeutig verbunden?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:OVERVIEW:links-complete -->


## Produktions- und Lieferaufträge manuell starten

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


## Lagerbestandsübersicht

<!-- meschede-projektwoche-v2:INVENTORY -->
## Ziel

Aktuelle Lagerbestände aus dem vorhandenen RabbitMQ-Projekt sind im MES sichtbar.

## Anforderungen

- Vorhandene RabbitMQ-Anbindung prüfen und wiederverwenden; Nachrichtenformat und Bestandsverantwortung mit der Lager-/ERP-Gruppe abstimmen.
- Bestandsnachrichten im Backend lesen, validieren und in PostgreSQL übernehmen.
- Produkt bzw. Artikel, verfügbaren Bestand und letzte Aktualisierung in der Oberfläche anzeigen.
- Snapshot- und Änderungsnachrichten korrekt unterscheiden; doppelte Zustellung darf Bestände nicht verfälschen.
- Bei Broker-Ausfall letzte bekannte Bestände erhalten und als veraltet kennzeichnen. Noch unbekannte Bestände sind nicht 0.

## Akzeptanzkriterien

- [ ] Eine gültige RabbitMQ-Nachricht verändert den richtigen Bestand in der UI.
- [ ] Doppelte oder ungültige Nachrichten erzeugen keine falschen Mengen.
- [ ] Verbindungsprobleme und fehlende Daten sind erkennbar.
- [ ] Letzte Bestände bleiben nach Backend-Neustart verfügbar.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** Bestände, Artikel/Produkte und Aktualitäts-/Verbindungsanzeige in die Übersicht einbauen.
- [ ] **Person 2 – Backend:** RabbitMQ-Consumer wiederverwenden/ergänzen; Validierung, persistente Bestände und Lese-API bereitstellen.
- [ ] **Person 3 – Anbindung und Prüfung:** Nachrichtenvertrag und RabbitMQ-Zugang mit der Lagergruppe klären; Updates, Duplikate und Ausfälle gemeinsam prüfen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Queue, welcher Routing-Key und welches Nachrichtenformat werden verwendet?
- Sind die Nachrichten vollständige Bestände oder Änderungen?
- Wie wird festgestellt, ob ein ereignisbasiert übermittelter Bestand noch aktuell ist?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:INVENTORY:links-complete -->


## Docker-Betrieb auf dem Synology NAS

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


## Integration, Tests und Projektdokumentation

<!-- meschede-projektwoche-v2:INTEGRATION -->
## Ziel

Die Themen sind am echten System gemeinsam geprüft, dokumentiert und anhand eines Beispielablaufs vorführbar.

## Anforderungen

- Schnittstellen und Datenfluss mit ERP-, Webshop-, Lager- und Steuerungsgruppe abstimmen und im NAS-Netzwerk prüfen.
- Je einen Produktions- und Lieferauftrag vom manuellen bzw. externen Aufruf bis zur Rückmeldung im Browser testen.
- Mengen, Laufdauer, Lagerupdates und Konfigurationsänderungen mit erwarteten Werten vergleichen.
- Wiederholung, Verbindungsabbruch und Neustart prüfen; relevante Befunde korrigieren und nachtesten.
- Durchführung, Entscheidungen, Schwierigkeiten und Ergebnisse während der Woche dokumentieren.
- Architektur, API-Verträge, tatsächliche OPC-UA-Nodes, Einstellungen und Bedienung beschreiben.
- Beispielablauf für die Präsentation vorbereiten und gemeinsam proben.

## Akzeptanzkriterien

- [ ] Erwartete und tatsächliche Ergebnisse der Kernabläufe sind dokumentiert.
- [ ] Produktions- und Lieferauftrag, Analysen und Lagerdaten sind am realen System nachvollziehbar.
- [ ] Ausfälle und Neustarts erzeugen keine unbemerkten Doppelstarts oder erfundenen Ergebnisse.
- [ ] Dokumentation beschreibt den tatsächlich erreichten Stand; nicht geprüfte Fälle bleiben erkennbar offen.
- [ ] Die Vorführung wurde gemeinsam geprobt.

## Arbeitspakete für drei Personen

- [ ] **Person 1 – Oberfläche:** UI-Abläufe prüfen, zugeordnete Fehler korrigieren, die eigenen Ergebnisse dokumentieren und Demo mit vorbereiten.
- [ ] **Person 2 – Backend:** API-/Datenverträge und Backend-Nachweise prüfen, die eigenen Ergebnisse dokumentieren und Demo mit vorbereiten.
- [ ] **Person 3 – Anbindung und Prüfung:** Gesamtdurchläufe, NAS-/Ausfall-/Neustarttests koordinieren, Schnittstellen abstimmen und die gemeinsame Dokumentation zusammenführen.

**Parallel starten:** Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab. Person 1 kann mit diesen Beispieldaten entwickeln, während Backend und reale Anbindung entstehen. Die Verbindung wird früh gemeinsam geprüft. Im Kommentarverlauf festhalten, wer welches Paket übernimmt und welche Schnittstelle vereinbart wurde. Tests der eigenen Änderungen und die eigene Dokumentation gehören jeweils dazu.

## Offene Fragen / Diskussion

- Welche Testaufträge und Anlagenzeiten stehen für die gemeinsame Prüfung zur Verfügung?
- Welche Nachweise und Aufteilung braucht die Projektarbeit?

Absprachen, Rückfragen und Fortschritt bitte im Kommentarverlauf dieses Issues festhalten. Bestätigte Änderungen an den Anforderungen anschließend in der Beschreibung nachführen. Das Thema umfasst die notwendige Oberfläche, Backend-Anbindung und Prüfung; die konkrete Codeaufteilung kann das Team innerhalb dieses Issues abstimmen.

[Projektwoche: Übersicht und gemeinsamer Rahmen](https://github.com/Berufskolleg-Meschede/MESchede/issues/19)

<!-- meschede-projektwoche-v2:INTEGRATION:links-complete -->



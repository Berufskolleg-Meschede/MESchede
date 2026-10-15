# Produktions- und Lieferaufträge manuell starten

## Meta

- **State:** Modified
- **Stand:** 15.10.2026
- **Status:** Software lokal umgesetzt und geprüft; SPS-Katalog lesend bestätigt und importiert. Anlagenabnahme echter Aufträge und Wiki-Veröffentlichung bleiben offen.
- **Issue:** [#30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30)
- **Idee:** [Harness-Idee I4](../../Harness/harness/ideas/I4%20Auftraege%20manuell%20starten%20Issue%2030.md)
- **Implementierungsplan:** [Issue-30-Plan](../plans/issue-30-manual-order-start.md)
- **Branch:** `spec/issue-30-manual-orders`

Die Feature-Spec liegt analog zu Issue #29 unter `docs/specs/`. Harness reserviert `Harness/spec/` für Bugfixes. Seine Regeln für Quellen, fachliche Klärung, atomare Akzeptanzkriterien, Testzuordnung und State werden übernommen.

## User Story

Als Anlagenbediener möchte ich Produktions- und Lieferaufträge mit mehreren Produkten erfassen und nach einer Zusammenfassung bestätigen, damit ich ihre Annahme und den tatsächlichen Lauf in der MES-Oberfläche verfolgen kann.

## Description

Beide Auftragsseiten erhalten eine gemeinsame Erfassung mit getrennten Identifikatoren, Produktzeilen und erforderlichen Kopfdaten. Automatische Vorbelegungen reduzieren die Eingabe und bleiben editierbar. Ein bestätigter Auftrag wird über die vorhandene dauerhafte MES-Annahme eingereiht und anschließend über die bestehenden Laufansichten verfolgt. Ein unbekanntes Requestergebnis wird zuerst lesend abgeglichen, bevor derselbe Auftrag erneut gesendet werden darf.

## Quellen und Entscheidungen

- [Aktuelles GitHub-Issue #30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30), am 14.10.2026 gelesen; keine zusätzlichen Kommentare.
- [Lokale Anforderungen](../issues/projektwoche/manual.md), [UI-Rahmen](projektwoche-mes-ui.md), [Übergabe](../handoffs/issue-30-manual-order-start.md).
- [Harness-UI-Regeln](../../Harness/harness/_uiux.md), [Issue-29-Spec](issue-29-order-production-overview.md), [PLC-Vertrag](../opc-ua-integration.md).
- Benutzerantworten vom 14.10.2026: mehrere Produktzeilen; Auftrag-ID und PLC-Auftragsnummer als zwei getrennte, automatisch vorbelegte und editierbare Felder; Datum/Uhrzeit automatisch und editierbar, ohne Offset; optionale Kundennummer; Standardwerte für editierbare Priorität und Parameter; Seriennummern fortlaufend **je Auftrag ab einer editierbaren Startnummer**.
- Aktueller Anwendungscode und vorhandene Tests sind in der [Idee](../../Harness/harness/ideas/I4%20Auftraege%20manuell%20starten%20Issue%2030.md) benannt und wurden vor der Spec gelesen. In dieser Dokumentationsphase wurden keine Tests ausgeführt.

## Ist-Verhalten vor der Umsetzung

- `/production-orders` und `/delivery-orders` verwenden `OrdersSection` für echte Auftragslisten, Warteschlangen, Laufzustände, Produktqueue, Details und Reviews. Ein Erfassungsformular fehlt.
- `OrderApiClient` unterstützt Listen, Übersicht, Detail und Review, noch keine Auftragserfassung. Die alten Mock-CRUD-Methoden verwenden `OrderFormData` und passen nicht zum aktuellen POST-Vertrag.
- `POST /productionorder/` und `POST /deliveryorder/` erwarten `OrderPayload` mit `order_id` und `mes_auftrag`. Die Menge ergibt sich aus der Anzahl der `Produktqueue`-Einträge.
- `OrderAdmissionService` bestätigt nach Datenbank-Commit mit `202`. Auftragsart plus normalisierte ID identifizieren den Auftrag. Gleicher Inhalt ist idempotent; anderer Inhalt ist ein Konflikt. PLC-Nummern sind je Auftragsart dauerhaft eindeutig, auch nach Abschluss.
- Der gemeinsame Worker vergibt höchstens einen Lauf gleichzeitig und verarbeitet beide Auftragsarten nach globalem FIFO. Ohne laufenden Worker lehnen die POST-Routen mit `503` ab.
- `DB_MES_Schnittstelle.Produktspezifikation` ist als verbindlicher Produktkatalog dokumentiert; der Leser fehlt. Automatische ID-Vorschläge und Informationen zur nutzbaren Queue-Kapazität fehlen ebenfalls.
- Der bestehende Detailvertrag enthält Lauf und Einheiten, aber nicht alle unveränderlichen Kopfdaten. Er reicht für einen vollständigen Inhaltsabgleich nach einer verlorenen Antwort noch nicht aus.
- Der Browserproxy kann nach einem Timeout `503` melden, obwohl die Annahme bereits gespeichert wurde. Das ist von einer belegten Ablehnung zu unterscheiden.

## Ergänzung: persistenter SPS-Produktkatalog (15.10.2026)

Der Benutzer beauftragt den Import der SPS-Produkte in PostgreSQL. PDF-Seiten 96–97 und der lesende Live-Abgleich belegen `DB_MES_Schnittstelle.Produktspezifikation`, Index 0 leer, Produkt-IDs 1–6, sowie 33 nutzbare Queue-Slots je Auftragsart. Der Singular ersetzt den bisherigen fehlerhaften Plural als verbindlichen Knotennamen; ein Plural wird nur als Kompatibilitätsalias unterstützt.

PostgreSQL spiegelt IDs, Texte, Quellindizes, Bauplandaten und Verfügbarkeit in separaten Katalogtabellen. `Article` wird nicht mit erfundenen Preisen befüllt. Ein erfolgreicher vollständiger Snapshot wird atomar und idempotent übernommen; verschwundene Produkte werden deaktiviert statt gelöscht. Fehler erhalten letzte gültige Daten und den letzten Erfolgszeitpunkt. Bestehende Auftragspayloads werden nicht nachträglich umgeschrieben.

Der Hintergrundabgleich läuft beim Backendstart und anschließend standardmäßig alle 30 Sekunden über einen getrennten lesenden Gateway. Die Katalog-Veraltungsgrenze ist separat konfigurierbar, standardmäßig 300 Sekunden. Live-Auftragsstatus behalten ihre bestehende kurze Veraltungsgrenze. `GET /orders/input-context` und die Auftragsannahme lesen nur den DB-Katalog; `POST /orders/catalog/sync?order_type=production|delivery` löst ausdrücklich einen neuen lesenden Abgleich aus. Ein einmaliger Import ist auch ohne Start des Auftragsworkers möglich.

Zusätzliche Akzeptanzkriterien:

| ID | Prüfaussage |
| --- | --- |
| CAT-01 | Der Leser verwendet den dokumentierten Singular und liest Produkt-IDs aus Feldern statt Indizes. |
| CAT-02 | Nach erfolgreichem Import sind alle gelesenen Produkte mit ihren Bauplandaten dauerhaft gespeichert. |
| CAT-03 | Wiederholter Import derselben Produkt-IDs erzeugt keine zusätzlichen Produkte. |
| CAT-04 | Ein fehlgeschlagener Abgleich entfernt keine gespeicherten Produkte und verändert den letzten Erfolgszeitpunkt nicht. |
| CAT-05 | Erst ein vollständiger erfolgreicher Snapshot deaktiviert darin fehlende Produkte. |
| CAT-06 | Die Vorbereitung und ein neuer Auftrags-POST verwenden den DB-Katalog ohne eigenen SPS-Aufruf. |
| CAT-07 | Produktabgleich startet keinen Produktions- oder Lieferauftrag und schreibt keine SPS-Nodes. |

Diese Ergänzung ersetzt die frühere ausschließlich flüchtige Kataloghaltung und den Live-Katalogaufruf vor jedem POST.

## Soll-Verhalten

### Erfassung und Bestätigung

„Neuer Auftrag“ öffnet auf der jeweiligen Auftragsseite einen Dialog für deren Auftragsart. Der Ablauf hat zwei Schritte: **Auftrag erfassen** und **Auftrag prüfen**. „Zusammenfassung anzeigen“ führt nach erfolgreicher Eingabeprüfung zum zweiten Schritt; „Zurück“ erhält alle Eingaben. Erst „Auftrag annehmen“ sendet die Bestellung. Vor der Bestätigung erfolgt keine Auftragsmutation und kein PLC-Schreibzugriff.

Die Erfassung zeigt die beiden Identifikatoren, Produktzeilen, Gesamtmenge und die Seriennummern-Startnummer. Jede Zeile besitzt Produkt, Menge und „Produktzeile entfernen“; „Produkt hinzufügen“ ergänzt eine Zeile. Mindestens eine vollständige Zeile ist erforderlich. Beim Öffnen wird kein Produkt stillschweigend ausgewählt. Neue Zeilen beginnen mit Menge 1. Wiederholte Auswahl desselben Produkts ist zulässig; Zeilen werden weder still zusammengeführt noch umsortiert.

Datum, Uhrzeit und optionale Kundennummer stehen bei den Auftragsdaten. Priorität sowie `Parameter0` und `Parameter1` werden unter „Weitere Angaben“ mit editierbaren Standardwerten angeboten. Status, Auftragsart und Steuerungsbefehle sind keine frei editierbaren Auftragsfelder.

Die Zusammenfassung zeigt Auftragsart, beide Identifikatoren, Produktzeilen in Queue-Reihenfolge, Einzelmengen, Gesamtmenge, Seriennummernbereich, Datum/Uhrzeit, Kundennummer und wirksame Prioritäts-/Parameterwerte. Sie erklärt, dass die Annahme den Auftrag in die gemeinsame Warteschlange stellt. Bekannte Startsperren erscheinen als Hinweis, dass der tatsächliche Start wartet. Das Formular kann während einer laufenden Produktion einen weiteren Auftrag annehmen, sofern die Annahmevoraussetzungen erfüllt sind.

### Felder und Grenzen

| UI-Feld | Vertrag | Vorbelegung und Regel |
| --- | --- | --- |
| Auftrag-ID | `order_id` | Automatischer freier Vorschlag für diese Auftragsart; editierbarer Text, getrimmt, 1–200 Zeichen, nicht nur Leerzeichen. Die Pfadwerte `.` und `..` sowie der Diagnoseroutenname `queue-status` sind reserviert, damit das Detail erreichbar bleibt. |
| PLC-Auftragsnummer | `mes_auftrag.kopf.Auftragsnummer` | Separater freier Vorschlag; editierbare ganze Zahl 0–65535, dauerhaft eindeutig je Auftragsart. |
| Produkt | `inhalt.Produktqueue[*].ProduktID`, `Produkttext` | Auswahl aus dem gültigen PLC-Katalog; ID und Text werden übernommen. Modellgrenzen: ID 0–255, Text höchstens 30 Zeichen. |
| Menge je Zeile | Anzahl wiederholter Einträge | Erforderliche ganze Zahl ab 1; Gesamtmenge innerhalb der für diese Auftragsart belegten Kapazität. |
| Seriennummer ab | `inhalt.SeriennummerStart` | Editierbare ganze Zahl 0–65535, Modellstandard 0; Vorschau zeigt den daraus folgenden Nummernbereich. |
| Startdatum | `kopf.Startdatum` | Aktuelles Anlagendatum beim Öffnen, editierbar; `YYYY-MM-DD`, im bestätigten SIMATIC-DATE-Bereich 1990-01-01 bis 2168-12-31. |
| Startzeit | `kopf.Startzeit` | Aktuelle lokale Anlagenzeit beim Öffnen, editierbar; `HH:mm:ss` ohne `Z` oder Offset. |
| Kundennummer | `kopf.Kundennummer` | Optional; leer entspricht 0, sonst ganze Zahl 0–65535. |
| Priorität | `kopf.Prioritaet` | Standard 1, editierbar als 0, 1 oder 2; beeinflusst die MES-FIFO-Reihenfolge nicht. |
| Parameter 0 / Parameter 1 | `kopf.Parameter0`, `kopf.Parameter1` | Je Standard 0, editierbare ganze Zahl 0–255. |

Die Backend-Uhr liefert die Vorbelegung in der konfigurierten Anlagenzeitzone; Ausgangswert ist `Europe/Berlin`. Der Browser überträgt deren lokale Datums-/Zeitwerte ohne UTC-Konvertierung. Eine andere Browserzeitzone darf die Vorbelegung nicht verändern. Datum/Uhrzeit werden beim Prüfen oder Wiederholen nicht neu berechnet. Sie sind Auftragsdaten; diese Funktion führt keine zusätzliche Terminplanung ein und behandelt sie nicht als beobachteten PLC-Startzeitpunkt.

Die freie Auftrag-ID und die freie PLC-Nummer werden unabhängig anhand der gespeicherten Aufträge ermittelt. Als einfacher Vorschlag wird jeweils die kleinste freie positive Dezimalnummer angeboten, bei der Auftrag-ID als Text; die editierbare Text-ID bleibt vom PLC-Wertebereich unabhängig. Ein Vorschlag reserviert keine Nummer und garantiert deren Verfügbarkeit beim späteren Absenden nicht. Die Annahme prüft atomar erneut. Bei Konflikt bleiben Eingaben erhalten; ein neuer Vorschlag wird nur auf Bedieneraktion übernommen und muss erneut bestätigt werden. Eine erschöpfte PLC-Nummernmenge erzeugt eine verständliche Meldung; kein Überlauf und keine automatische Wiederverwendung.

### Produkte, Menge und Seriennummern

Der verbindliche Katalog wird vom Backend aus `DB_MES_Schnittstelle.Produktspezifikation` gelesen. Sein leerer Index 0 wird ausgelassen; tatsächliche Produkt-IDs werden aus den belegten Produktfeldern gelesen. Der Katalogindex ist keine Produkt-ID. Die UI zeigt Produkttext und ID. Produkte ohne nachweisbar gültige Vertragsdaten sind nicht auswählbar. Zu lange Texte werden nicht still abgeschnitten.

Die nutzbare Kapazität wird für Produktion und Lieferung anhand der tatsächlich exponierten, lückenlos ab Index 0 erreichbaren Queue-Slots beziehungsweise belegter zusätzlicher Fachlimits bestimmt und durch 255 begrenzt. Eine bloße Slotanzahl darf fehlende Indizes nicht verdecken. Unbekannte oder nicht aktuell verifizierbare Katalog-/Kapazitätsdaten verhindern eine neue Annahme; letzte bekannte Werte dürfen als veraltet sichtbar bleiben. Beim Senden prüft das Backend die Produktauswahl und Gesamtmenge erneut. Bestehende Warteschlangen- und Laufansichten bleiben unabhängig von dieser Erfassung verwendbar. Es gibt keinen stillen Wechsel zu den alten Mock-Artikeln.

Produktzeilen werden in ihrer sichtbaren Reihenfolge expandiert: Für jede Zeile entstehen genau so viele Queue-Einträge wie ihre Menge. Die Auftragsqueue beginnt bei Index 0. Für Gesamtmenge `N`, Startnummer `S` und Queue-Index `i` gilt:

```text
SeriennummerStart = S
Produktqueue[i].Seriennummer = S + i       für i = 0 … N - 1
letzte Seriennummer = S + N - 1 <= 65535
```

Die Nummerierung beginnt bei einer neuen Produktzeile nicht erneut. Sie ist je Auftrag fortlaufend; eine globale Seriennummernvergabe über andere Aufträge ist nicht vereinbart. `Sequenznummer` und `Takt` bleiben bei ihren Modellstandards 0. Reale Fachvorgaben dafür sind vor der Anlagenabnahme zu prüfen. Ein Überlauf wird vor der Annahme abgelehnt; es gibt keinen Umlauf auf 0.

### Validierung und Annahme

Die UI zeigt Fehler an den betroffenen Feldern und führt den Fokus zur ersten ungültigen Eingabe. Fachlich relevante Regeln werden zusätzlich im Backend vor dem Commit geprüft. Mengen und numerische Werte akzeptieren keine Brüche, negativen Werte, booleschen Ersatzwerte oder stillen Rundungen. Datum, Uhrzeit ohne Offset und PLC-konforme Wertebereiche werden vor dem Einreihen geprüft. Eine nicht mehr gültige Produktauswahl muss korrigiert und erneut bestätigt werden.

Der bestehende `OrderPayload` bleibt der POST-Vertrag. Seine normalisierten, wirksamen Werte werden vor dem ersten Senden eingefroren. Katalogprüfung und Defaults dürfen den bestätigten Inhalt nicht still verändern. Identische Wiederholungen bereits angenommener Aufträge werden vor erneuter Prüfung veränderlicher Katalogdaten aufgelöst, damit ein späterer Katalogausfall ihre bestehende Annahme nicht rückwirkend ungültig macht.

Während des Sendens sind Senden, Eingabeänderungen, „Zurück“ und Dialogschließen gesperrt. Nach belegter Ablehnung wird die Erfassung mit erhaltenen Werten wieder freigegeben. Erwartete Fehler erhalten deutsche Meldungen; strukturierte `422`-Details werden den Feldern zugeordnet. Eine belegte Ablehnung wegen fehlendem Worker nennt den Backendstatus. Unklare `503`-Antworten folgen dagegen dem Abgleichablauf.

### Unbekanntes Requestergebnis und Wiederholung

Vor dem POST wird der Versuch mit Auftragsart, normalisierter ID und vollständigem eingefrorenem Inhalt in der Browsersitzung gesichert. Kann der Versuch nicht gesichert werden, wird vor dem Senden eine Meldung angezeigt. Nach einem Reload wird ein unaufgeklärter Versuch zuerst lesend abgeglichen, niemals automatisch erneut gesendet. Ein Reload darf Datum, Nummern oder Inhalt des Versuchs nicht verändern.

Der Abgleich nutzt `GET /productionorder/{order_id}` beziehungsweise `GET /deliveryorder/{order_id}`. Der Detailvertrag wird für diesen Zweck um die vollständig gespeicherten, normalisierten Eingabedaten `mes_auftrag` ergänzt. Auftragsart, normalisierte ID und sämtlicher Eingabeinhalt müssen übereinstimmen; nur dann gilt der Versuch als bereits angenommen. Ein gefundener anderer Inhalt wird als Konflikt angezeigt und nicht als Erfolg übernommen.

| Befund | UI-Reaktion |
| --- | --- |
| Auftrag mit identischem Inhalt gespeichert | Annahme anzeigen, dieselben Referenzen übernehmen, Übersicht/Detail laden; kein neuer POST. |
| Auftrag mit abweichendem Inhalt gespeichert | Konflikt erklären, bestehenden Auftrag erreichbar machen; kein automatisches Senden mit neuer ID. |
| Verlässliches `404` aus der Auftragsverwaltung | „Noch nicht gespeichert gefunden“; Wiederholung desselben eingefrorenen Requests auf ausdrücklichen Klick anbieten. |
| Abgleich nicht möglich, etwa Timeout, `503` oder ungültige Antwort | „Annahme noch unklar“; „Annahme prüfen“ anbieten und weitere POSTs dieses Versuchs sperren. |

Ein `404` kann mit einem noch laufenden ursprünglichen Request konkurrieren. Deshalb verwendet auch die erlaubte Wiederholung dieselbe Identität und denselben Inhalt und bleibt durch die atomare Backend-Idempotenz abgesichert. Neue automatische Vorschläge, eine neue Uhrzeit oder ein neuer Seriennummernbereich dürfen keinen Retry in einen anderen Auftrag verwandeln. Automatische Transport-Retries für POST werden nicht verwendet.

### Verfolgung nach Annahme

`202` bestätigt nur Speicherung und Einreihung, auch wenn der Lauf zwischenzeitlich weiter fortgeschritten ist. Die UI zeigt „Auftrag angenommen“ mit Auftragsart, beiden Identifikatoren und einer Aktion „Auftragsdetails anzeigen“. Sie lädt die typspezifische Übersicht und das Detail erneut. Bestehende Filter und Pagination werden so zurückgesetzt, dass der angenommene Auftrag sichtbar wird; sein Detail bleibt unabhängig von der aktuellen Listenseite erreichbar.

Das Detail wird während seiner Anzeige gezielt neu geladen. Die vorhandene Listenpolling-Abfrage genügt dafür nicht, wenn der Auftrag außerhalb der aktuell geladenen Seite liegt. Die UI verwendet die existierenden Backend-Laufphasen:

| Backendzustand | Bedeutung in der UI |
| --- | --- |
| `queued` | Angenommen, wartet in der MES-Reihenfolge. |
| `preparing` | Übergabe wird vorbereitet, noch kein bestätigter PLC-Start. |
| `start_pending` | Startbestätigung steht aus. |
| `running` mit korreliertem Nachweis | PLC-Start bestätigt. |
| `completion_observed`, `awaiting_reset`, `completed` | Bestätigter Abschluss nach bestehenden Regeln; ohne beobachteten Start keinen Startzeitpunkt erfinden. |
| `interrupted`, `review_required` | Fehler beziehungsweise Prüfbedarf gemäß gespeicherten Fakten. |

Ein Verbindungsfehler beim Nachladen widerruft die bereits bestätigte Annahme nicht. Die UI zeigt letzte gespeicherte Fakten und das Quellenproblem getrennt und sendet den Auftrag nicht erneut. PLC-Start, Ergebnisse und Review folgen weiterhin dem Vertrag von Issue #29. Offene Reviews und fehlende Bereitschaft sperren den tatsächlichen Start; eine neue Auftragannahme hebt diese Sperren nicht auf.

### UI-/UX und Abgrenzung

Die gemeinsame Erfassung verwendet die bestehenden Dialog-, Formular- und Tabellenbausteine, semantischen Farben, Systemschrift und deutschsprachigen Begriffe. Tastaturbedienung, Fokusführung, sichtbare Labels und Feldfehler sind erforderlich. Enter im Erfassungsschritt zeigt höchstens die Zusammenfassung; ein POST setzt die bewusste Bestätigung im Prüfschritt voraus. Der Dialog bleibt auf schmalen Geräten scrollbar; Produkt, Menge und Gesamtmenge bleiben verständlich.

Das Dashboard bleibt lesend. Pause, Abbruch, Bearbeitung oder Löschung angenommener Aufträge sowie manuelle PLC-Steuerungsaktionen gehören nicht zu dieser Spec. Das Entfernen einer noch nicht abgesendeten Produktzeile und das Abbrechen eines Entwurfs sind Bestandteil der Erfassung.

## Akzeptanzkriterien

| ID | Prüfaussage |
| --- | --- |
| AC-01 | Auf jeder Auftragsseite öffnet „Neuer Auftrag“ die Erfassung für deren Auftragsart. |
| AC-02 | Die Erfassung unterstützt mehrere Produktzeilen mit jeweils einer eigenen Menge. |
| AC-03 | Die Zusammenfassung enthält alle wirksamen Eingabewerte, bevor ein POST möglich ist. |
| AC-04 | Ein gültiger Produktionsauftrag wird über `POST /productionorder/` dauerhaft angenommen. |
| AC-05 | Ein gültiger Lieferauftrag wird über `POST /deliveryorder/` dauerhaft angenommen. |
| AC-06 | Auftrag-ID und PLC-Auftragsnummer sind getrennt editierbare Felder. |
| AC-07 | Die Vorbelegung schlägt unabhängig für beide Identifikatoren zum Abfragezeitpunkt freie Werte der jeweiligen Auftragsart vor. |
| AC-08 | Eine zwischen Vorschlag und Annahme belegte PLC-Nummer führt zu einem Konflikt ohne Überschreibung. |
| AC-09 | Datum und Uhrzeit werden aus der Anlagenzeitzone automatisch vorbelegt. |
| AC-10 | Geänderte Datums-/Zeitwerte werden unverändert und ohne Zeitzonenoffset übertragen. |
| AC-11 | Eine leere Kundennummer wird als 0 gesendet. |
| AC-12 | Priorität und beide Parameter können innerhalb ihrer Grenzen geändert werden. |
| AC-13 | Die Produktauswahl enthält ausschließlich validierte Einträge des verbindlichen PLC-Katalogs. |
| AC-14 | Der leere Katalogindex 0 wird nicht als Produkt angeboten. |
| AC-15 | Unbekannte oder veraltete Katalog-/Kapazitätsdaten verhindern eine neue Annahme. |
| AC-16 | Eine ungültige Zeilenmenge wird vor dem POST mit einem Feldfehler abgelehnt. |
| AC-17 | Eine Gesamtmenge oberhalb der belegten Kapazität wird vor dem Einreihen serverseitig abgelehnt. |
| AC-18 | Jede Zeilenmenge erzeugt genau diese Anzahl Queue-Einträge in sichtbarer Zeilenreihenfolge. |
| AC-19 | Die Seriennummern steigen ab der editierbaren Startnummer über alle Zeilen hinweg jeweils um 1. |
| AC-20 | Ein Seriennummernbereich oberhalb 65535 wird vor der Annahme abgelehnt. |
| AC-21 | Das Backend lehnt ungültige Produktdaten vor dauerhafter Annahme mit verständlicher Meldung ab. |
| AC-22 | Fachlich ungültige Kopfwerte werden vor dem Einreihen serverseitig abgelehnt. |
| AC-23 | Ein Doppelklick auf die Bestätigung erzeugt höchstens einen laufenden UI-Request. |
| AC-24 | Während des Sendens kann der bestätigte Inhalt nicht verändert werden. |
| AC-25 | Gleiche Auftragsart und ID mit identischem Inhalt liefern dauerhaft denselben Auftrag und Lauf. |
| AC-26 | Anderer Inhalt unter derselben Auftragsart und ID verursacht einen Konflikt ohne zusätzlichen Lauf. |
| AC-27 | Bei unbekanntem POST-Ergebnis prüft die UI die Annahme lesend vor jeder Wiederholung. |
| AC-28 | Ein fehlgeschlagener Abgleich sperrt die Wiederholung dieses Versuchs. |
| AC-29 | Ein gefundener Auftrag wird nur bei vollständiger Inhaltsübereinstimmung als erfolgreiche Annahme übernommen. |
| AC-30 | Eine angebotene Wiederholung sendet denselben eingefrorenen Inhalt einschließlich IDs, Zeit und Seriennummern. |
| AC-31 | Ein Reload eines unaufgeklärten Versuchs löst ausschließlich den lesenden Abgleich aus. |
| AC-32 | `202` allein erzeugt keine Meldung eines bestätigten PLC-Starts. |
| AC-33 | Nach Annahme ist der Auftrag trotz vorheriger Such-/Statusfilter in der Übersicht zugänglich. |
| AC-34 | Das Detail des angenommenen Auftrags wird unabhängig von der Listenseite neu geladen. |
| AC-35 | Ein Nachladefehler erhält die bestätigte Annahme und zeigt ein getrenntes Quellenproblem. |
| AC-36 | Neue Annahmen umgehen weder globale FIFO-Reihenfolge noch Start-/Reviewsperren. |
| AC-37 | Bei belegter Ablehnung bleiben die Formulareingaben erhalten. |
| AC-38 | Der gesamte Erfassungs- und Prüfschritt ist per Tastatur bedienbar. |
| AC-39 | Auf schmalem Bildschirm bleiben alle Dialoginhalte und Aktionen erreichbar. |
| AC-40 | Das Dashboard bietet weiterhin keine Auftragsmutation. |

## Umgesetzte Vertragsergänzungen

Die POST-Routen und `OrderPayload` bleiben die Integrationsgrenze. Folgende Fähigkeiten sind im Arbeitsbranch ergänzt und mit synthetischen Daten geprüft:

1. `GET /orders/input-context?order_type=production` beziehungsweise `delivery`: freie Vorschläge für Auftrag-ID und PLC-Nummer, lokales Anlagendatum/-zeit, validierter Produktkatalog, dessen Aktualität und nutzbare typspezifische Queue-Kapazität. Die Route reserviert keine Nummern, erzeugt keine Aufträge und schreibt keine PLC-Nodes. Nicht verfügbare Voraussetzungen liefern `available=false` mit Erklärung.
2. Serverseitige Validierung des bestätigten Inhalts gegen PLC-/Kataloggrenzen vor einer erstmaligen Annahme, hinter derselben Idempotenzgrenze wie die bestehenden POSTs.
3. `OrderDetailView` ergänzt `mes_auftrag`, `refresh_interval_s` und `stale_after_s` nur im typspezifischen Detail. Listen bleiben bei `OrderView` ohne vollständige Eingabepayload.
4. Strukturierte Fehlerzuordnung für Eingabefelder und Identitätskonflikte; vorhandene `404`, `409`, `422` und `503` behalten ihre fachliche Bedeutung.

## Angepasste Methoden und Erkenntnisse

| Methode / Funktion | Datei und Typ | Aufgabe, Änderung und Erkenntnis | Bezug |
| --- | --- | --- | --- |
| `validate_start_date`, `validate_start_time` | `backend/app/models/mes_auftrag.py`, `AuftragKopf` | Prüfen Writer-Grenzen schon am Eingang. Offsetfreie Anlagenzeit und SIMATIC-DATE-Bereich sind keine reine Anzeigevalidierung. Numerische Modellfelder sind zusätzlich strikt ganzzahlig. | AC-10, AC-22 |
| `normalize_order_id` | `backend/app/models/order_dto.py`, `OrderPayload` | Bewahrt die kanonische getrimmte Identität und lehnt die reservierten Werte `.`, `..` und `queue-status` ab. Andernfalls würde die Detailabfrage in Browsernormalisierung oder Diagnoseroute landen. | AC-06, AC-22, AC-34 |
| `admit` | `backend/app/repositories/order_repository.py`, `OrderRepository` | Nimmt einen Validierungsaufruf für neue Aufträge auf. Bestehende gleiche Identität/Inhalt wird davor aufgelöst; die Katalogprüfung erfolgt vor Commit unter derselben Annahmegrenze. | AC-17, AC-21, AC-25, AC-26 |
| `suggest_identifiers` | dieselbe Datei, `OrderRepository` | Liest unabhängige freie Vorschläge je Auftragstyp; Lesen reserviert keine Nummer. Annahme bleibt autoritativ. | AC-07, AC-08 |
| `accept` | `backend/app/services/order_admission_service.py`, `OrderAdmissionService` | Reicht die Erstannahmevalidierung an das Repository weiter und bestätigt unverändert nach Commit. | AC-04, AC-05, AC-25 |
| `_read_input_catalog_sync`, `read_input_catalog` | `backend/app/clients/plc_order_gateway.py`, `PlcOrderGateway` | Ergänzen lesenden Katalog-/Kapazitätszugang im vorhandenen I/O-Thread. Index 0 des Katalogs ist leer; nur lückenlose Queue-Slots ab 0 sind nutzbar. | AC-13 bis AC-15, AC-17 |
| `__init__`, `_root`, `_disconnect` | dieselbe Datei, `PlcOrderGateway` | Bewahren/verwerfen zusätzlich den gefundenen Datenbaustein für Katalogzugriffe; Lebensdauer bleibt an die bestehende Verbindung gebunden. | AC-13, AC-15 |
| `catalog`, `_fresh`, `prepare`, `validate`, `__init__` | `backend/app/services/order_input_service.py`, `OrderInputService` | Kapseln frische Voraussetzungen, lokale Zeit, Vorschläge und Erstannahmeprüfung. Bei Quellenfehler bleibt Annahme gesperrt, selbst wenn alte Produkte vorhanden sind. Seriennummernbereiche werden serverseitig auf Überlauf geprüft. | AC-07, AC-09, AC-13 bis AC-15, AC-17, AC-20, AC-21 |
| `get_order_input_context` | `backend/app/routers/orders_router.py` | Liefert Vorbereitung mit DB-Fehlerzuordnung. Der Browserproxy unterstützt den bestehenden Pfadbereich `orders` bereits. | AC-07, AC-09, AC-15 |
| `admit_order`, `execute_order_operation` | `backend/app/routers/order_dependencies.py` | Gemeinsame Erstannahme beider Typen, katalogunabhängige Wiederholung und strukturierte `422`-Feldfehler. Ein Proxy-503 beweist keine Nichtannahme. | AC-04, AC-05, AC-21, AC-25 bis AC-30 |
| `post_productionorder`, `post_deliveryorder`, `get_productionorder`, `get_deliveryorder` | jeweilige Dateien unter `backend/app/routers/` | Nutzen gemeinsame Annahme und `OrderDetailView` statt duplizierter Prüfung oder bloßer Laufansicht. | AC-04, AC-05, AC-29 |
| `detail` | `backend/app/services/order_query_service.py`, `OrderQueryService` | Liefert vollständige immutable Eingaben nur für Details. Einzelne Produkteinheiten allein belegen keine Gleichheit der Kopfdaten. | AC-29, AC-34 |
| `__init__`, `update_poll_interval` | `backend/app/workers/order_worker_host.py`, `OrderWorkerHost` | Setzen den Input-Service zusammen und halten dessen Betriebswerte mit dem Worker synchron. Dispatchregeln bleiben im bestehenden Service. | AC-15, AC-36 |
| `__post_init__`, `from_environment` | `backend/app/settings.py`, `OrderSettings` | Validieren/laden `ORDER_PLANT_TIMEZONE`, Standard `Europe/Berlin`. Der vorhandene `pytz`-Datenbestand funktioniert auch ohne Betriebssystem-Zeitzonendateien im Alpine-Image. | AC-09 |
| `request`, `detail`, `inputContext`, `create` | `frontend/lib/order-api.ts`, `OrderApiClient` | Ergänzen Erfassung, vollständiges Detail und Feldfehler; POST wird nicht automatisch wiederholt. | AC-04, AC-05, AC-21, AC-27 |
| `orderDraft`, `orderPayload`, `sameOrder`, `completeOrderInput`, `inputFieldErrors` | `frontend/lib/order-input.ts` | Initialisieren einmalig, prüfen Eingaben, expandieren Queue und vergleichen vollständigen Inhalt. Unvollständige Antworten sind kein belegter Inhaltskonflikt. | AC-06, AC-10 bis AC-12, AC-16, AC-18 bis AC-20, AC-29, AC-30 |
| `ManualOrderEntry`, `OrderEntryDialog`, `review`, `send`, `check`, `finish`, `readAttempt` | `frontend/components/manual-order-entry.tsx` | Führen Erfassung, Zusammenfassung, Sperren und Reload-Abgleich innerhalb derselben Browsersitzung. Session-Speicherfehler verhindern den ersten POST. | AC-01, AC-03, AC-23 bis AC-32, AC-37, AC-38 |
| `OrderEntryFields`, `input`, `rowChange`, `OrderEntrySummary` | `frontend/components/order-entry-fields.tsx`, `order-entry-summary.tsx` | Präsentieren editierbare Eingaben und alle wirksamen Werte; Labels, Feldfehler und sichtbare Zeilenreihenfolge bleiben erhalten. | AC-02, AC-03, AC-06, AC-11, AC-12, AC-18, AC-38, AC-39 |
| `OrdersSection`, `onAccepted`, `OrderDetailDialog` | `frontend/components/orders-section.tsx`, `order-detail-dialog.tsx` | Erweitern den Header, fokussieren die Suche auf die angenommene ID und aktualisieren Details unabhängig von der Liste. Annahme wird bei Nachladefehler nicht zurückgenommen. | AC-01, AC-32 bis AC-35 |
| `save`, `read`, `failed`, `__init__` | `backend/app/repositories/product_catalog_repository.py` | Spiegeln vollständige Produktstände atomar, ignorieren verspätete Produktstände, deaktivieren fehlende IDs und erhalten Daten bei Fehlern. Lesen erfolgt konsistent aus der DB. | CAT-02 bis CAT-06 |
| `synchronize`, `catalog`, `prepare`, `_fresh` | `backend/app/services/order_input_service.py` | Trennen SPS-Import von DB-Verwendung. Fehler verwerfen die Verbindung für einen späteren Neuversuch; Katalogfrische hat eine eigene Grenze. | CAT-01, CAT-05, CAT-06 |
| `start`, `_synchronize_catalog`, `stop`, `__init__` | `backend/app/workers/order_worker_host.py` | Starten und beenden den separaten Katalogtask samt eigener Verbindung; langsame Katalogzugriffe verzögern die Auftragsbeobachtung nicht. | CAT-06, CAT-07 |
| `create_app` / `lifespan` | `backend/app/main.py` | Injizieren den gesonderten Kataloggateway in den bestehenden Host. Ein Anwendungsstart startet weiterhin auch den Auftragsworker. | CAT-07 |
| `synchronize_product_catalog` | `backend/app/routers/orders_router.py` | Bietet einen ausdrücklich angeforderten SPS-Lese-/DB-Abgleich ohne Auftragsannahme; Fehler liefern 503. | CAT-05, CAT-06 |
| `synchronize` | `backend/app/scripts/sync_product_catalog.py` | Importiert einmalig mit gespeicherten Knoteneinstellungen ohne Anwendung, Dispatch oder Workerstart. | CAT-01 bis CAT-05 |
| `upgrade`, `downgrade` | `backend/alembic/versions/plc_catalog_01.py` | Verändern ausschließlich die beiden neuen Katalogtabellen. | CAT-02, CAT-04 |
| `__post_init__`, `from_environment` | `backend/app/settings.py` | Laden und prüfen die getrennten Abgleich-/Veraltungsintervalle, Standard 30/300 Sekunden. | CAT-07 |
| `synchronizeCatalog` | `frontend/lib/order-api.ts`, `frontend/components/manual-order-entry.tsx`; Delegation in `frontend/lib/api.ts` | Verbindet den Abgleichbutton mit dem Katalog-POST und lädt danach DB-Vorbereitung neu; kein Auftrags-POST. | CAT-06 |

## Implementierungsabgleich und Tests

- Testzuordnung und Ausführungsstand: [Issue-30-Einträge im Harness-Testkatalog](../../Harness/harness/_unittest.md#i30--erfassung-und-queueaufbau).
- Neue Backendfälle: 22 Erfassungsfälle und 6 Katalogpersistenz-/Lebenszyklusfälle bestanden, ausschließlich synthetische Gateways und isolierte PostgreSQL-Schemas. Browser inklusive bestehender Auftrags-/Proxyregression: 56 bestanden auf Desktop und 390×844; Produktionsbuild und TypeScript erfolgreich. Lint wird auf geänderte Dateien begrenzt.
- Vollständige Backendregression: 211 bestanden, 2 Fehler. Beide Fehler wurden separat im unveränderten `HEAD` reproduziert: `test_pages_filter_before_pagination_and_share_global_review` (aufgefüllte ID-Suche) und `test_message_id_can_supply_missing_event_id` (Lager-Zeitzone). Diese Bereiche wurden nicht ungefragt korrigiert.
- Vorhandene Idempotenz-, FIFO-, Recovery-, API- und Browserprüfungen bilden die Regressionbasis; ihr früheres Ergebnis ist kein Nachweis für diese neue Funktion.
- UI-Erkenntnisse: [Issue-30-Regeln im Harness](../../Harness/harness/_uiux.md#issue-30-agreed-manual-order-entry).
- State bleibt `Modified`, bis Anwendung, Kriterien, Methodendokumentation und erforderliche Nachweise übereinstimmen.

## Voraussetzungen für reale Anbindung

Am 15.10.2026 wurde der SPS-Katalog auf ausdrücklichen Benutzerauftrag anhand der PDF-Seiten 96–97 und direkt an der Anlage lesend geprüft: tatsächlicher Name `Produktspezifikation`, IDs/Texte 1–6, sämtliche Bauplanfelder und je 33 Slots bestätigt. Die additive Migration und der workerfreie Import spiegeln diese Daten in PostgreSQL; die drei bestehenden Aufträge bleiben erhalten. Es wurden keine SPS-Werte geschrieben und keine Aufträge gestartet.

Anlagenzeitbezug und fachliche Standardwertsemantik sowie reale Auftragsläufe über die neue UI bleiben als Anlagenabnahme offen. Reale Starts erfolgen separat mit abgestimmten Testdaten und einem freien Slot über den vorhandenen Worker. Spec-State bleibt bis zum vollständigen Nachweis und Wiki-Abgleich `Modified`.

# Auftrags- und Produktionsübersicht – Issue #29

## Meta

- **Typ:** Feature-Spezifikation
- **State:** Modified
- **Stand:** 2026-10-13
- **Review:** Vom Benutzer am 2026-10-13 fachlich bestätigt; noch nicht implementiert.
- **Implementierungsplan:** [Schrittweiser Plan mit OOP-Verantwortlichkeiten](../plans/issue-29-order-production-overview.md)
- **Issue:** [#29 – Auftrags- und Produktionsübersicht](https://github.com/Berufskolleg-Meschede/MESchede/issues/29)
- **Idee:** [Harness-Idee](../../Harness/harness/ideas/I1%20Auftrags-%20und%20Produktionsuebersicht%20Issue%2029.md)
- **Entscheidungsgrundlage:** [Recoveryberatung](../../Harness/harness/decisions/issue-29-recovery.md)

Die Ablage unter `docs/specs/` folgt der bestehenden Feature-Dokumentation. Harness reserviert `spec/` für Bugfixes; seine Regeln für Quellen, atomare Akzeptanzkriterien, Testzuordnung und State werden hier übernommen.

## User Story

Als Anlagenoperator möchte ich Produktions- und Lieferaufträge mit ihren wartenden Aufträgen, aktiven Produkteinheiten und bestätigten Ergebnissen verfolgen, damit ich den tatsächlichen Anlagenzustand erkenne und unklare Läufe nach einer Unterbrechung prüfen kann.

## Description

Die MES-Oberfläche zeigt getrennte Produktions- und Lieferansichten mit gemeinsamen fachlichen Status- und Mengenregeln. Ein separates, lesendes Dashboard kombiniert Zusammenfassungen beider Bereiche. Rückmeldungen aus der PLC werden eindeutig einem dauerhaft gespeicherten Lauf zugeordnet. Ein unklarer möglicherweise gestarteter Lauf blockiert weitere MES-Starts beider Auftragsarten bis zur Klärung. Produktion und Kommissionierung laufen im MES grundsätzlich nacheinander; die globale Annahmereihenfolge bestimmt den nächsten Auftrag.

## Ist-Verhalten

- `/production-orders` und `/delivery-orders` existieren bereits und verwenden die gemeinsame `OrdersSection`.
- `/dashboard` kombiniert Auftragssummaries, lädt seine Daten jedoch nur beim Öffnen.
- `frontend/lib/api.ts` verwendet `USE_MOCK = true`; die Datenänderungen sind prozesslokale Demoänderungen im Browser.
- Die bestehenden Frontend- und Datenbank-Auftragstypen enthalten ID, Artikel, Sollmenge und Status, aber keine vollständigen Lauf- oder Produktresultate.
- Die POST-Endpunkte nehmen `order_id` und `mes_auftrag` in zwei unabhängige `asyncio.Queue`-Warteschlangen auf. Dieser Ablauf speichert Annahme, Warteposition und Ergebnisse nicht dauerhaft in PostgreSQL.
- Der gemeinsame Handshake liest `StatusMES` beziehungsweise `Status_MES`, wartet auf Start/Ende und bestätigt anschließend Idle. Produktresultate und vollständige Auftragshistorie werden damit noch nicht bereitgestellt.
- Die Worker können unabhängig voneinander starten. Eine gemeinsame Vergabe des einzigen aktiven Laufs ist in diesem Ablauf nicht vorhanden.
- Worker-Diagnosen sind vorhanden; sie ersetzen keine dauerhafte Auftrags-/Produkthistorie oder manuelle Wiederaufnahmeprüfung.

Diese Aussagen beruhen auf Codeanalyse. In dieser Spezifikationsphase wurden keine Anlagenläufe oder Anwendungstests ausgeführt.

## Umfang und Abgrenzung

**Enthalten:** getrennte Auftragsansichten, kombinierte Dashboardsummaries, regelmäßige Aktualisierung, Quellenaktualität, PLC-Reader und Korrelation, dauerhafte Warteschlangen/Läufe/Resultate, Schutz gegen Doppelzählung, gemeinsame Startvergabe, Wiederanlaufabgleich und manuelle Laufprüfung.

**Separates Issue:** manuelle Auftragserstellung und Auslösung, einschließlich ihrer Formulare, werden über Issue #30 bearbeitet. Dieses Feature stellt die dauerhaft nachvollziehbaren Aufträge und den Laufzustand bereit, die jene Aktionen benötigen. Neue Pause-, Abbruch-, Editier-, Lösch- oder Wiederholungsaktionen sind hier nicht vereinbart. Der bisherige freie Demo-Statuseditor darf keine echten PLC-Abschlüsse vortäuschen.

Die Annahme bestehender API-Aufträge bleibt eine Eingangsmöglichkeit. Diese Aufträge müssen denselben Persistenz-, Reihenfolge- und Wiederanlaufregeln folgen. Neue ERP-/Webshop-Verträge, eine neue Anmeldung, Lagerlogik und zusätzliche Analysefunktionen gehören nicht zu dieser Spec.

## Soll-Verhalten

### Ansichten

| Bereich | Verhalten |
| --- | --- |
| `/production-orders` | Produktionsaufträge mit aktivem Lauf, wartenden Aufträgen, Produktergebnissen und Zugriff auf die manuelle Prüfung. |
| `/delivery-orders` | Entsprechende Ansicht für Lieferaufträge beziehungsweise Kommissionierung. |
| `/dashboard` | Zusammenfassungen beider Bereiche mit erkennbaren Auftragstypen, kombinierten Summen und Links auf die zuständige Auftragsseite; keine Mutation. |

Jede Auftragsseite unterscheidet wartende MES-Aufträge von Produkteinheiten des aktiven Auftrags. Ein wartender Auftrag ist keine Produkteinheit. Auftragsinformationen zeigen fachliche ID, Typ, Status, Sollmenge, bearbeitete Menge, Gutmenge und Fehlmenge. Produktinformationen zeigen vorhandene Produktkennung/-bezeichnung, Serien-/Sequenznummer, Ergebnis und Fehlercode. Nicht verfügbare Felder bleiben erkennbar unbekannt.

Die Auftragsinformation und ihre Resultate sind auf der zuständigen Seite erreichbar; eine neue Detailroute ist nicht vorgegeben. Das Dashboard zeigt einen globalen Sperr-/Prüfhinweis und verlinkt die betroffenen Läufe.

### Identität und Datenhoheit

- Fachliche Auftrag-ID und Auftragstyp identifizieren einen Auftrag gemeinsam; identische IDs zwischen Produktion und Lieferung dürfen nicht kollidieren.
- Ein Lauf besitzt eine dauerhafte, innerhalb des MES eindeutige Identität. Die Korrelation zur numerischen `Auftragsnummer` und zum PLC-Slot wird dauerhaft festgehalten.
- Ein PLC-Produktresultat wird anhand einer verifizierten Einheitenidentität innerhalb dieses Laufs zugeordnet. Wiederverwendete Arrayplätze allein sind keine belastbare Identität über verschiedene Läufe.
- Wiederholte Annahme derselben Auftragsart/ID mit gleichem Inhalt liefert denselben angenommenen Auftrag. Abweichender Inhalt unter derselben Identität erzeugt einen Konflikt statt eines weiteren Laufs. Damit bleibt auch eine wiederholte Annahme nach Neustart eindeutig; die manuelle Eingabeoberfläche bleibt Issue #30.
- Zustandsänderungen, Startberechtigung, Reviewvalidierung und Mengenregeln sind Backend-Verhalten. Ein Browser oder zweiter API-Aufruf kann diese Regeln nicht umgehen.
- Neue API-Feldnamen, Enum-Erweiterungen, Tabellen- oder Endpunktnamen werden erst im Implementierungsplan festgelegt. Die folgenden Begriffe beschreiben den fachlichen Vertrag, keine bereits existierenden DTOs.

### Status und Mengen

Ein Auftrag kann fachlich warten, zur Übergabe vorbereitet werden, bestätigt laufen, beendet sein oder einer Prüfung bedürfen. Das bisherige API-Vokabular `pending`, `in_progress`, `error`, `completed` bildet diese zusätzlichen Zustände noch nicht vollständig ab; die Oberfläche darf sie nicht durch eine falsche Erfolgsmeldung ersetzen.

- Annahme ist weder bestätigter Start noch Abschluss.
- Ein beobachtetes, korrekt zugeordnetes Endsignal beendet den Lauf. Ob Einheiten gut oder fehlerhaft sind, ergibt sich getrennt aus den Produktresultaten.
- Bearbeitete Menge ist die Anzahl eindeutig final bewerteter Einheiten; Gut- und Fehlmenge werden separat ausgewiesen. Bei vollständiger Ergebniserfassung entspricht bearbeitet der Summe aus Gut- und Fehlmenge.
- Wiederholtes Lesen zählt eine Einheit nicht erneut. Fremde Resultate und Restwerte früherer Läufe werden ausgeschlossen.
- Fehlende Resultate bleiben unbekannt beziehungsweise unvollständig. Unfertige Einheiten sind keine bestätigten Fehlteile. Eine Sollmenge darf fehlende Istmengen nicht ersetzen.
- Laufende und beendete Läufe mit fehlenden Einzelresultaten werden als solche mit unvollständigem Ergebnis dargestellt; das Ende ist kein Nachweis vollständiger Produktdaten.
- Start-/Endzeitpunkte beruhen auf bestätigten Signalen. Ein MES-Beobachtungszeitpunkt wird nicht als erfundener PLC-Zeitstempel ausgegeben.
- Ein Verbindungsfehler verändert nicht stillschweigend den zuletzt bekannten fachlichen Status oder bestätigte Mengen. Quellenstatus und fachlicher Status werden getrennt dargestellt.
- Lieferabschluss bedeutet den bestätigten Abschluss in der Fabriksimulation, keine belegte Zustellung beim Kunden.

### Persistenz und gemeinsame Reihenfolge

PostgreSQL bewahrt angenommene Aufträge, ihre globale Annahmereihenfolge, Laufzustände, Korrelationen, bestätigte Ergebnisse und Reviewentscheidungen. Eine erfolgreiche Annahme wird erst nach dauerhafter Speicherung bestätigt. Der Zustand vor einer möglichen Übergabe muss nachvollziehbar sein, auch wenn der Prozess zwischen Schreiben des Startbefehls und Empfang der Bestätigung abbricht.

Höchstens ein Produktions- oder Lieferlauf erhält gleichzeitig die MES-Startberechtigung. Die Regel gilt für beide Worker, gleichzeitige Annahmen und alle Aufrufwege gemeinsam. Sie ist eine MES-Betriebsregel; sie behauptet keine nachgewiesene physische Parallelfähigkeit der Anlage.

Der nächste wartende Auftrag ist der zuerst dauerhaft angenommene Auftrag, unabhängig von Produktion/Lieferung oder `Prioritaet`. Gleichzeitige Annahmen erhalten eine stabile Reihenfolge. Diese Reihenfolge bleibt nach Neustart erhalten. Ist der älteste Auftrag nicht ausführbar, bleibt der Grund sichtbar; jüngere Aufträge überholen ihn nicht stillschweigend.

### Wiederaufnahme

Nach Backend-Neustart und nach verlorenem Ausführungsnachweis werden offene Läufe und beide PLC-Slots abgeglichen, bevor ein neuer Start möglich ist. Ein Browserreload löst keine erneute Übergabe aus.

| Korrelierter Befund | Verhalten |
| --- | --- |
| Derselbe Lauf ist bestätigt aktiv | Den bisherigen Lauf weiter beobachten; kein weiterer Startbefehl. |
| Derselbe Lauf ist bestätigt beendet | Verfügbare Endresultate dauerhaft erfassen, bevor Reset oder Folgelauf sie überschreiben können; verifizierten Abschluss-/Resetablauf fortführen. |
| Dauerhaft belegt, dass noch keine Übergabe möglich war | Den Auftrag in seiner bisherigen Warteposition erhalten. |
| Möglicherweise gestartet, aber ohne belastbaren Endnachweis | Prüfbedarf anzeigen und weitere Starts beider Auftragsarten sperren. Idle allein löst dies nicht auf. |
| Fremder Lauf, widersprüchliche Identität oder unerreichbare PLC | Bekannte Daten bewahren, Quellen-/Zuordnungsproblem anzeigen und keine automatische Wiederholung auslösen. |

Eine zunächst wiederhergestellte Verbindung beendet eine erforderliche Prüfung nicht allein. Sind verifizierte, eindeutig korrelierte Fakten verfügbar, dürfen sie den technischen Ausführungsstand aufklären. Widersprüche mit bereits gespeicherten manuellen Bewertungen bleiben sichtbar und prüfbedürftig.

Neue Starts bleiben gesperrt, solange erforderliche Prüfungen offen sind. Nach ihrer Auflösung ist zusätzlich die bestätigte Bereitschaft der Anlage notwendig. Ein manuelles Review allein weist keine PLC-Bereitschaft nach und darf einen laufenden oder fremden PLC-Auftrag nicht übergehen.

### Manuelle Prüfung

Beim nächsten Öffnen der Oberfläche ist offener Prüfbedarf sichtbar. Das Dashboard bietet einen lesenden Hinweis mit Link; das Formular liegt beim betreffenden Lauf auf der Produktions- oder Lieferseite. Schließen des Formulars oder Browserreload entfernt den Prüfbedarf nicht.

Das Formular zeigt Auftragstyp/ID, betroffenen Lauf, betroffene Produkte, Sollmenge, bekannte Gut-/Fehlmengen, letzten beobachteten Zustand und Aktualität. Der Operator erfasst, was mit dem Lauf passiert ist und welche Mengen bekannt sind:

- Lauf beendet;
- Lauf fehlgeschlagen beziehungsweise unterbrochen;
- Ergebnis weiterhin unbekannt.

Bekannte endgültige Gut-/Fehlmengen werden als ganze, nicht negative Mengen angegeben. Unbekannte Mengen können ausdrücklich unbekannt bleiben. Angaben oberhalb der Sollmenge oder unterhalb bereits belegter Mengen dürfen nicht stillschweigend übernommen werden. Die vereinbarte Grenze ist eine Produkteinheit mit einem finalen Ergebnis pro Soll-Einheit dieses Laufs; Nacharbeit/Wiederholung ist hier nicht vereinbart.

Eine Erklärung oder Freitextnotiz ist nicht erforderlich. Die Zuordnung zum Lauf und der Reviewzeitpunkt werden gespeichert. Das Review enthält keine neue Start-/Stop-/Resetaktion.

Manuelle Mengen sind als manuell bestätigt gekennzeichnet, ersetzen keine PLC-Fakten und werden nicht zusätzlich zu bereits gezählten Mengen addiert. Einzelresultate und manuell bewertete Gesamtergebnisse bleiben unterscheidbar. Wiederholte beziehungsweise konkurrierende Reviews dürfen keine doppelte Mengenänderung oder unbemerkte Überschreibung einer zwischenzeitlichen Bewertung bewirken. Weiterhin unbekannt lässt den Prüfbedarf offen.

### Aktualität und Darstellung

Die API stellt konsistente Auftrags-/Lauf-/Produktinformationen samt Quellenstatus und letztem erfolgreichen Beobachtungszeitpunkt bereit. Produkt- und Laufdaten werden regelmäßig aktualisiert. Abfrageintervall und Veraltungsgrenze sind festgelegte, überprüfbare Konfigurationswerte; die Grenze liegt oberhalb des normalen Abfrageintervalls. Ihre konkreten Werte werden im Implementierungsplan abgestimmt und an der Anlage überprüft.

Ein fehlgeschlagener Leseversuch erneuert den letzten Erfolgszeitpunkt nicht. Bei Störung bleiben letzte gültige Daten sichtbar und werden als veraltet beziehungsweise nicht aktuell verifizierbar gekennzeichnet. Ohne bisherige Daten wird unbekannt statt eines bestätigten Nullwerts angezeigt. Eine teilweise nicht verfügbare Quelle darf bekannte Daten des anderen Bereichs nicht als verloren darstellen.

Die Oberfläche ist deutschsprachig, zeigt Status als Text zusätzlich zur Farbe und unterscheidet Laden, leere Daten, leere Suchergebnisse, fehlende Verbindung und unvollständige Resultate. Die vorhandene Harness-UI-Richtung bleibt maßgeblich. Tastaturbedienung und responsive Tabellen werden auf den verfügbaren Projektgeräten geprüft. Demodaten sind nur in explizit gekennzeichnetem Demobetrieb zulässig; Verbindungsfehler aktivieren keinen stillen Mock-Fallback.

## Akzeptanzkriterien

| ID | Prüfaussage |
| --- | --- |
| AC-01 | Die Produktionsseite zeigt ausschließlich Produktionsaufträge. |
| AC-02 | Die Lieferseite zeigt ausschließlich Liefer-/Kommissionieraufträge. |
| AC-03 | Das Dashboard zeigt die Zusammenfassungen beider Bereiche gemeinsam. |
| AC-04 | Das Dashboard bietet keine Auftragsmutation oder Revieweingabe. |
| AC-05 | Jede Auftragsseite stellt wartende Aufträge getrennt von den Produkteinheiten des aktiven Laufs dar. |
| AC-06 | Jeder angezeigte Auftrag besitzt eine erkennbare fachliche ID, Auftragstyp, Sollmenge und Laufstatus. |
| AC-07 | Die Auftragsansicht unterscheidet bearbeitete, erfolgreiche und fehlgeschlagene Mengen. |
| AC-08 | Verfügbare Produktidentitäten und Ergebnisse sind dem passenden Lauf zugeordnet. |
| AC-09 | Erneutes Lesen derselben finalen Einheit verändert die Mengen nicht. |
| AC-10 | Resultate eines früheren oder fremden PLC-Laufs verändern den aktuellen Lauf nicht. |
| AC-11 | Fehlende Produktresultate werden als unvollständig angezeigt. |
| AC-12 | Annahme eines Auftrags erzeugt keinen bestätigten Laufabschluss. |
| AC-13 | Ein Idle-Rohwert ohne korrelierten Endnachweis erzeugt keinen bestätigten Laufabschluss. |
| AC-14 | Ein erfolgreich angenommener wartender Auftrag bleibt nach Backend-Neustart vorhanden. |
| AC-15 | Die globale Annahmereihenfolge bleibt nach Backend-Neustart erhalten. |
| AC-16 | Gleichzeitige Produktions-/Lieferanfragen erzeugen höchstens einen aktiven MES-Dispatch. |
| AC-17 | Der älteste wartende Auftrag erhält als nächster die Startberechtigung, unabhängig von Auftragstyp oder Prioritätsfeld. |
| AC-18 | Gleiche Auftragstyp/ID mit gleichem Inhalt erzeugen keinen weiteren Lauf. |
| AC-19 | Gleiche Auftragstyp/ID mit anderem Inhalt werden als Konflikt abgelehnt. |
| AC-20 | Ein möglicherweise gestarteter Lauf wird nach Neustart vor einem weiteren Start abgeglichen. |
| AC-21 | Ein eindeutig identifizierter weiterlaufender Auftrag erhält keinen weiteren Startbefehl. |
| AC-22 | Ein ungeklärter möglicherweise aktiver Lauf sperrt neue Starts beider Auftragsarten. |
| AC-23 | Die globale Sperre bleibt bis zur erforderlichen Reviewauflösung bestehen. |
| AC-24 | Auch nach Review bleibt ein neuer Start bei unbestätigter PLC-Bereitschaft gesperrt. |
| AC-25 | Beim Öffnen der Oberfläche ist ungelöster Prüfbedarf sichtbar. |
| AC-26 | Ein Browserreload entfernt ungelösten Prüfbedarf nicht. |
| AC-27 | Ein Review kann ohne Erklärung/Freitextnotiz gespeichert werden. |
| AC-28 | Ein Review zeichnet die gewählte Laufbewertung und bekannte beziehungsweise unbekannte Gut-/Fehlmengen auf. |
| AC-29 | Ungültige oder widersprüchliche Reviewmengen werden vom Backend abgelehnt. |
| AC-30 | Eine manuelle Bewertung erzeugt keinen PLC-Steuerungsbefehl. |
| AC-31 | Manuelle Angaben werden in der Oberfläche als manuell bestätigt gekennzeichnet. |
| AC-32 | Wiederholtes Speichern eines Reviews zählt dessen Mengen nicht erneut. |
| AC-33 | Eine verlorene PLC-Verbindung verändert bekannte bestätigte Produktresultate nicht. |
| AC-34 | Ein fehlgeschlagener Leseversuch aktualisiert den letzten Erfolgszeitpunkt nicht. |
| AC-35 | Überschreiten der konfigurierten Veraltungsgrenze erzeugt eine sichtbare Veraltet-Kennzeichnung. |
| AC-36 | Ohne bekannte Beobachtung erscheinen Messwerte als unbekannt statt bestätigtem Nullwert. |
| AC-37 | Bei API-/PLC-Fehlern aktiviert die Oberfläche keine unmarkierten Demodaten. |
| AC-38 | Prüfung, Navigation und Tabelleninteraktion sind per Tastatur bedienbar. |
| AC-39 | Verfügbare Endresultate werden dauerhaft gespeichert, bevor die MES-Quittierung sie verlieren lassen kann. |
| AC-40 | Konkurrierende Reviews erzeugen keine unbemerkte Überschreibung einer neueren Bewertung. |

## PLC-Verifikation vor Live-Abnahme

Dies sind erforderliche technische Nachweise, keine erfundenen Signalverträge. Ohne ausreichenden Nachweis wird der betreffende Zustand als unbekannt dargestellt; die Live-Abnahme ist dann nicht erfüllt.

- Tatsächliche Nodes, Datentypen und lesbare Felder für beide Slots protokollieren; bekannte unterschiedliche Schreibweisen berücksichtigen.
- Start, Laufende, Idle/Reset und Bereitschaft am korrelierten Auftrag prüfen, einschließlich sehr kurzer Läufe.
- Finale Produktstatus-/Fehlercodes sowie Verhalten leerer, alter und wiederverwendeter Slots bestätigen.
- Eine eindeutige Zuordnung zwischen fachlichem Auftrag, Lauf, numerischer PLC-Auftragsnummer und Einheiten bestätigen; Nummern dürfen nicht durch Abschneiden oder ungeprüfte Wiederverwendung kollidieren.
- Prüfen, ob Endresultate vor beziehungsweise nach Quittierung erhalten bleiben; der Reader und Handshake müssen zum tatsächlichen Datenlebenszyklus passen.
- Bereitschaft für einen neuen Auftrag unter Berücksichtigung beider Slots und vorhandener Anlagensteuerung prüfen. Dieses Feature verändert keine HMI-Kommandos oder PLC-Feedbackfelder.
- Lieferabschluss in der Fabriksimulation dokumentieren; keine Kundenzustellung behaupten.

Kann der PLC-Vertrag eine benötigte Unterscheidung nicht liefern, wird der konkrete fehlende Nachweis dokumentiert und der zugehörige Lauf geprüft. Eine fehlende Beobachtung darf nicht durch eine angenommene Erfolgsmeldung ersetzt werden.

## Tests und Abnahme

Der [Harness-Testkatalog](../../Harness/harness/_unittest.md) erfasst den geplanten Testbedarf mit dieser Spec und ihren AC-IDs. Testnamen und neue Dateipfade werden erst aus der tatsächlichen Implementierung übernommen.

- Unit-/Verhaltenstests: Korrelation, Doppelzählung, unbekannte Resultate, FIFO, gegenseitiger Startausschluss, Sperrregeln und Reviewvalidierung.
- Integrationsprüfungen: PostgreSQL-Persistenz über Prozessneustart, Unterbrechung zwischen Startschreiben und Bestätigung, konkurrierende API-/Reviewaufrufe und API-/PLC-Ausfall.
- UI-Prüfungen: Datenzustände, Demokennzeichnung, Review ohne Pflichtnotiz, Dashboard ohne Mutation, Tastatur und Projektgeräte.
- Anlagenabnahme: mindestens ein realer Produktions- und ein realer Lieferauftrag bis zu korrelierten Endresultaten; Fehler-/Unterbrechungs-/Wiederanlauffälle mit protokollierten erwarteten und tatsächlichen Ergebnissen.

Vorhandene Backendtests für Client, Handshake und Workerdiagnosen dienen als Regressionseinstieg, belegen dieses Feature aber noch nicht. Diese Spec erhält erst `Implemented`, wenn Code, Tests und erforderliche Abnahmen nachweislich übereinstimmen. Nicht ausgeführte Anlagenprüfungen bleiben ausdrücklich offen.

## Angepasste Methoden

Noch keine Anwendungscodeänderungen. Tatsächliche Methoden, Verantwortungen und Erkenntnisse werden bei der Implementierung dokumentiert.

## UI-/UX-Erkenntnisse

Die vereinbarte Richtung ist in [Harness UI/UX](../../Harness/harness/_uiux.md#issue-29-agreed-order-overview-and-recovery) ergänzt. Sie beschreibt Soll-Verhalten, keinen bereits erreichten Integrationsstand.

## Quellen und Beziehungen

- Gemeinsam bestätigte Benutzerantworten zu Seitenstruktur, Mengen, Wiederaufnahme, globaler Sperre, Review ohne Pflichtnotiz und FIFO.
- [Themen-Spezifikation der Projektwoche](projektwoche-mes-ui.md), insbesondere Issue #29; diese Spec konkretisiert dessen Umfang.
- [Issue #29 Ausgangsdokument](../issues/projektwoche/overview.md).
- [Manuelles Starten – separates Issue #30](../issues/projektwoche/manual.md).
- [Aktueller OPC-UA-Stand](../opc-ua-integration.md).
- `frontend/app/dashboard/page.tsx`, `frontend/app/production-orders/page.tsx`, `frontend/app/delivery-orders/page.tsx`, `frontend/components/orders-section.tsx`, `frontend/lib/api.ts`, `frontend/lib/types.ts`.
- `backend/app/models/production_order.py`, `backend/app/models/delivery_order.py`, `backend/app/models/mes_auftrag.py`, beide Auftragsrouter und Queueworker, `backend/app/workers/plc_handshake.py`, `backend/app/workers/diagnostics.py`, `backend/app/clients/opc_ua_client.py`.

## Noch festzulegen beziehungsweise nachzuweisen

- Polling-/Veraltungswerte, DTO-Namen und API-Form sind im verlinkten Implementierungsplan als technische Entwurfsentscheidungen konkretisiert; vor Live-Abnahme prüfen.
- PLC-Vertragsnachweise und reale Testfälle gemäß obiger Verifikationsliste.
- Verfügbare Projektgeräte für responsive und Tastaturabnahme.
- Fachlicher Review abgeschlossen; Implementierungsplan erstellt. Umsetzung und Nachweise folgen als separate Phase.

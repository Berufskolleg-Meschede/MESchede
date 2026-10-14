# Auftrags- und Produktionsübersicht – Issue #29

## Meta

- **Typ:** Feature-Spezifikation
- **State:** Modified
- **Stand:** 2026-10-13
- **Review:** Vom Benutzer am 2026-10-13 fachlich bestätigt; Software umgesetzt und lokal geprüft, echte PLC-Vertragsprüfung/Anlagenabnahme offen.
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
- Fehlende Einzelresultate während eines laufenden Auftrags bleiben offen; unfertige Einheiten sind keine bestätigten Fehlteile.
- Ein eindeutig korrelierter PLC-Auftragsabschluss (`StatusMES=5`) gilt als erfolgreicher Auftrag. Bestätigte, zugeordnete PLC-Fehlercodes bleiben als Fehlteile gezählt; fehlende oder nicht zugeordnete Einzelresultate werden als erfolgreich angenommen und in der Mengenherkunft kenntlich gemacht.
- Ein kurzzeitiger Verlust der PLC-Rückmeldung während eines Laufs verlangt zunächst keine manuelle Prüfung. Wenn derselbe Auftrag später mit `StatusMES=5` bestätigt wird, wird er als erfolgreich abgeschlossen und eine nur aus dem transienten Lesefehler stammende Prüfung automatisch aufgelöst.
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

Ohne passenden Endstatus oder bei widersprüchlicher Auftragsidentität bleibt der Lauf prüfbedürftig. Ein korreliertes `StatusMES=5` löst die Prüfung auf; falls die Steuerung bereits auf Idle (`StatusMES=0`) zurückgesetzt wurde und ein Abschlusszeitpunkt gespeichert ist, wird der abgeschlossene Lauf ebenfalls freigegeben. Fehlende oder unbekannte Einzelstatuscodes werden als erfolgreich gezählt.

## Tests und Abnahme

Der [Harness-Testkatalog](../../Harness/harness/_unittest.md) verknüpft tatsächliche Backend-/Browsertests mit dieser Spec und ihren AC-IDs. PostgreSQL-Integration nutzt nur explizite Testdatenbanken und zufällige eigene Schemas; Browserdaten sind auf Testfixtures begrenzt.

- Unit-/Verhaltenstests: Korrelation, Doppelzählung, unbekannte Resultate, FIFO, gegenseitiger Startausschluss, Sperrregeln und Reviewvalidierung.
- Integrationsprüfungen: PostgreSQL-Persistenz über Prozessneustart, Unterbrechung zwischen Startschreiben und Bestätigung, konkurrierende API-/Reviewaufrufe und API-/PLC-Ausfall.
- UI-Prüfungen: Datenzustände, Demokennzeichnung, Review ohne Pflichtnotiz, Dashboard ohne Mutation, Tastatur und Projektgeräte.
- Anlagenabnahme: mindestens ein realer Produktions- und ein realer Lieferauftrag bis zu korrelierten Endresultaten; Fehler-/Unterbrechungs-/Wiederanlauffälle mit protokollierten erwarteten und tatsächlichen Ergebnissen.

Backendtests für Domäne, Repository, Services, Migration, API, Client, Gateway und Workerdiagnosen sowie Browserprüfungen sind implementiert und lokal erfolgreich ausgeführt. Diese Spec erhält erst `Implemented`, wenn Code, Tests und erforderliche Abnahmen nachweislich übereinstimmen. Nicht ausgeführte Anlagenprüfungen bleiben ausdrücklich offen.

### Lokaler Nachweisstand – 2026-10-13

- Backendregression mit isoliertem PostgreSQL: **130 Passed**, einschließlich Migration, separatem Wiederanlaufprozess, konkurrierender Annahme/Reservierung/Review, Führung, Timeout, Resultatcommit und Teilreset.
- Playwright: **22 Passed** bei 1440×1000 und 390×844; beide Auftragsseiten, Dashboard, Keyboard-Review, Versionskonflikt, idempotenter Retry, Mengenvalidierung, API-Ausfall/Veraltung, Filter und echter Next-HTTP-Proxy.
- Frontendbuild, TypeScript und geänderte/neue Dateien in ESLint erfolgreich; Screenshots der Seiten, des Dashboards und des Prüfdialogs visuell geprüft.
- Weitere PLC-Abnahmen und Prüfung auf Projektgeräten bleiben offen. Die Spec bleibt deshalb `Modified`; neue Starts benötigen PLC-Bereitschaft und dürfen keinen offenen Review übergehen.

## Angepasste Methoden

Die folgenden Verantwortlichkeiten bilden die tatsächliche Implementierung ab. Records und DTOs halten Daten; Fachlogik liegt in Services, HTTP-/PLC-/DB-Nebeneffekte an getrennten Grenzen. `OrderWorkerHost` ist der implementierte Name des im Plan zunächst `OrderRuntime` genannten Lebenszyklusobjekts.

| Datei / Typ | Tatsächliche Methoden | Aufgabe, Änderung und Erkenntnis | Bezug |
| --- | --- | --- | --- |
| `backend/app/domain/order_run.py` / `OrderRun` | `transition_to`, `status` | Erlaubt nur belegbare Laufübergänge; Ende ist unabhängig von Produktqualität, Idle ist kein Endnachweis. | AC-06, AC-12, AC-13 |
| `backend/app/repositories/order_repository.py` / `OrderRepository` | `transaction`, `initialize`, `lock_state`, `load_run`, `load_units` | Kurzlebige Sessions je Thread, gleiche Lockreihenfolge und idempotente Koordination. Keine DB-Transaktion bleibt während PLC-Wartezeit offen. | AC-14 bis AC-16, AC-40 |
| dieselbe Datei / `OrderRepository` | `admit`, `_check_plc_number`, `_create_units`, `reserve_next` | Normalisierte Annahme, globale Sequenz, identischer Retry ohne zweiten Lauf und Reservierung vor Start. Nummernwiederverwendung je Typ bleibt bis zur sicheren Generationsidentität ausgeschlossen. | AC-14 bis AC-20 |
| dieselbe Datei / `OrderRepository` | `snapshot`, `change_phase`, `transition`, `require_review`, `mark_review`, `block`, `release_completed`, `return_prepared_to_queue` | Konsistenter Read-only-Snapshot, dauerhafte Sperre und versionsgeschützte Übergänge. Neue Fakten und widersprechender Prüfbedarf können atomar gespeichert werden. | AC-20 bis AC-26, AC-33, AC-39, AC-40 |
| dieselbe Datei / `OrderRepository` | `source_success`, `source_failure` | Nur erfolgreiches Lesen erneuert Aktualität; Fehler bewahren letzte Beobachtung. | AC-33 bis AC-36 |
| `backend/app/repositories/worker_leadership.py` / `WorkerLeadership` | `_invoke`, `_acquire_sync`, `acquire`, `assert_owned`, `_release_sync`, `close` | Dedizierte PostgreSQL-Session mit Advisory-Lock; der Lock wird erst nach auslaufendem PLC-I/O freigegeben. | AC-16, AC-20, AC-21 |
| `backend/app/services/order_admission_service.py` / `OrderAdmissionService` | `accept` | Gibt dauerhafte Annahme samt Laufreferenz zurück. `202` beweist weder PLC-Start noch Abschluss. | AC-12, AC-14, AC-18, AC-19 |
| `backend/app/services/order_dispatch_service.py` / `OrderDispatchService` | `tick`, `_readiness_reason`, `_start` | Ein gemeinsamer FIFO-Dispatch prüft beide Slots und Reservierung; speichert Startunsicherheit vor dem Schreiben. | AC-16, AC-17, AC-20 bis AC-24 |
| dieselbe Datei / `OrderDispatchService` | `_continue`, `_continue_reviewed`, `_continue_reset`, `_acknowledge`, `_check_timeout` | Ergebnisse vor Reset sichern, Teilreset anhand gespeicherter Fakten fortführen, Timeout reserviert lassen und manuelle Bewertung ohne Reset weiterbeobachten. | AC-13, AC-21 bis AC-24, AC-30, AC-39 |
| `backend/app/services/product_result_service.py` / `ProductResultService` | `observe`, `_observe_phase`, `_observe_results`, `_check_manual_totals` | Typ/Nummer und geplante Einheitenidentität zuordnen, finale Ergebnisse idempotent speichern, unbekannte Codes unbekannt lassen. Spätere PLC-Widersprüche erhalten die Fakten und setzen neuen Prüfbedarf. | AC-07 bis AC-11, AC-31 bis AC-33, AC-39 |
| `backend/app/services/order_recovery_service.py` / `OrderRecoveryService` | `reconcile` | Beweisbar ungeschriebene Vorbereitung zurückstellen, aktiven korrelierten Lauf erhalten, fehlenden Nachweis manuell prüfen lassen. | AC-20 bis AC-26 |
| `backend/app/services/run_review_service.py` / `RunReviewService` | `review`, `_validate_quantities`, `_view` | Request-ID und Version prüfen, nullable Ganzzahlmengen ohne Notiz speichern und keine PLC-Abhängigkeit besitzen. | AC-27 bis AC-32, AC-40 |
| `backend/app/services/order_query_service.py` / `OrderQueryService` | `_source`, `_quantities`, `_view`, `_summary`, `_snapshot_views`, `overview`, `page`, `detail` | Gemeinsame DTOs aus gespeicherten Fakten; Filter vor Pagination, globale Wartepositionen/Reviews, manuelle Gesamtsummen ohne Addition zu PLC-Fakten und unabhängiger Quellenzustand. | AC-01 bis AC-11, AC-25, AC-26, AC-31 bis AC-37 |
| `backend/app/clients/plc_order_gateway.py` / `PlcOrderGateway` | `_invoke`, `_root`, `_optional_value`, `_read_sync`, `read`, `write`, `acknowledge`, `_disconnect`, `reconnect`, `close` | Ein I/O-Thread, Snapshotvergleich von Nummer/Anzahl/Status/Kommando vor/nach Lesen, unverfügbare Felder nullable. Reset prüft Identität unmittelbar vor Schreiben; Cancel wartet begonnenes I/O ab. | AC-08 bis AC-10, AC-20, AC-21, AC-33, AC-39 |
| `backend/app/clients/opc_ua_client.py` / `OpcUaClient` | `read_anzahl`, `write_anzahl`, `clear_product_queue`, `write_order` | Alle exponierten MES-Eingabeslots typgeprüft löschen/zurücklesen; Anzahl vor Resetkommando null. Eingaben vor Start zurücklesen, Start zuletzt; HMI-/Feedbackfelder unverändert. | AC-21, AC-24, AC-39 |
| `backend/app/workers/plc_handshake.py` | `wait_for_plc_ready`, `wait_for_plc_done` | Legacy-Helfer sind rein beobachtend; kein blinder Reset ohne persistierte Zuordnung und Resultatcommit. Der neue Dispatcher übernimmt den vollständigen Ablauf. | AC-10, AC-20, AC-39 |
| `backend/app/workers/order_worker_host.py` / `OrderWorkerHost` | `running`, `start`, `_finished`, `_run`, `_observe`, `_recover`, `_fail_active`, `stop`, `diagnostics` | Ein Task für beide Typen, unabhängige Quellen, Recovery vor Dispatch, sichtbare Fehler und Cleanup in Gateway-vor-Führung-Reihenfolge. | AC-14 bis AC-26, AC-33, AC-34 |
| `backend/app/main.py` | `create_app`, `lifespan` | Injizierbare Zusammensetzung und gemeinsamer Lifecycle. Nicht vorhandenen `sites_router` nicht importieren; Legacy-Modelle registrieren Mapperbeziehungen, ohne fachfremde Migration. | AC-01 bis AC-04, AC-14, AC-16 |
| `backend/app/db/db.py` | `get_engine`, `init_db`, `get_session` | Asynchrone Legacy-Engine erst bei tatsächlichem Zugriff erzeugen; injizierte Test-App lädt keine Projekt-DB-Konfiguration. | Isolierte Verifikation |
| `backend/alembic/env.py` und neue Revision `7a92c04e31bf` | `run_migrations_online`, `upgrade`, `downgrade` | Explizite isolierte Testverbindung; sechs neue Tabellen, Seedzustand, bestehende Maschinen-/Benutzerdaten erhalten. Migration deaktiviert bestehende Logger nicht. | AC-14 bis AC-19 |
| Produktions-/Lieferrouter, `orders_router.py`, `order_dependencies.py` | `list_productionorders`, `get_productionorder`, `post_productionorder`, `list_deliveryorders`, `get_deliveryorder`, `post_deliveryorder`, `get_order_overview`, `post_run_review`, `get_production_queue_status`, `get_delivery_queue_status`, `get_order_worker`, `execute_order_operation` | Dauerhafte Annahme und reine Lese-/Reviewzugänge, String-IDs, stabile 404/409/422/503-Fehler; Diagnoserouten vor dynamischen Pfaden. | AC-01 bis AC-04, AC-18, AC-19, AC-27 bis AC-30, AC-37 |
| `frontend/lib/api.ts` / `OrderApiClient` | `request`, `list`, `detail`, `overview`, `review` | Echte API, injizierbarer Fetch, verständliche HTTP-Fehler, keine Demodaten bei Ausfall. | AC-01 bis AC-04, AC-27 bis AC-32, AC-37 |
| `frontend/app/api/mes/[...path]/route.ts` | `forward` | Serverseitige Zieladresse, begrenzte Auftragsrouten, korrekter Backend-Listenpfad trotz Next-Slashnormalisierung, unveränderte Payload/Status und no-store. | AC-01 bis AC-04, AC-27 bis AC-30, AC-37 |
| `frontend/hooks/use-order-snapshot.ts` | `useOrderSnapshot`, `refresh` | Sequenzielle Abfragen, Abort bei Wechsel/Unmount, keine verspäteten Filterantworten, letzte Daten und Alter bei Fehlern erhalten. | AC-25, AC-26, AC-33 bis AC-37 |
| Frontend-Auftragskomponenten | `OrdersSection`, `OrderList`, `OrderFilters`, `OrderRows`, `WaitingOrders`, `RunSummary`, `ProductQueue`, `OrderPageFeedback`, `OrderSourceStatus`, `OrderDispatchNotice`, `StatusBadge` | Bestehende Seiten und Tabellen wiederverwenden, Warteschlange/Produkte trennen, globale Prüfung verlinken, Textstatus, unbekannte/manuelle/unvollständige Mengen und Datenzustände anzeigen. | AC-01, AC-02, AC-05 bis AC-11, AC-25, AC-26, AC-31 bis AC-38 |
| `frontend/components/run-review-dialog.tsx` | `parseQuantity`, `RunReviewDialog`, `refreshRun`, `save` | Kein Pflichttext, kontrollierte Mengen, Versionsbasis beim Öffnen, explizite Aktualisierung bei Konflikt, gleiche Request-ID bei unsicherem Retry, keine Doppelspeicherung während Request. | AC-27 bis AC-32, AC-38, AC-40 |
| `frontend/app/dashboard/page.tsx` | `DashboardPage` | Kombiniert Backendzusammenfassungen und Quellen; Links zu Prüfungen, keine Review-/Auftragsmutation. | AC-03, AC-04, AC-25, AC-31 bis AC-38 |

Der konkrete Testkatalog nennt die einzelnen Verhaltens-/Integrations-/Browserprüfungen. Triviale Konstruktoren/Recordfelder enthalten keine zusätzlichen fachlichen Nebenwirkungen.

## UI-/UX-Erkenntnisse

Die vereinbarte Richtung ist in [Harness UI/UX](../../Harness/harness/_uiux.md#issue-29-agreed-order-overview-and-recovery) ergänzt. Sie beschreibt den erreichten lokalen Softwarestand und trennt die noch offene Hardware-/Projektgeräteabnahme davon.

## Quellen und Beziehungen

- Gemeinsam bestätigte Benutzerantworten zu Seitenstruktur, Mengen, Wiederaufnahme, globaler Sperre, Review ohne Pflichtnotiz und FIFO.
- [Themen-Spezifikation der Projektwoche](projektwoche-mes-ui.md), insbesondere Issue #29; diese Spec konkretisiert dessen Umfang.
- [Issue #29 Ausgangsdokument](../issues/projektwoche/overview.md).
- [Manuelles Starten – separates Issue #30](../issues/projektwoche/manual.md).
- [Aktueller OPC-UA-Stand](../opc-ua-integration.md).
- `frontend/app/dashboard/page.tsx`, `frontend/app/production-orders/page.tsx`, `frontend/app/delivery-orders/page.tsx`, `frontend/components/orders-section.tsx`, `frontend/lib/api.ts`, `frontend/lib/types.ts`.
- `backend/app/models/production_order.py`, `backend/app/models/delivery_order.py`, `backend/app/models/mes_auftrag.py`, beide Auftragsrouter und Queueworker, `backend/app/workers/plc_handshake.py`, `backend/app/workers/diagnostics.py`, `backend/app/clients/opc_ua_client.py`.

## Noch festzulegen beziehungsweise nachzuweisen

- Polling standardmäßig 0,5 s, UI 2 s, stale nach 10 s; Werte, Zeitlimits und API-Form sind implementiert und in `backend/.env.example`/`frontend/README.md` dokumentiert. Vor Live-Abnahme passend zur Anlage prüfen.
- PLC-Auftragsnummern sind je Typ konservativ eindeutig; sichere Wiederverwendung erfordert einen zusätzlichen Generationsnachweis.
- PLC-Vertragsnachweise und reale Testfälle gemäß obiger Verifikationsliste.
- Verfügbare Projektgeräte für responsive und Tastaturabnahme.
- Software, lokale PostgreSQL-Integration und Browserprüfung sind umgesetzt. Ohne IoT-Netz wurde keine echte PLC kontaktiert oder ein Anlagenlauf durchgeführt.

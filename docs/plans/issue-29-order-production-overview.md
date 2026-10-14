# Implementierungsplan – Auftrags- und Produktionsübersicht

## Meta

- **State:** Active
- **Stand:** 2026-10-13
- **Spec:** [Issue #29](../specs/issue-29-order-production-overview.md), fachlich vom Benutzer bestätigt.
- **Branch:** `feature/29-order-production-overview`
- **Fortschritt:** Software umgesetzt; Backend-/Browserregression vorhanden. Reale PLC-Vertragsprüfung und Anlagenabnahme stehen aus.
- **Arbeitsweise:** Kleine, überprüfbare Schritte; vor jedem Schritt erklären, was umgesetzt wird und warum. Danach Änderungen, Prüfung und verbleibende Einschränkungen beschreiben.

## Ziel und feste Grenzen

Die bereits vorhandenen Tabs und Seiten für Fertigungs- und Lieferaufträge werden weiterverwendet. Das Dashboard bleibt eine separate, lesende Zusammenfassung. Das Backend liefert dauerhaft gespeicherte Aufträge, Laufzustände und Produktresultate; beide Auftragsarten teilen sich eine einzige Startvergabe mit FIFO-Reihenfolge. Unklare Läufe blockieren neue Starts bis zur Prüfung; Reviews erfassen Laufbewertung und Mengen ohne Pflichtnotiz.

Manuelle Auftragserstellung/Auslösung bleibt bei Issue #30. Die dauerhafte Annahme vorhandener API-Payloads, Datenabfragen und Reviews gehören zu diesem Plan. Bestehende Formulare und UI-Bausteine werden erhalten beziehungsweise angepasst, aber Demo-Statusänderungen dürfen keine realen Ergebnisse erzeugen.

Dieser Plan ersetzt für Issue #29 die alten Annahmen über zwei gleichzeitig laufende Queues. Der historische Juni-Plan ist keine Grundlage für aktuelle Signalnamen oder Abschlussregeln.

## Clean Code und OOP

- Klassen haben eine konkrete Verantwortung. Domänenlogik kennt weder FastAPI noch React noch OPC-UA-Nodes.
- Services erhalten Repository, PLC-Gateway, Konfiguration und Uhr über Konstruktoren. Tests ersetzen diese Abhängigkeiten durch kleine Fakes.
- Schnittstellen nur an tatsächlichen Austauschgrenzen: Persistenz, PLC und Zeit. Keine leeren Basisklassen oder künstlichen Vererbungshierarchien.
- Python-Bezeichner sind englisch und folgen den bestehenden Python-Konventionen. Verantwortungen und öffentliche Verträge werden durch deutsche Docstrings dokumentiert. Die C#-XML-/Namensregeln des Harness werden nicht als C#-Syntax in Python oder TypeScript übertragen; die dort beschriebene Sprachabgrenzung bleibt erhalten.
- Neue Methoden bleiben kurz und nachvollziehbar. Validierung, Zustandsübergänge, Mengenberechnung und Nebenwirkungen werden getrennt geprüft.
- Ein Repository bündelt transaktionale Auftragsdatenzugriffe. Es entscheidet nicht über PLC-Status. Ein PLC-Gateway übersetzt das bestätigte Nodeformat, entscheidet aber nicht über FIFO oder manuelle Mengen.
- Fehler werden fachlich unterschieden: Validierung, Identitätskonflikt, Reviewkonflikt, fehlender Nachweis, Quellenfehler und Persistenzfehler. Erwartete Fehler werden an ihrer zuständigen Grenze behandelt; Hintergrundfehler werden im Lifecycle sichtbar gemacht.
- React bleibt bei funktionalen Komponenten und Hooks. Der OOP-Ansatz liegt vor allem in Backend-Domäne, Services und API-Client; React-Klassen werden nicht künstlich eingeführt.
- Die vorhandene industrielle Gestaltung, semantische Farben, Typografie und Navigation bleiben die Basis. Die bestätigte Projektgestaltung hat Vorrang vor allgemeinen Design-Skill-Vorschlägen für neue Fonts oder dekorative Animationen.

## Geplante Verantwortlichkeiten

Die folgenden Klassen sind im Arbeitsbranch umgesetzt. `OrderWorkerHost` ersetzt den bisherigen Entwurfsnamen `OrderRuntime`; er steuert ausschließlich den Lebenszyklus.

| Klasse | Verantwortung | Ort |
| --- | --- | --- |
| `OrderRun` | Zulässige Laufübergänge, Prüfbedarf und Unterscheidung von Laufende und Produktqualität. | `backend/app/domain/order_run.py` |
| `OrderRepository` | Atomare Annahme, globale Reihenfolge, Laufreservierung, Resultat-Upserts, Reviewversionen und konsistente Abfragen. | `backend/app/repositories/order_repository.py` |
| `OrderAdmissionService` | Vorhandene Payloads normalisieren, Identität/Inhalt prüfen und dauerhafte Annahme veranlassen. | `backend/app/services/order_admission_service.py` |
| `OrderDispatchService` | Ältesten Auftrag reservieren und den vorbereiteten Lauf durch den bestätigten Handshake führen. | `backend/app/services/order_dispatch_service.py` |
| `ProductResultService` | Rückmeldungen zuordnen, eindeutige finale Einheiten erfassen und nachvollziehbare Mengen ableiten. | `backend/app/services/product_result_service.py` |
| `OrderRecoveryService` | Offene Läufe mit PLC-Beobachtungen abgleichen; Beobachtung fortsetzen oder Prüfbedarf setzen. | `backend/app/services/order_recovery_service.py` |
| `RunReviewService` | Reviewmengen und Version prüfen; manuelle Bewertung ohne PLC-Schreibzugriff speichern. | `backend/app/services/run_review_service.py` |
| `OrderQueryService` | Konsistente Lese-DTOs für Auftragsseiten und Dashboard aufbauen. | `backend/app/services/order_query_service.py` |
| `PlcOrderGateway` | Vorhandenen `OpcUaClient` kapseln, beide Slots lesen und dessen Operationen geordnet ausführen. | `backend/app/clients/plc_order_gateway.py` |
| `OrderWorkerHost` | Services zusammensetzen, Task-/Verbindungslebensdauer und Diagnose des einzigen Dispatchers verwalten. | `backend/app/workers/order_worker_host.py` |

`OrderWorkerHost` enthält keine Mengen- oder Fachstatuslogik. Die bisherigen Workerdateien werden gezielt als Kompatibilitätszugang zum gemeinsamen Runtime angepasst; ihre doppelten Dispatchschleifen werden abgelöst. Getrennte Auftragstypen benötigen keinen duplizierten Ablauf: eine kleine Typkonfiguration wählt Slot und `AuftragsArt`.

## Persistenzentwurf

Neue SQLModel-Records werden getrennt von Domänenobjekten und Pydantic-API-Modellen gehalten. Die vorhandene Migration legt nur `machine` und `user` an. Existierende `ProductionOrder`-/`DeliveryOrder`-Klassen und ihre Artikelbeziehungen beweisen daher keine bereits vorhandenen Tabellen.

| Geplanter Record | Gespeicherter Inhalt / Invariante |
| --- | --- |
| `MesOrderRecord` | UUID, Auftragstyp, fachliche String-ID, normalisierter PLC-Eingabeinhalt, Annahmezeit und gemeinsame Annahmesequenz. Unique auf Typ plus fachlicher ID. |
| `OrderRunRecord` | Lauf-UUID, Auftragsreferenz, Laufphase, korrelierter Slot/PLC-Auftragsnummer, letzter belegter Zustand, Start-/Endbeobachtung, Prüfbedarf und Versionsnummer. Kein zusätzlicher Lauf durch wiederholte Annahme. |
| `ProductUnitRecord` | Geplante Einheit eines Laufs, nachgewiesene Einheitenidentität, verfügbare Produktfelder, finales Ergebnis/Fehlercode und Herkunft. Unique auf Lauf plus Queueindex; gelesene Produkt-/Serien-/Sequenzidentität muss dazu passen. |
| `RunReviewRecord` | Laufreferenz, Bewertung, bekannte oder unbekannte Gut-/Fehlmengen, Zeitpunkt und zugrunde liegende Version. Keine Pflichtnotiz. |
| `DispatchStateRecord` | Genau ein globaler Koordinationsdatensatz mit Annahmezähler, reserviertem Lauf und blockierendem Grund. |
| `PlcSourceStateRecord` | Quellenzustand je Slot, letzter erfolgreicher Beobachtungszeitpunkt, Diagnose; Quellenfehler erhalten den letzten Erfolgszeitpunkt. |

Die PLC-nahe Annahme bleibt ohne vorausgesetzte Artikel-Fremdschlüssel möglich. Gemischte Produktqueues werden aus dem bestehenden Payload übernommen; Artikelbezeichnungen werden nur bei belegter Zuordnung ergänzt. Historische Demoaufträge werden nicht als echte Läufe importiert.

### Transaktions- und Ausfallregeln

- Annahme sperrt den Koordinationsdatensatz kurz, vergibt die nächste Sequenz und speichert Auftrag/Lauf atomar. So entspricht die FIFO-Reihenfolge der erfolgreichen dauerhaften Annahme; reine Uhrzeiten oder vorab vergebene IDs reichen nicht.
- Dispatch sperrt denselben Koordinationsdatensatz, prüft globale Sperren und reserviert ausschließlich den ältesten wartenden Auftrag. Die Reservierung wird vor jeder möglichen PLC-Übergabe committed.
- Eine Datenbanktransaktion bleibt nicht während PLC-Wartezeiten offen. `SELECT FOR UPDATE` schützt die kurze Entscheidung; der persistierte reservierte Lauf schützt den Zeitraum nach Commit. Ein abgelaufener Timeout löscht diese Reservierung nicht automatisch. Diese Lock-Abgrenzung stützt sich auf die [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/18/explicit-locking.html).
- FIFO verwendet kein Überspringen eines gesperrten älteren Auftrags. Ein nicht ausführbarer ältester Auftrag bleibt mit sichtbarem Grund stehen.
- Resultate und Laufabschluss werden vor der Abschlussquittierung committed. Scheitert das Speichern, erfolgt keine Quittierung, die Ergebnisse verlieren lassen könnte.
- Repositoryoperationen öffnen und schließen ihre eigene Session am Ausführungsort. Synchrones DB-I/O wird außerhalb des Eventloops ausgeführt; ORM-Sessions werden nicht zwischen Threads/Tasks geteilt. Siehe [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks).
- Ein einzelner PLC-schreibender Runtime wird zusätzlich über eine dedizierte PostgreSQL-Verbindung mit Session-Advisory-Lock gegen gleichzeitig gestartete Runtimeinstanzen geschützt. Das Lock wird beim Shutdown erst nach dem Beenden laufender Gatewayoperationen freigegeben. Die Verbindung wird nicht zwischenzeitlich in den allgemeinen Pool zurückgegeben. Session-Locks enden beim Verbindungsende; deshalb bleibt die dauerhafte Laufreservierung die Grundlage der Wiederaufnahme, wie in der [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/18/explicit-locking.html#ADVISORY-LOCKS) beschrieben.
- Geht die Runtime-/DB-Verbindung verloren, erfolgen keine weiteren Übergaben. Ein bereits gestarteter synchroner PLC-Aufruf kann noch laufen; sein Ergebnis gilt bei fehlendem Nachweis als unklar. Kein automatischer Lock-/Leaseablauf darf daraus einen neuen Start ableiten.

## Geplanter API-Vertrag

Dies sind neue beziehungsweise konkretisierte Verträge für die Umsetzung; die bestehenden POST-Payloads `order_id` und `mes_auftrag` bleiben Eingangsbasis.

| Route | Umsetzung |
| --- | --- |
| `POST /productionorder/`, `POST /deliveryorder/` | Nach Commit `202` mit vorhandenen Annahmefeldern plus dauerhafter Auftrags-/Laufreferenz. Wiederholung desselben Inhalts liefert dieselbe Referenz; anderer Inhalt unter gleicher Typ/ID liefert `409`. Annahme meldet keinen bestätigten Start. |
| `GET /productionorder/`, `GET /deliveryorder/` | Typspezifische paginierte Liste und Bereichssnapshot: aktiver Lauf, wartende Aufträge samt globaler Sequenz, offene Reviews und Quellenmetadaten. |
| `GET /productionorder/{order_id}`, `GET /deliveryorder/{order_id}` | Auftrag und Lauf mit Einheiten/Resultaten; fachliche ID bleibt String. Keine vorausgesetzte numerische Frontend-ID. |
| `GET /orders/overview` | Konsistenter kombinierter Dashboard-/Dispatchsnapshot einschließlich globaler Sperre und offener Reviews. |
| `POST /orders/runs/{run_id}/reviews` | Laufbewertung, nullable Gut-/Fehlmengen, erwartete Laufversion und clientseitige Reviewanforderungs-ID. Speichern ohne Erklärung; Konflikte liefern `409`, ungültige Mengen `422`. Kein PLC-Schreibzugriff. |
| Vorhandene `GET .../queue-status` | Diagnosezugang erhalten; Daten aus gemeinsamem Runtime und dauerhaftem Auftragsspeicher statt unterschiedlicher In-Memory-Queues. |

Statische Routen werden vor variablen ID-Routen registriert. DTOs sind eigene Pydantic-Modelle; Roh-ORM-Objekte und PLC-Nodes werden nicht direkt ausgeliefert. Eine Annahme bei globaler Reviewsperre darf wartend gespeichert werden, löst aber keinen Start aus; der Sperrgrund bleibt sichtbar. Die bestehende Ablehnung bei tatsächlich nicht laufendem Runtime bleibt als `503` erhalten. DB-Ausfälle bestätigen keine Annahme.

Geplante Kernfelder: `order_id`, `order_type`, interne `order_ref`, `run_id`, `plc_order_number`, `accepted_sequence`, `status`, `run_phase`, `planned_quantity`, `processed_quantity`, `good_quantity`, `error_quantity`, `result_complete`, `quantity_source`, `review_required`, `version` und `source`. Quellenfelder umfassen `connection_status`, `last_success_at`, `freshness` und lesbare Diagnose. Unbekannte Werte sind `null`; UTC-Beobachtungszeitpunkte bleiben von tatsächlichen PLC-Zeitpunkten unterscheidbar.

`status` erhält eine definierte Abbildung zum vorhandenen Vokabular; `review_required` wird ausdrücklich unterstützt. `run_phase` unterscheidet Vorbereitung, unbestätigten Start, Lauf, erkanntes Ende und Reset. Ein erkanntes Ende kann vor bestätigtem Idle sichtbar sein, während die globale Startvergabe noch blockiert ist.

Einheiten enthalten nur verfügbare Produktkennungen/-texte, Serien-/Sequenznummern, finalen Status und Fehlercode. Neue Ergebniscodes werden erst aus verifizierten PLC-Beispielen abgeleitet. Das Backend kann eine Startbereitschaft beziehungsweise Reviewsperre darstellen, ohne fehlende Werte als Null zu behandeln.

## Aktualisierung und Konfiguration

Als technische Startwerte dieses Plans werden Backend-Beobachtung alle **0,5 s**, UI-Aktualisierung alle **2 s** und Veraltungsgrenze **10 s** vorgesehen. Der Backendwert entspricht dem bestehenden Handshakeintervall; die übrigen Werte sind neue, zu prüfende Startwerte und keine bereits vorhandenen Settings.

Die Werte werden zentral konfiguriert, auf positive Intervalle und Veraltungsgrenze oberhalb des Beobachtungsintervalls validiert und vor Livebetrieb auf PLC-Last geprüft. Konkrete neue Settingsnamen werden bei Einführung dokumentiert. Der API-Snapshot liefert die effektiven Aktualitätsregeln; die UI verteilt keine unabhängigen Schwellwerte auf mehrere Komponenten. Damit bleibt die spätere Settingsoberfläche anschlussfähig.

Der Browser fragt gespeicherte Snapshots ab, nicht direkt die PLC. Ein GET löst keinen PLC-Schreibzugriff aus. Bei laufender Abfrage startet kein überlappender UI-Request; veraltete Antworten überschreiben keine neueren Daten. Nach einem Review wird unmittelbar neu geladen. Ein ausgefallener Read erneuert `last_success_at` nicht; Quelle und zuletzt bekannter Lauf bleiben getrennt.

## Umsetzungsschritte

### 1. Ausgangsstand und PLC-Vertrag sichern

**Was umgesetzt wird:** Ein nachvollziehbarer Ausgangsstand und die Grundlage für echte Produktresultate, bevor unbekannte Nodes als Ergebnisquelle verwendet werden.

**Betroffene Dateien:** bestehende Tests in `backend/tests/`, `docs/opc-ua-integration.md`; neue Verifikationsnachweise unter `docs/` erst bei tatsächlicher Erhebung benennen.

- [x] Bestehende Client-, Modell-, Handshake-, Diagnose- und Startuptests einmal als Baseline ausführen; neue Fehler eindeutig von bestehenden Befunden trennen.
- [ ] Nodes/Datentypen/Identitäten beider Slots, finale Produktstatuscodes und den Lebenszyklus der Resultate vor/nach Reset prüfen und protokollieren.
- [ ] Nachweisen, wie ein kurzer Lauf, wiederverwendete Nummern/Slots, leere Einträge und HMI-/Fremdaufträge erkannt werden.
- [x] Für noch nicht geprüfte Signale keine Produktstatuszuordnung aktivieren. Persistenz/API/UI können mit ausdrücklich gekennzeichneten Vertragsbeispielen entwickelt werden; Live-Abnahme wartet auf den Nachweis.

**Prüfung:** AC-08, AC-10, AC-13, AC-20, AC-21, AC-24, AC-39. Keine unkontrollierten Start-/Resetbefehle zur bloßen Nodeanalyse.

### 2. Laufmodell, DTOs und Grenzen definieren

**Was umgesetzt wird:** Kleine Domänenobjekte für Laufübergänge und ein gemeinsamer Datenvertrag für beide Auftragsseiten.

**Geplante Dateien:** `backend/app/domain/order_run.py`, neue Pydantic-DTOs unter `backend/app/models/`; `frontend/lib/types.ts` anpassen.

- [x] Übergänge für wartend, vorbereitet, Start unbestätigt, laufend, Ende erkannt, Reset ausstehend, abgeschlossen/unterbrochen und prüfbedürftig modellieren.
- [x] Reviewbedarf, Quellenfehler und Produktqualität getrennt vom Laufende halten.
- [x] Neue DTOs mit String-Auftrag-ID, Typ, Laufreferenz, Mengenherkunft, nullable Messwerten und Versionsnummer definieren.
- [x] Bestehende PLC-Eingabemodelle weiterverwenden; Konvertierung zwischen API-, Domänen- und Datenbankobjekten an klarer Grenze implementieren.

**Prüfung:** Zustands-/Validierungstests einschließlich Annahme ohne Startnachweis und Laufende mit fehlerhaften oder fehlenden Produkteinheiten. AC-06 bis AC-13, AC-28, AC-29, AC-36.

### 3. Dauerhafte Annahme und Migration implementieren

**Was umgesetzt wird:** PostgreSQL als verlässliche Quelle für angenommene Aufträge, Wartepositionen und offene Läufe.

**Betroffene/geplante Dateien:** neue Records unter `backend/app/models/`, `backend/app/models/__init__.py`, `backend/alembic/env.py`, neue Alembicrevision unter `backend/alembic/versions/`, `OrderRepository`, `OrderAdmissionService`, beide vorhandenen Auftragsrouter.

- [x] Neue Tabellen gezielt migrieren; bestehende `machine`-/`user`-Daten erhalten. Fehlende alte Artikeltabellen nicht ungeprüft voraussetzen oder bestehende Historie umdeuten.
- [x] Neue Modelle für Alembic registrieren und die erzeugte Migration gegen tatsächliche Metadaten prüfen; keine fachfremden Autogenerate-Änderungen übernehmen.
- [x] Payloads einschließlich Defaults/Aliases normalisieren; Typ/ID und Inhalt unter Transaktion vergleichen.
- [x] Globale Annahmesequenz atomar vergeben, geplante Einheiten aus `Produktqueue` speichern und `202` erst nach Commit zurückgeben.
- [x] Wiederholte und gleichzeitig eintreffende Annahmen ohne zweiten Lauf behandeln; Inhaltskonflikte explizit ablehnen.

**Prüfung:** PostgreSQL-Integration für neue und bestehende Datenbank, Rollback vor Annahmebestätigung, gleichzeitige Annahmen, Doppelklick/Retry und Wiederholung nach Prozessneustart. AC-14, AC-15, AC-18, AC-19.

### 4. Gemeinsame FIFO-Startvergabe einführen

**Was umgesetzt wird:** Eine einzige Stelle entscheidet, welcher Produktions- oder Lieferauftrag starten darf.

**Betroffene/geplante Dateien:** `OrderDispatchService`, `OrderWorkerHost`, `OrderRepository`, bestehende `production_queue.py`, `delivery_queue.py`, `main.py` und `diagnostics.py`.

- [x] Alte In-Memory-Queues als Wahrheitsquelle ablösen; dauerhafte Aufträge werden aus PostgreSQL ausgewählt. Eine lokale Benachrichtigung darf nur aufwecken, nicht Auftragsdaten besitzen.
- [x] Kurzzeitig gesperrten Koordinationsdatensatz für Reservierung nutzen; globale Reviewsperre und ältesten wartenden Auftrag prüfen.
- [x] Lauf-/Übergabezustand vor PLC-Schreiben speichern. Reservierung über Erfolg, Fehler, Timeout und Shutdown hinweg nachvollziehbar halten.
- [x] Beide Auftragstypen durch den gleichen Dispatchablauf führen; Slot/`AuftragsArt` sind Typkonfiguration.
- [x] Runtimeinstanzen gegen paralleles Schreiben schützen und alle bisherigen Startwege auf den gemeinsamen Ablauf verweisen.

**Prüfung:** Zwei konkurrierende Vergeber, gemischte Produktions-/Lieferreihenfolge, Prioritätsfeld ohne Vorziehen, nicht ausführbarer ältester Auftrag und persistierte Reservierung nach Abbruch. AC-15 bis AC-17, AC-20, AC-22 bis AC-24.

### 5. PLC-Gateway und Resultatsicherung ergänzen

**Was umgesetzt wird:** Aus bestätigten PLC-Beobachtungen werden eindeutige Produktresultate und Mengen, die vor dem Reset gespeichert sind.

**Betroffene/geplante Dateien:** vorhandener `OpcUaClient`, `plc_handshake.py`, `PlcOrderGateway`, `ProductResultService`, `OrderRepository`.

- [x] Vorhandene Nodeauflösung, beide bestätigten Arraylayouts, Aliasnamen, Wertvalidierung und Start-als-letztes-Schreiben wiederverwenden.
- [x] Zusammenhängende Leseoperationen als Snapshot mit Auftragsidentität vor/nach dem Lesen absichern; bei Identitätswechsel keinen gemischten Snapshot übernehmen.
- [x] Gatewayzugriffe geordnet außerhalb des Eventloops ausführen. Ein exklusiver I/O-Ausführungsweg verhindert kollidierendes Lesen/Schreiben auf derselben Clientverbindung.
- [x] Finale Resultate nach verifiziertem Vertrag upserten, nicht bei jedem Poll incrementieren. Fehlende/alte/fremde Einheiten bleiben ausgeschlossen beziehungsweise unbekannt.
- [x] Start/Ende einmalig erfassen; Endresultate und Abschlussbeobachtung committen, erst danach quittieren und Idle bestätigen.
- [x] Den bisherigen blinden Abschlussreset im Bereitschaftscheck ablösen: nach Neustart erst Korrelation und Resultatsicherung, dann autorisierte Quittierung.

**Prüfung:** Bestehende Client-/Handshaketests erweitern beziehungsweise verhaltensgerecht anpassen; Timeout, kurzer Lauf, doppelte Resultate, wechselnde Auftrag-ID und fehlgeschlagener Resultatcommit prüfen. AC-07 bis AC-13, AC-21, AC-33, AC-39.

### 6. Wiederaufnahme und Shutdown absichern

**Was umgesetzt wird:** Der Backendneustart rekonstruiert offene Läufe und entscheidet zwischen Weiterbeobachten, belegtem Abschluss und Reviewbedarf.

**Betroffene/geplante Dateien:** `OrderRecoveryService`, `OrderWorkerHost`, `main.py`, Gateway-/Repositorygrenzen, `diagnostics.py`.

- [x] Beim Startup neue Starts sperren, offene Reservierungen laden und beide Slots abgleichen.
- [x] Aktive korrelierte Läufe ohne erneuten Start weiterbeobachten; belegte Enden resultatsicher abschließen; Idle ohne Nachweis oder fremde Identität auf Prüfung setzen.
- [x] Bei Störung zuletzt belegte Daten und Sperrgrund erhalten; kein verlorener Auftrag durch `task_done()` oder Client-Reconnect.
- [x] Beim Shutdown keine neue Auswahl beginnen; laufende I/O-Operationen begrenzt abwarten und unklare Ergebnisse dauerhaft offen lassen.
- [x] Nicht annehmen, dass das Canceln einer Coroutine den bereits laufenden synchronen PLC-Aufruf beendet. Erst nach sicherem Abschluss der I/O-Operation den Ausführungsweg beziehungsweise Runtime-Lock freigeben. Siehe [Python-Threadausführung](https://docs.python.org/3.14/library/asyncio-task.html#asyncio.to_thread) und [Future.cancel](https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Future.cancel).

**Prüfung:** Prozessneustarts vor Übergabe, nach Startschreiben, bei aktivem Lauf, nach Resultatcommit vor Reset und nach Reset vor Idlebestätigung; zusätzlich DB-/PLC-Verlust während eines laufenden I/O-Aufrufs. AC-20 bis AC-26, AC-33, AC-39.

### 7. Review und lesende API fertigstellen

**Was umgesetzt wird:** Sichere Operatorbewertung ohne Maschinensteuerung und eine gemeinsame API für beide Seiten und das Dashboard.

**Betroffene/geplante Dateien:** `RunReviewService`, `OrderQueryService`, Auftragsrouter, geplanter `backend/app/routers/orders_router.py`, DTOs und `main.py`.

- [x] Review gegen aktuelle Laufversion prüfen, Bewertung/Mengen speichern und Anfrage-ID für wiederholte identische Speicherung verwenden.
- [x] Backendgrenzen für nicht negative Ganzzahlen, Sollmenge und schon belegte Mengen durchsetzen; keine erforderliche Erklärung hinzufügen.
- [x] Manuell bekannte Gesamtmengen als Gesamtbewertung speichern, nicht auf PLC-Einheiten addieren. Fehlende Einzelresultate nicht erfinden; spätere widersprüchliche PLC-Werte erzeugen sichtbaren Prüfbedarf.
- [x] Weiterhin unbekannt lässt die globale Reviewsperre bestehen. Beendet/unterbrochen löst nur den passenden Prüfbedarf; neue Starts benötigen außerdem aktuelle PLC-Bereitschaft.
- [x] List-/Detailsnapshots mit konsistenter Version und unabhängigen Quelleninformationen erstellen; Übersichtsaggregationen im Backend berechnen.
- [x] HTTP-Verhalten für `404`, `409`, `422`, `503` sowie statische/variable Routen prüfen. GET und Review besitzen keinen PLC-Schreibpfad.

**Prüfung:** API-/Servicetests für Review ohne Notiz, nullable Mengen, Mengenwidersprüche, doppelte/konkurrierende Reviews und Dashboardabfrage ohne PLC-Zugriff. AC-23 bis AC-37, AC-40.

### 8. Vorhandene Fertigungs- und Lieferseiten anbinden

**Was umgesetzt wird:** Die vorhandenen Tabs und `OrdersSection` erhalten echte Daten und passende Unteransichten; keine zweite parallele Auftragsoberfläche.

**Betroffene/geplante Dateien:** `frontend/lib/api.ts`, `frontend/lib/types.ts`, vorhandene Auftragsseiten, `orders-section.tsx`, `status-badge.tsx`, geplante Unterkomponenten und ein Aktualisierungshook unter `frontend/components/` beziehungsweise `frontend/hooks/`.

- [x] Bestehende Tabellen, Suche, Filter und gemeinsame Darstellung wiederverwenden; String-IDs und fehlende Artikelzuordnung korrekt anzeigen.
- [x] `OrderApiClient` als kleine Transportklasse mit injizierbarer Basisadresse/Fetchfunktion einführen; Komponenten enthalten keine URL-/HTTP-Fehlerlogik oder PLC-Abbildung.
- [x] Echte typspezifische Listen/Details und Reviewrequests an den neuen Vertrag anbinden. Demo-Modus ausdrücklich kennzeichnen; kein automatischer Mock-Fallback.
- [x] Aktiver Lauf, wartende Aufträge mit globaler Position und Produkteinheiten als getrennte Abschnitte darstellen. Unbekannt, unvollständig und tatsächlich null Mengen unterscheiden.
- [x] Reviewdialog aus vorhandenen Dialog-/Input-/Selectbausteinen zusammensetzen. Nur fehlende erforderliche shadcn-Primitives gezielt ergänzen, vorhandene nicht ersetzen; Registry/CLI und deren Dokumentation vor tatsächlichem Hinzufügen prüfen.
- [x] Fokus, Field-Komposition, `aria-invalid`, Statusbeschriftungen, Formularwerte bei Fehlern und Schutz vor konkurrierendem Speichern umsetzen.
- [x] Bestehende manuelle Startformulare für Issue #30 weiter nutzbar vorbereiten; in der Liveübersicht keine fiktiven Create/Edit/Delete-Erfolge oder freie Laufstatusmutation anbieten.

**Prüfung:** AC-01, AC-02, AC-05 bis AC-08, AC-25 bis AC-38. Browserfälle für beide Tabs, gemischte Produkte, fehlende Bezeichnungen, ungelöste Reviews nach Reload und fehlerhafte Backendantworten.

### 9. Dashboard und gemeinsame Aktualität anbinden

**Was umgesetzt wird:** Das bestehende Dashboard zeigt dieselben bestätigten Daten zusammengefasst und verlinkt erforderliche Prüfungen.

**Betroffene Dateien:** `frontend/app/dashboard/page.tsx`, API-Client/Typen, bestehende StatCard-/Statusbausteine und Aktualisierungshook; `OrderQueryService`.

- [x] Dashboard von Demo-/Maschinenlistenabhängigkeiten auf den kombinierten Snapshot umstellen. Vorhandene Maschinenanzeige nur bei tatsächlich belegten Daten weiterführen; keine neuen Maschinenendpunkte allein für dekorative Kennzahlen.
- [x] Produktions-/Lieferzusammenfassungen und kombinierte Gesamtwerte aus den Backendwerten anzeigen; Typ neben gleichen IDs erhalten.
- [x] Globalen Sperrhinweis mit Links zu den betroffenen Läufen anzeigen. Das Dashboard enthält keine Revieweingabe oder mutationauslösende Buttons.
- [x] Quellenzustand, letzte Beobachtung, fehlende Erstwerte und Veraltungsgrenze mit gemeinsamen Regeln darstellen; Polling beim Unmount abbrechen und stale Antworten vermeiden.
- [x] Vorhandene geplante Stückzahlsummen nur mit klarer Bedeutung und echten Eingangsdaten erhalten; Sollmenge nicht als tatsächliches Produktionsergebnis ausgeben.

**Prüfung:** AC-03, AC-04, AC-25, AC-26, AC-31, AC-33 bis AC-38; ausfallende Teilquelle beeinträchtigt nicht die bekannten Werte des anderen Bereichs.

### 10. Integration, Anlagenabnahme und Harness-Abgleich

**Was umgesetzt wird:** Der gesamte Ablauf wird nachgewiesen und seine Dokumentation mit dem erreichten Verhalten synchronisiert.

**Betroffene Dateien:** tatsächliche Tests, Spec, Harness-Testkatalog/-UI-Guide, `docs/opc-ua-integration.md` und neue Abnahmeprotokolle erst nach tatsächlicher Durchführung.

- [ ] Alle 40 Akzeptanzkriterien gegen Tests beziehungsweise dokumentierte Browser-/Anlagennachweise prüfen.
- [x] PostgreSQL-Integration mit unabhängigen Sessions/Prozessen durchführen. SQLite ersetzt weder PostgreSQL-Lock- noch Neustartnachweise.
- [ ] Produktions- und Lieferauftrag real nacheinander vom bestehenden API-Eingang bis zu den zugeordneten Resultaten und sichtbaren Mengen prüfen.
- [ ] Ausfall/Neustart, globales Reviewblocking, mengenbasierte Prüfung ohne Notiz, FIFO und erneutes Lesen real beziehungsweise gezielt im Simulator prüfen.
- [x] Tatsächliche Methoden und Erkenntnisse in der Spec dokumentieren; Testnamen/-dateien in den Harness-Katalog übernehmen und States erst nach erfolgreicher Ausführung aktualisieren.
- [ ] `Implemented` erst bei vollständiger Übereinstimmung und erforderlicher Abnahme setzen. Fehlende Anlagennachweise bleiben benannt; kein vorweggenommenes Erfolgsergebnis.

**Prüfung:** Vollständige AC-01 bis AC-40; keine geplante Prüfung wird als bereits bestanden dargestellt.

## Verifikation und Werkzeuge

Die Implementierung wird mit folgenden Befehlen geprüft:

```bash
# Arbeitsverzeichnis backend
python3 -m pytest -q
alembic upgrade head
```

Migrationen werden zunächst auf einer isolierten Testdatenbank ausgeführt. Die Lauf-/Locktests benötigen echten PostgreSQL-Betrieb. Testkonfiguration enthält keine produktiven Zugangsdaten und darf keine echte PLC ansprechen. Ein Backend-Lint-/Formatbefehl ist derzeit im Repository nicht definiert; keine C#-Beispielbefehle als echte Pythonchecks übernehmen.

```bash
# Arbeitsverzeichnis frontend
npm run lint -- <tatsächlich-geänderte-ts-und-tsx-Dateien>
npm run build
```

Der Dateiplatzhalter wird bei Ausführung durch die tatsächlichen Pfade ersetzt. Für wiederholbare kritische UI-Flows ist ein kleiner Playwright-Testaufbau als reine Entwicklungsabhängigkeit vorgesehen; `npm run test:e2e` führt `frontend/tests/orders.spec.ts` und `proxy.spec.ts` auf Desktop und schmalem Layout aus. Ein Build ersetzt keinen Browser-/Tastaturnachweis.

## Reihenfolge und Abschluss jeder Etappe

1 → 2 → 3 → 4 bildet die Grundlage. Produktfeedback und Recovery folgen mit 5 → 6; die lesende und Review-API mit 7; bestehende Tabs und Dashboard mit 8 → 9; Abnahme und Dokumentation mit 10. Verifizierte Vertragsbeispiele erlauben UI-Arbeit vor dem Anlagenabschluss, aber keinen behaupteten Live-Nachweis.

Jeder Schritt endet mit einer verständlichen Erklärung: **Was wurde geändert? Welche Verantwortung hat der neue oder angepasste Code? Welches Nutzerverhalten ist jetzt möglich? Wie wurde es geprüft? Was bleibt offen?** Erst danach wird die entsprechende Checkbox abgeschlossen. Commit, Push oder weitere Branchaktionen erfolgen nur auf gesonderten Auftrag.

## Beziehungen und Pflege

- **Voraussetzung:** bestätigte [Feature-Spec](../specs/issue-29-order-production-overview.md).
- **Tests:** [Harness-Testkatalog](../../Harness/harness/_unittest.md).
- **UI:** [Harness UI/UX](../../Harness/harness/_uiux.md), `frontend/components.json`, lokale Skills `frontend-design` und `shadcn`.
- **Bestehende Anbindung:** [OPC-UA-Stand](../opc-ua-integration.md).
- **Aktualisierung:** Beim Start und Abschluss jeder Etappe, nach PLC-Vertragsnachweisen und bei notwendigen Plananpassungen.
- **Offene externe Nachweise:** tatsächliche Produktsignale/-identitäten, Datenlebenszyklus bei Reset, Anlagenbereitschaft und verfügbare Projektgeräte.

## Erreichte Umsetzung und offene Abnahme

- Migration `7a92c04e31bf` ergänzt sechs Auftragstabellen; frisches Upgrade und Upgrade mit bestehenden Maschinen-/Benutzerdaten sind isoliert geprüft.
- Gemeinsame Reservierung und Session-Advisory-Lock schützen beide Auftragstypen; `start_pending` ist vor dem PLC-Schreiben committed.
- Endresultate werden vor Reset gesichert. Reset löscht nur MES-Produktinput, prüft Readback und setzt Anzahl vor Kommando null. Teilreset verwendet bereits gesicherte Fakten.
- Review hat keinen Gateway; eine korrelierte PLC-Abschlussmeldung gilt als erfolgreicher Auftrag und setzt fehlende Einzelresultate auf erfolgreich. Ist die Steuerung nach dem gespeicherten Abschluss bereits auf Idle zurückgesetzt, wird eine veraltete Review-Sperre beim Abgleich aufgehoben.
- Gemeinsame UI-Komponenten `OrderList`, `WaitingOrders`, `RunSummary`, `RunReviewDialog`, `OrderPageFeedback` sowie der Pollinghook sind an die reale API angebunden.
- Browserprüfungen und visueller Vergleich sind erfolgt. Reale Codes, Produktstatusfelder, Identitäten, Reset-Lebenszyklus und Anlagenbereitschaft sind noch extern zu bestätigen.
- Produktstatuscodes werden nur mit bestätigter Zuordnung ausgewertet; ohne Zuordnung gilt ein korrelierter Endstatus als erfolgreicher Auftrag, und fehlende Einzelwerte werden als erfolgreich angenommen. Ein realer Simulationslauf wurde am 2026-10-14 beendet und manuell mit 2/2 erfolgreich bewertet; die automatische Abschlussregel ist danach entsprechend angepasst. Weitere Anlagenabnahmen bleiben offen.

**Letzter lokaler Nachweis:** 130 Backendtests und 22 Browserprüfungen bestanden; Build, TypeScript und ESLint erfolgreich. Tatsächliche Testzuordnung siehe Harness-Testkatalog.

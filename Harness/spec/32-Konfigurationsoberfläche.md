# Konfigurationsoberfläche

## Meta

- **State:** Implemented
- **Art:** Feature (adaptiert auf das Bugfix-Spec-Format aus `harness/_requirements.md`, da das Harness kein eigenes Feature-Template vorsieht)
- **Quelle:** GitHub Issue #32 – „Konfigurationsoberfläche" (extern; kein vorgelagertes Harness-Idea-Dokument unter `harness/ideas/` angelegt, siehe „Abweichung vom Harness-Ablauf" unter Offene Punkte)

## User Story

Als MES-Administrator möchte ich die OPC-UA-Zielnodes für Produktions- und Lieferaufträge sowie das Abfrageintervall über eine gemeinsame Oberfläche einsehen und ändern können, damit Anpassungen an der Anlagenanbindung ohne Codeänderung und Neudeployment möglich sind, ohne laufende Aufträge zu gefährden.

## Entscheidungen

Folgende offene Punkte wurden geklärt, um die Spec umsetzungsreif zu machen:

- **Zielnodes:** Die bestehenden, im Code hartcodierten Browse-Namen werden als editierbare Default-Werte in die Settings übernommen (siehe „Einstellungsfelder"). Die endgültige Bestätigung dieser Werte durch die Steuerungsgruppe bleibt Teil des Arbeitspakets Person 3 und ist unter „Offene Punkte" vermerkt.
- **Intervall-Grenzen:** Es wird ein vorläufiger Grenzwertbereich von 100 ms bis 10.000 ms festgelegt (siehe „Einstellungsfelder"). Die endgültige Bestätigung durch die Steuerungsgruppe bleibt unter „Offene Punkte" vermerkt.
- **Zugriffsmodell:** Die Konfigurationsoberfläche bleibt vorerst ungeschützt, wie der Rest der Anwendung. Diese Spec führt keinen Zugriffsschutz ein; die im Issue gestellte Frage nach der Abgrenzung im „vorhandenen Zugangsmodell" entfällt, da aktuell kein Zugangsmodell existiert.
- **Harness-Ablauf:** Die Abweichung vom Standardablauf (direkte Spec-Erstellung ohne vorgelagertes Idea-Dokument, Bugfix-Format auf dieses Feature adaptiert) wurde bestätigt und bleibt so bestehen.

## Description

Die MES-Einstellungen (OPC-UA-Zielnodes für Produktions- und Lieferaufträge, Abfrageintervall mit eindeutiger Einheit) werden zentral über eine Oberfläche verwaltet. Das Backend validiert Eingaben, persistiert bestätigte Einstellungen in PostgreSQL und lädt sie nach einem Neustart wieder. Eine Änderung der Zielnodes während eines aktiven Auftrags darf diesen nicht unbemerkt umleiten; sie wird zurückgestellt oder abgelehnt. Lade-, Speicher- und Übernahmezustand sind in der Oberfläche erkennbar.

## Ist-Verhalten

- Es existiert kein Settings-Modell, keine Settings-Tabelle und kein Settings-Router im Backend (`backend/app/models/`, `backend/app/routers/`).
- Die OPC-UA-Zielnodes sind als Browse-Name-Konstanten im Code hinterlegt, nicht konfigurierbar:
  - `find_db_mes_schnittstelle` sucht den Knoten `"DB_MES_Schnittstelle"` (`backend/app/clients/opc_ua_client.py:104-105`).
  - Der Produktionsauftrags-Einstiegsknoten `"MESAuftragProduktion"` wird in `backend/app/workers/production_queue.py:160` gesucht.
  - Der Lieferauftrags-Einstiegsknoten `"MESAuftragKommissionieren"` wird in `backend/app/workers/delivery_queue.py:160` gesucht (inkl. Alias-Behandlung einer Schreibweise `"MESAuftragKommisionieren"` in `opc_ua_client.py:18-20`).
  - Weitere strukturelle Kindknoten (`"Kopf"`, `"Inhalt"`, `"Feedback"`, `"Auftragssteuerung_MES"`, `"StatusMES"`/`"Status_MES"`, `"Produktqueue[{index}]"`) sind ebenfalls als Konstanten in `opc_ua_client.py` hinterlegt.
  - Konfigurierbar ist ausschließlich die Verbindungs-URL über die Umgebungsvariable `OPC_UA_URL` (`backend/app/workers/production_queue.py:146`, `backend/app/workers/delivery_queue.py:146`, `backend/.env.example`).
- Das Abfrageintervall des PLC-Handshakes ist als Konstante `POLL_INTERVAL_S = 0.5` (Sekunden) fest codiert (`backend/app/workers/plc_handshake.py:9`) und wird in den Warteschleifen `wait_for_plc_started`/`wait_for_plc_done` verwendet (`plc_handshake.py:41`, `:65`).
- Eine Änderung eines Zielnodes oder des Intervalls erfordert aktuell eine Codeänderung und ein Neudeployment; es gibt keine Validierung, keine Persistenz und keinen Lade-/Speicher-/Übernahmezustand in der Oberfläche dafür.
- Es existiert kein Zugriffs- oder Rollenmodell im Backend oder Frontend: `User`/`UserBase` enthält ausschließlich `id` und `email` (`backend/app/models/user.py`), keine Rolle, keine Berechtigung; es gibt keine Auth-Middleware und keine `Depends(get_current_user)`-artige Absicherung in den bestehenden Routern. Diese Spec führt daher bewusst keinen Zugriffsschutz ein (siehe „Entscheidungen").
- `ProductionOrder`/`DeliveryOrder` (`backend/app/models/production_order.py`, `backend/app/models/delivery_order.py`) besitzen kein Feld für einen Zielnode-Bezug; der tatsächliche OPC-UA-Auftragsfluss läuft über ein separates `MESAuftrag`-Payload-Objekt durch eine In-Memory-Queue, nicht über diese DB-Tabellen.

## Soll-Verhalten

- Nutzer der MES-Oberfläche können die OPC-UA-Zielnodes für Produktions- und Lieferaufträge sowie das Abfrageintervall (mit eindeutiger Einheit) einsehen und ändern; die Oberfläche bleibt dabei wie der Rest der Anwendung ohne zusätzlichen Zugriffsschutz.
- Eingaben werden serverseitig validiert, bei Gültigkeit vollständig in PostgreSQL persistiert und nach einem Backend-Neustart unverändert wieder geladen.
- Das Backend verwendet für nachfolgende OPC-UA-Zugriffe ausschließlich die zuletzt bestätigten, gültigen Einstellungen.
- Ungültige Eingaben werden vollständig abgelehnt, ohne eine Teiländerung an den gespeicherten Werten vorzunehmen; die Ablehnung wird verständlich am betroffenen Feld bzw. als Meldung in der Oberfläche angezeigt.
- Eine Änderung eines Zielnodes während eines aktiven Auftrags leitet diesen nicht unbemerkt um: Die Änderung wird bis zu einem sicheren Zeitpunkt zurückgestellt oder eindeutig zurückgewiesen.
- Ladevorgang, Speichervorgang und erfolgreiche Übernahme der Einstellungen sind in der Oberfläche jeweils eigenständig erkennbar.

## Reproduktion

1. Ausgangszustand: Die Steuerungsgruppe möchte ein geändertes Zielnode-Schema oder ein anderes Abfrageintervall an der Anlage nutzen.
2. Aktion: Es gibt keine Oberfläche oder Backend-Einstellung dafür; eine Anpassung erfordert eine Änderung der Konstanten in `opc_ua_client.py`/`plc_handshake.py` durch Entwickler sowie ein Neudeployment des Backends.
3. Beobachtbares Ergebnis: Eine fachliche Anpassung der Anlagenanbindung ist ohne Code-Release nicht möglich; es existieren keine Validierung, keine Persistenz, keine Wiederherstellung nach Neustart und kein erkennbarer Lade-/Speicherzustand.

## Akzeptanzkriterien

- Gültige Zielnodes und ein gültiges Abfrageintervall lassen sich speichern und werden nach einem Neustart des Backends unverändert angezeigt.
- Das Backend verwendet nach einer bestätigten Änderung ausschließlich die neuen Werte für nachfolgende OPC-UA-Zugriffe.
- Eine ungültige Eingabe (leerer Zielnode oder Intervall außerhalb von 100–10.000 ms) wird vollständig abgelehnt, ohne dass bereits gespeicherte Werte verändert werden.
- Die Fehlermeldung einer ungültigen Eingabe ist dem betroffenen Feld zugeordnet oder als Meldung in der Oberfläche sichtbar.
- Eine Änderung eines Zielnodes während eines aktiven Auftrags wird zurückgestellt oder abgelehnt; der aktive Auftrag verwendet bis zu einem sicheren Zeitpunkt weiterhin den zuvor bestätigten Zielnode.
- Ladevorgang, Speichervorgang und erfolgreiche Übernahme der Einstellungen sind in der Oberfläche jeweils eigenständig erkennbar.

## Einstellungsfelder (Default-Werte)

Die bestehenden, im Code hartcodierten Browse-Namen werden als editierbare Default-Werte in die Settings übernommen. `DB_MES_Schnittstelle` bleibt als fester Basisknoten unverändert und ist nicht Teil der editierbaren Einstellungen (nicht Gegenstand des Issues).

| Feld | Bedeutung | Default-Wert | Grenzen |
|---|---|---|---|
| `opcua_node_production_order` | Ziel-Browse-Name für Produktionsaufträge unterhalb von `DB_MES_Schnittstelle` (ersetzt die Konstante `"MESAuftragProduktion"` in `production_queue.py:160`) | `"MESAuftragProduktion"` | nicht leer; finale Bestätigung durch Steuerungsgruppe ausstehend |
| `opcua_node_delivery_order` | Ziel-Browse-Name für Lieferaufträge unterhalb von `DB_MES_Schnittstelle` (ersetzt die Konstante `"MESAuftragKommissionieren"` in `delivery_queue.py:160`) | `"MESAuftragKommissionieren"` | nicht leer; finale Bestätigung durch Steuerungsgruppe ausstehend |
| `polling_interval_ms` | Abfrageintervall des PLC-Handshakes, Einheit Millisekunden (ersetzt die Konstante `POLL_INTERVAL_S = 0.5` in `plc_handshake.py:9`) | `500` | vorläufig 100–10.000; finale Grenzen durch Steuerungsgruppe ausstehend |

## Arbeitspakete

Aus dem Issue übernommene Aufteilung für drei Personen; die konkrete Codeaufteilung kann das Team innerhalb des Issues abstimmen.

- **Person 1 – Oberfläche:** Formular für Nodes und Intervalle, Laden/Speichern und verständliche Fehlermeldungen.
- **Person 2 – Backend:** Settings-API, serverseitige Validierung, PostgreSQL-Persistenz und sichere Aktivierung (keine unbemerkte Umleitung aktiver Aufträge).
- **Person 3 – Anbindung und Prüfung:** Node-/Intervallangaben mit der Steuerungsgruppe klären und Änderungen am laufenden Testsystem prüfen.

Empfohlener Start: Person 2 und 3 stimmen zuerst die benötigten Felder und Beispielwerte ab, damit Person 1 mit Beispieldaten entwickeln kann, während Backend und reale Anbindung entstehen.

## Begleitend behobene Blocker

Während der Umsetzung wurden drei vom Feature unabhängige, aber blockierende Defekte gefunden und auf ausdrücklichen Wunsch mitbehoben, da sie das Backend am Start hinderten bzw. meine eigene Änderung ausgelöst/benötigt hat:

- `backend/app/main.py` importierte `sites_router`, der nie existierte (`backend/app/services/sites_services.py` ist leer) – das Backend konnte dadurch gar nicht starten. Import und `include_router`-Aufruf entfernt.
- `backend/app/models/__init__.py` importierte nur `Machine`/`User`; `Article`, `ProductionOrder`, `DeliveryOrder`, `Storage` fehlten. Das blieb unbemerkt, solange nichts beim Start eine SQLAlchemy-Mapper-Konfiguration auslöste. Der neue Startup-Settings-Load tut das, und deckte dadurch einen `InvalidRequestError` für `Storage.article → "Article"` auf. Fehlende Imports ergänzt.
- `backend/alembic.ini` hatte kein `prepend_sys_path = .`; `alembic revision`/`upgrade` scheiterte mit `ModuleNotFoundError: No module named 'app'`, da das CWD nicht auf `sys.path` lag. Ergänzt.

## Angepasste Methoden

### `SettingsBase._node_not_empty` / `SettingsBase._interval_within_bounds`

- **Datei:** `backend/app/models/settings.py`
- **Typ:** `SettingsBase` (neu)
- **Aufgabe:** Validiert `opcua_node_production_order`/`opcua_node_delivery_order` (nicht leer, getrimmt) und `polling_interval_ms` (100–10.000) beim Parsen des Request-Bodys, bevor Endpoint-Code läuft.
- **Änderung:** Neu erstellt.
- **Erkenntnis:** Pydantic-Feldvalidierung auf dem Base-Modell macht ungültige PUT-Bodies bereits vor dem Endpoint ungültig (422) und verhindert dadurch jede Teiländerung an der DB-Zeile, ohne dass der Router das selbst prüfen muss.
- **Bezug:** „Eine ungültige Eingabe … wird vollständig abgelehnt, ohne dass bereits gespeicherte Werte verändert werden."

### `settings_service.load_settings` / `get_current_settings` / `apply_settings`

- **Datei:** `backend/app/services/settings_service.py`
- **Typ:** Modul `settings_service` (neu)
- **Aufgabe:** Hält die bestätigten Settings als In-Memory-Cache, lädt sie beim Start aus PostgreSQL (legt bei Fehlen die Default-Zeile an) und schreibt eine bestätigte Intervalländerung sofort in `plc_handshake.POLL_INTERVAL_S`.
- **Änderung:** Neu erstellt.
- **Erkenntnis:** Worker lesen Nodes über `get_current_settings()` statt über eine beim Verbindungsaufbau einmalig aufgelöste Variable; dadurch wirkt eine bestätigte Änderung ab dem nächsten Auftrag, ohne dass die OPC-UA-Verbindung neu aufgebaut werden muss.
- **Bezug:** „Das Backend verwendet nach einer bestätigten Änderung ausschließlich die neuen Werte für nachfolgende OPC-UA-Zugriffe."

### `put_settings` / `get_settings` / `_field_error`

- **Datei:** `backend/app/routers/settings_router.py`
- **Typ:** Router `settings_router` (neu)
- **Aufgabe:** `GET /settings/` liefert die aktuellen Settings; `PUT /settings/` prüft den Aktiv-Auftrag-Schutz für beide Zielnodes und persistiert erst danach atomar.
- **Änderung:** Neu erstellt.
- **Erkenntnis:** „Aktiver Auftrag" wird über `production_queue.get_current_order_id()`/`delivery_queue.get_current_delivery_order_id()` erkannt (die tatsächlich den OPC-UA-Auftragsfluss antreiben), nicht über den `ProductionOrder`/`DeliveryOrder`-DB-Status, der von diesem Fluss entkoppelt ist (siehe Ist-Verhalten). Die Spec entscheidet sich für klare Ablehnung (409) statt automatischer Zurückstellung.
- **Bezug:** „Eine Änderung eines Zielnodes während eines aktiven Auftrags wird zurückgestellt oder abgelehnt …"

### `_worker_loop` / `_get_root_node` (Produktion und Lieferung)

- **Datei:** `backend/app/workers/production_queue.py`, `backend/app/workers/delivery_queue.py`
- **Typ:** Worker-Module `production_queue`, `delivery_queue`
- **Aufgabe:** Verarbeiten die Auftragswarteschlange; lösen den PLC-Zielknoten auf und fahren den PLC-Handshake.
- **Änderung:** Knotenauflösung aus dem Verbindungsblock (einmalig bei `connect`) in die Pro-Auftrag-Verarbeitung verschoben; `_get_root_node` nimmt jetzt einen `node_name`-Parameter statt eines hartcodierten Strings und liest ihn aus `settings_service.get_current_settings()`.
- **Erkenntnis:** Vorher blockierte ein Knotenauflösungsfehler die gesamte Verbindung (Endlos-Retry); jetzt scheitert nur der einzelne Auftrag, der Rest der Verbindung bleibt nutzbar – eine bewusste Verhaltensänderung, die durch die neue Konfigurierbarkeit nötig wurde.
- **Bezug:** „Das Backend verwendet nach einer bestätigten Änderung ausschließlich die neuen Werte für nachfolgende OPC-UA-Zugriffe."

### `start_background_workers`

- **Datei:** `backend/app/main.py`
- **Typ:** FastAPI-Startup-Hook
- **Aufgabe:** Initialisiert Backend-Hintergrundzustand beim Start.
- **Änderung:** Lädt die persistierten Settings (bzw. legt die Default-Zeile an) vor dem Start der Worker; kaputten `sites_router`-Import entfernt.
- **Erkenntnis:** Der Settings-Load muss vor `start_worker()`/`start_delivery_worker()` laufen, damit der erste Auftrag bereits die persistierten statt der Default-Werte verwendet.
- **Bezug:** „Gültige Zielnodes und ein gültiges Abfrageintervall … werden nach einem Neustart des Backends unverändert angezeigt."

### `SettingsForm`

- **Datei:** `frontend/components/settings-form.tsx`
- **Typ:** React-Client-Komponente (neu)
- **Aufgabe:** Lädt, zeigt und speichert die Settings; zeigt Lade-, Speicher- und Übernahmezustand sowie feldbezogene Fehler.
- **Änderung:** Neu erstellt.
- **Erkenntnis:** `ApiValidationError.fieldErrors` (aus dem Backend-`detail[].loc`-Array abgeleitet) wird direkt auf die jeweilige `Input`-Fehleranzeige gemappt; Lade-/Speicher-/Übernahme-Zustand sind drei getrennte State-Variablen (`loading`, `saving`, `savedAt`), nicht ein gemeinsamer Spinner.
- **Bezug:** „Die Fehlermeldung einer ungültigen Eingabe ist dem betroffenen Feld zugeordnet …"; „Ladevorgang, Speichervorgang und erfolgreiche Übernahme … sind … eigenständig erkennbar."

### `api.settings.get` / `api.settings.update` / `buildApiError`

- **Datei:** `frontend/lib/api.ts`
- **Typ:** Modul `api` (erweitert)
- **Aufgabe:** Kapselt den Zugriff auf `/settings/`; parst Backend-Fehlerantworten in `ApiValidationError` mit `fieldErrors`.
- **Änderung:** Neu erstellt (`settings`-Eintrag, `buildApiError`, `validateMockSettingsOrThrow`); `apiFetch`s Fehlerzweig nutzt jetzt `buildApiError` statt eines generischen `Error`.
- **Erkenntnis:** Der Mock-Modus (`USE_MOCK`) spiegelt dieselben Validierungsgrenzen client-seitig, damit die Oberfläche auch ohne Backend ein realistisches Fehlerbild zeigt.
- **Bezug:** „Die Fehlermeldung einer ungültigen Eingabe ist dem betroffenen Feld zugeordnet oder als Meldung in der Oberfläche sichtbar."

## Tests

Siehe `harness/_unittest.md`, Abschnitte „Settings werden persistiert …" bis „Lade-, Speicher- und Übernahmezustand sind in der Oberfläche erkennbar". Backend-Teile sind durch `backend/tests/test_settings.py` automatisiert abgedeckt (`docker compose exec backend python -m pytest tests/test_settings.py -q` → bestanden); die beiden rein UI-bezogenen Akzeptanzkriterien sind `NotApplicable` für Unit-Tests (kein Frontend-Testframework im Projekt) und wurden manuell über Build/SSR-Rendering sowie Code-Inspektion verifiziert.

## UI-/UX-Erkenntnisse

- Das Frontend hat aktuell kein Test-Framework (`frontend/package.json` enthält keine Test-Dependency); UI-Verhalten wird in diesem Projekt bislang nur durch `npm run build`/`npx eslint` und manuelle Prüfung abgesichert, nicht durch automatisierte Komponententests.
- `USE_MOCK` in `frontend/lib/api.ts` ist aktuell global auf `true` hartcodiert – ohne Codeänderung spricht keine Seite der Anwendung (auch nicht die neue Settings-Seite) mit dem echten Backend. Für eine echte Inbetriebnahme muss das bewusst umgeschaltet werden.

## Offene Punkte

- **Finale Bestätigung der Zielnodes:** Die Default-Werte `"MESAuftragProduktion"`/`"MESAuftragKommissionieren"` (siehe „Einstellungsfelder") sind die aktuell im Code verwendeten Browse-Namen, aber noch nicht von der Steuerungsgruppe als endgültig bestätigt (Arbeitspaket Person 3).
- **Finale Bestätigung der Intervall-Grenzen:** Der vorläufige Bereich 100–10.000 ms (Default 500 ms) ist noch nicht von der Steuerungsgruppe als endgültig zulässig bestätigt (Arbeitspaket Person 3).

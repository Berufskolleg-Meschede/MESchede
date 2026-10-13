# Unit-Test-Konventionen und Testkatalog

Diese Datei erfasst Unit Tests, die aus Specs entstehen oder durch deren Umsetzung angepasst werden. Sie stellt die Nachvollziehbarkeit zwischen Spec, Akzeptanzkriterium und Test sicher.

## Pflege-Regeln

- Für jedes testbare Verhalten einer neuen oder geänderten Spec wird geprüft, ob ein passender Unit Test existiert.
- Neu angelegte und fachlich angepasste Unit Tests werden in dieser Datei erfasst.
- Rein technische Refactorings bestehender Tests ohne Verhaltensänderung werden nicht aufgenommen.
- Ein Eintrag wird angelegt, sobald der Testbedarf aus der Spec bekannt ist.
- Der State wird nach Implementierung und erfolgreicher Ausführung aktualisiert.
- Nicht durch Unit Tests abdeckbare Kriterien erhalten eine Begründung und die vorgesehene andere Prüfart.
- Testnamen und Dateipfade werden ausschließlich aus der tatsächlichen Implementierung übernommen und nicht vorab erfunden.

## State-Werte

| State | Bedeutung |
|---|---|
| `Planned` | Der Testbedarf ist aus der Spec abgeleitet, aber noch nicht umgesetzt. |
| `Implemented` | Der Test ist implementiert, wurde jedoch noch nicht erfolgreich ausgeführt. |
| `Passed` | Der Test wurde in der aktuellen Implementierung erfolgreich ausgeführt. |
| `NotApplicable` | Ein Unit Test ist ungeeignet; Begründung und alternative Prüfung sind dokumentiert. |

## Eintragsformat

Für jeden durch eine Spec entstehenden oder geänderten Test wird dieser Block ergänzt:

```markdown
## {Fachliches Testziel}

- **Spec:** {relativer Pfad zur Bugfix-Spec}
- **Akzeptanzkriterium:** {eindeutige, kurze Wiedergabe}
- **State:** Planned | Implemented | Passed | NotApplicable
- **Testdatei:** {tatsächlicher relativer Pfad oder „Noch nicht vorhanden“}
- **Test:** {tatsächlicher Testname oder „Noch nicht vorhanden“}
- **Prüft:** {beobachtbares Verhalten}
- **Ausführung:** {ausgeführter Testbefehl und Ergebnis oder „Noch nicht ausgeführt“}
- **Hinweis:** {Randfall, Begründung oder „Keiner“}
```

## Testkatalog

## Settings werden persistiert und nach Neustart unverändert geladen

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Gültige Zielnodes und ein gültiges Abfrageintervall lassen sich speichern und werden nach einem Neustart des Backends unverändert angezeigt.
- **State:** Passed
- **Testdatei:** `backend/tests/test_settings.py`
- **Test:** `test_load_settings_creates_default_row_when_missing`, `test_load_settings_returns_the_persisted_row_unchanged`, `test_put_settings_persists_confirmed_values_and_updates_the_cache`
- **Prüft:** Fehlende Settings-Zeile wird mit Default-Werten angelegt; eine vorhandene Zeile wird unverändert zurückgegeben (simuliert den Neustart-Fall); eine bestätigte Änderung wird in die Session committet.
- **Ausführung:** `docker compose exec backend python -m pytest tests/test_settings.py -q` → bestanden.
- **Hinweis:** Zusätzlich manuell über `curl` gegen die laufende Anwendung mit echter PostgreSQL-Instanz verifiziert (GET/PUT/GET zeigt den persistierten Wert).

## Backend verwendet nach einer Änderung ausschließlich die neuen Werte

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Das Backend verwendet nach einer bestätigten Änderung ausschließlich die neuen Werte für nachfolgende OPC-UA-Zugriffe.
- **State:** Passed
- **Testdatei:** `backend/tests/test_settings.py`
- **Test:** `test_put_settings_persists_confirmed_values_and_updates_the_cache`, `test_apply_settings_updates_the_plc_handshake_poll_interval`, `test_production_worker_resolves_the_currently_configured_node_per_order`, `test_delivery_worker_resolves_the_currently_configured_node_per_order`
- **Prüft:** Eine bestätigte Änderung aktualisiert den In-Memory-Cache und `plc_handshake.POLL_INTERVAL_S`; `production_queue`/`delivery_queue` lösen den Zielnode pro Auftrag anhand der aktuell im Cache stehenden Einstellung auf, nicht anhand eines beim Verbindungsaufbau zwischengespeicherten Wertes.
- **Ausführung:** `docker compose exec backend python -m pytest tests/test_settings.py -q` → bestanden.
- **Hinweis:** Keiner.

## Ungültige Eingabe wird ohne Teiländerung abgelehnt

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Eine ungültige Eingabe (leerer Zielnode oder Intervall außerhalb von 100–10.000 ms) wird vollständig abgelehnt, ohne dass bereits gespeicherte Werte verändert werden.
- **State:** Passed
- **Testdatei:** `backend/tests/test_settings.py`
- **Test:** `test_empty_or_blank_node_is_rejected`, `test_interval_outside_bounds_is_rejected`, `test_interval_at_bounds_is_accepted`
- **Prüft:** Pydantic-Validierung lehnt leere/blanke Zielnodes sowie Intervalle außerhalb der Grenzen bereits beim Parsen des Request-Bodys ab, bevor der Endpoint-Code läuft; dadurch ist niemals eine Teiländerung an der DB-Zeile möglich.
- **Ausführung:** `docker compose exec backend python -m pytest tests/test_settings.py -q` → bestanden.
- **Hinweis:** Zusätzlich manuell über `curl` verifiziert: ungültiges PUT liefert 422, ein anschließendes GET zeigt die zuvor gespeicherten, unveränderten Werte.

## Fehlermeldung ist dem betroffenen Feld zugeordnet

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Die Fehlermeldung einer ungültigen Eingabe ist dem betroffenen Feld zugeordnet oder als Meldung in der Oberfläche sichtbar.
- **State:** NotApplicable
- **Testdatei:** Keine
- **Test:** Keiner
- **Prüft:** –
- **Hinweis:** Kein Frontend-Testframework im Projekt vorhanden (`frontend/package.json` enthält keine Test-Dependency). Die Zuordnung ist stattdessen manuell verifiziert: das Backend liefert `detail: [{"loc": ["body", "<feldname>"], "msg": ...}]` (siehe `curl`-Verifikation der Settings-API), und `components/settings-form.tsx` mappt `loc[-1]` über `ApiValidationError.fieldErrors` auf das jeweilige Eingabefeld.
- **Ausführung:** Noch nicht automatisiert ausgeführt.

## Zielnode-Änderung während eines aktiven Auftrags wird abgelehnt

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Eine Änderung eines Zielnodes während eines aktiven Auftrags wird zurückgestellt oder abgelehnt; der aktive Auftrag verwendet bis zu einem sicheren Zeitpunkt weiterhin den zuvor bestätigten Zielnode.
- **State:** Passed
- **Testdatei:** `backend/tests/test_settings.py`
- **Test:** `test_put_settings_rejects_production_node_change_during_an_active_production_order`, `test_put_settings_rejects_delivery_node_change_during_an_active_delivery_order`, `test_put_settings_allows_interval_change_while_an_order_is_active`
- **Prüft:** Ist `production_queue.get_current_order_id()`/`delivery_queue.get_current_delivery_order_id()` nicht `None` und ändert sich der zugehörige Zielnode, wird die gesamte Anfrage mit 409 abgelehnt und die gespeicherte Zeile bleibt unverändert; eine reine Intervalländerung bleibt trotz aktivem Auftrag möglich.
- **Ausführung:** `docker compose exec backend python -m pytest tests/test_settings.py -q` → bestanden.
- **Hinweis:** Diese Spec entscheidet sich für „klar zurückweisen" statt „zurückstellen und später automatisch anwenden" (siehe Entscheidungen in der Spec); Letzteres wurde nicht umgesetzt.

## Lade-, Speicher- und Übernahmezustand sind in der Oberfläche erkennbar

- **Spec:** `spec/32-Konfigurationsoberfläche.md`
- **Akzeptanzkriterium:** Ladevorgang, Speichervorgang und erfolgreiche Übernahme der Einstellungen sind in der Oberfläche jeweils eigenständig erkennbar.
- **State:** NotApplicable
- **Testdatei:** Keine
- **Test:** Keiner
- **Prüft:** –
- **Hinweis:** Kein Frontend-Testframework im Projekt vorhanden. Manuell geprüft: `npm run build` sowie ein SSR-Abruf von `/settings` zeigen den Ladezustand ("Lade Einstellungen…"); `components/settings-form.tsx` unterscheidet Laden (`loading`), Speichern (`saving`, Button-Text „Speichert…") und Übernahme (`savedAt`-Banner mit Zeitstempel) über getrennte State-Variablen.
- **Ausführung:** Noch nicht automatisiert ausgeführt.

## RabbitMQ-Bestandsereignisse

- **Spec:** Keine; neues Feature, erfasst in `harness/ideas/I2 Lagerbestände per RabbitMQ übernehmen.md`.
- **Akzeptanzkriterium:** Snapshots und Änderungen werden validiert und doppelte Ereignisse verändern den Bestand nicht erneut.
- **State:** Implemented
- **Testdatei:** `backend/tests/test_storage_consumer.py`
- **Test:** `test_snapshot_persists_stock_and_duplicate_is_ignored`, `test_delta_without_snapshot_does_not_assume_zero`, `test_invalid_delta_is_rejected`, `test_message_id_can_supply_missing_event_id`
- **Prüft:** Persistenz, Idempotenz, unbekannte Basisbestände und Pflichtfelder des Vertragsentwurfs.
- **Ausführung:** Noch nicht ausgeführt; die Sitzung enthält weder pytest noch SQLModel.
- **Hinweis:** Die Gruppenschnittstelle ist noch unbestätigt; Tests prüfen den dokumentierten Vertragsentwurf.

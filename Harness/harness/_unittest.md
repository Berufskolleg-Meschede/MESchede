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

## I29 – Auftragsidentität und wiederholte Annahme

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-18, AC-19: identische Annahme ohne zweiten Lauf; abweichender Inhalt ist Konflikt.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_repository.py`
- **Test:** `test_duplicate_acceptance_returns_same_run_after_repository_restart`, `test_changed_payload_is_rejected_without_another_order`, `test_equal_business_ids_in_different_types_do_not_collide`, `test_concurrent_identical_acceptances_persist_one_order`
- **Prüft:** Gleiche fachliche ID bei unterschiedlichem Auftragstyp; gleiche und abweichende Payloads, auch nach Wiederanlauf.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Backend-Verhaltenstests; konkrete Testnamen erst aus der Implementierung übernehmen.

## I29 – Eindeutige Produkteinheiten und Ergebnismengen

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-07 bis AC-11: getrennte Mengen, Korrelation, keine Doppelzählung und unvollständige Ergebnisse.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_services.py`, `backend/tests/test_order_reliability.py`
- **Test:** `test_repeated_product_results_do_not_increment_quantities`, `test_unverified_codes_do_not_fabricate_good_or_failed_quantities`, `test_foreign_order_does_not_change_product_results`, `test_unknown_verified_product_codes_keep_quantities_unknown`, `test_later_plc_contradiction_preserves_facts_and_requires_new_review`
- **Prüft:** Wiederholte Resultate, wiederverwendete PLC-Slots, fremde Läufe, unbekannte Ergebnisse und gemischte Gut-/Fehlresultate.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Synthetische Fixtures 11/12 sind ausdrücklich kein Live-Vertragsnachweis; echte Codes bleiben offen.

## I29 – Globaler Startausschluss und FIFO

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-16, AC-17: höchstens ein Dispatch; ältester angenommener Auftrag zuerst.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_repository.py`, `backend/tests/test_order_dispatch.py`, `backend/tests/test_order_reliability.py`
- **Test:** `test_oldest_delivery_precedes_new_production_regardless_of_priority`, `test_concurrent_dispatchers_reserve_only_one_run`, `test_production_and_delivery_complete_in_global_fifo_order`, `test_only_one_worker_leader_can_write_until_connection_released`
- **Prüft:** Gleichzeitige Anforderungen beider Worker, gemischte Reihenfolge, gleiche Annahmezeit und ignorierte Produktions-/Lieferpriorität.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Zusätzlich Integrationstest für konkurrierende API-Aufrufe und dauerhaft gespeicherte Reihenfolge.

## I29 – Persistenz über Prozessneustart

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-14, AC-15, AC-20: Aufträge, Reihenfolge und mögliche Übergabe bleiben nachvollziehbar.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_reliability.py`
- **Test:** `test_new_process_preserves_fifo_and_marks_uncertain_start_for_review`
- **Prüft:** Neustart mit wartenden Aufträgen und Unterbrechung zwischen möglichem Startschreiben und Bestätigung.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Durch echten neuen Pythonprozess mit unveränderter PostgreSQL-Testpersistenz geprüft; kein Anlagenneustartnachweis.

## I29 – Wiederanlaufabgleich ohne Doppelstart

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-12, AC-13, AC-21: Annahme/Idle sind kein Abschluss; aktiver korrelierter Lauf wird nicht erneut gestartet.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_services.py`, `backend/tests/test_order_reliability.py`
- **Test:** `test_idle_after_unconfirmed_start_requires_review`, `test_active_correlated_run_is_preserved_on_recovery`, `test_recovery_finishes_partially_cleared_reset_without_losing_results`
- **Prüft:** Aktiver korrelierter Auftrag, sehr kurzer Lauf, fehlender Abschlussnachweis, fremder Auftrag und verlorene Verbindung.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Vorhandene Handshaketests bleiben Regressionseinstieg; simulierte PLC plus reale Abnahme erforderlich.

## I29 – Globale Reviewsperre und Bereitschaft

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-22 bis AC-24: beide Startarten blockiert bis zur Prüfung und bestätigter PLC-Bereitschaft.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_repository.py`, `backend/tests/test_order_reliability.py`, `backend/tests/test_order_dispatch.py`
- **Test:** `test_uncertain_production_blocks_delivery_after_restart`, `test_manual_review_never_resets_active_plc_and_blocks_next_kind`, `test_status_zero_with_nonzero_count_is_not_ready`, `test_execution_timeout_preserves_reservation_and_requires_review`, `test_unverified_contract_never_writes_start`
- **Prüft:** Produktionsreview sperrt Lieferung und umgekehrt; mehrere offene Reviews; Review erledigt bei weiterhin aktiver oder unbekannter PLC.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Alle Aufrufwege müssen dieselbe backendseitige Sperre respektieren.

## I29 – Review ohne Pflichtnotiz und gültige Mengen

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-27 bis AC-29: Bewertung und Mengen ohne Erklärung speicherbar; ungültige Angaben abgelehnt.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_services.py`, `backend/tests/test_orders_api.py`
- **Test:** `test_manual_review_without_note_keeps_unknown_quantities_unknown`, `test_review_rejects_total_above_plan_and_stale_version`, `test_review_http_rejects_invalid_quantities`, `test_http_review_without_note_is_idempotent_and_keeps_reservation`
- **Prüft:** Bekannte/unkannte Mengen, negative und gebrochene Werte, Sollmengenüberschreitung und Widerspruch zu belegten PLC-Mengen.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Unfertige Einheiten gelten nicht automatisch als Fehlteile; Erfolg setzt Gutmenge nicht automatisch auf Sollmenge.

## I29 – Review ohne Steuerungsbefehl oder Doppelzählung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-30, AC-32, AC-40: Review steuert PLC nicht; Wiederholung/Konkurrenz überschreiben Ergebnisse nicht unbemerkt.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_services.py`, `backend/tests/test_order_reliability.py`
- **Test:** `test_repeated_review_does_not_change_version_or_count_twice`, `test_competing_reviews_allow_only_one_version_update`, `test_manual_review_never_resets_active_plc_and_blocks_next_kind`
- **Prüft:** Kein Start/Stop/Reset beim Review; wiederholtes Speichern und konkurrierende Änderung derselben Bewertung.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Konkurrierende Speicheraufrufe zusätzlich mit Datenbankintegration prüfen.

## I29 – Resultatsicherung vor Quittierung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-39: verfügbare Endresultate werden vor möglichem Verlust durch MES-Quittierung dauerhaft gesichert.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_reliability.py`, `backend/tests/test_plc_order_gateway.py`
- **Test:** `test_failed_result_commit_does_not_acknowledge_plc`, `test_recovery_finishes_partially_cleared_reset_without_losing_results`, `test_reset_clears_inputs_then_count_then_command`, `test_foreign_order_is_not_reset_even_with_end_signal`, `test_failed_count_readback_never_sends_reset_command`, `test_cancel_waits_for_inflight_io_before_closing_gateway`
- **Prüft:** Laufende mit nach Reset verschwindenden Resultaten; fehlgeschlagene Speicherung darf keinen stillen Datenverlust erzeugen.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** PLC-Simulator für Reihenfolge, PostgreSQL-Integration für Speicherbestätigung und Anlagenprüfung für tatsächlichen Datenlebenszyklus.

## I29 – Quellenstatus und Aktualität

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-33 bis AC-36: gültige Resultate bleiben erhalten; Fehllesen erneuert keine Aktualität; stale/unknown bleiben erkennbar.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_repository.py`, `backend/tests/test_order_services.py`, `backend/tests/test_plc_order_gateway.py`
- **Test:** `test_source_failure_preserves_last_successful_observation`, `test_missing_and_stale_sources_are_not_reported_as_fresh`, `test_changed_feedback_during_snapshot_is_rejected`
- **Prüft:** Fehllesen, Reconnect, Zeitüberschreitung der konfigurierten Grenze, fehlende Erstbeobachtung und teilweise verfügbare Quelle.
- **Ausführung:** `cd backend; python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`: 130 Passed am 2026-10-13, einschließlich Start-/Lauf-/Resettimeout.
- **Hinweis:** Kontrollierte Uhr; keine echte Wartezeit nötig. Sichtbare UI-Kennzeichnung zusätzlich im Browser prüfen.

## I29 – Seitenstruktur, Dashboard und Datenzustände

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-01 bis AC-06, AC-25, AC-26, AC-31, AC-37: getrennte Seiten, lesendes Dashboard, persistenter Prüfhinweis und Quellenkennzeichnung.
- **State:** NotApplicable
- **Testdatei:** `frontend/tests/orders.spec.ts`
- **Test:** `production: getrennte Queues und Prüfung nach Reload`, `delivery: getrennte Queues und Prüfung nach Reload`, `Dashboard kombiniert beide Bereiche und bleibt lesend`, `API-Ausfall erhält letzte Daten und kennzeichnet deren Veraltung`, `Erstausfall zeigt keine erfundenen Aufträge`, `Suche und Status senden echte Backendfilter`
- **Prüft:** Produktions-/Lieferansicht, Warte-/Produktqueue-Trennung, Dashboardlinks, manuell markierte Mengen, Reload und API-Ausfall ohne stillen Mock-Fallback.
- **Ausführung:** `cd frontend; npm run test:e2e`: 22 Passed, Chromium bei 1440×1000 und 390×844. Produktions-/Liefer-Screenshots visuell geprüft.
- **Hinweis:** UI-/Browserprüfungen statt reiner Backend-Unit-Tests; bekannte/fehlende Daten jeweils prüfen.

## I29 – Tastatur und responsive Bedienung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-38: Prüfung, Navigation und Tabelleninteraktion sind per Tastatur bedienbar.
- **State:** NotApplicable
- **Testdatei:** `frontend/tests/orders.spec.ts`
- **Test:** `Tastaturprüfung speichert unbekannte Mengen ohne Notiz`, `Versionskonflikt erhält Eingaben und verlangt explizite Aktualisierung`, `unsichere Speicherantwort wird mit derselben Anfrage-ID wiederholt`
- **Prüft:** Fokusreihenfolge, Reviewdialog, Beschriftungen, Linkziele und Tabellen auf Projektgeräten.
- **Ausführung:** `cd frontend; npm run test:e2e`: 22 Passed, Chromium bei 1440×1000 und 390×844. Produktions-/Liefer-Screenshots visuell geprüft.
- **Hinweis:** Manuelle Browser-/Geräteprüfung; Unit Tests allein belegen Bedienbarkeit nicht.

## I29 – Reale PLC-Korrelation und Laufabnahme

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-08, AC-10, AC-13, AC-20, AC-21, AC-24, AC-39: verifizierte Identitäten, Übergänge und Resultatsicherung.
- **State:** NotApplicable
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Realer Produktions- und Lieferlauf, kurze Läufe, alte Resultate, Abbruch/Reconnect/Neustart sowie Bereitschaft beider Slots.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Anlagenprotokoll mit erwarteten/tatsächlichen Werten erforderlich. Keine Live-Abnahme allein aufgrund simulierter Tests.

## I29 – Migration, HTTP und Proxy

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-01 bis AC-04, AC-14 bis AC-19, AC-25 bis AC-30, AC-37, AC-40.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_migrations.py`, `backend/tests/test_orders_api.py`, `frontend/tests/proxy.spec.ts`.
- **Test:** `test_fresh_migration_creates_order_domain_and_initial_state`, `test_upgrade_preserves_existing_machine_and_user_rows`, `test_pages_filter_before_pagination_and_share_global_review`, `test_injected_app_lifespan_works_without_live_plc`, `Proxy erhält Pfad, Query, Reviewinhalt und Konfliktstatus`.
- **Prüft:** Upgrade ohne Verlust bestehender Daten, globaler Prüfhinweis, Filter vor Pagination, injizierter App-Lifecycle und echter Next-HTTP-Transport.
- **Ausführung:** Backendregression: 130 Passed. `npm run test:e2e`: 22 Passed, Proxy in beiden Browserprojekten erfolgreich.
- **Hinweis:** Jede DB-Prüfung verwendet ausschließlich ein isoliertes zufälliges PostgreSQL-Schema. Kein Laden produktiver env-Dateien. HTTP-Transportfixture ist im Frontend-Testordner.

## I29 – Beobachtungsintervalle und UI-Mengenvalidierung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-29, AC-35, AC-38.
- **State:** Passed
- **Testdatei:** `backend/tests/test_order_domain.py`, `frontend/tests/orders.spec.ts`.
- **Test:** `test_invalid_observation_intervals_are_rejected`, `ungültige Gesamtmenge bleibt im Dialog und sendet keine Bewertung`.
- **Prüft:** Nicht endliche/ungültige Pollingwerte werden abgelehnt; zu hohe Gesamtmenge bleibt als beschrifteter Fehler im Reviewdialog ohne HTTP-Speicherung.
- **Ausführung:** Backend: 130 Passed; Playwright: 22 Passed am 2026-10-13.
- **Hinweis:** Backend validiert Mengen weiterhin unabhängig von der Browserprüfung.

## Ausführungsstand Issue 29

- Backend: **130 Passed** in 7,24 s, echte isolierte PostgreSQL-Schemas und separater Prozess.
- Browser: **22 Passed** in 7,4 s, Chromium bei 1440×1000 und 390×844; Screenshots der beiden Seiten, des Dashboards und des Reviewdialogs visuell geprüft.
- Frontendbuild, TypeScript und ESLint der geänderten/neuen Dateien erfolgreich. `git diff --check` erfolgreich.
- Bestehender Toolhinweis: baseline-browser-mapping ist veraltet; kein aufgabenfremdes Dependency-Upgrade vorgenommen.
- Keine echte PLC kontaktiert oder geschrieben. Reale Produktstatuscodes/Identitäten, vollständiger Reset-Lebenszyklus, physische Laufabnahme sowie Projektgeräteprüfung bleiben offen.

## I29 – Expliziter Testdaten-Wrapper

- **Spec:** `../../docs/specs/issue-29-ui-preview.md`.
- **Akzeptanzkriterium:** PV-01 bis PV-07: bestehende UI, Kennzeichnung, globaler Lauf/FIFO, temporäre Bewertung/Reset und explizite Aktivierung ohne PLC-/DB-Zugriff.
- **State:** Passed
- **Testdatei:** `frontend/tests/preview/store.test.mjs`, `frontend/tests/preview/ui.spec.ts`, `frontend/tests/orders.spec.ts`.
- **Test:** `Vorschau besitzt einen reservierten Lauf und typspezifische FIFO-Ansichten`, `Bewertung ist idempotent und überschreibt keine neue Version`, `Unklar und widersprüchliche Mengen bleiben erkennbar`, `Zurücksetzen entfernt Bewertungen und alte Laufreferenzen`, `Suche und Status werden vor der Pagination kombiniert`, `bestehende UI zeigt gekennzeichnete Testdaten und temporäre Bewertungen`, `Dashboard kombiniert beide Bereiche und bleibt lesend`.
- **Prüft:** Rein lokaler API-Speicher, tatsächliche bestehende Seiten/Proxy, manuelle Mengen statt Doppelzählung, Reload, Reset und keine Vorschaukennzeichnung im normalen Modus.
- **Ausführung:** `cd frontend; npm run test:preview`: 5 Speichertests und 2 Browserfälle bestanden. TypeScript/ESLint und Produktionsbuild erfolgreich; normaler Browserregressionslauf einschließlich fehlender Vorschaukennzeichnung: 22 Passed.
- **Hinweis:** Wrapper braucht Node.js 22.14+ und bindet nur `127.0.0.1:3030`/`127.0.0.1:18030`. Kein echter PLC-/Persistenznachweis; Hauptspec bleibt wegen Anlagenabnahme Modified.

# Übergabe: Issue #30 – Aufträge manuell über die UI starten

Stand: 14.10.2026

## Ziel

Issue [#30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30) bearbeiten: Bediener sollen Produktions- und Lieferaufträge in der MES-Oberfläche erfassen, bestätigen und anschließend verfolgen können. Issue #29 liefert bereits die getrennten Auftragsseiten und den gemeinsamen Laufstatus; manuelles Auslösen war dort ausdrücklich ausgeklammert.

## Verbindliche Ausgangspunkte

- Lokale Issue-Fassung und Anforderungen: [`docs/issues/projektwoche/manual.md`](../issues/projektwoche/manual.md).
- Übergreifender UI-Rahmen: [`docs/specs/projektwoche-mes-ui.md`](../specs/projektwoche-mes-ui.md), Abschnitt „Produktions- und Lieferaufträge manuell starten“.
- Für UI-Muster zuerst [`Harness/harness/_uiux.md`](../../Harness/harness/_uiux.md) lesen.
- Harness-Ablauf beachten: Idee erfassen, genau drei kritische Fragen bewerten, offene Fachentscheidungen klären, erst danach Spec und Implementierungsplan erstellen. Einstieg: [`Harness/AGENTS.md`](../../Harness/AGENTS.md).

## Bereits vereinbarter Umfang

- Formulare/Dialoge für beide Auftragsarten mit Auftrag-ID, Produkten, Menge und erforderlichen Auftragsdaten.
- Eingaben prüfen und vor dem Senden eine verständliche Zusammenfassung zeigen.
- Während des Sendens Mehrfachklicks verhindern; Annahme, bestätigten PLC-Start und Fehler getrennt darstellen.
- Bei unklarem Request-Ergebnis zuerst nachsehen, ob der Auftrag schon gespeichert wurde; keine Doppelstarts durch Retry.
- Nach Annahme zur Auftragsübersicht und zum Detail führen.
- Dashboard bleibt lesend. Keine zusätzlichen Pause-, Abbruch-, Bearbeiten- oder Löschen-Aktionen hinzufügen, sofern Issue #30 sie nicht ausdrücklich verlangt.

## Aktueller Implementierungsstand und Einstiegspunkte

- Vorhandene Seiten: `frontend/app/production-orders/page.tsx`, `frontend/app/delivery-orders/page.tsx`; beide verwenden `frontend/components/orders-section.tsx`.
- `OrdersSection` zeigt Listen, Status, wartende Aufträge, Details und Review, enthält aktuell aber kein Erfassungs-/Startformular.
- `frontend/lib/api.ts` enthält ältere `create/update/delete`-Methoden auf Basis von `OrderFormData` (`quantity`, `status`, `article_id`). Diese passen nicht zum aktuellen Backend-Auftragsvertrag; nicht ungeprüft wiederverwenden.
- Aktuelle POST-Routen: `POST /productionorder/` und `POST /deliveryorder/`. Beide nehmen `OrderPayload` entgegen: `order_id` plus `mes_auftrag`.
- `mes_auftrag` ist in `backend/app/models/mes_auftrag.py` modelliert: `kopf` mit numerischer `Auftragsnummer`, Kunden-/Start-/Prioritäts-/Parameterdaten sowie `inhalt.Produktqueue` mit mindestens einem Produktdatensatz. PLC-Grenzen und Pflichtwerte dort prüfen.
- `202 Accepted` bedeutet dauerhaft angenommen/eingereiht, noch nicht PLC-gestartet. Die UI muss auf bestätigte Statusänderung warten und den Backendzustand anschließend neu laden.
- Auftragannahme und Idempotenz laufen über `OrderAdmissionService`; beide Auftragsarten teilen einen Worker und eine globale FIFO-Reihenfolge. Bei nicht laufendem Worker lehnt das Backend derzeit mit `503` ab.

## Vor Umsetzung zu klären

- Woher kommen gültige Produkt-IDs/-texte und zulässige Mengen? Im Issue ist die Produktauswahlquelle offen.
- Welche Auftragsfelder sind für die UI erforderlich bzw. sinnvoll vorbelegt (Startdatum/-zeit, Kundennummer, Seriennummern, Priorität, Parameter)?
- Wie wird die fachliche Auftrags-ID eindeutig der numerischen PLC-Auftragsnummer zugeordnet?
- Einzelproduktformular ausreichend oder gemischte Produktqueue nötig? Das Issue lässt dies offen.
- Vor Implementierung den aktuellen API-/Frontendcode und Tests erneut prüfen; dieser Übergabestand kann sich ändern.

## Arbeitsbaum beim Übergabestand

Branch `main`. Vor dem Anlegen dieser Übergabe war der Arbeitsbaum sauber. Frühere Änderungen zur PLC-Node-Schreibweise sind im aktuellen Arbeitsbaum nicht offen. Diese Übergabedatei ist neu.

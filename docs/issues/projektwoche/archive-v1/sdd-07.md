# [SDD-07] MES-Aggregations-API und dauerhafte manuelle Auftragsannahme umsetzen

<!-- meschede-projektwoche-v1:SDD-07 -->
## Ziel

Die UI erhält zusammenhängende Ansichten und kann über die vorhandenen POST-Schnittstellen Aufträge zuverlässig annehmen lassen.

## Einordnung

- Bereich: Backend; Schätzung: 6 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-04, REQ-05, REQ-06.
- Abhängigkeiten: SDD-01, SDD-04, SDD-05, SDD-06
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `backend/app/routers/productionorders_router.py`, `deliveryorders_router.py`, `storage_router.py`, neue Dashboard-/Analytics-Services

## Umsetzung

- Listen/Details je Art, Dashboard mit getrennten aktiven Slots und wartenden Aufträgen aus den persistierten Quellen aufbauen.
- Bestehende POST-Payloads validieren und vor 202 dauerhaft speichern; mehrfachen Start durch Art+ID und identischen Payload vermeiden.
- Manuellen UI-Aufruf durch dieselben Worker/Schreibwege wie externe Aufträge leiten; keine unabhängige Direkt-Start-Logik.
- Analytics nach vereinbartem Zeitraum/Art aus tatsächlichen Produktresultaten und UTC-Laufzeiten berechnen; Mengen nach Art trennen.
- Einheitliche Fehler, null-Werte, Aktualität je Quelle und OpenAPI-Vertrag bereitstellen; Diagnose-/Healthstatus ergänzen.

## Akzeptanzkriterien

- [ ] Liste, Detail und Dashboard stimmen für denselben Auftrag in Status/Mengen überein.
- [ ] 202 bedeutet dauerhaft angenommen; identischer Retry liefert denselben Auftrag ohne zweiten PLC-Start; geänderter Payload ergibt 409.
- [ ] Beide POST-Arten behalten den bisherigen Payload-Vertrag und nutzen nur ihre korrekten OPC-UA-Slots.
- [ ] Fixture Soll=10, gut=7, fehlerhaft=2 zeigt bearbeitet=9; Liefermengen erhöhen Produktionsmenge nicht.
- [ ] Bei bekannten Start-/Endzeiten wird die korrekte Dauer geliefert; fehlende Zeiten ergeben null; externer Ausfall erhält letzte Daten mit stale.

## Nachweis und Review

API-Vertragstests für Annahme/Retry, beide Arten, Aggregation, Teil-Ausfall und Zeitraumgrenzen. Fixtures aus SDD-01 verwenden.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

## Bezug zu bestehenden Aufgaben

- [#8: Auftrags-Router entwickeln](https://github.com/Berufskolleg-Meschede/MESchede/issues/8): Geschlossenes Grundlagen-Ticket; bestehende Annahme bleibt kompatibel, diese Erweiterung ergänzt Persistenz und UI-Lese-/Auswertungsverträge.

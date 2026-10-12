# [SDD-11] Produktions- und Lieferaufträge anzeigen und manuell auslösen

<!-- meschede-projektwoche-v1:SDD-11 -->
## Ziel

Benutzer können beide Auftragsarten über validierte Dialoge annehmen lassen und ihren bestätigten Fortschritt verfolgen.

## Einordnung

- Bereich: Frontend; Schätzung: 4 Teamstunden.
- Anforderungen: REQ-02, REQ-03, REQ-05, REQ-08.
- Abhängigkeiten: SDD-09
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `frontend/app/production-orders/page.tsx`, `delivery-orders/page.tsx`, Auftrags-Tabellen/Dialog-Komponenten

## Umsetzung

- Suche/Statusfilter tatsächlich mit den Listen verbinden; Detail für Ergebnisse und Laufzeiten zugänglich machen.
- Je Art Dialog mit ID, Produkt-ID/Produkten, Menge und bestätigten Pflichtfeldern implementieren; in bestehendes MESAuftrag-Payload transformieren.
- Zusammenfassung vor Absenden; Doppelklick blockieren; 202 als angenommen kennzeichnen; Erfolg über Statusabfrage bestätigen.
- Bei unbekanntem Requestergebnis zuerst vorhandenen Auftrag lesen; 422/409/Netzwerkfehler mit verständlicher Rückmeldung.
- Generische Statusänderung/Bearbeiten/Löschen nur bei bestätigtem API-Vertrag anbieten.

## Akzeptanzkriterien

- [ ] Gültiges Formular jeder Art erzeugt den passenden POST-Vertrag und das richtige Auftragsziel.
- [ ] Ungültige/zu große Menge oder unzulässige Produkt-ID verhindert Absenden und nennt den Fehler.
- [ ] Mehrfacher Klick/Retry führt mit SDD-07 zu einem Auftrag; UI behauptet nach 202 keinen bestätigten Produktionsstart.
- [ ] ID-Suche/Statusfilter wirken; Details zeigen unbekannte Felder ausdrücklich.
- [ ] Fehler und Dialoge sind per Tastatur bedienbar; Formulare funktionieren mit Vertragsfixtures und nach Integration real.

## Nachweis und Review

Payloads für beide Arten prüfen; Validierung, Retry/Timeout und echten manuellen Start mit anschließender PLC-Rückmeldung testen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

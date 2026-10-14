# [SDD-01] MVP-Spezifikation, API-Verträge und UI-Zustände festlegen

<!-- meschede-projektwoche-v1:SDD-01 -->
## Ziel

Frontend, Backend und Integration arbeiten gegen dieselben Fachregeln und JSON-Beispiele. Die vorbereitete Spec wird anhand des Anlagen-Spikes bestätigt.

## Einordnung

- Bereich: Analyse; Schätzung: 7 Teamstunden.
- Anforderungen: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05, REQ-06, REQ-07, REQ-08, REQ-09.
- Abhängigkeiten: Keine; kann sofort beginnen.
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `docs/specs/projektwoche-mes-ui.md`, `frontend/lib/types.ts`, `frontend/lib/api.ts`, `frontend/lib/api-client.ts`, `backend/app/models/mes_auftrag.py`

## Umsetzung

- Bestand und MVP prüfen; offene Fragen mit Zuständigkeit dokumentieren. Entwurf parallel zu SDD-02, verbindlicher Abschluss mit dessen Ergebnissen.
- Liste/Detail, Dashboard, Lager, Auswertung, Auftragsannahme, Fehler und Settings als DTOs/OpenAPI-Beispiele festlegen; aktuelle POST-Payloads kompatibel halten.
- Status klein schreiben; Auftragsart + fachliche ID, PLC-Korrelation, Zeitstempel, null-Werte und Aktualitätsmetadaten festlegen.
- UI-Flows und Fixtures für Laden, leer, aktiv, fertig, Fehler, veraltet und unbekannt festhalten. Auslieferung fachlich von Kommissionierung abgrenzen.
- MVP-Entscheidungen zu Mengenlimits, Polling, Zeitraumsemantik, Adminzugang und Einzel-/Mehrproduktformular dokumentieren.

## Akzeptanzkriterien

- [ ] Jeder REQ-01 bis REQ-09 ist einem Issue und einem beobachtbaren Abnahmekriterium zugeordnet.
- [ ] Verträge enthalten realistische Beispiele für beide Auftragsarten einschließlich gemischter Produktqueue sowie wiederholtem POST und PLC-Ausfall.
- [ ] Annahmen und bestätigte Anlagenfakten sind unterscheidbar; keine erfundenen NodeIds, Hostnamen oder RabbitMQ-Felder.
- [ ] Alle drei Teammitglieder können anhand derselben Fixtures parallel umsetzen; offene Punkte blockieren nur davon abhängige Funktionen.

## Nachweis und Review

Vertragsreview im Team; JSON-Beispiele gegen DTOs prüfen. Ergebnis als versionierte Spezifikation und Schnittstellenbeispiele im Repository dokumentieren.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

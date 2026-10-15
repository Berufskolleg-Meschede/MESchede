# Implementierungsplan – Aufträge manuell starten

## Meta

- **State:** Active
- **Stand:** 15.10.2026
- **Spec:** [Issue #30](../specs/issue-30-manual-order-start.md)
- **Idee:** [Harness-Idee I4](../../Harness/harness/ideas/I4%20Auftraege%20manuell%20starten%20Issue%2030.md)
- **Branch:** `spec/issue-30-manual-orders`
- **Fortschritt:** Backend, gemeinsame Erfassung, Annahmeabgleich und Detailpolling lokal umgesetzt und geprüft. SPS-Katalog lesend verifiziert und DB-Import ergänzt; Anlagenabnahme echter Aufträge offen; Spec bleibt `Modified`.

## Ziel und Abhängigkeiten

Die vorhandenen Auftragsseiten erhalten denselben Erfassungs-/Prüfablauf. Dauerhafte Annahme, Idempotenz, globales FIFO, PLC-Korrelation und Reviews werden über die vorhandenen Services verwendet. Die alten Mock-CRUD-Methoden sind keine Integrationsgrundlage.

Am 15.10.2026 hat der Benutzer den lesenden SPS-Katalogzugriff und die Speicherung ausdrücklich beauftragt. PDF-Seiten 96–97 und die Anlage bestätigen den singulären Knotennamen, sechs Produkte samt Bauplandaten und 33 Slots je Auftragsart. Der einmalige Import läuft ohne Auftragsworker. Echte Auftragsstarts sind weiterhin keine ausgeführte Abnahme.

## Aktueller Umsetzungsstand

| Schritt | Stand |
| --- | --- |
| 1 – Reale PLC-Vertragsprüfung | Katalog, Bauplanfelder und Slots lesend bestätigt. Standardwertsemantik und echte Auftragsläufe bleiben offen; keine SPS-Schreibzugriffe. |
| 2 – Vorbereitung/Validierung | Lokal umgesetzt: `GET /orders/input-context`, freie Vorschläge, Anlagenzeit, persistenter Katalogspiegel, typspezifische Kapazität und Erstannahmevalidierung. |
| 3 – Detail/API-Client | Umgesetzt: `OrderDetailView` mit unveränderlicher Payload, Client-POST und strukturierte Feldfehler. |
| 4 – Gemeinsamer Dialog | Umgesetzt und im Browser geprüft: beide Identifikatoren, mehrere Produktzeilen, fortlaufende Seriennummern, Kopfwerte und Zusammenfassung. |
| 5 – Unklare Annahme | Umgesetzt und mit verlorener Antwort, Retry, Konflikt, Speicherfehler und Reload geprüft. |
| 6 – Verfolgung | Umgesetzt: Annahmehinweis, gezielte Listensuche und unabhängig aktualisiertes Detail. |
| 7 – Nachweise/Dokumentation | Lokale Nachweise vorhanden; reale Anlage und öffentliche Wiki-Aktualisierung noch offen. Wiki-Änderungen sind als [lokaler Patch](../wiki/issue-30-update.md) vorbereitet, nicht veröffentlicht. |

Neue Backendfälle: 22 Erfassungsfälle und 6 Katalogpersistenz-/Lebenszyklusfälle bestanden. Browser inklusive bestehender Auftrags-/Proxyregression: 56 bestanden, Desktop und 390×844. TypeScript und Produktionsbuild bestanden; visuelle Kontrolle der Zusammenfassung erfolgt. Vollständige Backendregression: 211 bestanden und zwei im unveränderten HEAD ebenfalls reproduzierte Fehler (aufgefüllte ID-Suche, Lagerzeitstempel). Details und Befehle im [Harness-Testkatalog](../../Harness/harness/_unittest.md#ausfuehrungsstand-issue-30).

Der vorhandene Entwicklungsserver wurde nicht beendet. Die Browserprüfung verwendet einen separaten Produktionsbuild mit webpack unter `.next/issue30-tests`, einen eigenen Port und die lokale HTTP-Fixture. Die temporäre Python-Testumgebung enthält das fehlende Projektpaket `pika`; keine globalen Python-Pakete oder Projektdaten wurden dafür geändert.

## Verantwortlichkeiten

| Bestehender Bereich | Geplante Verantwortung |
| --- | --- |
| PLC-Clients/Gateway | Produktkatalog und Queue-Kapazitäten lesend erfassen; tatsächliche IDs und Browsenamen verwenden. |
| `OrderRepository` | Freie ID-/PLC-Nummernvorschläge aus Persistenz lesen; atomare Annahme und Unique-Constraints erhalten. |
| `OrderAdmissionService` | Identische Wiederholung zuerst auflösen; erstmalige Annahme fachlich validieren und committen. |
| `OrderQueryService` / DTOs | Erfassungsvorbereitung sowie vollständige immutable Eingabedaten im Detail bereitstellen. |
| Auftragsrouter | Zusätzliche lesende Fähigkeiten anbinden und Feldfehler übertragen; dieselben POST-Wege erhalten. |
| `OrderApiClient` / Browserproxy | Vorbereitung, typspezifische Annahme und Inhaltsabgleich transportieren; keine automatischen POST-Retries. |
| `OrdersSection` / neue Erfassung | Eingaben und Queue-Aufbau, Zusammenfassung, Requestsperre und Abgleichzustände führen. |
| Detail-/Snapshot-Anbindung | Den angenommenen Auftrag unabhängig von Filter/Pagination gezielt aktualisieren. |

Neue Typen und Dateien werden erst bei der Umsetzung nach ihrer tatsächlichen Aufgabe benannt. Backend-Fachlogik bleibt unabhängig von FastAPI und React. Uhr, Katalogzugang und Persistenz sind austauschbare Abhängigkeiten. Die vorhandenen Python-/TypeScript-Konventionen und die Sprachabgrenzung der Harness-Coderichtlinien gelten.

## Schritt 1 – PLC-Vertrag lesend belegen

- `DB_MES_Schnittstelle.Produktspezifikation` browsen: Struktur, Indexgrenzen, ID-/Textfelder, Datentypen und verfügbare Produkte dokumentieren. Index 0 überspringen, ID nicht aus dem Index ableiten.
- Queue-Slots für Produktion und Lieferung getrennt lesen; maximale zulässige Gesamtmenge aus verfügbarer Kapazität und bestätigten Fachlimits ableiten, höchstens 255.
- Startdatum-/Startzeitkonvertierung, lokale Anlagenzeitzone und fachliche Verwendbarkeit der Standardwerte für Seriennummernstart, `Sequenznummer` und `Takt` prüfen.
- Gültige Beispiele aus diesen Daten für Entwicklung/Abnahme auswählen. Keine PLC-Schreibzugriffe in diesem Schritt.
- **Ergebnis:** Belegter Eingabevertrag und Testdatengrundlage. Abweichende Fachgrenzen werden zuerst in der Spec nachgeführt.

## Schritt 2 – Vorbereitung und Annahmevalidierung

- Lesenden Katalogzugang mit Quellenstatus, erfolgreichem Beobachtungszeitpunkt und Veraltungsgrenze ergänzen. Erfassung bei unbekannter/veralteter Grundlage sperren.
- Freie Auftrag-ID und freie PLC-Nummer pro Auftragsart unabhängig vorschlagen. Vorschläge reservieren nichts; Unique-Constraints und atomare Konfliktprüfung bleiben autoritativ.
- Backend-Uhr mit konfigurierbarer Anlagenzeitzone (`Europe/Berlin` als Ausgangswert) für lokale Datums-/Zeitvorbelegung verwenden.
- Konkrete Vorbereitungsschnittstelle festlegen; neue URLs und DTOs ausdrücklich als Erweiterung dokumentieren. Bei einer neuen Pfadgruppe die Proxy-Allowlist gezielt ergänzen. Statische Auftragsrouten müssen vor `/{order_id:path}` aufgelöst werden.
- Die vorhandene Annahme um Prüfung der tatsächlichen Produkte, Gesamtmenge, integergenauen Kopfwerte, offsetfreien Uhrzeit, SIMATIC-DATE-Grenzen und Seriennummern erweitern.
- Reihenfolge erhalten: Bereits gespeicherte gleiche Identität/Inhalt liefert die ursprüngliche Annahme; ein abweichender Inhalt bleibt Konflikt. Erstmalige Aufträge durchlaufen die Katalog-/Kapazitätsprüfung vor dem Commit.
- Backendprüfungen nicht nur in einer UI-Sonderroute ausführen: beide bestehenden POST-Wege verwenden dieselbe fachliche Grenze.
- **Ergebnis:** Vorbereitungsdaten und konsistente Fehlerrückmeldungen; die Anwendung erzeugt weiterhin höchstens einen Lauf je fachlicher Identität.

## Schritt 3 – Detailvertrag und API-Client

- Typspezifischen Detailvertrag um die vollständig gespeicherte normalisierte `mes_auftrag`-Payload ergänzen. Bestehende Listen/Summaries bleiben schlank.
- `OrderApiClient` und die delegierenden Methoden in `lib/api.ts` für Vorbereitung und POST auf Basis von `OrderPayload` erweitern; `OrderFormData` nicht wiederverwenden.
- Strukturierte `422`-Details und `409`-Konflikte für den Dialog abbilden; fehlende oder unlesbare Antworten als unklaren Ausgang behandeln.
- Sicherstellen, dass der Proxy Timeout/Upstream-Ausfall nicht als belegte Nichtannahme ausgibt. Kein automatischer POST-Retry.
- **Ergebnis:** Vollständige Transportgrundlage für Erfassung und Abgleich.

## Schritt 4 – Gemeinsamer Dialog mit Queue-Aufbau

- „Neuer Auftrag“ in beide bestehenden Header integrieren, Erfassung mit denselben UI-Primitives erstellen.
- Getrennte editierbare Identifikatoren, Produktzeilen, Einzel-/Gesamtmenge und editierbare Seriennummernstartnummer anbieten.
- Queue deterministisch in Zeilenreihenfolge expandieren; Nummern `S … S+N-1`, `SeriennummerStart=S`, `Sequenznummer=0`, `Takt=0`. Überlauf verhindern.
- Datum/Uhrzeit aus der Vorbereitung ohne UTC-Konvertierung übernehmen. Kundennummer leer zu 0; weitere Angaben mit den Modellstandards initialisieren.
- Eingabe- und Prüfschritt mit verständlichen Feldfehlern, vollständiger Zusammenfassung und expliziter Annahmeaktion umsetzen.
- Während POST Änderungen, zweite Bestätigung und Dismissal sperren. Nach belegter Ablehnung Werte erhalten und freigeben.
- **Ergebnis:** Beide Auftragsarten verwenden denselben überprüfbaren Bedienablauf.

## Schritt 5 – Unklare Annahme sicher aufklären

- Unveränderlichen Versuch vor POST in der Browsersitzung sichern. Speicherfehler vor dem Senden sichtbar behandeln.
- Nach verlorenem Ergebnis oder Reload zuerst typspezifisches Detail lesen und normalisierten vollständigen Inhalt vergleichen.
- Bei Treffer denselben Auftrag übernehmen; bei Abweichung Konflikt zeigen; bei fehlgeschlagenem GET ausschließlich erneutes Prüfen ermöglichen.
- Bei verlässlichem `404` denselben eingefrorenen Request auf Bedieneraktion wiederholen. Identität, Datum/Uhrzeit und Seriennummern bleiben erhalten, auch wenn der erste Request noch läuft.
- Unaufgeklärten Versuch nicht durch neue Vorschläge oder stilles Bearbeiten in einen zweiten Auftrag verwandeln.
- **Ergebnis:** Doppelklick, Timeout, Retry und Reload verursachen keinen unbeabsichtigten zweiten Start.

## Schritt 6 – Bestätigte Annahme und Lauf verfolgen

- `202` mit Annahmehinweis zeigen, Liste neu laden und Filter/Pagination für den neuen Auftrag auflösen.
- Den Auftrag über typbezogene Detailabfrage erreichbar machen; geöffnetes Detail unabhängig von der Listenseite regelmäßig aktualisieren.
- `queued`, `preparing`, `start_pending` und bestätigt `running` verständlich unterscheiden. Sehr schnelle Abschlüsse ohne beobachteten Start korrekt anzeigen.
- Nachladefehler von der bereits bestätigten Annahme trennen. FIFO, Start-/Reviewsperren, Mengenherkunft und Recovery unverändert verwenden.
- **Ergebnis:** Durchgehender Weg von Eingabe bis gespeicherter PLC-Rückmeldung.

## Schritt 7 – Nachweise und Dokumentation

- Testbedarf gemäß [Harness-Testkatalog](../../Harness/harness/_unittest.md#i30--erfassung-und-queueaufbau) umsetzen; reale Namen erst danach eintragen.
- Modell-/Servicetests für Grenzen und Queue-Aufbau; isolierte PostgreSQL-Prüfungen für Vorschlagsrennen, Annahme und Idempotenz; Browserprüfungen für beide Dialoge, Doppelbestätigung, verlorene Antwort, Retry, Reload und Detailpolling.
- Bei PostgreSQL-Prüfungen ausschließlich eine ausdrücklich konfigurierte Testdatenbank über die bestehenden Fixtures nutzen. Keine Projekt-/Anlagendaten als Testdatenbank verwenden.
- Relevante Backendtests und Frontendprüfungen ausführen; Lint auf geänderte Dateien begrenzen und den Produktionsbuild ausführen. Tests verwenden ausschließlich Fakes beziehungsweise die ausdrücklich konfigurierte isolierte Datenbank.
- Tastatur, Fokus, lange Text-IDs/Produkttexte, mehrere Zeilen und schmalen Bildschirm im gerenderten Dialog prüfen. Grenzwerte und falsche Browserzeitzone gezielt abdecken.
- Reale Anlagenabnahme: je einen gültigen Produktions- und Lieferauftrag mit belegten Produktdaten vom UI-Aufruf bis zur korrelierten Rückmeldung verfolgen; Retry-/Doppelklickschutz zuerst isoliert prüfen.
- Bei Umsetzung README/API-/PLC-Dokumentation und betroffene Wiki-Seiten mit dem tatsächlichen Vertrag synchronisieren; UI-Regeln und Testkatalog pflegen.
- State erst nach vollständigem Abgleich auf `Implemented` setzen; anschließend den Harness-Commit erstellen. Kein Commit oder Push allein für die aktuelle Spec-Erstellung vorausgesetzt.

## Aufteilung gemäß Issue

| Arbeitspaket | Inhalt und Übergabe |
| --- | --- |
| Oberfläche | Schritte 3–6 für Client/Dialog/Verfolgung, inklusive Browsernachweisen. |
| Backend | Vorbereitung, Vorschläge, Validierung, Detailvertrag und Idempotenz; Schritte 2–3 und zugehörige Nachweise. |
| Anbindung und Prüfung | Lesende PLC-Vertragsprüfung, gültige Beispieldaten, gemeinsamer Durchlauf und reale Abnahme; Schritte 1 und 7. |

Keine konkreten Personen wurden zugewiesen. Die API-Datenbeispiele und Regeln werden vor der UI-Anbindung gemeinsam festgehalten.

# Aufträge manuell starten

## Meta

- **Typ:** Idee
- **State:** Specified
- **Geltungsbereich:** GitHub Issue #30; manuelle Erfassung und Annahme von Produktions- und Lieferaufträgen sowie anschließende Verfolgung.
- **Stand:** 15.10.2026
- **Branch:** `spec/issue-30-manual-orders`

## Zweck

Issue #30 gemeinsam mit dem Projektverantwortlichen zu einer prüfbaren Feature-Spec ausarbeiten. Der Implementierungsplan folgt nach Klärung der wesentlichen Fachentscheidungen.

## Kontext

Die beiden bestehenden Auftragsseiten verwenden `OrdersSection` für Listen, Wartepositionen, Laufzustände, Produktqueue, Details und Reviews. Ein Erfassungsformular fehlt. Issue #29 hat die manuelle Auftragserfassung ausdrücklich ausgeklammert.

Die laufenden Auftragsansichten greifen über `OrderApiClient` und `/api/mes` auf echte Backenddaten zu. Die weiterhin vorhandenen älteren Mock-CRUD-Methoden in `frontend/lib/api.ts` verwenden einen anderen Vertrag (`quantity`, `status`, `article_id`) und eignen sich nicht als Ausgangspunkt für diese Mutation.

Beide POST-Routen nehmen `OrderPayload` mit `order_id` und `mes_auftrag` entgegen. Das Backend speichert den Auftrag und genau einen Lauf dauerhaft, bevor es `202` meldet. Identische Wiederholungen liefern dieselben Referenzen; anderer Inhalt bei gleicher Auftragsart und ID verursacht einen Konflikt. Eine PLC-Auftragsnummer ist je Auftragsart auch über abgeschlossene Aufträge hinweg eindeutig. Produktion und Lieferung teilen einen Worker und die globale FIFO-Reihenfolge.

Die Übergabe wird gegen den aktuellen Code geprüft. Die neue Funktion erweitert die Auftragsseiten; das Dashboard bleibt lesend. Zusätzliche Pause-, Abbruch-, Bearbeiten- oder Löschen-Aktionen gehören nicht zum Auftrag.

## Quellen

- Benutzerauftrag und Übergabe vom 14.10.2026; anschließende Antworten im Chat.
- [GitHub Issue #30](https://github.com/Berufskolleg-Meschede/MESchede/issues/30), live gelesen am 14.10.2026; keine Kommentare vorhanden.
- [Lokale Issue-Fassung](../../../docs/issues/projektwoche/manual.md).
- [Übergreifender UI-Rahmen](../../../docs/specs/projektwoche-mes-ui.md).
- [Übergabe](../../../docs/handoffs/issue-30-manual-order-start.md).
- [Issue-29-Spec](../../../docs/specs/issue-29-order-production-overview.md).
- [UI-/UX-Regeln](../_uiux.md), [Ideenregeln](../_idea.md), [Spec-Regeln](../_requirements.md), [Testkatalog](../_unittest.md).
- `frontend/components/orders-section.tsx`, `frontend/lib/order-api.ts`, `frontend/lib/api.ts`, `frontend/hooks/use-order-snapshot.ts`, `frontend/app/api/mes/[...path]/route.ts`.
- `backend/app/models/order_dto.py`, `backend/app/models/mes_auftrag.py`.
- `backend/app/routers/productionorders_router.py`, `backend/app/routers/deliveryorders_router.py`, `backend/app/routers/order_dependencies.py`.
- `backend/app/services/order_admission_service.py`, `backend/app/repositories/order_repository.py`, `backend/app/services/order_dispatch_service.py`.
- `backend/app/clients/opc_ua_client.py`, [PLC-Dokumentation und Produktquelle](../../../docs/opc-ua-integration.md).
- `backend/tests/test_mes_auftrag.py`, `backend/tests/test_order_repository.py`, `backend/tests/test_orders_api.py`, `backend/tests/test_order_services.py`, `frontend/tests/orders.spec.ts`; gelesen, in dieser Dokumentationsphase nicht ausgeführt.

## Inhalt

### Ursprünglicher Prompt

Auf Grundlage der Übergabe und des aktuellen GitHub-Issues #30 eine Spec schreiben und die Anforderungen im Gespräch klären. Vor der Arbeit einen Branch erstellen und den Harness-Ablauf verwenden: Idee erfassen, genau drei kritische Fragen bewerten, offene Fachentscheidungen klären, anschließend Spec und Implementierungsplan erstellen.

### Kritische Bewertung

#### 1. Welche Eingaben gehören zum manuellen Auftrag und welche Datenquellen sind verbindlich?

**Antwort:** Beide Auftragsarten erhalten dieselbe Erfassung mit Auftrag-ID, Produkten und Mengen sowie den benötigten Kopfdaten. Der Benutzer hat mehrere Produktzeilen mit eigener Menge bestätigt. Die Zeilen werden in ihrer sichtbaren Reihenfolge in einzelne Einheiten der `Produktqueue` überführt. Ein Queue-Eintrag repräsentiert ein Stück; die Gesamtmenge entspricht der Summe aller Zeilenmengen.

Die dokumentierte verbindliche Produktquelle ist `DB_MES_Schnittstelle.Produktspezifikationen`. Dort ist Index 0 leer; die Auftragsqueue beginnt hingegen bei Index 0. Katalogindex und `ProduktID` dürfen nicht gleichgesetzt werden. Ein Katalogleser ist im aktuellen Backend noch nicht implementiert. Gültige IDs und Texte, verfügbare Queue-Slots beider Auftragsarten und mögliche zusätzliche Fachlimits müssen vor der realen Anbindung lesend geprüft werden. Das Modell erlaubt 1–255 Queue-Einträge, Produkt-IDs und Parameter von 0–255, Produkttexte bis 30 Zeichen sowie UInt-Werte von 0–65535. Diese Typgrenzen belegen keine fachliche Gültigkeit eines Produkts oder eine verfügbare PLC-Kapazität.

Der Benutzer verlangt zwei getrennte Felder für die fachliche Auftrag-ID und die PLC-Auftragsnummer. Beide werden mit einem freien Vorschlag vorbelegt und bleiben editierbar. Datum und Uhrzeit werden automatisch vorbelegt und bleiben editierbar; die API-Zeit enthält keinen Zeitzonenoffset. Kundennummer ist optional. Priorität und Parameter erhalten Standardwerte und bleiben editierbar. Seriennummern laufen je Auftrag ab einer editierbaren Startnummer über alle Produktzeilen hinweg fortlaufend; eine auftragsübergreifende Vergabe wurde ausdrücklich nicht gewählt.

#### 2. Welches beobachtbare Verhalten wird von Erfassung bis Verfolgung erwartet?

**Antwort:** Der Bediener öffnet auf der jeweiligen Auftragsseite „Neuer Auftrag“, erfasst die Produktzeilen und prüft vor dem Senden eine verständliche Zusammenfassung. Ungültige Eingaben verhindern das Absenden und erzeugen Meldungen an den betroffenen Feldern. Während des Sendens sind Mehrfachklicks und konkurrierende Änderungen am abgesendeten Inhalt gesperrt.

`202` bedeutet ausschließlich dauerhaft angenommen. Danach werden die Übersicht neu geladen und der angenommene Auftrag samt Details erreichbar gemacht, auch wenn Suchfilter ihn ausblenden. Ein bestätigter PLC-Start wird ausschließlich anhand des neu geladenen, korrelierten Backendzustands angezeigt. Wartend, Übergabe vorbereitet, Start noch unbestätigt, laufend, Fehler und Prüfbedarf dürfen nicht durch eine pauschale Erfolgsmeldung ersetzt werden. Offene Reviews und fehlende Bereitschaft verhindern weiterhin den tatsächlichen Start beider Auftragsarten; Priorität hebt FIFO nicht auf.

#### 3. Welche Randfälle und Regressionen können Doppelstarts oder falsche Rückmeldungen verursachen?

**Antwort:** Die fachliche Identität ist Auftragsart plus normalisierte `order_id`. Auch automatische Vorbelegungen benötigen eine serverseitige Eindeutigkeitsprüfung bei Annahme, da zwei Browser denselben Vorschlag erhalten können. Konflikte dürfen keine bestehenden Inhalte überschreiben und keine neue ID ohne erneute Bestätigung senden.

Bei Timeout, Verbindungsabbruch oder einer unklaren Proxy-/Serverantwort muss zuerst die typspezifische Detailabfrage prüfen, ob der Auftrag gespeichert wurde. Der Proxy kann `503` nach einem bereits erfolgten Commit zurückgeben; diese Antwort ist kein sicherer Nichtannahmenachweis. Eine Wiederholung verwendet exakt dieselbe ID und dieselbe eingefrorene Payload, einschließlich Datum, Uhrzeit und Produktreihenfolge. Ein fehlgeschlagener GET beweist keine Nichtannahme. Ein gefundener Auftrag muss als derselbe Inhalt nachweisbar sein: der bestehende Detailvertrag enthält nicht alle Kopfdaten, sodass hierfür eine Ergänzung oder ein belastbarer Inhaltsvergleich nötig ist. Ein Browserreload darf weder automatisch erneut senden noch eine neue Identität für einen unklaren Versuch erzeugen.

Im Bestand abgesicherte Nachbarfunktionen sind persistente Annahme, gleiche und widersprüchliche Wiederholungen, getrennte Auftragsarten, FIFO, globale Start-/Reviewsperre und Wiederaufnahme. Die neue Erfassung muss diese Regeln verwenden. Produktkatalogausfall, unbekannte Kapazität, Nummernerschöpfung, Seriennummernüberlauf, unvollständige Rückmeldungen sowie bereits aktive oder sehr schnell abgeschlossene Läufe sind relevante Randfälle. Geplantes Datum und geplante Uhrzeit dürfen nicht als beobachteter Start erscheinen; eine zeitgesteuerte Terminplanung ist im aktuellen Dispatch nicht belegt.

### Ergänzung vom 15.10.2026: SPS-Katalog in PostgreSQL

Der Benutzer hat den lesenden SPS-Abgleich und die Übernahme des Produktkatalogs in die Datenbank ausdrücklich beauftragt. `SchnittstelleMES.pdf`, Seiten 96–97, und anschließendes lesendes Browsen belegen `DB_MES_Schnittstelle.Produktspezifikation` im Singular. Index 0 ist leer; die sechs tatsächlichen Produkte besitzen die IDs 1–6. Beide Auftragsqueues exponieren die Slots 0–32. Der bisher angenommene Plural war falsch. Es wurden keine SPS-Werte geschrieben und kein Auftrag ausgelöst.

Die drei bestehenden Bewertungsfragen erhalten folgende ergänzende Antworten:

- Zu 1: Produkte werden aus dem dokumentierten und gelesenen SPS-Katalog bezogen; PostgreSQL speichert ID, Text, Bauplandaten, Quellindex und Synchronisationsstatus. Der bestehende Artikelstamm mit Preis bleibt unabhängig, da keine Preise aus der SPS belegt sind.
- Zu 2: Die UI liest den synchronisierten DB-Katalog; der POST validiert gegen dessen frischen Stand. Ein Hintergrundabgleich hält ihn aktuell, eine explizite Aktualisierung kann erneut abgleichen. Die Auftragsannahme selbst fragt die SPS nicht zusätzlich ab.
- Zu 3: Ein vollständiger erfolgreicher Snapshot wird atomar übernommen. Fehlende Produkte werden erst nach erfolgreichem Gesamtabgleich als nicht verfügbar markiert. Fehler oder Teilantworten erhalten die letzten gespeicherten Produkte und ihren ursprünglichen Erfolgszeitpunkt; alte Aufträge behalten ihre ursprünglichen Payloads. Wiederholter Import erzeugt keine Duplikate.

### Bestätigte Fachentscheidungen

| Thema | Entscheidung im Chat |
| --- | --- |
| Produkte | Mehrere Produktzeilen mit eigener Menge. |
| Identifikatoren | Auftrag-ID und PLC-Auftragsnummer als zwei getrennte Felder; jeweils freien Vorschlag anzeigen, beide editierbar. |
| Seriennummern | Je Auftrag fortlaufend ab einer editierbaren Startnummer, ohne Neustart pro Produktzeile. |
| Datum und Uhrzeit | Automatisch vorbelegen, editierbar; API-Payload ohne Zeitzonenoffset. |
| Kundennummer | Optional; Modellstandard 0 bei leerer Eingabe. |
| Priorität | Modellstandard 1; editierbar unter weiteren Angaben, keine Änderung der globalen FIFO-Reihenfolge. |
| Parameter | Modellstandards `Parameter0=0` und `Parameter1=0`; editierbar unter weiteren Angaben. |
| Produktquelle | Bereits dokumentierte verbindliche PLC-Produktspezifikationen verwenden. |

### Entscheidung

Specified. Die drei kritischen Fragen sind bewertet und die wesentlichen Fachentscheidungen im Chat geklärt. Die Feature-Spec liegt analog zu Issue #29 unter `docs/specs/`. Reale Katalogdaten, Queue-Kapazitäten und fachliche Verwendbarkeit der Modellstandardwerte müssen vor der Anlagenanbindung belegt werden; das ist als erster Schritt im Implementierungsplan festgelegt. Unbekannte Voraussetzungen verhindern eine neue Annahme. `Harness/spec/` bleibt gemäß Harness für Bugfix-Specs reserviert.

### Abgeleitete Specs

- [Feature-Spec Issue #30](../../../docs/specs/issue-30-manual-order-start.md).
- [Implementierungsplan Issue #30](../../../docs/plans/issue-30-manual-order-start.md).

## Beziehungen

- **Voraussetzung:** Bestehende Auftragsübersicht und persistente Auftragsannahme aus Issue #29.
- **Ergänzt:** `docs/issues/projektwoche/manual.md` und `docs/specs/projektwoche-mes-ui.md`.
- **Ergebnis:** `docs/specs/issue-30-manual-order-start.md` und `docs/plans/issue-30-manual-order-start.md`.

## Offene Punkte

- Keine offene Entscheidung zu UI-Umfang, ID-Zuordnung oder Seriennummernregel.
- Katalogfelder, gültige Produkt-IDs/Texte und Queue-Slots wurden am 15.10.2026 lesend bestätigt; sechs Produkte sind ohne Duplikate in PostgreSQL importiert. Die Modellstandardwerte benötigen weiterhin eine fachliche Anlagenabnahme.
- Anlagenzeitzone und fachliche Verwendbarkeit von `Sequenznummer=0`, `Takt=0` und Modellstandard 0 für die editierbare Seriennummernstartnummer bei der lesenden Vertragsprüfung belegen.
- Vorbereitungsschnittstelle und expliziter Katalogabgleich sind in der Spec konkret dokumentiert und implementiert.

## Pflege

- **Aktualisierung:** Bei weiteren Antworten im Chat, bei abweichendem aktuellem API-Vertrag und beim Übergang zur Spec.
- **Ablösung:** Durch die verlinkte Feature-Spec; die Idee bewahrt ursprünglichen Auftrag und Fachentscheidungen.

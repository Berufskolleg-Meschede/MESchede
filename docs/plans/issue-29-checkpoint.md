# Issue 29 – Fortsetzungsstand

Stand: 2026-10-13. Nach der Pause wieder aufgenommen; lokale Softwareimplementierung und Verifikation abgeschlossen. Kein IoT-Netz benötigt oder reale PLC kontaktiert.

## Gesicherter Stand

- Branch: `feature/29-order-production-overview`.
- Spec: `docs/specs/issue-29-order-production-overview.md`, weiter `Modified` wegen ausstehender Anlagenabnahme.
- Plan: `docs/plans/issue-29-order-production-overview.md`, tatsächliche Klassen/Etappen aktualisiert.
- Harness-Testkatalog und UI-/UX-Guide enthalten den erreichten Softwarestand.
- Änderungen liegen auf dem Datenträger, darunter neue Dateien. Kein neuer Commit oder Push ausgeführt; bei Fortsetzung Status prüfen und erhalten.
- Die bestehenden Auftragsseiten zeigen echte Daten, getrennte Warte-/Produktqueues, Laufprüfung und Quellenzustand. Das Dashboard kombiniert beide Bereiche lesend.
- Backend hat sechs neue Tabellen, gemeinsame FIFO-Reservierung, Workerführung, Ergebnisse vor Reset, Wiederanlauf und versionsgeschützte idempotente Reviews. `OrderWorkerHost` ersetzt den Entwurfsnamen `OrderRuntime`.
- Review sendet keinen PLC-Befehl. Spätere widersprechende PLC-Fakten bleiben erhalten und erfordern erneute Prüfung.
- Frontendproxy verwendet serverseitig `MES_BACKEND_URL`; Produktions-Compose setzt `http://backend:8000`. Kein automatischer Demodaten-Fallback.

## Abgeschlossene lokale Prüfung

- Backend: **130 Passed**, einschließlich echter isolierter PostgreSQL-Schemas, Migration und neuem Pythonprozess.
- Browser: **22 Passed**, Chromium 1440×1000/390×844. Queues, Reload, Dashboard, Tastaturreview, 409/Retry, Mengenvalidierung, Quellenfehler/Veraltung, Backendfilter und Next-Proxy geprüft.
- Build, TypeScript, ESLint der geänderten/neuen Dateien und `git diff --check` erfolgreich.
- Produktions-/Lieferseiten, Dashboard und Reviewdialog anhand Screenshots visuell geprüft.
- Testartefakte werden unter `frontend/test-results/` ignoriert. Playwright startet/beendet eigene lokale Testserver.

## Nächster fachlicher Schritt – wenn das IoT-Netz verfügbar ist

1. Vor Änderungen Status/Branch, Spec und Harness lesen. Nicht neu implementieren.
2. Rein lesend echte Produktstatusfelder, finale Codes und Produkt-/Serien-/Sequenzidentitäten beider Slots bestätigen. Synthetische Tests 11/12 sind kein Live-Vertrag.
3. Vor-/Nach-Reset-Lebenszyklus und globale Anlagenbereitschaft einschließlich fremder/HMI-Läufe prüfen. Der Reset löscht MES-Produkteingaben, dann Anzahl, dann MES-Kommando; gespeicherte Ergebnisse bleiben erhalten.
4. Erst nach dokumentiertem Vertrag `OPC_UA_CONTRACT_VERIFIED` und echte `OPC_UA_PRODUCT_RESULTS` passend setzen. Standard bleibt false/{}.
5. Reale Produktion und Lieferung nacheinander abnehmen: Mengenvergleich, kurze Läufe, Ausfall/Neustart, Reviewblocking und FIFO. Erwartete/tatsächliche Werte dokumentieren.
6. Projektgeräte/Tastatur/Zoom prüfen. Erst nach allen erforderlichen Nachweisen Spec auf `Implemented` setzen.

## Lokale Prüfungen wiederholen

Eigener Testcontainer: `meschede-issue29-test-db`, PostgreSQL `postgres:18.3-alpine3.23`, Port `127.0.0.1:55429`, Testnutzer/-passwort `mes_test`, DB `mes_test`, tmpfs `/var/lib/postgresql`. Testdaten dürfen wegfallen; niemals Projektdatenbank einsetzen. Container bei Bedarf starten oder mit diesen Parametern neu erstellen.

Backend: `python3 -m pytest -q --tb=short --order-test-db-url=postgresql+psycopg2://mes_test:mes_test@127.0.0.1:55429/mes_test`.
Frontend: `npm run build`, `npm run test:e2e`; Chromium wurde installiert. Lokale Ports/DB-Zugriffe benötigen in Codex Sandboxfreigabe.

## Fachliche Grenzen

- Genau ein Produktions- ODER Lieferlauf; globale Annahmereihenfolge ohne Typpriorität.
- Unklare Ausführung blockiert beide Arten bis zur Prüfung plus bestätigter Bereitschaft.
- Review speichert Laufbewertung und bekannte/unkannte Mengen ohne Pflichtnotiz.
- PLC-Auftragsnummer bleibt je Typ konservativ eindeutig; Wiederverwendung benötigt einen sicheren Generationsnachweis.
- Manuelles Erstellen/Starten/Bearbeiten/Löschen bleibt Issue 30.

## Nachträglich autorisierte UI-Vorschau

Der Benutzer hat anschließend ausdrücklich einen Testdaten-Wrapper beauftragt. `cd frontend; npm run dev:preview` startet dieselbe UI mit gekennzeichneten Daten unter `http://127.0.0.1:3030`; lokaler API-Speicher auf Port 18030. Bewertungen und Reset betreffen nur den Vorschauprozess. Dateien unter `frontend/tests/preview/`, Hinweis in `order-preview-notice.tsx`; Anleitung in `frontend/README.md`. Spec `docs/specs/issue-29-ui-preview.md` dokumentiert die Zusatzentwicklung. Keine UI-Kopie und kein automatischer Fallback.

Vorschau geprüft: 5 Speichertests und 2 Browserfälle erfolgreich; normale Browserregression weiterhin 22 Passed, Produktionsbuild/TypeScript/ESLint erfolgreich. Vorschau-Starter erzwingt den Entwicklungsmodus nur für seinen Kindprozess.

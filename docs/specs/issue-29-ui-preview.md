# Optionale Testdaten-Vorschau für Issue 29

## Meta

- **State:** Implemented
- **Idee:** `../../Harness/harness/ideas/I2 Testdaten-Wrapper fuer UI-Pruefung.md`
- **Freigabe:** Benutzerauftrag für Testdaten-Wrapper; bestehende UI wiederverwenden.

## User Story

Als Projektentwickler möchte ich die bestehenden Auftragsseiten mit gekennzeichneten Testdaten prüfen, damit ich auch außerhalb des IoT-Netzes Darstellung und Laufbewertung beurteilen kann.

## Description

Ein expliziter lokaler Entwicklungsstart stellt einen temporären API-Wrapper bereit. Die bestehenden Seiten erhalten den gleichen Vertrag wie vom Backend. Die Vorschau enthält wartende, prüfbedürftige, abgeschlossene und fehlerhafte Aufträge sowie bekannte/unkannte Produktmengen.

## Soll-Verhalten

- `npm run dev:preview` startet die bestehende UI und einen ausschließlich lokalen Testdatenserver.
- Ein dauerhafter Hinweis kennzeichnet simulierte Daten und temporäre Bewertungen.
- Bewertungen ändern ausschließlich den Vorschauzustand im Speicher; gleiche Anfrage-ID ist idempotent und konkurrierende Versionen werden abgelehnt.
- Zurücksetzen erstellt den Ausgangsdatensatz neu und macht erneute Prüfung möglich.
- Der normale UI-Start bleibt am realen API-Vertrag; kein automatischer Testdaten-Fallback. Vorschaukennzeichnung wird ausschließlich im expliziten Entwicklungsmodus aktiv.

## Akzeptanzkriterien

| ID | Prüfkriterium |
| --- | --- |
| PV-01 | Die vorhandenen Routen und Komponenten zeigen vom Wrapper gelieferte Testaufträge. |
| PV-02 | Dashboard und Auftragsseiten zeigen durchgehend die Testdatenkennzeichnung. |
| PV-03 | Die Vorschau enthält global höchstens einen reservierten Lauf und eine gemeinsame FIFO-Warteliste. |
| PV-04 | Bewertung, unbekannte Mengen, Versionskonflikt und identischer Retry sind mit temporären Daten prüfbar. |
| PV-05 | Zurücksetzen stellt die Ausgangsdaten wieder her; zuvor gespeicherte Bewertungen sind entfernt. |
| PV-06 | Wrapper und Bewertungen besitzen keine Produktionsdatenbank- oder PLC-Verbindung. |
| PV-07 | Normale Starts und Produktionsbuild aktivieren keinen automatischen Vorschau-Fallback. |

## Angepasste Methoden

| Datei / Typ | Methoden | Verantwortung / Erkenntnis |
| --- | --- | --- |
| `frontend/tests/preview/store.mts` / `PreviewOrderStore` | `reset`, `createOrder`, `views`, `source`, `summary`, `dispatch` | Erzeugt sechs eindeutig simulierte Aufträge, einen reservierten Lauf und eine globale Warteliste ausschließlich im Speicher. Reset vergibt neue Laufreferenzen. |
| dieselbe Datei / `PreviewOrderStore` | `overview`, `page`, `detail` | Derselbe DTO-Vertrag wie die echten Seiten, Filter vor Pagination und unabhängige Kopien der Ergebnisse. |
| dieselbe Datei / `PreviewOrderStore` | `review`, `validateRequest`, `validateQuantities`, `observed` | Versionen und Mengen prüfen, Request-ID idempotent behandeln, manuelle Gesamtsummen statt doppelter Addition; kein Gateway/DB-Zugriff. |
| `frontend/tests/preview/start.mjs` | HTTP-Handler, `stop` | Bindet nur Loopback, startet dieselbe Next-App auf Port 3030 und setzt ausschließlich für den Kindprozess die Vorschaukonfiguration. Stop beendet beide Dienste. |
| `frontend/components/order-preview-notice.tsx` | `OrderPreviewNotice`, `reset` | Sichtbare Testkennzeichnung auf allen Seiten; Zurücksetzen über denselben Next-Proxy, anschließend Reload. |
| `frontend/app/layout.tsx` | `RootLayout` | Hinweis nur bei explizitem Vorschauflag im Entwicklungsmodus rendern. Produktionsbuild und normaler Start besitzen keinen Fallback. |

Die Testdatenimplementierung ist eine Entwicklungshilfe unter `frontend/tests/preview/`; React-Seiten und deren Tabellen-/Reviewkomponenten wurden nicht kopiert.

## Tests

- `npm run test:preview`: 5 Speichertests und 2 Browserfälle erfolgreich (Desktop und 390×844).
- Speichertests prüfen globalen reservierten Lauf, typspezifische FIFO-Ansichten, Versionsschutz/Idempotenz, widersprüchliche Mengen, Reset und Filter/Pagination.
- Browserfall `bestehende UI zeigt gekennzeichnete Testdaten und temporäre Bewertungen` prüft tatsächliche Seiten/Proxy, Kennzeichnung, Review, Reload und Reset; Screenshot visuell geprüft.
- TypeScript und ESLint der geänderten/neuen Dateien erfolgreich. Produktionsbuild erfolgreich; normaler Browserregressionslauf: 22 Passed, einschließlich fehlender Vorschaukennzeichnung.
- Zuordnung: `Harness/harness/_unittest.md`, Abschnitt „I29 – Expliziter Testdaten-Wrapper“.

## Beziehungen

Diese Entwicklungshilfe belegt keine reale PLC-Abnahme der Hauptspec. Die Hauptspec bleibt wegen der dort dokumentierten Hardware-Nachweise `Modified`.

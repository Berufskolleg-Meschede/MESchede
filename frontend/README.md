# MESchede Frontend

Next.js-App mit den vorhandenen Seiten `/dashboard`, `/production-orders` und `/delivery-orders`. Das Dashboard fasst beide Auftragsarten lesend zusammen. Die Auftragsseiten zeigen Warteschlange, Lauf und Produkteinheiten getrennt und bieten die manuelle Prüfung unklarer Läufe.

## Lokal starten

```bash
npm install
npm run dev
```

Im normalen Betrieb kommen die Auftragsdaten ausschließlich vom FastAPI-Backend. Der serverseitige Proxy `/api/mes/*` verwendet `MES_BACKEND_URL`, standardmäßig `http://127.0.0.1:8000`. Eine Vorlage steht in `.env.example`; bei Bedarf nach `.env.local` kopieren. Im Produktions-Compose wird `http://backend:8000` gesetzt. Browser benötigen nur Zugriff auf das Frontend.

Bei API-Ausfall bleiben letzte Daten mit Fehler-/Aktualitätshinweis sichtbar. Ohne erste Daten erscheinen unbekannte Werte; es gibt keinen automatischen Demodaten-Fallback. Ein Browserreload entfernt keine dauerhaft gespeicherten Reviews.

## Aufträge manuell erfassen (Issue #30)

Auf beiden Auftragsseiten öffnet **Neuer Auftrag** die gemeinsame Erfassung. Sie unterstützt mehrere Produktzeilen mit Menge, getrennte editierbare Vorschläge für Auftrag-ID und PLC-Auftragsnummer sowie eine editierbare Seriennummernstartnummer. Die Seriennummern laufen innerhalb dieses Auftrags über alle Zeilen hinweg fortlaufend. Datum und Uhrzeit kommen aus der Anlagenzeitzone; die Übertragung erfolgt ohne Zeitzonenoffset. Kundennummer ist optional; Priorität und Parameter sind unter **Weitere Angaben** editierbar.

Vor **Auftrag annehmen** zeigt **Auftrag prüfen** den vollständigen Inhalt. Während des Sendens sind Änderungen und Mehrfachbestätigung gesperrt. `202` bestätigt ausschließlich Speicherung und Einreihung. Übersicht und Auftragsdetail werden anschließend unabhängig aktualisiert. Ein verlorenes Requestergebnis oder Reload führt zuerst zum gespeicherten Inhaltsabgleich; eine Wiederholung verändert weder IDs noch Zeitwerte oder Seriennummern.

Die Vorbereitung nutzt `GET /orders/input-context?order_type=production` beziehungsweise `delivery` und liest den persistenten DB-Spiegel des SPS-Katalogs. Der Hintergrundabgleich liest beim Backendstart und anschließend standardmäßig alle 30 Sekunden; **Produktdaten abgleichen** fordert mit `POST /orders/catalog/sync` zusätzlich einen lesenden Abgleich an. Fehler oder ein mehr als 300 Sekunden alter Stand sperren neue Aufträge; gespeicherte Produkte bleiben erhalten. Auch die Auftragsannahme validiert ausschließlich gegen den DB-Katalog.

Am 15.10.2026 wurden der tatsächliche Knoten `DB_MES_Schnittstelle.Produktspezifikation`, die sechs Produkte (IDs 1–6), sämtliche Bauplanfelder und jeweils 33 Queue-Slots an der Anlage lesend bestätigt. Die Anlagenabnahme echter neuer Aufträge bleibt offen. Es gibt keinen Ersatz durch die alten Mock-Artikel. [Spec und Einschränkungen](../docs/specs/issue-30-manual-order-start.md).

Browserprüfungen bauen in `.next/issue30-tests` und starten dort einen eigenen Produktionsserver gegen eine lokale HTTP-Fixture. Der normale Entwicklungsserver und sein Build werden nicht beendet oder ersetzt.

Die Oberfläche verwendet Systemschriften und benötigt beim Start/Build keinen Fontdownload.

## Vorhandene UI mit Testdaten ansehen

```bash
npm run dev:preview
```

Unter [http://127.0.0.1:3030](http://127.0.0.1:3030) erscheint die vorhandene UI mit sechs gekennzeichneten Testaufträgen. Enthalten sind ein prüfbedürftiger Lauf, globale Warteschlange, vollständige/teilweise/unbekannte Mengen sowie abgeschlossene und unterbrochene Beispiele.

Die Vorschau braucht Node.js 22.14 oder neuer, verwendet natives Type-Stripping und startet ihren lokalen Datenserver auf `127.0.0.1:18030`. Kein zusätzlicher Paketdownload, Backend, PostgreSQL oder IoT-Netz nötig. Der Starter setzt die API-Adresse ausschließlich für seinen eigenen Frontendprozess; keine env-Datei wird geändert.

Der Hinweis **Testdaten-Vorschau · simulierte Aufträge** erscheint auf allen Seiten. **Testdaten zurücksetzen** stellt den Anfangszustand wieder her. Bewertungen bleiben über Browserreload erhalten, verschwinden jedoch beim Zurücksetzen oder Beenden des Vorschauprozesses. Neue Starts und Anlagenbereitschaft werden nicht simuliert.

Mit `Ctrl+C` werden Frontend und Testdatenserver gemeinsam beendet. Der normale Start `npm run dev` verwendet die echte Backendadresse. Der Vorschauhinweis wird nur im expliziten Entwicklungsmodus gerendert, nicht im Produktionsbuild.

`npm run test:preview` prüft Speicher, Idempotenz, Konflikte, Suche und die Vorschau im Desktop-/schmalen Browser.

## Prüfen

```bash
npm run build
npx playwright install chromium
npm run test:e2e
```

Playwright startet ausschließlich lokale Testserver auf `127.0.0.1:3029` und `127.0.0.1:18029`. Browserfixtures sind im Testordner und sprechen keine PLC an. Desktop- und schmale Layouts prüfen getrennte Queues, Reload, Tastatur, Review ohne Notiz, Konflikte, idempotente Wiederholung, Quellenfehler, Backendfilter und den echten Next-HTTP-Proxy. Testartefakte liegen ignoriert unter `test-results/`.

ESLint wird gemäß Harness nur für tatsächlich geänderte TS-/TSX-Dateien ausgeführt. Die Nachweise und die noch ausstehende Anlagenabnahme stehen in [der Feature-Spezifikation](../docs/specs/issue-29-order-production-overview.md).

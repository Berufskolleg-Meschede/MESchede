# MESchede Frontend

Next.js-App mit den vorhandenen Seiten `/dashboard`, `/production-orders` und `/delivery-orders`. Das Dashboard fasst beide Auftragsarten lesend zusammen. Die Auftragsseiten zeigen Warteschlange, Lauf und Produkteinheiten getrennt und bieten die manuelle Prüfung unklarer Läufe.

## Lokal starten

```bash
npm install
npm run dev
```

Im normalen Betrieb kommen die Auftragsdaten ausschließlich vom FastAPI-Backend. Der serverseitige Proxy `/api/mes/*` verwendet `MES_BACKEND_URL`, standardmäßig `http://127.0.0.1:8000`. Eine Vorlage steht in `.env.example`; bei Bedarf nach `.env.local` kopieren. Im Produktions-Compose wird `http://backend:8000` gesetzt. Browser benötigen nur Zugriff auf das Frontend.

Bei API-Ausfall bleiben letzte Daten mit Fehler-/Aktualitätshinweis sichtbar. Ohne erste Daten erscheinen unbekannte Werte; es gibt keinen automatischen Demodaten-Fallback. Ein Browserreload entfernt keine dauerhaft gespeicherten Reviews. Manuelle Erstellung und Auslösung bleiben Issue 30.

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

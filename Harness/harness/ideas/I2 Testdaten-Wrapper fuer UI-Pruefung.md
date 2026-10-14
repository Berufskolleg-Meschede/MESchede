# Testdaten-Wrapper für UI-Prüfung

## Meta

- **Typ:** Idee
- **State:** Specified
- **Geltungsbereich:** Optionale lokale Prüfung der bestehenden Issue-29-Oberfläche.

## Zweck

Die Oberfläche ohne Produktionsdaten mit aussagekräftigen Auftrags- und Laufzuständen ansehen und manuelle Bewertungen ausprobieren.

## Kontext

Die bestehenden Seiten verwenden echte API-Abfragen und zeigen bei fehlendem Backend keine erfundenen Aufträge. Der Benutzer möchte jetzt ausdrücklich einen Testdaten-Wrapper; zuvor stellte er klar, dass keine separate UI-Kopie gewünscht ist.

## Quellen

- Benutzer: „kannst du doch irgendwie ein testdata wrapper machen damit ich das besser sehen und prüfen kann?“
- `frontend/app/layout.tsx`, `frontend/lib/api.ts`, `frontend/tests/order-fixtures.ts`.

## Inhalt

### Ursprünglicher Prompt

Optionalen Testdaten-Wrapper erstellen, um die bestehende UI ohne IoT-/Produktionsdaten zu prüfen.

### Kritische Bewertung

#### 1. Welche Oberfläche wird verwendet?

**Antwort:** Die bestehenden Seiten und Komponenten, gemäß Benutzerwunsch; der Wrapper ersetzt ausschließlich die Datenquelle und ergänzt eine erkennbare Vorschaukennzeichnung.

#### 2. Welche Prüfungen sollen möglich sein?

**Antwort:** Warteschlange, Lauf/Produkteinheiten, bekannte/unkannte Mengen, Dashboard, Suche/Filter und manuelle Bewertung. Zurücksetzen erlaubt wiederholte Prüfung.

#### 3. Welche Grenzen gelten für Testaktionen?

**Antwort:** Nur temporäre Daten im Speicher; keine PLC-/DB-Verbindung, keine echte Auftragssteuerung. Expliziter Start statt automatischem Fallback. Dies ergibt sich aus der bestehenden Spec und dem fehlenden IoT-Netz.

### Entscheidung

Specified. Der Benutzer hat die Erstellung ausdrücklich beauftragt; keine zusätzliche fachliche Entscheidung nötig.

### Abgeleitete Specs

- `../../../docs/specs/issue-29-ui-preview.md`.

## Beziehungen

- **Voraussetzung:** Bestehende Issue-29-Auftragsoberfläche.
- **Ergänzt:** `../../../docs/specs/issue-29-order-production-overview.md`.
- **Ergebnis:** Optionaler Entwicklungsstart mit Testdaten.

## Offene Punkte

- Keine fachlichen Entscheidungen offen. Umsetzung und lokale Verifikation folgen.

## Pflege

- **Aktualisierung:** Bei Änderungen des API-Vertrags oder Vorschauverhaltens.
- **Ablösung:** Durch ausdrücklich beauftragten anderen Entwicklungsablauf.

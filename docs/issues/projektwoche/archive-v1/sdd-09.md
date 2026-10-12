# [SDD-09] Frontend-Datenvertrag und API-Zugriff vereinheitlichen

<!-- meschede-projektwoche-v1:SDD-09 -->
## Ziel

Alle Frontend-Seiten benutzen denselben typisierten Vertrag und eine NAS-taugliche API-Adresse.

## Einordnung

- Bereich: Frontend; Schätzung: 2 Teamstunden.
- Anforderungen: REQ-01, REQ-08, REQ-09.
- Abhängigkeiten: SDD-01
- Spezifikation: `docs/specs/projektwoche-mes-ui.md` (Arbeitsfassung v0.1; im Sammel-Issue vollständig enthalten).
- Einstieg im Code: `frontend/lib/api.ts`, `lib/api-client.ts`, `lib/types.ts`, `hooks/use-orders.ts`, bestehende Status-Badges

## Umsetzung

- Doppelte API-Schichten und widersprüchliche Groß-/Kleinschreibung bereinigen; ID als Zeichenfolge und gemischte Queue korrekt typisieren.
- Relative API-Basis bzw. vereinbarte NAS-Konfiguration verwenden; zentrale Fehler-/Lade-/Refreshlogik schaffen.
- Mocks nur über ausdrücklich aktivierten, sichtbaren Demo-Modus; Vertragsfixtures für parallele Entwicklung nutzen.
- Bestehende fehlende Typen/Imports/Dependencies, soweit sie Build und diese Seiten blockieren, anhand der Paketdateien bereinigen.

## Akzeptanzkriterien

- [ ] Alle relevanten Seiten verwenden denselben API-Vertrag und dieselben Statuswerte.
- [ ] NAS-Betrieb ruft keine hardcodierte localhost-Adresse auf.
- [ ] API-Ausfall aktiviert keine Mockdaten; Demo-Daten sind als solche erkennbar.
- [ ] Typecheck, Lint und Produktionsbuild laufen durch oder vorhandene unabhängige Blocker sind konkret dokumentiert und SDD-17 zugeordnet.

## Nachweis und Review

Frontend-Typecheck/Lint/Build; Browser-Netzwerkaufruf prüfen und Fehlerfixture darstellen. Aufwand nach Bestandsprüfung überprüfen.

Vor Implementierung den relevanten Vertrag aus SDD-01/02 lesen. Änderungen an Fachregeln zuerst in Spec und Issue festhalten. PR referenziert dieses Issue und die REQ-IDs; Akzeptanznachweise und Dokumentation gehören zum Abschluss. Eine Person übernimmt, eine zweite prüft. Schätzung nach dem Anlagen-Spike bei Bedarf aktualisieren.

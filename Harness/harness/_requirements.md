# Bugfix-Spec-Konventionen

Regeln für die Dokumentation ausgereifter Bugfixes. Unter `spec/` werden ausschließlich Bugfix-Specs abgelegt. Ideen, Arbeitsanweisungen, Testkataloge und UI-/UX-Wissen verbleiben unter `harness/`.

Die vorgelagerte Ideenbewertung ist ausschließlich in `_idea.md` geregelt.

## Ordner- und Dateistruktur

```text
spec/
└── B{n} {Bugfix-Name}.md
```

- `B` bezeichnet einen Bugfix.
- Die Nummerierung startet bei 1.
- Neue Bugfix-Specs werden hinten angehängt.
- Bestehende Nummern bleiben stabil.
- Die Nummer wird nicht zusätzlich im Titel wiederholt.
- Es werden keine allgemeinen Leitlinien, Ideen oder Katalogdateien unter `spec/` abgelegt.

## Bugfix-Spec-Format

Jede Bugfix-Spec folgt dieser Struktur:

```markdown
# {Bugfix-Titel}

## Meta

- **State:** Modified | Implemented
- **Idee:** {relativer Pfad zur auslösenden Idee}

## User Story

Als {Rolle} möchte ich {korrigiertes Verhalten}, damit {Nutzen}.

## Description

Kurze fachliche Beschreibung des betroffenen Verhaltens und der Abgrenzung. Keine technische Lösung.

## Ist-Verhalten

Das aktuell belegte fehlerhafte Verhalten der Anwendung.

## Soll-Verhalten

Das nach dem Bugfix erwartete, von außen beobachtbare Verhalten.

## Reproduktion

1. {Ausgangszustand}
2. {Aktion}
3. {Beobachtbares fehlerhaftes Ergebnis}

## Akzeptanzkriterien

- …
- …

## Angepasste Methoden

### `{MethodName}`

- **Datei:** {tatsächlicher relativer Pfad}
- **Typ:** {tatsächlicher Klassen- oder Typname}
- **Aufgabe:** {fachlich-technische Verantwortung der Methode}
- **Änderung:** {was durch den Bugfix geändert wurde}
- **Erkenntnis:** {wiederverwendbares Wissen über Verhalten, Abhängigkeiten oder Seiteneffekte}
- **Bezug:** {betroffenes Akzeptanzkriterium}

## Tests

- {Verweis auf den Eintrag in `harness/_unittest.md`}

## UI-/UX-Erkenntnisse

- {Verweis auf den Eintrag in `harness/_uiux.md` oder „Keine“}
```

## Meta-Block und State

| State | Bedeutung |
|---|---|
| `Modified` | Die Spec ist neu oder wurde inhaltlich geändert; die Implementierung entspricht ihr noch nicht nachweislich. |
| `Implemented` | Spec, Anwendungscode, Methodendokumentation und erforderliche Tests sind synchron. |

- Jede inhaltliche Änderung einer `Implemented`-Spec setzt den State auf `Modified`.
- Reine Codeänderungen ohne Spec-Änderung verändern den State nicht.
- Werden Spec und Code gemeinsam angepasst und vollständig geprüft, wird der State direkt auf `Implemented` gesetzt.
- Bei unklarem Synchronstand bleibt der State `Modified`.
- Der State wird bei jeder Spec-Bearbeitung ausdrücklich geprüft.

## Regeln für Bugfix-Verhalten

- Das Ist-Verhalten beschreibt ausschließlich belegte Beobachtungen.
- Die Reproduktion enthält den kleinsten zuverlässig nachvollziehbaren Ablauf.
- Das Soll-Verhalten beschreibt das fachlich erwartete Ergebnis, nicht die technische Lösung.
- Mindestens ein Akzeptanzkriterium bildet den ursprünglichen Fehlerfall als Regressionstestfall ab.
- Relevante Randfälle werden als eigene atomare Akzeptanzkriterien dokumentiert.
- Vermutete Ursachen gehören in die Ideenbewertung oder technische Analyse, nicht in fachliche Akzeptanzkriterien.
- Bereits korrektes Verhalten außerhalb des Fix-Umfangs darf durch die Änderung nicht beeinflusst werden.

## Dokumentation angepasster Methoden

- Jede im Rahmen des Bugfixes inhaltlich angepasste Methode wird erfasst.
- Reine Formatierungsänderungen werden nicht erfasst.
- Methodenname, Typ und Dateipfad werden aus dem tatsächlichen Code übernommen und nicht vorab erfunden.
- Die Aufgabe beschreibt die Verantwortung der Methode im Anwendungskontext.
- Die Änderung beschreibt nur den konkreten Bugfix, nicht den vollständigen Quellcode.
- Die Erkenntnis hält wiederverwendbares Wissen über Datenfluss, Zustände, Aufrufbeziehungen, Seiteneffekte oder Fehlerbehandlung fest.
- Wenn mehrere Methoden dieselbe Erkenntnis tragen, bleiben ihre jeweiligen Verantwortungen getrennt dokumentiert.
- Entfernte Methoden werden mit ihrem letzten tatsächlichen Namen sowie dem Grund der Entfernung erfasst.
- Der Abschnitt wird erst nach der Codeänderung vervollständigt und anschließend gegen den Diff geprüft.

## Akzeptanzkriterien nach INVEST

Akzeptanzkriterien sind:

- **Independent:** möglichst unabhängig; notwendige Abhängigkeiten werden ausdrücklich benannt.
- **Negotiable:** sie beschreiben Verhalten statt Implementierungsdetails.
- **Valuable:** jedes Kriterium liefert fachlichen oder nutzerbezogenen Mehrwert.
- **Estimable:** der Umfang ist ausreichend konkret abschätzbar.
- **Small:** jedes Kriterium enthält genau eine prüfbare Aussage.
- **Testable:** jedes Kriterium besitzt ein eindeutiges Pass/Fail-Ergebnis.

### Formulierungsbeispiele

- Gut: „Nach dem Bestätigen bleibt der Dialog geöffnet, wenn das Backend die Änderung ablehnt.“
- Gut: „Die Fehlermeldung des Backends ist im Dialog sichtbar.“
- Gut: „Nach erfolgreichem Speichern zeigt die Ansicht den aktualisierten Wert.“
- Schlecht: „Fehler werden korrekt behandelt.“
- Schlecht: „Speichern, Validierung und Anzeige funktionieren.“
- Schlecht: „Die Methode verwendet einen zusätzlichen Null-Check.“

## Abgrenzung UI und Backend

Fachlogik, Validierung und Eindeutigkeitsprüfungen werden als Backend-Verhalten formuliert. Das UI beschreibt nur Eingabe, Anzeige und Reaktion auf das Backend-Ergebnis.

Clientseitige Validierung darf als UX-Hilfe spezifiziert werden. Ist dieselbe Regel fachlich relevant, wird sie client- und serverseitig validiert; das Backend bleibt autoritativ.

## Felder, Entitäten und technische Namen

- Feldnamen werden in Backticks und in der Schreibweise des bestehenden Codes beziehungsweise Datenmodells notiert.
- Methoden-, Typ- und Event-Namen werden in Backticks notiert.
- Enum-Werte werden in Backticks und mit ihrem tatsächlichen Wert notiert.
- Nicht im Bestand belegte Namen, IDs, Endpunkte oder Events dürfen nicht erfunden werden.

## Abgleich mit der Anwendung

- Vor einer Spec wird der betroffene Anwendungscode untersucht.
- Bestehende Tests und relevante Dokumentation werden berücksichtigt.
- Abweichungen zwischen Idee und aktuellem Verhalten werden ausdrücklich dokumentiert.
- Nach der Implementierung werden die Akzeptanzkriterien gegen Code und Tests geprüft.
- Der Abschnitt „Angepasste Methoden“ wird gegen die tatsächlichen Änderungen geprüft.
- Erst nach erfolgreichem Gesamtabgleich erhält die Bugfix-Spec den State `Implemented`.

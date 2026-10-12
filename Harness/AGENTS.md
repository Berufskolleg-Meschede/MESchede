# Idea-to-Spec-Harness

Diese Datei steuert den Arbeitsablauf von KI-Assistenten und Entwicklern in diesem Repository. Sie wird im Projektstamm abgelegt und von KI-Werkzeugen als Projektanweisung gelesen.

## Projektparameter

Beim Einrichten in einem neuen Projekt werden diese Werte einmalig festgelegt. Unbekannte Werte bleiben `{offen}` und werden nicht erfunden.

- **Projektsprache** (Kommunikation, Dokumentation, Kommentare, Exception-Meldungen): {z. B. Deutsch}
- **Namespace-Präfix** (`Firma.Produkt`): {MES}
- **Build-Befehl:** {z. B. `dotnet build`}
- **Test-Befehl:** {z. B. `dotnet test`, `npm test`}
- **Lint-/Format-Befehl:** {z. B. `npm run lint`, `dotnet format` oder „keiner“}
- **Harness einchecken:** {ja}

## Verpflichtend

Diese Dokumente werden bei jeder Bearbeitung berücksichtigt:

- [Übersicht] <harness/README.md>
- [Ideen] <harness/\_idea.md>
- [Spezifikationen] <harness/\_requirements.md>
- [Dokumentvorlage] <harness/\_template.md>
- [UI/UX] <harness/\_uiux.md>
- [Unit Tests] <harness/\_unittest.md>
- [Coderichtlinien] <harness/\_codeguidelines.md>

## Geltungsbereich

- Diese Datei steuert den Arbeitsablauf in diesem Repository.
- Kommunikation, Dokumentation und Kommentare erfolgen in der Projektsprache; Code-Bezeichner bleiben US-Englisch.
- Bestehender Anwendungscode ist bei Analyse und Dokumentation die maßgebliche Quelle für das aktuelle Verhalten.
- IDs, Versionen, Branches, Komponenten, Reviewer, Work-Items, Zugangsdaten und Befehle dürfen nicht erfunden werden.
- Git-Schreibaktionen (Commit, Push, Branch, Tag, Rebase) erfolgen nur nach ausdrücklichem Auftrag.

## Bugfixes

- Ein Bugfix dokumentiert beobachtetes Ist-Verhalten, erwartetes Soll-Verhalten, Reproduktion und betroffenen Umfang.
- Die drei kritischen Fragen prüfen Ursache beziehungsweise Abgrenzung, erwartetes Verhalten und Regressionsrisiko.
- Akzeptanzkriterien beschreiben das korrigierte, von außen prüfbare Verhalten.
- Testbares Verhalten wird durch passende Unit Tests abgesichert.
- Neue oder angepasste Unit Tests werden mit ihrer Spec-Zuordnung in `harness/_unittest.md` erfasst.
- Neu verstandenes UI-/UX-Verhalten wird in `harness/_uiux.md` dokumentiert.
- Jede durch den Bugfix angepasste Methode wird mit ihrer tatsächlichen Aufgabe und der gewonnenen Erkenntnis in der zugehörigen Spec erfasst.
- Relevante Tests, Build und Lint werden ausgeführt; Ausnahmen werden benannt.
- Der Linter wird nur für geänderte oder neue Dateien ausgeführt.

## Codeänderungen

- Änderungen bleiben minimal, aufgabenbezogen und folgen bestehenden Patterns.
- Die Coderichtlinien (`harness/_codeguidelines.md`) werden vollständig eingehalten, insbesondere die vorgeschriebene XML-Dokumentation für Klassen, Methoden, Properties und weitere Member.
- Verstöße gegen die Coderichtlinien in bestehendem, nicht geändertem Code werden mit Regel-Nr. und Fix-Vorschlag gemeldet, aber nicht ungefragt korrigiert.
- Zusätzliche erklärende Code-Kommentare werden nur bei Bugfixes ergänzt und dokumentieren den Grund für den Fix.
- Sobald Code und Spec nachweislich übereinstimmen, wird der Spec-State in derselben Session auf `Implemented` gesetzt.

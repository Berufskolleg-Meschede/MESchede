# Ideen-Konventionen

Regeln für die Erfassung, kritische Bewertung und Reifung von Ideen vor ihrer Überführung in fachliche Specs.

## Grundsatz

Jeder neue Prompt wird zunächst als Idee behandelt. Eine Idee wird erst dann zu einer Spec, wenn sie nach kritischer Bewertung fachlich sinnvoll, ausreichend abgegrenzt und ohne wesentliche offene Entscheidungen umsetzbar ist.

Eine Idee ist noch keine Umsetzungsfreigabe. Vor der Reifeentscheidung werden bestehender Anwendungscode, Tests und vorhandene Dokumentation als Quellen für das aktuelle Verhalten geprüft.

## Idea-to-Spec-Ablauf

- Alle unter „Verpflichtend“ in `AGENTS.md` aufgeführten Dokumente werden bei jeder Bearbeitung berücksichtigt.
- Neue Markdown-Dokumente unter `harness/` folgen `_template.md` sowie den zusätzlichen Regeln ihres Dokumenttyps.
- Unter `spec/` werden ausschließlich Bugfix-Specs abgelegt; Leitlinien und sonstige Harness-Dateien sind dort unzulässig.
- Erst nach einer ausgereiften Spec wird eine Implementierung vorgenommen.

## Ablauf

1. Der ursprüngliche Prompt wird unter `harness/ideas/` dokumentiert.
2. Der aktuelle Stand und der betroffene Anwendungsbereich werden belegt.
3. Es werden genau drei kritische Fragen formuliert und beantwortet.
4. Nicht belegbare Annahmen werden ausdrücklich als offen gekennzeichnet.
5. Wesentliche offene fachliche Entscheidungen werden vor der Spec-Erstellung geklärt.
6. Eine ausgereifte Idee wird gemäß `_requirements.md` in eine oder mehrere Specs überführt.
7. Die abgeleiteten Specs werden in der Idee verlinkt und ihr State wird auf `Specified` gesetzt.

## Kritische Bewertung

Die drei Fragen decken mindestens diese Perspektiven ab:

1. Welche fachliche Ursache, Abgrenzung oder konkrete Fehlersituation liegt vor?
2. Welches beobachtbare Verhalten wird erwartet und welchen Nutzen erzeugt es?
3. Welche Auswirkungen, Randfälle und Regressionsrisiken müssen berücksichtigt werden?

Antworten werden aus Prompt, Anwendungscode, Tests und bestehender Dokumentation abgeleitet. Vermutungen werden nicht als Tatsachen dargestellt.

## Reifekriterien

Eine Idee ist reif für eine Spec, wenn:

- Problem und betroffener Umfang nachvollziehbar beschrieben sind,
- Ist- und Soll-Verhalten voneinander abgegrenzt sind,
- die drei kritischen Fragen belastbar beantwortet sind,
- wesentliche Randfälle und Regressionsrisiken bekannt sind,
- keine offene Entscheidung die Akzeptanzkriterien grundlegend verändern kann,
- der erwartete Nutzen die Änderung rechtfertigt.

Ist mindestens ein Reifekriterium nicht erfüllt, bleibt die Idee `New` oder `Assessed`. Eine fachlich ungeeignete Idee wird mit Begründung `Discarded`.

## Ideen-Format

Ideen verwenden `harness/_template.md` mit den dort definierten zusätzlichen Ideenabschnitten und werden wie folgt abgelegt:

```text
harness/ideas/I{n} {Ideen-Name}.md
```

- Die Nummerierung startet bei 1.
- Neue Ideen werden hinten angehängt.
- Bestehende Nummern bleiben stabil.
- Die Nummer wird nicht im Titel wiederholt.

## State-Werte

| State | Bedeutung |
|---|---|
| `New` | Die Idee wurde erfasst, aber noch nicht vollständig bewertet. |
| `Assessed` | Genau drei kritische Fragen wurden beantwortet; mindestens eine für die Spec relevante Klärung ist noch offen. |
| `Specified` | Die Idee erfüllt die Reifekriterien und wurde in mindestens eine verlinkte Spec überführt. |
| `Discarded` | Die Idee wird mit dokumentierter Begründung nicht weiterverfolgt. |

## Regeln für Bugfix-Ideen

- Das beobachtete Fehlverhalten und der kleinste bekannte Reproduktionsweg werden festgehalten.
- Erwartetes Verhalten wird von einer vermuteten technischen Lösung getrennt.
- Die Bewertung grenzt den betroffenen Umfang und bereits korrektes Nachbarverhalten ab.
- Mindestens eine Antwort behandelt das Risiko, bestehendes Verhalten unbeabsichtigt zu verändern.
- Technische Ursachen werden nur als belegt bezeichnet, wenn sie anhand des Codes oder eines reproduzierbaren Tests nachgewiesen wurden.


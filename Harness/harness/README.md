# Lokales Harness

Dieses Verzeichnis enthält verbindliche Regelwerke, Vorlagen, Ideen und Wissenskataloge für den Idea-to-Spec-Ablauf. Projektabhängige Werte stehen in `AGENTS.md` im Projektstamm.

## Ablauf

1. Prompt als Idee erfassen.
2. Idee mit genau drei kritischen Fragen und Antworten bewerten.
3. Offene fachliche Entscheidungen klären.
4. Akzeptierte Idee in eine Spec unter `spec/` überführen.
5. Änderung implementieren und testen.
6. Spec und Implementierung abgleichen und den State pflegen.

Neue Markdown-Dokumente verwenden `_template.md`. Regelwerke und Vorlagen mit führendem `_` sind verbindlich. Unter `spec/` liegen ausschließlich ausgereifte Bugfix-Specs.


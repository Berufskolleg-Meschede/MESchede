# Allgemeine Harness-Dokumentvorlage

Diese Vorlage gilt für neue Markdown-Dokumente unter `harness/`. Nicht anwendbare optionale Abschnitte werden entfernt. Verbindliche Abschnitte bleiben erhalten.

# {Dokumenttitel}

## Meta

- **Typ:** Regelwerk | Vorlage | Idee | Katalog | Wissen
- **State:** Draft | Active | Superseded
- **Geltungsbereich:** {betroffener Arbeitsablauf oder Anwendungsbereich}

Für Ideen werden stattdessen die State-Werte aus `_idea.md` verwendet.

## Zweck

{Welches Problem löst dieses Dokument und wie wird es verwendet?}

## Kontext

{Belegter Ausgangszustand, betroffener Bereich und notwendige Abgrenzung}

## Quellen

- {Prompt, relativer Codepfad, Test, bestehende Dokumentation oder reproduzierbare Beobachtung}

Nicht belegbare Annahmen werden ausdrücklich als offen gekennzeichnet.

## Inhalt

{Regeln, Erkenntnisse, Katalogeinträge oder die für den Dokumenttyp vorgeschriebenen Abschnitte}

## Beziehungen

- **Voraussetzung:** {relativer Pfad oder „Keine“}
- **Ergänzt:** {relativer Pfad oder „Keine“}
- **Ergebnis:** {relativer Pfad oder „Noch keines“}

## Offene Punkte

- {offener Punkt oder „Keine“}

## Pflege

- **Aktualisierung:** {Ereignis, bei dem dieses Dokument geprüft oder fortgeschrieben wird}
- **Ablösung:** {Bedingung oder Nachfolgedokument}

## Zusätzliche Abschnitte für Ideen

Ideen enthalten unter `## Inhalt` zusätzlich genau diese Struktur:

```markdown
### Ursprünglicher Prompt

{Prompt unverändert oder sinngemäß dokumentieren}

### Kritische Bewertung

#### 1. {Frage zur fachlichen Abgrenzung oder Ursache}

**Antwort:** {Belegte Antwort oder klar gekennzeichneter offener Punkt}

#### 2. {Frage zum erwarteten Verhalten und Nutzen}

**Antwort:** {Belegte Antwort oder klar gekennzeichneter offener Punkt}

#### 3. {Frage zu Auswirkungen, Risiken oder Regressionen}

**Antwort:** {Belegte Antwort oder klar gekennzeichneter offener Punkt}

### Entscheidung

{Specified, Discarded oder weitere Klärung erforderlich; mit kurzer Begründung}

### Abgeleitete Specs

- {Relativer Pfad zur Bugfix-Spec oder „Noch keine“}
```


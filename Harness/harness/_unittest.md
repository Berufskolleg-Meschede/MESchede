# Unit-Test-Konventionen und Testkatalog

Diese Datei erfasst Unit Tests, die aus Specs entstehen oder durch deren Umsetzung angepasst werden. Sie stellt die Nachvollziehbarkeit zwischen Spec, Akzeptanzkriterium und Test sicher.

## Pflege-Regeln

- Für jedes testbare Verhalten einer neuen oder geänderten Spec wird geprüft, ob ein passender Unit Test existiert.
- Neu angelegte und fachlich angepasste Unit Tests werden in dieser Datei erfasst.
- Rein technische Refactorings bestehender Tests ohne Verhaltensänderung werden nicht aufgenommen.
- Ein Eintrag wird angelegt, sobald der Testbedarf aus der Spec bekannt ist.
- Der State wird nach Implementierung und erfolgreicher Ausführung aktualisiert.
- Nicht durch Unit Tests abdeckbare Kriterien erhalten eine Begründung und die vorgesehene andere Prüfart.
- Testnamen und Dateipfade werden ausschließlich aus der tatsächlichen Implementierung übernommen und nicht vorab erfunden.

## State-Werte

| State | Bedeutung |
|---|---|
| `Planned` | Der Testbedarf ist aus der Spec abgeleitet, aber noch nicht umgesetzt. |
| `Implemented` | Der Test ist implementiert, wurde jedoch noch nicht erfolgreich ausgeführt. |
| `Passed` | Der Test wurde in der aktuellen Implementierung erfolgreich ausgeführt. |
| `NotApplicable` | Ein Unit Test ist ungeeignet; Begründung und alternative Prüfung sind dokumentiert. |

## Eintragsformat

Für jeden durch eine Spec entstehenden oder geänderten Test wird dieser Block ergänzt:

```markdown
## {Fachliches Testziel}

- **Spec:** {relativer Pfad zur Bugfix-Spec}
- **Akzeptanzkriterium:** {eindeutige, kurze Wiedergabe}
- **State:** Planned | Implemented | Passed | NotApplicable
- **Testdatei:** {tatsächlicher relativer Pfad oder „Noch nicht vorhanden“}
- **Test:** {tatsächlicher Testname oder „Noch nicht vorhanden“}
- **Prüft:** {beobachtbares Verhalten}
- **Ausführung:** {ausgeführter Testbefehl und Ergebnis oder „Noch nicht ausgeführt“}
- **Hinweis:** {Randfall, Begründung oder „Keiner“}
```

## Testkatalog

> Einträge werden bei jeder Spec-Umsetzung am Ende ergänzt. Der folgende Eintrag ist ein Platzhalter-Beispiel und wird beim ersten echten Eintrag ersetzt.

## {Fachliches Testziel}

- **Spec:** `spec/B1 {Bugfix-Name}.md`
- **Akzeptanzkriterium:** {eindeutige, kurze Wiedergabe}
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** {beobachtbares Verhalten}
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Keiner

## RabbitMQ-Bestandsereignisse

- **Spec:** Keine; neues Feature, erfasst in `harness/ideas/I2 Lagerbestände per RabbitMQ übernehmen.md`.
- **Akzeptanzkriterium:** Snapshots und Änderungen werden validiert und doppelte Ereignisse verändern den Bestand nicht erneut.
- **State:** Implemented
- **Testdatei:** `backend/tests/test_storage_consumer.py`
- **Test:** `test_snapshot_persists_stock_and_duplicate_is_ignored`, `test_delta_without_snapshot_does_not_assume_zero`, `test_invalid_delta_is_rejected`, `test_message_id_can_supply_missing_event_id`
- **Prüft:** Persistenz, Idempotenz, unbekannte Basisbestände und Pflichtfelder des Vertragsentwurfs.
- **Ausführung:** Noch nicht ausgeführt; die Sitzung enthält weder pytest noch SQLModel.
- **Hinweis:** Die Gruppenschnittstelle ist noch unbestätigt; Tests prüfen den dokumentierten Vertragsentwurf.

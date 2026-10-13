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

## I29 – Auftragsidentität und wiederholte Annahme

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-18, AC-19: identische Annahme ohne zweiten Lauf; abweichender Inhalt ist Konflikt.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Gleiche fachliche ID bei unterschiedlichem Auftragstyp; gleiche und abweichende Payloads, auch nach Wiederanlauf.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Backend-Verhaltenstests; konkrete Testnamen erst aus der Implementierung übernehmen.

## I29 – Eindeutige Produkteinheiten und Ergebnismengen

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-07 bis AC-11: getrennte Mengen, Korrelation, keine Doppelzählung und unvollständige Ergebnisse.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Wiederholte Resultate, wiederverwendete PLC-Slots, fremde Läufe, unbekannte Ergebnisse und gemischte Gut-/Fehlresultate.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Verifizierte PLC-Vertragsbeispiele als Fixtures; keine erfundenen Statuscodes.

## I29 – Globaler Startausschluss und FIFO

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-16, AC-17: höchstens ein Dispatch; ältester angenommener Auftrag zuerst.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Gleichzeitige Anforderungen beider Worker, gemischte Reihenfolge, gleiche Annahmezeit und ignorierte Produktions-/Lieferpriorität.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Zusätzlich Integrationstest für konkurrierende API-Aufrufe und dauerhaft gespeicherte Reihenfolge.

## I29 – Persistenz über Prozessneustart

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-14, AC-15, AC-20: Aufträge, Reihenfolge und mögliche Übergabe bleiben nachvollziehbar.
- **State:** NotApplicable
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Neustart mit wartenden Aufträgen und Unterbrechung zwischen möglichem Startschreiben und Bestätigung.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Unit Tests allein können echte Persistenz über Prozessneustart nicht belegen; PostgreSQL-/Prozessintegration erforderlich.

## I29 – Wiederanlaufabgleich ohne Doppelstart

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-12, AC-13, AC-21: Annahme/Idle sind kein Abschluss; aktiver korrelierter Lauf wird nicht erneut gestartet.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Aktiver korrelierter Auftrag, sehr kurzer Lauf, fehlender Abschlussnachweis, fremder Auftrag und verlorene Verbindung.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Vorhandene Handshaketests bleiben Regressionseinstieg; simulierte PLC plus reale Abnahme erforderlich.

## I29 – Globale Reviewsperre und Bereitschaft

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-22 bis AC-24: beide Startarten blockiert bis zur Prüfung und bestätigter PLC-Bereitschaft.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Produktionsreview sperrt Lieferung und umgekehrt; mehrere offene Reviews; Review erledigt bei weiterhin aktiver oder unbekannter PLC.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Alle Aufrufwege müssen dieselbe backendseitige Sperre respektieren.

## I29 – Review ohne Pflichtnotiz und gültige Mengen

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-27 bis AC-29: Bewertung und Mengen ohne Erklärung speicherbar; ungültige Angaben abgelehnt.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Bekannte/unkannte Mengen, negative und gebrochene Werte, Sollmengenüberschreitung und Widerspruch zu belegten PLC-Mengen.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Unfertige Einheiten gelten nicht automatisch als Fehlteile; Erfolg setzt Gutmenge nicht automatisch auf Sollmenge.

## I29 – Review ohne Steuerungsbefehl oder Doppelzählung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-30, AC-32, AC-40: Review steuert PLC nicht; Wiederholung/Konkurrenz überschreiben Ergebnisse nicht unbemerkt.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Kein Start/Stop/Reset beim Review; wiederholtes Speichern und konkurrierende Änderung derselben Bewertung.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Konkurrierende Speicheraufrufe zusätzlich mit Datenbankintegration prüfen.

## I29 – Resultatsicherung vor Quittierung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-39: verfügbare Endresultate werden vor möglichem Verlust durch MES-Quittierung dauerhaft gesichert.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Laufende mit nach Reset verschwindenden Resultaten; fehlgeschlagene Speicherung darf keinen stillen Datenverlust erzeugen.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** PLC-Simulator für Reihenfolge, PostgreSQL-Integration für Speicherbestätigung und Anlagenprüfung für tatsächlichen Datenlebenszyklus.

## I29 – Quellenstatus und Aktualität

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-33 bis AC-36: gültige Resultate bleiben erhalten; Fehllesen erneuert keine Aktualität; stale/unknown bleiben erkennbar.
- **State:** Planned
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Fehllesen, Reconnect, Zeitüberschreitung der konfigurierten Grenze, fehlende Erstbeobachtung und teilweise verfügbare Quelle.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Kontrollierte Uhr; keine echte Wartezeit nötig. Sichtbare UI-Kennzeichnung zusätzlich im Browser prüfen.

## I29 – Seitenstruktur, Dashboard und Datenzustände

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-01 bis AC-06, AC-25, AC-26, AC-31, AC-37: getrennte Seiten, lesendes Dashboard, persistenter Prüfhinweis und Quellenkennzeichnung.
- **State:** NotApplicable
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Produktions-/Lieferansicht, Warte-/Produktqueue-Trennung, Dashboardlinks, manuell markierte Mengen, Reload und API-Ausfall ohne stillen Mock-Fallback.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** UI-/Browserprüfungen statt reiner Backend-Unit-Tests; bekannte/fehlende Daten jeweils prüfen.

## I29 – Tastatur und responsive Bedienung

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-38: Prüfung, Navigation und Tabelleninteraktion sind per Tastatur bedienbar.
- **State:** NotApplicable
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Fokusreihenfolge, Reviewdialog, Beschriftungen, Linkziele und Tabellen auf Projektgeräten.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Manuelle Browser-/Geräteprüfung; Unit Tests allein belegen Bedienbarkeit nicht.

## I29 – Reale PLC-Korrelation und Laufabnahme

- **Spec:** `../../docs/specs/issue-29-order-production-overview.md`
- **Akzeptanzkriterium:** AC-08, AC-10, AC-13, AC-20, AC-21, AC-24, AC-39: verifizierte Identitäten, Übergänge und Resultatsicherung.
- **State:** NotApplicable
- **Testdatei:** Noch nicht vorhanden
- **Test:** Noch nicht vorhanden
- **Prüft:** Realer Produktions- und Lieferlauf, kurze Läufe, alte Resultate, Abbruch/Reconnect/Neustart sowie Bereitschaft beider Slots.
- **Ausführung:** Noch nicht ausgeführt
- **Hinweis:** Anlagenprotokoll mit erwarteten/tatsächlichen Werten erforderlich. Keine Live-Abnahme allein aufgrund simulierter Tests.

# Wiederaufnahme und manuelle Prüfung von Auftragsläufen

## Meta

- **Typ:** Wissen
- **State:** Superseded
- **Geltungsbereich:** Fachliche Entscheidungsvorlage für Issue #29; Stand 2026-10-13, keine Implementierungsfreigabe.

## Zweck

Eine konkrete Empfehlung für die gemeinsame Entscheidung zur Wiederaufnahme unterbrochener Produktions- und Lieferläufe festhalten. Bestätigte Anforderungen und noch offene Vorschläge bleiben unterscheidbar.

Die Beratung ist abgeschlossen. Maßgeblich ist jetzt `../../../docs/specs/issue-29-order-production-overview.md`. Der Benutzer hat die globale Startsperre bis zur Prüfung und die gemeinsame FIFO-Reihenfolge bestätigt. Eine erforderliche Erklärung wurde ausdrücklich abgelehnt; das Review erfasst Laufbewertung und Mengen. Die folgende Beratung bleibt als Entscheidungsherkunft erhalten.

## Kontext

Der Benutzer hat getrennte Produktions- und Lieferseiten, ein ausschließlich lesendes Dashboard, getrennte Gut-/Fehlmengen und Abgleich vor manueller Prüfung bestätigt. Manuelles Auslösen von Aufträgen wird in einem separaten Issue bearbeitet. Als verbindliche MES-Betriebsregel soll Produktion nicht gleichzeitig mit Kommissionierung laufen. Dies ist eine vorsichtige Projektentscheidung; die tatsächliche Fähigkeit der Anlage zum Parallelbetrieb ist nicht nachgewiesen.

Aktuell starten die beiden Worker unabhängig voneinander und prüfen jeweils ihren eigenen PLC-Slot. Ein Backend-Abbruch unterbricht seine Beobachtung; daraus folgt kein belegter physischer Abbruch des PLC-Laufs. Die Anwendung darf deshalb einen offenen Lauf nach Wiederanlauf nicht allein aus dem Prozesszustand als fehlgeschlagen oder erfolgreich behandeln.

## Quellen

- Benutzerantworten im Gespräch zu Issue #29, einschließlich Abgrenzung manueller Starts und Entscheidung gegen Parallelbetrieb.
- `../ideas/I1 Auftrags- und Produktionsuebersicht Issue 29.md`
- `../../../backend/app/workers/production_queue.py`
- `../../../backend/app/workers/delivery_queue.py`
- `../../../backend/app/workers/plc_handshake.py`
- `../../../docs/opc-ua-integration.md`
- `../../../docs/issues/projektwoche/manual.md`

## Inhalt

### Bestätigte Anforderungen

- Produktion und Lieferung besitzen getrennte Seiten; das Dashboard kombiniert ihre Zusammenfassungen und bleibt lesend.
- Manuelle Auftragserstellung und Auslösung gehören zum separaten Issue. Pause, Abbruch und Wiederholung sind in dieser Entscheidungsvorlage nicht als neue Steuerungsaktionen vorgesehen.
- Gut- und Fehlmengen werden im MES anhand bestätigter PLC-Produktresultate getrennt erfasst. Wiederholte Beobachtungen zählen nicht mehrfach.
- Laufzustand und wartende Aufträge bleiben nach Neustart erhalten.
- Vor erneutem Schreiben wird ein möglicherweise gestarteter Lauf mit der PLC abgeglichen. Verbleibende Unklarheit erfordert Operatorprüfung.
- Der MES-Betrieb erlaubt höchstens einen Produktions- oder Lieferlauf gleichzeitig; physische Parallelfähigkeit bleibt ungeprüft.

### Empfohlener Ablauf nach Neustart oder Verbindungsverlust

Die folgenden Regeln sind Vorschläge zur Bestätigung, keine bereits vereinbarte Spezifikation.

1. Vor einem möglichen Start bleibt dauerhaft nachvollziehbar, welcher Auftrag und Lauf an welchen Slot übergeben werden soll. Der Zustand muss auch einen Absturz zwischen Startschreiben und Bestätigung abdecken.
2. Ein Backend-Neustart beginnt mit Abgleich offener Läufe und beider PLC-Slots. Ein Browserreload verändert keinen Laufzustand und sendet keinen Startbefehl.
3. Eine passende, eindeutig identifizierte PLC-Rückmeldung erlaubt Fortsetzung der Beobachtung oder Abschluss des bisherigen Laufs. Ein fremder Auftrag, fehlende Rückmeldung oder Idle ohne belastbare Abschlussinformation beweist keinen erfolgreichen Lauf.
4. Bei verbleibender Unklarheit bleibt der Lauf prüfbedürftig. Empfohlen ist, weitere MES-Starts beider Auftragsarten zu blockieren, solange ein möglicherweise aktiver Lauf nicht geklärt und die Anlage nicht nachweislich bereit ist.
5. Beim nächsten Öffnen der Oberfläche wird Prüfbedarf prominent angezeigt. Das Dashboard verlinkt zur zuständigen Auftragsseite; dort erfolgt die Prüfung. Wegklicken oder Reload erledigt die Prüfung nicht.
6. Eine manuelle Bewertung verändert die dokumentierte Einschätzung des Laufs. Sie startet, stoppt oder quittiert die PLC nicht. Der nächste Lauf darf erst nach geklärtem bisherigen Lauf und bestätigter Bereitschaft starten.

### Entscheidungstabelle

| Beobachtung nach Abgleich | Empfohlenes Verhalten |
| --- | --- |
| Passender Auftrag läuft nachweislich weiter | Bisherigen Lauf weiter beobachten; kein erneutes Startschreiben. |
| Passender Auftrag ist nachweislich beendet | Verfügbare Endresultate dauerhaft erfassen, bevor sie durch Quittierung oder den nächsten Auftrag verloren gehen können; verifizierten Handshake fortsetzen. |
| Auftrag wurde nachweislich noch nicht übergeben und die Anlage ist bereit | Als wartend erhalten; keine manuelle Erfolgsentscheidung nötig. |
| PLC ist Idle, aber ein möglicherweise gestarteter Lauf besitzt keinen belastbaren Abschlussnachweis | Manuelle Prüfung verlangen; Idle allein ist kein Abschlussnachweis. |
| PLC nicht erreichbar, fremder Auftrag oder widersprüchliche Identität | Letzte gültige Werte mit Quellenproblem anzeigen; keine automatische Wiederholung und keine erfundenen Endmengen. |

Ein bestätigtes Laufende bedeutet nicht automatisch, dass alle Einheiten erfolgreich waren. Gut-/Fehlerergebnis und Laufende werden getrennt beurteilt.

### Empfohlenes Reviewformular

- Sichtbarer Auftragstyp, fachliche ID, PLC-Auftragsnummer, letzter beobachteter Zustand, bekannte Gut-/Fehlmengen, letzte erfolgreiche Beobachtung und Grund des Prüfbedarfs.
- Auswahl: Lauf beendet; Lauf fehlgeschlagen beziehungsweise unterbrochen; Ergebnis weiterhin unbekannt.
- Bekannte endgültige Gut-/Fehlmengen optional erfassen; unbekannte Mengen bleiben ausdrücklich unbekannt. Unfertige Einheiten sind nicht automatisch Fehlteile.
- Keine erforderliche Notiz oder Erklärung. Laufbewertung, bekannte Mengen und Erfassungszeitpunkt festhalten. Eine Operatoridentität wird nur erfasst, wenn sie tatsächlich verfügbar ist; eine neue Anmeldung ist hier nicht automatisch im Umfang.
- PLC-belegte Fakten bleiben erhalten. Manuelle Angaben sind als solche gekennzeichnet. Konflikte mit späteren PLC-Resultaten bleiben sichtbar und werden nicht stillschweigend überschrieben.
- Eine manuelle Gesamtmenge ersetzt keine vorhandenen Einzelresultate und wird nicht zusätzlich auf sie addiert. Fehlen Einzelresultate, darf die UI keine fiktiven Seriennummern oder Produktergebnisse erzeugen.
- Bei weiterhin unbekanntem Ergebnis bleibt die Prüfung offen. Ein abgeschlossenes Review bewahrt seinen Verlauf; Browserreload und wiederholtes Speichern erzeugen keine weiteren Mengen.

### Vorschläge für prüfbare Akzeptanzkriterien

Diese Kriterien sind eine Diskussionsgrundlage und werden nach Entscheidung in die Feature-Spezifikation übernommen.

- Ein Backend-Neustart verliert keine dauerhaft angenommenen wartenden Aufträge.
- Ein Backend-Neustart sendet für einen möglicherweise gestarteten Lauf keinen erneuten Startbefehl ohne geklärten Ausführungsstand.
- Bei eindeutig zugeordnetem weiterlaufendem Auftrag wird die Beobachtung des bisherigen Laufs fortgesetzt.
- Ein Idle-Rohwert ohne korrelierten Abschlussnachweis erzeugt keine Erfolgsmeldung.
- Ein PLC-Verbindungsfehler verändert bekannte Produktresultate nicht.
- Ein ungeklärter möglicherweise aktiver Produktionslauf verhindert einen neuen Lieferstart; umgekehrt gilt dieselbe Regel.
- Ein Operatorreview löst keinen PLC-Steuerungsbefehl aus.
- Eine manuelle Erfolgsentscheidung setzt unbekannte Gutmengen nicht automatisch auf die Sollmenge.
- Erneutes Lesen desselben Produktresultats verändert Gut-/Fehlmengen nicht.
- Ein Browserreload bewahrt ungelösten Prüfbedarf.
- Das Dashboard bietet nur einen Link zur Prüfung; die Bewertung erfolgt auf der zuständigen Auftragsseite.
- Nach geklärtem Lauf bleibt ein neuer Start blockiert, solange die PLC-Bereitschaft nicht bestätigt ist.

## Beziehungen

- **Voraussetzung:** `../ideas/I1 Auftrags- und Produktionsuebersicht Issue 29.md`
- **Ergänzt:** `../../../docs/issues/projektwoche/overview.md`
- **Ergebnis:** `../../../docs/specs/issue-29-order-production-overview.md`

## Offene Punkte

- PLC-Vertrag für eindeutige Lauf-/Produktidentität, Endresultate und Bereitschaft beider Slots; am realen System zu prüfen.
- Aktualisierungs-/Veraltungsgrenzen und praktische UI-Abnahme; weitere Pflege in der Feature-Spec.

## Pflege

- **Aktualisierung:** Nach Benutzerentscheidungen und nach verifizierten PLC-Vertragsbeispielen.
- **Ablösung:** Durch die verlinkte Feature-Spezifikation erfolgt; State `Superseded`.

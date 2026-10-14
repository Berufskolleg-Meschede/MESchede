# Coderichtlinien (C#)

## Meta

- **Typ:** Regelwerk
- **State:** Active
- **Geltungsbereich:** Alle neu geschriebenen oder geänderten C#-Dateien im Repository, einschließlich Unit Tests. Für andere Sprachen (z. B. TypeScript, JavaScript) gilt ausschließlich Regel 58; im Übrigen gilt dort der Linter bzw. Formatter des Projekts.

## Zweck

Dieses Dokument fasst die Coderichtlinien als ein einziges verbindliches Regelwerk zusammen. Es wird bei jeder Codeänderung, jedem Review und jeder Codeerklärung angewendet. Die Regeln sind fortlaufend nummeriert; Verstoßmeldungen verweisen auf die Regel-Nr.

## Kontext

Die Richtlinien bestehen aus 66 Einzelregeln in neun Kategorien und gelten unabhängig von einem bestimmten Projekt. Projektabhängige Werte (Projektsprache, Namespace-Präfix, Projektstruktur) werden in `AGENTS.md` festgelegt. Die Regeln werden vollständig eingehalten, insbesondere die XML-Dokumentation. Die Nummerierung bleibt stabil: Neue Regeln werden hinten angehängt, entfallene Regeln bleiben als „entfallen“ erhalten.

## Quellen

- Coderichtlinien (vollständiger Regelsatz mit 66 Regeln in neun Kategorien)

Auslegungen bei Mehrdeutigkeiten sind unter „Festgelegte Auslegungen“ dokumentiert.

## Inhalt

### Anwendung

- Neuer und geänderter Code hält alle Regeln vollständig ein. Bei Konflikt mit bestehenden Mustern im Code haben die Richtlinien Vorrang.
- Bestehender, nicht geänderter Code wird nicht ungefragt umgebaut. Verstöße darin werden gemeldet: `Regel {Nr}: {relativer Pfad}:{Zeile} – {Fix-Vorschlag}`. Dies gilt auch in Reviews und Erklärungen, ohne dass danach gefragt wurde.
- Bestehende Verstöße werden nicht vergrößert. Neue Logik wird in eine eigene regelkonforme Methode ausgelagert, statt eine bereits zu lange Methode (Regel 9) oder einen bereits zu komplexen Ausdruck (Regel 22) zu erweitern.
- Generierter Code (EF-Migrationen, `*.Designer.cs`, generierte API-Clients) wird nicht angepasst.
- XML-Dokumentation (Regel 53) und regelpflichtige Kommentare (Regel 11, 25) sind verpflichtend und zählen nicht als überflüssige erklärende Kommentare. Alle Kommentare stehen in der Projektsprache (Regel 66); Bezeichner sind US-Englisch (Regel 29).

### 1. Klassen-Design

| Nr. | Regel |
|---|---|
| 1 | Eine Klasse oder ein Interface hat genau einen Zweck (Single Responsibility). Ein „And“ im Namen ist ein Warnsignal. |
| 2 | Keine statischen Klassen oder Methoden. Ausnahmen: Klassen für Erweiterungsmethoden (Suffix `Extension`, siehe Regel 31), `Program.Main` (Regel 23) und statische Factory-Methoden (Regel 63). |
| 3 | Die Compiler-Warnung CS0114 wird nie mit `new` unterdrückt; stattdessen wird mit `override` überschrieben. |
| 4 | Basisklassen kennen ihre abgeleiteten Klassen nicht (keine `is`-Prüfungen oder Casts auf Subtypen). Unterschiedliches Verhalten wird über `virtual` oder `abstract` ausgedrückt. |
| 5 | Keine bidirektionale Abhängigkeit zwischen zwei Klassen. Eine Seite wird über ein Interface entkoppelt, typischerweise per Dependency Injection. |

### 2. Eigenschaften-Design

| Nr. | Regel |
|---|---|
| 6 | Properties sind in beliebiger Reihenfolge setzbar. Setter haben keine Seiteneffekte und lösen keine Logik aus, die andere Properties voraussetzt. |
| 7 | Eine Property, Methode oder lokale Funktion erfüllt genau eine Aufgabe. |
| 8 | Methoden geben keine veränderbaren Collections (`List<T>`, Arrays) zurück, sondern `IReadOnlyList<T>`, `IReadOnlyCollection<T>` oder `IEnumerable<T>`. |

### 3. Wartbarkeit

| Nr. | Regel |
|---|---|
| 9 | Eine Methode hat höchstens 30 Anweisungen (Warnung ab 20, Fehler ab 30). Längere Methoden werden in klar benannte Methoden zerlegt. |
| 10 | Auf `if`, `else`, `do`, `while`, `for`, `foreach` und `switch` folgt immer ein `{}`-Block, auch bei einer einzelnen Anweisung. |
| 11 | Jeder `switch` hat einen `default`-Block. Ist er fachlich unnötig, erklärt ein Kommentar darin, warum. Darf er nie erreicht werden, wird eine Exception geworfen (z. B. `InvalidOperationException`). |
| 12 | Jede `if-else-if`-Kette endet mit `else`. Darf dieser Fall nie eintreten, wird eine Exception geworfen. |
| 13 | Einfache bedingte Zuweisungen erfolgen direkt oder ternär (`bool isPositive = value > 0;`), nicht mit `if-else`. |
| 14 | Keine doppelten Negierungen. Eine negativ benannte Property (`HasNoOrders`) wird nicht mit `!` negiert; stattdessen wird die positive Property (`HasOrders`) verwendet. |
| 15 | Boolesche Ausdrücke werden nie mit `true` oder `false` verglichen: `if (!isAvailable)`, `while (condition)`. |
| 16 | Eine Quelldatei enthält genau einen Typ. Ausnahme: Typen, die sich nur in der Anzahl ihrer generischen Parameter unterscheiden (`Repository` und `Repository<T>`). |
| 17 | Typen werden per `using` eingebunden, nicht vollqualifiziert. Bei Namenskonflikt wird ein Alias vergeben (`using Label = System.Web.UI.WebControls.Label;`). |
| 18 | Jede Variable wird in einer eigenen Anweisung zugewiesen. Keine Kettenzuweisungen (`a = b = Get();`). |
| 19 | Es wird der konkrete Typ verwendet, nicht `var`. |
| 20 | Kein `dynamic`; stattdessen statisch typisierte Modelle oder Interfaces. |
| 21 | Zeichenfolgen werden mit `$"..."` zusammengesetzt, nicht mit `string.Format`, `+` oder `string.Concat`. Ausnahme: Resource-Strings dürfen mit `string.Format` formatiert werden. |
| 22 | Ausdrücke und Bedingungen mit drei oder mehr logischen Teilen werden in eine benannte Methode, Property oder lokale Funktion ausgelagert. |
| 23 | Keine Top-Level-Statements. Der Einstieg erfolgt über eine explizite `Program`-Klasse mit `Main`. |
| 24 | Kein auskommentierter Code im Repository. Offene Aufgaben gehören in das Ticketsystem, Historie in die Versionsverwaltung. |
| 25 | Keine leeren Methoden, Interfaces oder Klassen. Folgt die Implementierung später, wird `NotImplementedException` mit erklärendem Kommentar geworfen. |
| 26 | Code bleibt debugbar. Verschachtelte Aufrufe wie `A(B(C()))` werden in Einzelschritte mit Zwischenvariablen zerlegt. |
| 27 | Kein `goto`. |
| 28 | Kein `this`. Namenskonflikte werden durch eindeutige Bezeichner vermieden. |

### 4. Namenskonventionen

| Nr. | Regel |
|---|---|
| 29 | Alle Bezeichner sind sprechendes, grammatikalisch korrektes US-Englisch. Keine Begriffe anderer Sprachen, keine Kollision mit Schlüsselwörtern gängiger Sprachen. |
| 30 | Casing und Präfixe gemäß der Tabelle „Casing“ unten. Basisklassen tragen das Präfix `Base`. |
| 31 | Klassen tragen ihre Rolle als Suffix und enthalten nur die dafür zulässigen Methoden (Tabelle „Klassenrollen“ unten). |
| 32 | Projekte werden nach Rolle benannt und in festen Ordnern organisiert (Tabelle „Projektstruktur“ unten). Gibt das Projekt eine eigene Struktur vor, gilt diese; die Tabelle ist die Vorgabe für neue Projekte. |
| 33 | Keine Zahlen in Bezeichnern: `primaryEmail` und `secondaryEmail` statt `email1` und `email2`. |
| 34 | Keine Feld-Präfixe wie `m`, `m_`, `s_` oder `g_`. Ausnahme: die in Regel 30 definierten Präfixe (`_` für private Felder). |
| 35 | Bezeichner werden nach Bedeutung benannt, nicht nach Typ: `customers` statt `customerListArray`, `filePath` statt `strFileName`. Collections tragen Pluralnamen. |
| 36 | Typen heißen wie Nomen, Nominal- oder Adjektivphrasen. `Utility`, `Utilities` und `Helper` sind verboten. |
| 37 | Der Name einer Klasse oder Enumeration wird in ihren Membernamen nicht wiederholt: `Employee.Delete()` statt `Employee.DeleteEmployee()`. |
| 38 | Properties heißen wie Nomen oder Nominalphrasen. Boolesche Properties sind positiv formuliert mit `Is`, `Has` oder `Can`. Eine Enum-Property darf wie ihr Enum-Typ heißen (`CacheLevel CacheLevel`). |
| 39 | Events enden auf `-ing` (vor der Aktion) oder `-ed` (nach der Aktion): `Closing`, `Closed`. Kein `Before`, `After`, `Begin` oder `End`. |
| 40 | Event-Handler-Methoden beginnen mit `On`: `OnClosing`, `OkButtonOnClick`. Nicht `HandleClosing` oder `okButton_Click`. |
| 41 | Methoden und lokale Funktionen, die `Task` oder `Task<T>` zurückgeben, enden auf `Async`. |
| 42 | Jedes Member und jeder Typ hat einen expliziten Zugriffsmodifizierer. |
| 43 | Namespaces beginnen mit dem in `AGENTS.md` festgelegten Präfix `Firma.Produkt`. Ein Namespace enthält nie einen Typnamen; Plural-Nomen (`Collections`) sind erlaubt. |
| 44 | Assembly, Dateiname und Namespace stimmen überein: `Firma.Produkt.Web.Binding.dll` für `Firma.Produkt.Web.Binding`. Ausnahme: Enthält eine Assembly mehrere unabhängige Namespaces, endet sie auf `.Core`; dieses Suffix steht nie im Namespace. |
| 45 | Der Dateiname entspricht dem Typnamen in PascalCase, ohne Unterstriche und ohne Generics-Angabe (`List.cs`, nicht `ListOfT.cs`). |
| 46 | Dateien eines `partial`-Typs werden nach ihrer logischen Funktion benannt: `MyClass.cs`, `MyClass.Designer.cs`; nicht `Part1.cs`. |

#### Casing (Regel 30)

| Sichtbarkeit | Sprachelement | Casing | Präfix | Beispiel |
|---|---|---|---|---|
| Private | Method, Local function, Local variable, Parameter, Tuple-Variable | camelCase | – | `formatText()`, `typeName` |
| Private | Field, Static readonly field | camelCase | `_` | `_listItem`, `_redValue` |
| Non-private | Namespace, Type parameter, Class, Struct, Enum, Enum member, Resource key | PascalCase | – | `System.Drawing`, `TView`, `FatalError` |
| Non-private | Interface | PascalCase | `I` | `IBusinessService` |
| Non-private | Field, Property, Event, Method, Tuple element | PascalCase | – | `MainPanel`, `BackColor`, `Click` |
| Alle | Constant field (auch private) | UPPER_SNAKE_CASE | – | `MAXIMUM_ITEMS` |

Bei Mehrdeutigkeit gilt die höherstehende Kategorie der Tabelle (Private vor Non-private).

#### Klassenrollen (Regel 31)

| Suffix | Zulässige Methoden |
|---|---|
| `Manager` | `Update`, `Add`, `Remove`, `Get*` |
| `Validator` | `Validate`, `ValidateFor*` |
| `Calculator` | `Calculate*` |
| `Factory` | `Create`, `Create*` |
| `Context` | Entity-Framework-`DbContext` |
| `Cloner` | `Clone`, `Clone*` |
| `Workflow` | `Run` |
| `Exception` | Fehlerklassen |
| `Cache` | `Get`, `Set`, `IsCached`, `Invalidate`, `Remove` |
| `Mapper` | `Map`, `MapTo*` |
| `Logger` | `LogInfo`, `LogError`, `LogFatal`, `LogDebug`, `LogWarn` |
| `DataProvider` | `Get*`, `Insert`, `Delete`, `Update` |
| `Sender` | `Send`, `SendTo*` |
| `Extension` | Statische Erweiterungsmethoden |
| `Analyser` | `Get*` |
| `Parser` | `Parse`, `ParseFrom*` |
| `Renderer` | `Render*` |
| `Converter` | `ConvertTo*` |
| `Controller` | `Update`, `Add`, `Remove`, `Get*` |

#### Projektstruktur (Regel 32)

| Zweck | Ordner | Projekt-Suffix | Beispiel |
|---|---|---|---|
| Benutzeroberfläche | `UI` | `Client` | `ProductClient` |
| Domänenlogik | `Logic\Domain` | `Management` | `CustomerManagement` |
| Domänen-Interfaces | `Logic\Domain` | `Management.Contract` | `CustomerManagement.Contract` |
| Workflows | `Logic\Workflow` | `Workflow` | `OrderProcessingWorkflow` |
| Mapping und DI-Konfiguration | `Infrastructure` | `Mapping` | `ApplicationMapping` |
| Datenzugriff | `Data` | `Storage` | `InvoiceStorage` |
| Datenzugriff-Interfaces | `Data` | `Storage.Contract` | `InvoiceStorage.Contract` |
| Modelle und Datenklassen | `CrossCutting` | `Models` | `CustomerModels` |

### 5. Performance

| Nr. | Regel |
|---|---|
| 47 | Bei `IEnumerable<T>` wird `Any()` statt `Count() > 0` verwendet. |
| 48 | `async`/`await` wird nie mit `Task.Wait()` oder `Task.Result` kombiniert (Deadlock-Gefahr). |
| 49 | Der asynchrone Fluss bleibt durchgängig; kein Mischen mit blockierendem Zugriff über `.Result` oder `.Wait()`. |

### 6. Framework

| Nr. | Regel |
|---|---|
| 50 | C#-Aliase (`int`, `string`, `object`) statt `System`-Typen (`Int32`, `String`, `Object`), auch bei statischen Members (`int.Parse`). |
| 51 | Sprachsyntax statt Implementierungstypen: `(string, int)`, `DateTime?` und `int[]` statt `ValueTuple<…>`, `Nullable<T>` und `Int32[]`. |
| 52 | Umgebungsabhängige Strings (Verbindungszeichenfolgen, Serveradressen, API-Keys) werden nie hardcodiert. Sie kommen aus `appsettings.json`, `app.config`, `web.config`, `ConfigurationManager`, Resources oder der generierten `Settings`-Klasse. Keine eigenen Konfigurationsstrukturen. |

### 7. Dokumentation

| Nr. | Regel |
|---|---|
| 53 | Alle `public`, `protected`, `private` und `internal` Klassen, Interfaces, Methoden, Properties und Felder erhalten XML-Dokumentation (mindestens `/// <summary>`). |
| 66 | Alle Kommentare im Code stehen in der in `AGENTS.md` festgelegten Projektsprache: Zeilenkommentare (`//`), Blockkommentare (`/* */`), XML-Dokumentation (`///`) und Hinweise in allen Sprachen des Projekts, auch in Unit Tests. Bezeichner bleiben US-Englisch (Regel 29). Exception-Meldungen sind keine Kommentare und fallen unter Regel 64. |

### 8. Layout

| Nr. | Regel |
|---|---|
| 54 | Höchstens 130 Zeichen pro Zeile; lange Ausdrücke werden umbrochen. |
| 55 | Einrückung mit 4 Leerzeichen, keine Tabs. |
| 56 | Nach Schlüsselwörtern (`if`, `while`, `for`, `switch`) steht genau ein Leerzeichen; kein Leerzeichen nach `(` oder vor `)`. |
| 57 | Binäre Operatoren (`+`, `-`, `==`, `<` usw.) sind von Leerzeichen umgeben. |
| 58 | C#: `{` und `}` stehen jeweils in einer eigenen Zeile. Ausnahme: Auto-Property oder Event ohne Body einzeilig. TypeScript und JavaScript: `{` in derselben Zeile wie die Deklaration (K&R), `}` in einer eigenen Zeile. |
| 59 | Objekt- und Collection-Initializer werden nicht zusätzlich eingerückt; jede Property steht in einer eigenen Zeile. |
| 60 | Lambda-Blöcke werden nicht zusätzlich eingerückt: `=>` steht am Zeilenende, `{` in der nächsten Zeile auf der Einrückung der Anweisung, die das Lambda enthält (siehe Beispiel unten). |
| 61 | LINQ-Abfragen stehen in einer Zeile oder haben alle Schlüsselwörter auf gleicher Einrückung. Alle `from` stehen zusammen am Anfang, nicht vermischt mit `where`. |
| 62 | `using`-Direktiven sind alphabetisch sortiert (z. B. `Firma.Produkt…`, `Microsoft…`, `Newtonsoft…`, `System…`). |
| 63 | Member-Reihenfolge: (1) `private`, (2) `protected`, (3) `public` Felder und Konstanten; (4) bis (6) `private`, `protected`, `public` `static readonly` Felder; (7) bis (9) `private`, `protected`, `public` Properties; (10) Konstruktoren; (11) Events; (12) Factory-Methoden; (13) bis (15) `private`, `protected`, `public` Methoden. |

#### Layout-Beispiele (Regel 58 bis 61)

```csharp
public void Execute()
{
    if (isValid)
    {
        Run();
    }
    else
    {
        Handle();
    }
}

public string Value { get; set; } = "default";
public event EventHandler Clicked;
```

```ts
private execute(): void {
    if (isValid) {
        run();
    } else {
        handle();
    }
}
```

```csharp
ConsumerDto dto = new ConsumerDto
{
    Id = 123,
    Name = "Microsoft",
    ShoppingCart =
    {
        ["VisualStudio"] = 1
    }
};

methodThatTakesAnAction.Do(source =>
{
    // Hier erfolgt die Verarbeitung.
});

Product[] query =
    from product in products
    where product.Price > 10
    select product;
```

### 9. Anderes

| Nr. | Regel |
|---|---|
| 64 | Eine Exception-Meldung ist in der Projektsprache verfasst und nennt den Grund und was zur Behebung zu tun ist (Beispiel Deutsch): `"Die E-Mail-Adresse des Benutzers darf nicht null sein. Bitte eine gültige E-Mail-Adresse angeben."` Mehrsprachigkeit muss jederzeit nachrüstbar sein: Meldungen sind vollständige, in sich geschlossene Sätze mit Platzhaltern für dynamische Werte, werden nicht aus Satzteilen zusammengesetzt und dürfen in Resources abgelegt werden (Regel 21 erlaubt dort `string.Format`). |
| 65 | In Anwendungslogik wird weder `catch (Exception)` noch `catch (SystemException)` verwendet. Allgemeine Ausnahmen darf nur der globale Fehlerbehandler der obersten Ebene abfangen (Logging, sauberer Shutdown). |

### Festgelegte Auslegungen

Bei Mehrdeutigkeiten der Regeln gelten diese Entscheidungen verbindlich:

| Regel | Entscheidung |
|---|---|
| 30, 34 | Private Felder tragen das Präfix `_` (`_listItem`). |
| 30 | Alle Konstanten, auch private, sind `UPPER_SNAKE_CASE`. |
| 2 | Statik ist zusätzlich bei `Program.Main` und statischen Factory-Methoden erlaubt. |
| 60 | Bei Lambda-Blöcken steht `{` in der nächsten Zeile (entspricht Regel 58). |
| 64 | Exception-Meldungen sind in der Projektsprache verfasst und bleiben für Mehrsprachigkeit vorbereitet. |

### Referenzbeispiel

Die Klasse zeigt u. a. die Regeln 8, 10, 11, 19, 26, 28, 30, 53, 62, 63, 64 und 66. Namespace ist weggelassen; Kommentare und Meldungen stehen hier beispielhaft auf Deutsch.

```csharp
using Firma.Produkt.Commerce.Contract;
using System;
using System.Collections.Generic;
using System.Linq;

/// <summary>
/// Verwaltet die Bestellungen eines Kunden.
/// </summary>
public class OrderManager
{
    /// <summary>
    /// Speicher, aus dem die Bestellungen gelesen werden.
    /// </summary>
    private readonly IOrderStorage _storage;

    /// <summary>
    /// Initialisiert eine neue Instanz der <see cref="OrderManager"/>-Klasse.
    /// </summary>
    public OrderManager(IOrderStorage storage)
    {
        _storage = storage;
    }

    /// <summary>
    /// Holt alle offenen Bestellungen des Kunden.
    /// </summary>
    public IReadOnlyList<Order> GetOpenOrders(int customerId)
    {
        IReadOnlyList<Order> orders = _storage.GetOrders(customerId);
        List<Order> openOrders = orders.Where(order => order.IsOpen).ToList();
        return openOrders;
    }

    /// <summary>
    /// Holt den Anzeigetext des Bestellstatus.
    /// </summary>
    public string GetStatusText(OrderState state)
    {
        switch (state)
        {
            case OrderState.Open:
            {
                return "Offen";
            }

            case OrderState.Closed:
            {
                return "Geschlossen";
            }

            default:
            {
                throw new InvalidOperationException(
                    $"Der Bestellstatus '{state}' wird nicht unterstützt. Bitte den Status in GetStatusText ergänzen.");
            }
        }
    }
}
```

## Beziehungen

- **Voraussetzung:** Keine
- **Ergänzt:** `harness/_unittest.md` (Testcode folgt denselben Regeln)
- **Ergebnis:** Noch keines

## Offene Punkte

- Keine

## Pflege

- **Aktualisierung:** Bei Änderungen an den Coderichtlinien, bei neu erkannten Widersprüchen oder Mehrdeutigkeiten (Ergänzung unter „Festgelegte Auslegungen“).
- **Ablösung:** Durch eine neue Fassung der Coderichtlinien; dann wird der State auf `Superseded` gesetzt.

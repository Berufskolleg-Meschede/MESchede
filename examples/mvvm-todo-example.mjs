import assert from "node:assert/strict";

// Das Model enthält nur fachliche Daten: To-do-Aufgaben.
export class TodoModel {
  #todos = [];
  #nextId = 1;

  addTodo(title) {
    const todo = {
      id: this.#nextId++,
      title,
      completed: false,
    };

    this.#todos.push(todo);
    return todo;
  }

  getTodos() {
    // Eine Kopie verhindert, dass die Oberfläche das Model direkt verändert.
    return this.#todos.map((todo) => ({ ...todo }));
  }
}

// Das ViewModel kennt weder HTML-Elemente noch eine konkrete View.
// Es stellt nur Werte und Commands für eine Oberfläche bereit.
export class TodoViewModel {
  #listeners = new Set();

  constructor(model) {
    this.model = model;
    this.newTodoText = ""; // UI-Zustand: Inhalt des Eingabefelds
    this.errorMessage = ""; // UI-Zustand: sichtbare Fehlermeldung
  }

  get canAddTodo() {
    // UI-Zustand: Der Button kann an diesen Wert gebunden werden.
    return this.newTodoText.trim().length > 0;
  }

  get state() {
    return Object.freeze({
      newTodoText: this.newTodoText,
      errorMessage: this.errorMessage,
      canAddTodo: this.canAddTodo,
      todos: this.model.getTodos(),
    });
  }

  subscribe(listener) {
    this.#listeners.add(listener);
    listener(this.state); // Die View erhält sofort den aktuellen Zustand.
    return () => this.#listeners.delete(listener);
  }

  setNewTodoText(text) {
    this.newTodoText = text;
    this.errorMessage = "";
    this.#notify();
  }

  // Ein Command beschreibt eine Absicht der Nutzenden: „Aufgabe hinzufügen“.
  addTodoCommand() {
    const title = this.newTodoText.trim();

    if (!title) {
      this.errorMessage = "Bitte gib eine Aufgabe ein.";
      this.#notify();
      return false;
    }

    this.model.addTodo(title); // Fachliche Daten werden im Model gespeichert.
    this.newTodoText = "";
    this.errorMessage = "";
    this.#notify();
    return true;
  }

  #notify() {
    for (const listener of this.#listeners) {
      listener(this.state);
    }
  }
}

// Diese einfache Konsolen-View repräsentiert die Benutzeroberfläche.
// Sie kennt das ViewModel; die umgekehrte Abhängigkeit existiert nicht.
export class ConsoleTodoView {
  constructor(viewModel) {
    this.viewModel = viewModel;
    this.unsubscribe = viewModel.subscribe((state) => this.render(state));
  }

  typeIntoInput(text) {
    // In einer echten Web-View wäre dies ein input-Event.
    this.viewModel.setNewTodoText(text);
  }

  clickAddButton() {
    // In einer echten Web-View wäre dies ein click-Event.
    return this.viewModel.addTodoCommand();
  }

  render(state) {
    console.log("\n--- View wird gerendert ---");
    console.log(`Eingabe: ${state.newTodoText || "(leer)"}`);
    console.log(`Hinzufügen aktiv: ${state.canAddTodo}`);
    console.log(`Fehler: ${state.errorMessage || "(keiner)"}`);
    console.log(`Aufgaben: ${state.todos.map((todo) => todo.title).join(", ") || "(keine)"}`);
  }
}

function testViewModelWithoutView() {
  const model = new TodoModel();
  const viewModel = new TodoViewModel(model);

  // Das ViewModel lässt sich vollständig ohne Fenster, Browser oder View testen.
  assert.equal(viewModel.addTodoCommand(), false);
  assert.equal(viewModel.errorMessage, "Bitte gib eine Aufgabe ein.");

  viewModel.setNewTodoText("Mathe lernen");
  assert.equal(viewModel.canAddTodo, true);
  assert.equal(viewModel.addTodoCommand(), true);
  assert.deepEqual(model.getTodos(), [
    { id: 1, title: "Mathe lernen", completed: false },
  ]);
}

function runDemo() {
  testViewModelWithoutView();
  console.log("Test ohne View: erfolgreich");

  const model = new TodoModel();
  const viewModel = new TodoViewModel(model);
  const view = new ConsoleTodoView(viewModel);

  view.clickAddButton(); // Fehler wird über den ViewModel-Zustand angezeigt.
  view.typeIntoInput("Präsentation fertigstellen");
  view.clickAddButton(); // Das Command ändert das Model und die View rendert neu.

  view.unsubscribe();
}

runDemo();

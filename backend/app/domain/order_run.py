"""Laufzustände ohne Abhängigkeit von Datenbank, HTTP oder PLC-Bibliothek."""

from dataclasses import dataclass
from enum import StrEnum


class OrderType(StrEnum):
    """Unterscheidet die fachlichen Auftragsarten und ihre PLC-Slots."""

    PRODUCTION = "production"
    DELIVERY = "delivery"


class RunPhase(StrEnum):
    """Beschreibt den belegten Fortschritt eines Laufs einschließlich Reset."""

    QUEUED = "queued"
    PREPARING = "preparing"
    START_PENDING = "start_pending"
    RUNNING = "running"
    COMPLETION_OBSERVED = "completion_observed"
    AWAITING_RESET = "awaiting_reset"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    REVIEW_REQUIRED = "review_required"


class ReviewOutcome(StrEnum):
    """Erlaubt eine Laufbewertung unabhängig von der Qualität einzelner Produkte."""

    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    UNKNOWN = "unknown"


class OrderConflict(ValueError):
    """Kennzeichnet widersprüchliche Identitäten oder konkurrierende Änderungen."""


class InvalidTransition(ValueError):
    """Kennzeichnet einen nicht durch einen Nachweis erlaubten Zustandswechsel."""


@dataclass
class OrderRun:
    """Prüft Laufübergänge; ein Endsignal ist kein Nachweis einer Gutmenge."""

    phase: RunPhase

    def transition_to(self, target: RunPhase) -> None:
        """Ändert den Zustand nur entlang eines belegbaren Fortschritts."""
        transitions = {
            RunPhase.QUEUED: {RunPhase.PREPARING},
            RunPhase.PREPARING: {RunPhase.START_PENDING, RunPhase.QUEUED},
            RunPhase.START_PENDING: {RunPhase.RUNNING, RunPhase.COMPLETION_OBSERVED},
            RunPhase.RUNNING: {RunPhase.COMPLETION_OBSERVED},
            RunPhase.COMPLETION_OBSERVED: {RunPhase.AWAITING_RESET},
            RunPhase.AWAITING_RESET: {RunPhase.COMPLETED},
        }
        if target == self.phase:
            return
        if target == RunPhase.REVIEW_REQUIRED:
            self.phase = target
            return
        if target not in transitions.get(self.phase, set()):
            raise InvalidTransition(
                f"Der Lauf kann nicht von {self.phase} nach {target} wechseln. Bitte den Nachweis prüfen."
            )
        self.phase = target

    @property
    def status(self) -> str:
        """Liefert die fachliche Anzeige ohne Gleichsetzung von Fehler und Verbindungsverlust."""
        if self.phase == RunPhase.REVIEW_REQUIRED:
            return "review_required"
        if self.phase in {RunPhase.COMPLETED, RunPhase.COMPLETION_OBSERVED, RunPhase.AWAITING_RESET}:
            return "completed"
        if self.phase == RunPhase.INTERRUPTED:
            return "error"
        if self.phase == RunPhase.QUEUED:
            return "pending"
        return "in_progress"

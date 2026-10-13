"""Mengenbasierte Operatorbewertungen ohne Abhängigkeit zum PLC-Schreibzugriff."""

from sqlmodel import select

from app.domain.order_run import OrderConflict, ReviewOutcome, RunPhase
from app.models.order_dto import ReviewRequest, ReviewView
from app.models.run_review_record import RunReviewRecord
from app.repositories.order_repository import OrderRepository


class RunReviewService:
    """Persistiert explizite Bewertungen mit Versionsschutz und idempotenter Anfrage-ID."""

    def __init__(self, repository: OrderRepository) -> None:
        """Besitzt bewusst keinen PLC-Gateway und kann keine Anlage steuern."""
        self.repository = repository

    def review(self, run_id: str, request: ReviewRequest) -> ReviewView:
        """Erfasst bekannte Mengen und Laufbewertung ohne Pflichtnotiz."""
        payload = request.model_dump(mode="json")
        with self.repository.transaction() as session:
            self.repository.lock_state(session)
            previous = session.get(RunReviewRecord, str(request.request_id))
            if previous is not None:
                if previous.run_id != run_id or previous.request_payload != payload:
                    raise OrderConflict("Die Review-Anfrage wurde bereits mit anderem Inhalt gespeichert.")
                return self._view(previous)
            run = self.repository.load_run(session, run_id)
            if run.version != request.expected_version:
                raise OrderConflict("Der Lauf wurde inzwischen geändert. Bitte die Ansicht aktualisieren.")
            if not run.review_required:
                raise OrderConflict("Dieser Lauf benötigt keine manuelle Prüfung.")
            units = self.repository.load_units(session, run_id)
            self._validate_quantities(request, units)
            run.manual_good_quantity = request.good_quantity
            run.manual_error_quantity = request.error_quantity
            run.has_manual_review = True
            run.review_required = request.outcome == ReviewOutcome.UNKNOWN
            if not run.review_required:
                run.phase = RunPhase.COMPLETED.value if request.outcome == ReviewOutcome.COMPLETED else RunPhase.INTERRUPTED.value
                run.review_reason = None
            run.version += 1
            record = RunReviewRecord(
                request_id=str(request.request_id), run_id=run_id, outcome=request.outcome.value,
                good_quantity=request.good_quantity, error_quantity=request.error_quantity,
                reviewed_at=self.repository.clock(), request_payload=payload,
            )
            session.add(record)
            return self._view(record)

    def _validate_quantities(self, request: ReviewRequest, units: list) -> None:
        """Verhindert Mengen oberhalb der Planung oder unter bereits belegten Resultaten."""
        quantities = {"good": request.good_quantity, "failed": request.error_quantity}
        for result, amount in quantities.items():
            if amount is not None and (amount > len(units) or amount < sum(unit.result == result for unit in units)):
                raise ValueError("Die Menge widerspricht der Sollmenge oder bereits belegten Produktresultaten.")
        effective_good = request.good_quantity if request.good_quantity is not None else sum(unit.result == "good" for unit in units)
        effective_failed = request.error_quantity if request.error_quantity is not None else sum(unit.result == "failed" for unit in units)
        if effective_good + effective_failed > len(units):
            raise ValueError("Gut- und Fehlmenge dürfen zusammen die Sollmenge nicht überschreiten.")

    def _view(self, record: RunReviewRecord) -> ReviewView:
        """Gibt die tatsächlich gespeicherte Bewertung zurück."""
        return ReviewView(
            request_id=record.request_id, run_id=record.run_id, outcome=record.outcome,
            good_quantity=record.good_quantity, error_quantity=record.error_quantity, reviewed_at=record.reviewed_at,
        )

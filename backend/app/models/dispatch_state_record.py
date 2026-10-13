"""Gemeinsame dauerhafte Koordination beider Auftragsarten."""

from sqlmodel import Field, SQLModel


class DispatchStateRecord(SQLModel, table=True):
    """Serialisiert Annahmereihenfolge und exklusiv reservierten Anlagenlauf."""

    __tablename__ = "dispatch_state"

    id: int = Field(default=1, primary_key=True)
    accepted_sequence: int = 0
    active_run_id: str | None = Field(default=None, foreign_key="order_run.id")
    blocked_reason: str | None = None

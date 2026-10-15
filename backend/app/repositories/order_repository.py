"""Atomare Auftragsannahme, gemeinsame Reservierung und nachvollziehbare Ergebnisse."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Engine, String, cast, func, or_, text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.domain.order_run import OrderConflict, OrderRun, OrderType, RunPhase
from app.models.dispatch_state_record import DispatchStateRecord
from app.models.mes_order import MesOrderRecord
from app.models.order_dto import OrderPayload
from app.models.order_run_record import OrderRunRecord
from app.models.plc_source_state_record import PlcSourceStateRecord
from app.models.product_unit_record import ProductUnitRecord
from app.models.run_review_record import RunReviewRecord


def utc_now() -> datetime:
    """Liefert einen Zeitzonen-bezogenen MES-Beobachtungszeitpunkt."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class StoredOrder:
    """Verbindet einen Auftrag mit genau seinem Lauf und seinen Produkteinheiten."""

    order: MesOrderRecord
    run: OrderRunRecord
    units: tuple[ProductUnitRecord, ...]


@dataclass(frozen=True)
class OrderSnapshot:
    """Erhält Daten aus einer konsistenten lesenden Transaktion."""

    orders: tuple[StoredOrder, ...]
    sources: tuple[PlcSourceStateRecord, ...]
    dispatch: DispatchStateRecord


class OrderRepository:
    """Bündelt Transaktionen; Sessions verlassen ihren Ausführungs-Thread nicht."""

    def __init__(self, engine: Engine, clock: Callable[[], datetime] = utc_now) -> None:
        """Übernimmt Engine und austauschbare Uhr ohne globale Session."""
        self.engine = engine
        self.clock = clock

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Öffnet eine kurzlebige Transaktion und gibt keine abgelaufenen ORM-Objekte zurück."""
        with Session(self.engine, expire_on_commit=False) as session:
            with session.begin():
                yield session

    def initialize(self) -> None:
        """Legt Koordination und Quellen idempotent nach erfolgreicher Migration an."""
        with self.transaction() as session:
            session.execute(insert(DispatchStateRecord).values(id=1, accepted_sequence=0).on_conflict_do_nothing())
            for kind in OrderType:
                session.execute(
                    insert(PlcSourceStateRecord).values(
                        order_type=kind.value, connection_status="unknown",
                    ).on_conflict_do_nothing()
                )

    def lock_state(self, session: Session) -> DispatchStateRecord:
        """Serialisiert Annahme, Laufreservierung und Review in gleicher Lockreihenfolge."""
        state = session.exec(select(DispatchStateRecord).where(DispatchStateRecord.id == 1).with_for_update()).one()
        return state

    def load_run(self, session: Session, run_id: str) -> OrderRunRecord:
        """Lädt einen gesperrten Lauf oder meldet eine unbekannte Referenz."""
        run = session.exec(select(OrderRunRecord).where(OrderRunRecord.id == run_id).with_for_update()).first()
        if run is None:
            raise LookupError("Der angegebene Lauf ist nicht vorhanden.")
        return run

    def load_units(self, session: Session, run_id: str) -> list[ProductUnitRecord]:
        """Liefert die geplanten Einheiten in ihrer Queue-Reihenfolge."""
        return list(session.exec(
            select(ProductUnitRecord).where(ProductUnitRecord.run_id == run_id).order_by(ProductUnitRecord.queue_index)
        ).all())

    def admit(self, kind: OrderType, payload: OrderPayload,
              validate: Callable[[OrderPayload], None] | None = None) -> StoredOrder:
        """Bestätigt gleiche Annahmen erneut und lehnt widersprüchliche Inhalte ab."""
        normalized = payload.mes_auftrag.model_dump(mode="json")
        with self.transaction() as session:
            state = self.lock_state(session)
            existing = session.exec(select(MesOrderRecord).where(
                MesOrderRecord.order_type == kind.value, MesOrderRecord.order_id == payload.order_id,
            )).first()
            if existing is not None:
                if existing.payload != normalized:
                    raise OrderConflict("Die Auftrag-ID ist bereits mit anderen Auftragsdaten belegt.")
                run = session.exec(select(OrderRunRecord).where(OrderRunRecord.order_ref == existing.id)).one()
                return StoredOrder(existing, run, tuple(self.load_units(session, run.id)))
            self._check_plc_number(session, kind, payload.mes_auftrag.kopf.Auftragsnummer)
            if validate is not None:
                validate(payload)
            state.accepted_sequence += 1
            order = MesOrderRecord(
                id=str(uuid4()), order_type=kind.value, order_id=payload.order_id,
                plc_order_number=payload.mes_auftrag.kopf.Auftragsnummer,
                accepted_sequence=state.accepted_sequence, accepted_at=self.clock(), payload=normalized,
            )
            run = OrderRunRecord(id=str(uuid4()), order_ref=order.id, phase_changed_at=self.clock())
            session.add(order)
            session.flush()
            session.add(run)
            session.flush()
            units = self._create_units(run.id, payload)
            session.add_all(units)
            return StoredOrder(order, run, tuple(units))

    def suggest_identifiers(self, kind: OrderType) -> tuple[str, int | None]:
        """Liest unabhängige freie Vorschläge; die Annahmetransaktion reserviert später."""
        with self.transaction() as session:
            rows = session.exec(select(MesOrderRecord.order_id, MesOrderRecord.plc_order_number).where(
                MesOrderRecord.order_type == kind.value,
            )).all()
        ids = {row[0] for row in rows}
        numbers = {row[1] for row in rows}
        candidate = 1
        while str(candidate) in ids:
            candidate += 1
        plc_number = next((value for value in range(1, 65536) if value not in numbers),
                          0 if 0 not in numbers else None)
        return str(candidate), plc_number

    def _check_plc_number(self, session: Session, kind: OrderType, number: int) -> None:
        """Verhindert unbelegte Nummernwiederverwendung innerhalb desselben PLC-Slots."""
        existing = session.exec(select(MesOrderRecord.id).where(
            MesOrderRecord.order_type == kind.value, MesOrderRecord.plc_order_number == number,
        )).first()
        if existing is not None:
            raise OrderConflict(
                "Die PLC-Auftragsnummer wurde in diesem Slot bereits verwendet. Bitte eine eindeutige Nummer wählen."
            )

    def _create_units(self, run_id: str, payload: OrderPayload) -> list[ProductUnitRecord]:
        """Übernimmt geplante Eingabeeinheiten ohne erfundene Produktresultate."""
        return [ProductUnitRecord(
            id=str(uuid4()), run_id=run_id, queue_index=index,
            product_id=item.ProduktID, product_text=item.Produkttext,
            serial_number=item.Seriennummer, sequence_number=item.Sequenznummer,
        ) for index, item in enumerate(payload.mes_auftrag.inhalt.Produktqueue)]

    def snapshot(self) -> OrderSnapshot:
        """Liest Lauf, Einheiten und Sperre ohne gemischte Versionen und ohne PLC-Zugriff."""
        with self.transaction() as session:
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            pairs = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).order_by(MesOrderRecord.accepted_sequence)).all()
            run_ids = [run.id for _, run in pairs]
            units_by_run: dict[str, list[ProductUnitRecord]] = {run_id: [] for run_id in run_ids}
            if run_ids:
                for unit in session.exec(select(ProductUnitRecord).where(
                    ProductUnitRecord.run_id.in_(run_ids),
                ).order_by(ProductUnitRecord.run_id, ProductUnitRecord.queue_index)).all():
                    units_by_run[unit.run_id].append(unit)
            orders = tuple(StoredOrder(order, run, tuple(units_by_run[run.id])) for order, run in pairs)
            sources = tuple(session.exec(select(PlcSourceStateRecord)).all())
            state = session.get(DispatchStateRecord, 1)
            if state is None:
                raise RuntimeError("Auftragsdaten sind nicht initialisiert. Bitte Migration und Workerstart prüfen.")
            return OrderSnapshot(orders, sources, state)

    def active_order(self) -> tuple[StoredOrder | None, DispatchStateRecord]:
        """Liest ausschließlich die aktive Reservierung und ihre Einheiten für den Pollzyklus."""
        with self.transaction() as session:
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            state = session.get(DispatchStateRecord, 1)
            if state is None:
                raise RuntimeError("Auftragsdaten sind nicht initialisiert. Bitte Migration und Workerstart prüfen.")
            if not state.active_run_id:
                return None, state
            pair = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(OrderRunRecord.id == state.active_run_id)).first()
            if pair is None:
                return None, state
            order, run = pair
            stored = StoredOrder(order, run, tuple(self.load_units(session, run.id)))
            return stored, state

    def order_detail(self, kind: OrderType, order_id: str):
        """Lädt genau einen Auftragslauf samt Einheiten und passendem PLC-Quellenstatus."""
        with self.transaction() as session:
            pair = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value, MesOrderRecord.order_id == order_id)).first()
            if pair is None:
                return None
            order, run = pair
            units = tuple(self.load_units(session, run.id))
            source = session.get(PlcSourceStateRecord, kind.value)
            if source is None:
                raise RuntimeError("Die PLC-Quelle ist nicht initialisiert.")
            return StoredOrder(order, run, units), source

    def queue_size(self, kind: OrderType) -> int:
        """Zählt wartende Aufträge eines Typs direkt in der Datenbank."""
        with Session(self.engine) as session:
            return session.exec(select(func.count()).select_from(OrderRunRecord).join(
                MesOrderRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value,
                    OrderRunRecord.phase == RunPhase.QUEUED.value)).one()

    def diagnostics(self, kind: OrderType) -> dict:
        """Liefert Queue-Kennzahlen ohne Laufhistorie oder Produkteinheiten zu laden."""
        with Session(self.engine) as session:
            state = session.get(DispatchStateRecord, 1)
            active_id = None
            if state is not None and state.active_run_id:
                active_id = session.exec(select(MesOrderRecord.order_id).join(
                    OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
                ).where(OrderRunRecord.id == state.active_run_id,
                        MesOrderRecord.order_type == kind.value)).first()
            queued = session.exec(select(func.count()).select_from(OrderRunRecord).join(
                MesOrderRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value,
                    OrderRunRecord.phase == RunPhase.QUEUED.value)).one()
            last_id = session.exec(select(MesOrderRecord.order_id).where(
                MesOrderRecord.order_type == kind.value,
            ).order_by(MesOrderRecord.accepted_sequence.desc()).limit(1)).first()
            completed_id = session.exec(select(MesOrderRecord.order_id).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value,
                    OrderRunRecord.phase == RunPhase.COMPLETED.value).order_by(
                        MesOrderRecord.accepted_sequence.desc()).limit(1)).first()
            return {"queue_size": queued, "current_order_id": active_id,
                    "last_order_id": last_id, "last_completed_order_id": completed_id}

    def page_snapshot(self, kind: OrderType, offset: int, limit: int, search: str, status: str | None):
        """Paginiert Auftragsköpfe in SQL und lädt Einheiten nur für sichtbare/relevante Läufe."""
        phases = {
            "pending": [RunPhase.QUEUED.value],
            "in_progress": [RunPhase.PREPARING.value, RunPhase.START_PENDING.value, RunPhase.RUNNING.value],
            "completed": [RunPhase.COMPLETED.value, RunPhase.COMPLETION_OBSERVED.value, RunPhase.AWAITING_RESET.value],
            "error": [RunPhase.INTERRUPTED.value],
            "review_required": [RunPhase.REVIEW_REQUIRED.value],
        }
        with self.transaction() as session:
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            base = select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value)
            total = session.exec(select(func.count()).select_from(base.subquery())).one()
            query = base
            normalized = search.strip().casefold()
            if normalized:
                pattern = f"%{normalized}%"
                unit_match = select(ProductUnitRecord.id).where(
                    ProductUnitRecord.run_id == OrderRunRecord.id,
                    or_(func.lower(ProductUnitRecord.product_text).like(pattern),
                        cast(ProductUnitRecord.product_id, String).like(pattern)),
                ).exists()
                query = query.where(or_(func.lower(MesOrderRecord.order_id).like(pattern),
                                        cast(MesOrderRecord.plc_order_number, String).like(pattern), unit_match))
            if status is not None:
                query = query.where(OrderRunRecord.phase.in_(phases[status]))
            filtered_total = session.exec(select(func.count()).select_from(query.subquery())).one()
            selected = session.exec(query.order_by(MesOrderRecord.accepted_sequence).offset(offset).limit(limit)).all()
            state = session.get(DispatchStateRecord, 1)
            if state is None:
                raise RuntimeError("Auftragsdaten sind nicht initialisiert. Bitte Migration und Workerstart prüfen.")
            summary_rows = session.exec(select(OrderRunRecord.phase, func.count()).join(
                MesOrderRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(MesOrderRecord.order_type == kind.value).group_by(OrderRunRecord.phase)).all()
            summary = {phase: count for phase, count in summary_rows}
            context_pairs = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(or_(OrderRunRecord.review_required.is_(True),
                        OrderRunRecord.phase == RunPhase.QUEUED.value,
                        OrderRunRecord.id == state.active_run_id)).order_by(MesOrderRecord.accepted_sequence)).all()
            all_pairs = {run.id: (order, run) for order, run in (*selected, *context_pairs)}
            unit_run_ids = {run.id for _, run in selected}
            unit_run_ids.update(run.id for _, run in context_pairs if run.review_required or run.id == state.active_run_id)
            units_by_run: dict[str, list[ProductUnitRecord]] = {run_id: [] for run_id in unit_run_ids}
            if unit_run_ids:
                units = session.exec(select(ProductUnitRecord).where(
                    ProductUnitRecord.run_id.in_(unit_run_ids),
                ).order_by(ProductUnitRecord.run_id, ProductUnitRecord.queue_index)).all()
                for unit in units:
                    units_by_run[unit.run_id].append(unit)
            orders = tuple(StoredOrder(order, run, tuple(units_by_run.get(run.id, ())))
                           for order, run in sorted(all_pairs.values(), key=lambda pair: pair[0].accepted_sequence))
            sources = tuple(session.exec(select(PlcSourceStateRecord)).all())
            return OrderSnapshot(orders, sources, state), [run.id for _, run in selected], total, filtered_total, summary

    def overview_snapshot(self):
        """Lädt nur aktive, wartende und zu prüfende Aufträge plus aggregierte Statuszahlen."""
        with self.transaction() as session:
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            state = session.get(DispatchStateRecord, 1)
            if state is None:
                raise RuntimeError("Auftragsdaten sind nicht initialisiert. Bitte Migration und Workerstart prüfen.")
            pairs = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(or_(OrderRunRecord.review_required.is_(True),
                        OrderRunRecord.phase == RunPhase.QUEUED.value,
                        OrderRunRecord.id == state.active_run_id)).order_by(MesOrderRecord.accepted_sequence)).all()
            unit_run_ids = {run.id for _, run in pairs if run.review_required or run.id == state.active_run_id}
            units_by_run: dict[str, list[ProductUnitRecord]] = {run_id: [] for run_id in unit_run_ids}
            if unit_run_ids:
                for unit in session.exec(select(ProductUnitRecord).where(
                    ProductUnitRecord.run_id.in_(unit_run_ids),
                ).order_by(ProductUnitRecord.run_id, ProductUnitRecord.queue_index)).all():
                    units_by_run[unit.run_id].append(unit)
            orders = tuple(StoredOrder(order, run, tuple(units_by_run.get(run.id, ()))) for order, run in pairs)
            sources = tuple(session.exec(select(PlcSourceStateRecord)).all())
            summary_rows = session.exec(select(MesOrderRecord.order_type, OrderRunRecord.phase, func.count()).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).group_by(MesOrderRecord.order_type, OrderRunRecord.phase)).all()
            summaries: dict[str, dict[str, int]] = {}
            for kind, phase, count in summary_rows:
                summaries.setdefault(kind, {})[phase] = count
            return OrderSnapshot(orders, sources, state), summaries

    def reserve_next(self) -> StoredOrder | None:
        """Reserviert atomar genau den ältesten wartenden Auftrag beider Arten."""
        with self.transaction() as session:
            state = self.lock_state(session)
            if state.active_run_id or state.blocked_reason or self._has_reviews(session):
                return None
            pair = session.exec(select(MesOrderRecord, OrderRunRecord).join(
                OrderRunRecord, MesOrderRecord.id == OrderRunRecord.order_ref,
            ).where(OrderRunRecord.phase == RunPhase.QUEUED.value).order_by(
                MesOrderRecord.accepted_sequence,
            ).limit(1)).first()
            if pair is None:
                return None
            order, run = pair
            self.change_phase(run, RunPhase.PREPARING)
            state.active_run_id = run.id
            return StoredOrder(order, run, tuple(self.load_units(session, run.id)))

    def _has_reviews(self, session: Session) -> bool:
        """Prüft die globale Sperre ohne Auftragstyppriorität."""
        return session.exec(select(OrderRunRecord.id).where(OrderRunRecord.review_required).limit(1)).first() is not None

    def change_phase(self, run: OrderRunRecord, phase: RunPhase) -> None:
        """Wendet fachliche Übergänge an und erhöht die Version nur bei einer Änderung."""
        if run.phase == phase.value:
            return
        domain = OrderRun(RunPhase(run.phase))
        domain.transition_to(phase)
        run.phase = domain.phase.value
        run.phase_changed_at = self.clock()
        run.version += 1

    def transition(self, run_id: str, phase: RunPhase) -> None:
        """Persistiert einen belegten Übergang vor dem nächsten Nebeneffekt."""
        with self.transaction() as session:
            self.lock_state(session)
            self.change_phase(self.load_run(session, run_id), phase)

    def require_review(self, run_id: str, reason: str) -> None:
        """Erhält die Laufreservierung und sperrt beide Auftragsarten dauerhaft."""
        with self.transaction() as session:
            state = self.lock_state(session)
            run = self.load_run(session, run_id)
            self.mark_review(run, state, reason)

    def mark_review(self, run: OrderRunRecord, state: DispatchStateRecord, reason: str) -> None:
        """Markiert Unsicherheit atomar zusammen mit neu belegten Produktresultaten."""
        if not run.review_required or run.review_reason != reason:
            previous_version = run.version
            self.change_phase(run, RunPhase.REVIEW_REQUIRED)
            if run.version == previous_version:
                run.version += 1
            run.review_required = True
            run.review_reason = reason
        state.blocked_reason = "Ein Lauf muss geprüft werden."

    def block(self, reason: str | None) -> None:
        """Setzt Quellen-/Bereitschaftssperren, ohne offene Reviews zu entfernen."""
        with self.transaction() as session:
            state = self.lock_state(session)
            state.blocked_reason = "Ein Lauf muss geprüft werden." if self._has_reviews(session) else reason

    def release_completed(self, run_id: str) -> None:
        """Gibt eine Reservierung erst nach extern bestätigter Idlebereitschaft frei."""
        with self.transaction() as session:
            state = self.lock_state(session)
            run = self.load_run(session, run_id)
            if run.review_required or run.phase not in {RunPhase.COMPLETED.value, RunPhase.INTERRUPTED.value}:
                raise OrderConflict("Der Lauf ist noch nicht geklärt. Bitte zuerst die Bewertung prüfen.")
            if state.active_run_id != run_id:
                raise OrderConflict("Der Lauf besitzt nicht die aktive Anlagenreservierung.")
            state.active_run_id = None
            state.blocked_reason = None if not self._has_reviews(session) else "Ein Lauf muss geprüft werden."

    def source_success(self, kind: OrderType, observed_at: datetime) -> None:
        """Aktualisiert ausschließlich eine tatsächlich erfolgreiche PLC-Beobachtung."""
        with self.transaction() as session:
            source = session.get(PlcSourceStateRecord, kind.value)
            if source is None:
                raise RuntimeError("Die PLC-Quelle ist nicht initialisiert.")
            source.connection_status = "connected"
            source.last_success_at = observed_at
            source.error = None

    def return_prepared_to_queue(self, run_id: str) -> None:
        """Erhält die Reihenfolge, wenn der persistierte Zustand einen Start ausschließt."""
        with self.transaction() as session:
            state = self.lock_state(session)
            run = self.load_run(session, run_id)
            if state.active_run_id != run_id or run.phase != RunPhase.PREPARING.value:
                raise OrderConflict("Die Vorbereitung kann nicht ohne belegten Zustand zurückgestellt werden.")
            self.change_phase(run, RunPhase.QUEUED)
            state.active_run_id = None

    def source_failure(self, kind: OrderType, reason: str) -> None:
        """Bewahrt den letzten Erfolgszeitpunkt auch nach einem Verbindungsfehler."""
        with self.transaction() as session:
            source = session.get(PlcSourceStateRecord, kind.value)
            if source is None:
                raise RuntimeError("Die PLC-Quelle ist nicht initialisiert.")
            source.connection_status = "disconnected"
            source.error = reason

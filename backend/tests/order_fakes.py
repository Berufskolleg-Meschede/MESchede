"""Explizit synthetische PLC-Rückmeldungen für isolierte Verhaltenstests."""

from dataclasses import replace
from datetime import datetime, timezone

from app.domain.order_run import OrderType
from app.domain.plc_snapshot import PlcSnapshot, ProductObservation


class FakeLeadership:
    """Ersetzt nur die technische Führungsverbindung, nicht die PostgreSQL-Reservierung."""

    def __init__(self):
        """Startet mit einem explizit gewährten Testnachweis."""
        self.owned = True
        self.closed = False

    async def acquire(self):
        """Liefert die testseitig kontrollierte Führungsberechtigung."""
        return self.owned

    async def assert_owned(self):
        """Verweigert Schreiboperationen bei testseitigem Führungsverlust."""
        if not self.owned:
            raise RuntimeError("Testführung verloren")

    async def close(self):
        """Dokumentiert die geordnete Lebensdauer."""
        self.closed = True


class SimulatedGateway:
    """Liefert bewusst synthetische Resultatcodes 11/12 statt angenommener PLC-Semantik."""

    def __init__(self, repository=None, auto_progress=False):
        """Beginnt mit zwei unabhängigen Idle-Slots bei einer gemeinsamen Startvergabe."""
        self.repository = repository
        self.auto_progress = auto_progress
        self.events = []
        self.closed = False
        self.reads = 0
        self.active_reads = 0
        self.snapshots = {kind: PlcSnapshot(kind, 0, 0, 0, datetime.now(timezone.utc)) for kind in OrderType}

    async def read(self, kind):
        """Erlaubt kurze vollständige Läufe ohne echten Netz- oder Hardwarezugriff."""
        self.reads += 1
        snapshot = self.snapshots[kind]
        if self.auto_progress and snapshot.command == 1:
            self.active_reads += 1
            if self.active_reads > 1:
                snapshot = replace(snapshot, status=5)
                self.snapshots[kind] = snapshot
        return replace(snapshot, observed_at=datetime.now(timezone.utc))

    async def write(self, kind, payload):
        """Prüft gemeinsamen Idle vor dem Start und behält Eingabeeinheiten bei."""
        assert all(snapshot.ready for snapshot in self.snapshots.values())
        self.events.append(("start", kind, payload.kopf.Auftragsnummer))
        self.active_reads = 0
        products = tuple(ProductObservation(
            index, item.ProduktID, item.Seriennummer, item.Sequenznummer,
            11 if index == 0 else 12, 0 if index == 0 else 7,
        ) for index, item in enumerate(payload.inhalt.Produktqueue))
        self.snapshots[kind] = PlcSnapshot(kind, payload.kopf.Auftragsnummer, 1, 1,
                                            datetime.now(timezone.utc), products, len(products))

    async def acknowledge(self, kind, expected_order_number):
        """Belegt vor Reset bereits persistierte Endresultate."""
        assert self.snapshots[kind].status == 5
        assert self.snapshots[kind].order_number == expected_order_number
        if self.repository is not None:
            snapshot = self.repository.snapshot()
            stored = next(item for item in snapshot.orders if item.run.id == snapshot.dispatch.active_run_id)
            assert stored.run.ended_at is not None
            assert all(unit.result is not None for unit in stored.units)
        self.events.append(("ack", kind))
        self.snapshots[kind] = replace(self.snapshots[kind], command=0, status=0, products=(), product_count=0)

    async def close(self):
        """Erhält einen prüfbaren Shutdownnachweis ohne Socketzugriff."""
        self.closed = True

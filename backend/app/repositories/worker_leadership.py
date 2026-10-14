"""Exklusive Lebensdauer eines PLC-schreibenden Workers je Datenbankschema."""

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import Engine, text


class WorkerLeadership:
    """Bewahrt ein Session-Advisory-Lock auf einer dedizierten Verbindung."""

    def __init__(self, engine: Engine) -> None:
        """Isoliert auch den Verbindungszugriff in einem einzelnen Thread."""
        self.engine = engine
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mes-leader")
        self.connection = None
        self.owned = False
        self.key = None

    async def _invoke(self, operation):
        """Beendet einen bereits laufenden Verbindungszugriff vor Taskcancel."""
        future = asyncio.get_running_loop().run_in_executor(self.executor, operation)
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            await future
            raise

    def _acquire_sync(self) -> bool:
        """Erhält genau einen Lockinhaber ohne eine offene Fachtransaktion."""
        if self.connection is None:
            self.connection = self.engine.connect().execution_options(isolation_level="AUTOCOMMIT")
            schema = self.connection.execute(text("SELECT current_schema()")).scalar_one()
            self.key = int.from_bytes(hashlib.sha256(f"mes-orders:{schema}".encode()).digest()[:8], signed=True)
        if not self.owned:
            self.owned = bool(self.connection.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": self.key}).scalar_one())
        return self.owned

    async def acquire(self) -> bool:
        """Liefert false, solange eine andere Runtime die Anlage betreibt."""
        return await self._invoke(self._acquire_sync)

    async def assert_owned(self) -> None:
        """Verhindert neue Schreibaufträge nach verlorener Führungsverbindung."""
        def check():
            """Prüft die noch bestehende Session ohne das Lock erneut zu stapeln."""
            if not self.owned or self.connection is None:
                raise RuntimeError("Der Auftragsworker besitzt keine Anlagenberechtigung.")
            self.connection.execute(text("SELECT 1"))
        await self._invoke(check)

    def _release_sync(self) -> None:
        """Gibt das Lock erst nach dem geordneten Auslaufen der PLC-Operationen frei."""
        if self.connection is not None:
            try:
                if self.owned:
                    self.connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": self.key})
            finally:
                self.connection.close()
                self.connection = None
                self.owned = False

    async def close(self) -> None:
        """Beendet die dedizierte Session und ihren Ausführungsweg."""
        try:
            await self._invoke(self._release_sync)
        finally:
            self.executor.shutdown(wait=True, cancel_futures=False)

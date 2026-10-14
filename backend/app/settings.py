"""Validierte Betriebswerte für Auftragsbeobachtung und Produktergebniszuordnung."""

import json
import math
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderSettings:
    """Wertet Produktstatuscodes nur mit explizit bestätigter Zuordnung aus."""

    poll_interval_s: float = 0.5
    refresh_interval_s: float = 2.0
    stale_after_s: float = 10.0
    start_timeout_s: float = 30.0
    completion_timeout_s: float = 600.0
    reset_timeout_s: float = 30.0
    rest_buffer_s: float = 3.0
    contract_verified: bool = False
    product_results: dict[int, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Verhindert unbrauchbare Intervalle und unbelegte Ergebniscodes."""
        intervals = (
            self.poll_interval_s, self.refresh_interval_s,
            self.start_timeout_s, self.completion_timeout_s, self.reset_timeout_s,
        )
        if any(not math.isfinite(value) for value in (*intervals, self.rest_buffer_s, self.stale_after_s)) or min(intervals) <= 0 or self.rest_buffer_s < 0:
            raise ValueError("Die Abfrageintervalle müssen positiv sein. Bitte die Konfiguration prüfen.")
        if self.stale_after_s <= self.poll_interval_s:
            raise ValueError("Die Veraltungsgrenze muss über dem PLC-Abfrageintervall liegen.")
        if any(value not in {"good", "failed"} for value in self.product_results.values()):
            raise ValueError("Produktsignale müssen als good oder failed zugeordnet werden.")
        if self.product_results and not self.contract_verified:
            raise ValueError("Produktcodes benötigen eine bestätigte Ergebniszuordnung.")

    @classmethod
    def from_environment(cls) -> "OrderSettings":
        """Lädt zentrale Werte; unbekannte Einzelresultate werden nach Status 5 erfolgreich angenommen."""
        results = json.loads(os.getenv("OPC_UA_PRODUCT_RESULTS", "{}"))
        return cls(
            poll_interval_s=float(os.getenv("ORDER_POLL_INTERVAL_S", "0.5")),
            refresh_interval_s=float(os.getenv("ORDER_REFRESH_INTERVAL_S", "2")),
            stale_after_s=float(os.getenv("ORDER_STALE_AFTER_S", "10")),
            start_timeout_s=float(os.getenv("ORDER_START_TIMEOUT_S", "30")),
            completion_timeout_s=float(os.getenv("ORDER_COMPLETION_TIMEOUT_S", "600")),
            reset_timeout_s=float(os.getenv("ORDER_RESET_TIMEOUT_S", "30")),
            rest_buffer_s=float(os.getenv("ORDER_REST_BUFFER_S", "3")),
            contract_verified=os.getenv("OPC_UA_CONTRACT_VERIFIED", "false").lower() == "true",
            product_results={int(key): value for key, value in results.items()},
        )

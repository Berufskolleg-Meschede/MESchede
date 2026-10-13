from pydantic import field_validator
from sqlmodel import Field, SQLModel

SETTINGS_ID = 1

MIN_POLLING_INTERVAL_MS = 100
MAX_POLLING_INTERVAL_MS = 10_000

DEFAULT_PRODUCTION_NODE = "MESAuftragProduktion"
DEFAULT_DELIVERY_NODE = "MESAuftragKommissionieren"
DEFAULT_POLLING_INTERVAL_MS = 500


class SettingsBase(SQLModel):
    opcua_node_production_order: str = Field(default=DEFAULT_PRODUCTION_NODE)
    opcua_node_delivery_order: str = Field(default=DEFAULT_DELIVERY_NODE)
    polling_interval_ms: int = Field(default=DEFAULT_POLLING_INTERVAL_MS)

    @field_validator("opcua_node_production_order", "opcua_node_delivery_order")
    @classmethod
    def _node_not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Zielnode darf nicht leer sein.")
        return stripped

    @field_validator("polling_interval_ms")
    @classmethod
    def _interval_within_bounds(cls, value: int) -> int:
        if value < MIN_POLLING_INTERVAL_MS or value > MAX_POLLING_INTERVAL_MS:
            raise ValueError(
                f"Abfrageintervall muss zwischen {MIN_POLLING_INTERVAL_MS} "
                f"und {MAX_POLLING_INTERVAL_MS} Millisekunden liegen."
            )
        return value


class Settings(SettingsBase, table=True):
    id: int = Field(default=SETTINGS_ID, primary_key=True, nullable=False)

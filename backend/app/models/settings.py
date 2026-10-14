from pydantic import field_validator
from sqlmodel import Field, SQLModel

SETTINGS_ID = 1

MIN_POLLING_INTERVAL_MS = 100
MAX_POLLING_INTERVAL_MS = 10_000

DEFAULT_PRODUCTION_NODE = "MESAuftragProduktion"
DEFAULT_DELIVERY_NODE = "MESAuftragKommissionieren"
DEFAULT_POLLING_INTERVAL_MS = 500

DEFAULT_KOPF_NODE = "Kopf"
DEFAULT_INHALT_NODE = "Inhalt"
DEFAULT_FEEDBACK_NODE = "Feedback"
DEFAULT_AUFTRAGSSTEUERUNG_NODE = "Auftragssteuerung_MES"
DEFAULT_STATUS_NODE = "StatusMES"
DEFAULT_PRODUKTQUEUE_PATTERN = "Produktqueue[{index}]"

_NODE_NAME_FIELDS = (
    "opcua_node_production_order",
    "opcua_node_delivery_order",
    "opcua_node_kopf",
    "opcua_node_inhalt",
    "opcua_node_feedback",
    "opcua_node_auftragssteuerung",
    "opcua_node_status",
)


class SettingsBase(SQLModel):
    opcua_node_production_order: str = Field(default=DEFAULT_PRODUCTION_NODE)
    opcua_node_delivery_order: str = Field(default=DEFAULT_DELIVERY_NODE)
    polling_interval_ms: int = Field(default=DEFAULT_POLLING_INTERVAL_MS)

    # Struktureller Knotenbaum unterhalb von MESAuftragProduktion/-Kommissionieren.
    # Die Rollen (welcher Knoten unter welchem liegt) sind fest, da der OPC-UA-Client
    # sie so interpretiert; nur die Browse-Namen selbst sind editierbar.
    opcua_node_kopf: str = Field(default=DEFAULT_KOPF_NODE)
    opcua_node_inhalt: str = Field(default=DEFAULT_INHALT_NODE)
    opcua_node_feedback: str = Field(default=DEFAULT_FEEDBACK_NODE)
    opcua_node_auftragssteuerung: str = Field(default=DEFAULT_AUFTRAGSSTEUERUNG_NODE)
    opcua_node_status: str = Field(default=DEFAULT_STATUS_NODE)
    opcua_node_produktqueue_pattern: str = Field(default=DEFAULT_PRODUKTQUEUE_PATTERN)

    @field_validator(*_NODE_NAME_FIELDS)
    @classmethod
    def _node_not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Knotenname darf nicht leer sein.")
        return stripped

    @field_validator("opcua_node_produktqueue_pattern")
    @classmethod
    def _produktqueue_pattern_valid(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Namensmuster darf nicht leer sein.")
        if "{index}" not in stripped:
            raise ValueError("Namensmuster muss den Platzhalter {index} enthalten.")
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

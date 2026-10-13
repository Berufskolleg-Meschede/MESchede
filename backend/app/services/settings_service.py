"""In-memory MES settings used by settings API and worker loops."""

from ..models.settings import Settings
from ..workers import plc_handshake

_current = Settings()


def get_current_settings() -> Settings:
    return _current


def apply_settings(settings: Settings) -> None:
    global _current
    _current = Settings.model_validate(settings.model_dump())
    plc_handshake.POLL_INTERVAL_S = settings.polling_interval_ms / 1000

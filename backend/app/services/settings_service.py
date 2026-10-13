"""In-memory cache of the persisted MES settings, kept in sync with PostgreSQL.

Worker loops read node names via `get_current_settings()` instead of hardcoded
constants. `apply_settings` also pushes the confirmed polling interval into
`plc_handshake.POLL_INTERVAL_S`, the module-level constant its sleep calls read.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.settings import SETTINGS_ID, Settings
from ..workers import plc_handshake

logger = logging.getLogger(__name__)

_current: Optional[Settings] = None


async def load_settings(session: AsyncSession) -> Settings:
    """Return the persisted settings row, creating the default row on first use."""
    settings = await session.get(Settings, SETTINGS_ID)
    if settings is None:
        settings = Settings(id=SETTINGS_ID)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
        logger.info("Settings: no row found, created defaults %s", settings)
    apply_settings(settings)
    return settings


def get_current_settings() -> Settings:
    """Return the effective in-memory settings; defaults if never loaded."""
    if _current is None:
        return Settings(id=SETTINGS_ID)
    return _current


def apply_settings(settings: Settings) -> None:
    """Make newly confirmed settings take effect for subsequent OPC UA access."""
    global _current
    _current = settings
    plc_handshake.POLL_INTERVAL_S = settings.polling_interval_ms / 1000

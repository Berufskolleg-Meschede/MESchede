"""add structural opc ua node settings

Revision ID: 1cd957b0fc37
Revises: b8dad9f2556c
Create Date: 2026-10-13 06:57:52.161995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1cd957b0fc37'
down_revision: Union[str, Sequence[str], None] = 'b8dad9f2556c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Autogenerate also proposed creating 'article'/'deliveryorder'/
    # 'productionorder'/'storage'; those already exist in the database but were
    # never tracked by an Alembic migration (pre-existing gap, out of scope
    # here). Only the settings columns below are intentional for this change.
    # server_default backfills the existing settings row with the names the
    # OPC UA client used as hardcoded constants before this migration.
    op.add_column('settings', sa.Column(
        'opcua_node_kopf', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='Kopf',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_inhalt', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='Inhalt',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_feedback', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='Feedback',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_auftragssteuerung', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='Auftragssteuerung_MES',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='StatusMES',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_produktqueue_pattern', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='Produktqueue[{index}]',
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('settings', 'opcua_node_produktqueue_pattern')
    op.drop_column('settings', 'opcua_node_status')
    op.drop_column('settings', 'opcua_node_auftragssteuerung')
    op.drop_column('settings', 'opcua_node_feedback')
    op.drop_column('settings', 'opcua_node_inhalt')
    op.drop_column('settings', 'opcua_node_kopf')

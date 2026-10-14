"""add lager opc ua node settings

Revision ID: 1172056ef1d5
Revises: merge_issue29_main_heads
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1172056ef1d5'
down_revision: Union[str, Sequence[str], None] = 'merge_issue29_main_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('settings', sa.Column(
        'opcua_node_lager_gehaeuse', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='LagerGehaeuse',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_magazin_deckel_1', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='MagazinDeckel_1',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_magazin_deckel_2', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='MagazinDeckel_2',
    ))
    op.add_column('settings', sa.Column(
        'opcua_node_lager_produkte', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='LagerProdukte',
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('settings', 'opcua_node_lager_produkte')
    op.drop_column('settings', 'opcua_node_magazin_deckel_2')
    op.drop_column('settings', 'opcua_node_magazin_deckel_1')
    op.drop_column('settings', 'opcua_node_lager_gehaeuse')

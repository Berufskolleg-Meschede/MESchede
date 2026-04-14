"""add product, storage, production order, delivery order models and extend user model

Revision ID: a1b2c3d4e5f6
Revises: 13bbe5395414
Create Date: 2026-04-14 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '13bbe5395414'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Extend user table with password and role fields
    op.add_column('user',
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    op.add_column('user',
        sa.Column('role', sa.Enum('ADMIN', 'OPERATOR', 'VIEWER', name='userrole'), nullable=False,
                  server_default='VIEWER')
    )
    op.add_column('user',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )

    # Create product table
    op.create_table('product',
        sa.Column('product_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('unit', sa.Enum('PIECE', 'KILOGRAM', 'LITER', 'METER', name='productunit'), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_number')
    )

    # Create storageitem table
    op.create_table('storageitem',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create productionorder table
    op.create_table('productionorder',
        sa.Column('order_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=True),
        sa.Column('quantity_planned', sa.Float(), nullable=False),
        sa.Column('quantity_produced', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['machine_id'], ['machine.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )

    # Create deliveryorder table
    op.create_table('deliveryorder',
        sa.Column('order_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('order_type', sa.Enum('INBOUND', 'OUTBOUND', name='deliveryordertype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='orderstatus',
                                    create_type=False), nullable=False),
        sa.Column('partner_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )

    # Create deliveryorderitem table
    op.create_table('deliveryorderitem',
        sa.Column('delivery_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity_planned', sa.Float(), nullable=False),
        sa.Column('quantity_actual', sa.Float(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['delivery_order_id'], ['deliveryorder.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('deliveryorderitem')
    op.drop_table('deliveryorder')
    op.drop_table('productionorder')
    op.drop_table('storageitem')
    op.drop_table('product')
    op.drop_column('user', 'is_active')
    op.drop_column('user', 'role')
    op.drop_column('user', 'hashed_password')
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS deliveryordertype")
    op.execute("DROP TYPE IF EXISTS productunit")

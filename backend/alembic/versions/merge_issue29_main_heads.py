"""Merge the persistent order and mainline settings migration heads."""

from typing import Sequence, Union

revision: str = "merge_issue29_main_heads"
down_revision: Union[str, Sequence[str], None] = ("1cd957b0fc37", "c1a9f8274d65")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join independent schema histories without changing table data."""


def downgrade() -> None:
    """Keep this merge reversible without dropping either feature schema."""

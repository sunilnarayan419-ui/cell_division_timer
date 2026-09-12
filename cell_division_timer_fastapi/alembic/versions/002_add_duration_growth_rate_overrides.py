"""002 Add explicit override columns for division_duration_minutes / growth_rate

Revision ID: 002_add_overrides
Revises: 001_initial_schema
Create Date: 2025-01-01 00:00:00.000000

Scientific data-integrity fix:
Previously, `division_duration_minutes` and `growth_rate` could be supplied
directly on create and would silently override the value implied by
`division_start_time`/`division_end_time` and `cell_cycle_duration_hours`.
This migration adds explicit, clearly-named override columns so that a
manual override is always distinguishable from a calculated value, and
always carries a documented reason.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_overrides"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("cell_division_records") as batch_op:
        batch_op.add_column(sa.Column("duration_override_minutes", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("duration_override_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("growth_rate_override", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("growth_rate_override_reason", sa.Text(), nullable=True))
        batch_op.create_check_constraint(
            "ck_duration_override_requires_reason",
            "(duration_override_minutes IS NULL) = (duration_override_reason IS NULL)",
        )
        batch_op.create_check_constraint(
            "ck_growth_rate_override_requires_reason",
            "(growth_rate_override IS NULL) = (growth_rate_override_reason IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("cell_division_records") as batch_op:
        batch_op.drop_constraint("ck_growth_rate_override_requires_reason", type_="check")
        batch_op.drop_constraint("ck_duration_override_requires_reason", type_="check")
        batch_op.drop_column("growth_rate_override_reason")
        batch_op.drop_column("growth_rate_override")
        batch_op.drop_column("duration_override_reason")
        batch_op.drop_column("duration_override_minutes")

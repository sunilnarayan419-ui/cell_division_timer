"""001 Initial Schema for Cells and Division Records

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-03-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create cells table
    op.create_table(
        "cells",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("organism", sa.String(length=128), nullable=False),
        sa.Column("cell_type", sa.String(length=128), nullable=False),
        sa.Column("passage_number", sa.Integer(), nullable=True),
        sa.Column("source_line", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cells_id", "cells", ["id"])
    op.create_index("ix_cells_name", "cells", ["name"])
    op.create_index("ix_cells_organism", "cells", ["organism"])
    op.create_index("ix_cells_cell_type", "cells", ["cell_type"])
    op.create_index("ix_cells_created_at", "cells", ["created_at"])

    # 2. Create cell_division_records table
    op.create_table(
        "cell_division_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cell_id", sa.String(length=64), nullable=False),
        sa.Column("experimental_batch", sa.String(length=64), nullable=False),
        sa.Column("replicate", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("experimental_condition", sa.String(length=128), nullable=False),
        sa.Column("medium", sa.String(length=128), nullable=False),
        sa.Column("temperature_celsius", sa.Float(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("division_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("division_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("division_duration_minutes", sa.Float(), nullable=False),
        sa.Column("cell_cycle_duration_hours", sa.Float(), nullable=False),
        sa.Column("growth_rate", sa.Float(), nullable=False),
        sa.Column("is_outlier", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("quality_flag", sa.String(length=32), nullable=False, server_default="PASS"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["cell_id"], ["cells.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("division_end_time >= division_start_time", name="ck_division_end_after_start"),
        sa.CheckConstraint("division_duration_minutes >= 0", name="ck_positive_division_duration"),
        sa.CheckConstraint("cell_cycle_duration_hours > 0", name="ck_positive_cell_cycle_duration"),
        sa.CheckConstraint("temperature_celsius >= -10.0 AND temperature_celsius <= 100.0", name="ck_plausible_temperature"),
    )
    op.create_index("ix_cell_division_records_id", "cell_division_records", ["id"])
    op.create_index("ix_cell_division_records_cell_id", "cell_division_records", ["cell_id"])
    op.create_index("ix_cell_division_records_experimental_batch", "cell_division_records", ["experimental_batch"])
    op.create_index("ix_cell_division_records_experimental_condition", "cell_division_records", ["experimental_condition"])
    op.create_index("ix_cell_division_records_temperature_celsius", "cell_division_records", ["temperature_celsius"])
    op.create_index("ix_cell_division_records_generation", "cell_division_records", ["generation"])
    op.create_index("ix_cell_division_records_division_start_time", "cell_division_records", ["division_start_time"])
    op.create_index("ix_cell_division_records_division_end_time", "cell_division_records", ["division_end_time"])
    op.create_index("ix_cell_division_records_division_duration_minutes", "cell_division_records", ["division_duration_minutes"])
    op.create_index("ix_cell_division_records_cell_cycle_duration_hours", "cell_division_records", ["cell_cycle_duration_hours"])
    op.create_index("ix_cell_division_records_growth_rate", "cell_division_records", ["growth_rate"])
    op.create_index("ix_cell_division_records_is_outlier", "cell_division_records", ["is_outlier"])
    op.create_index("ix_cell_division_records_quality_flag", "cell_division_records", ["quality_flag"])
    op.create_index("ix_divisions_batch_condition", "cell_division_records", ["experimental_batch", "experimental_condition"])
    op.create_index("ix_divisions_cell_gen", "cell_division_records", ["cell_id", "generation"])


def downgrade() -> None:
    op.drop_table("cell_division_records")
    op.drop_table("cells")

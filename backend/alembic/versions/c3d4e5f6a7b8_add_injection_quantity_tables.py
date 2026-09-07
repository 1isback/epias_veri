"""add injection quantity tables

Revision ID: c3d4e5f6a7b8
Revises: b241bec85ad6
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b241bec85ad6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "injection_quantity_powerplants",
        sa.Column("epias_powerplant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("short_name", sa.String(length=255), nullable=True),
        sa.Column("eic", sa.String(length=64), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("epias_powerplant_id"),
    )
    op.create_index("ix_injection_quantity_powerplants_epias_powerplant_id", "injection_quantity_powerplants", ["epias_powerplant_id"])
    op.create_table(
        "injection_quantities",
        sa.Column("epias_powerplant_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("interval_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("injection_quantity", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("epias_powerplant_id", "interval_start", name="uq_injection_quantity_plant_interval"),
    )
    op.create_index("ix_injection_quantities_plant_interval", "injection_quantities", ["epias_powerplant_id", "interval_start"])


def downgrade() -> None:
    op.drop_index("ix_injection_quantities_plant_interval", table_name="injection_quantities")
    op.drop_table("injection_quantities")
    op.drop_index("ix_injection_quantity_powerplants_epias_powerplant_id", table_name="injection_quantity_powerplants")
    op.drop_table("injection_quantity_powerplants")

"""create users and alerts tables

Revision ID: 20260228_0001
Revises: None
Create Date: 2026-02-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260228_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("severity_level", sa.String(length=20), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_region"), "alerts", ["region"], unique=False)
    op.create_index(
        op.f("ix_alerts_severity_level"), "alerts", ["severity_level"], unique=False
    )
    op.create_index(op.f("ix_alerts_timestamp"), "alerts", ["timestamp"], unique=False)
    op.create_index(
        "ix_alerts_region_timestamp", "alerts", ["region", "timestamp"], unique=False
    )
    op.create_index(
        "ix_alerts_severity_timestamp",
        "alerts",
        ["severity_level", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_alerts_severity_timestamp", table_name="alerts")
    op.drop_index("ix_alerts_region_timestamp", table_name="alerts")
    op.drop_index(op.f("ix_alerts_timestamp"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_severity_level"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_region"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

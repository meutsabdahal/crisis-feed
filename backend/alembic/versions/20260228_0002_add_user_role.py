"""add role to users

Revision ID: 20260228_0002
Revises: 20260228_0001
Create Date: 2026-02-28 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260228_0002"
down_revision = "20260228_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=30), nullable=True))
    op.execute("UPDATE users SET role = 'analyst' WHERE role IS NULL")
    op.alter_column("users", "role", existing_type=sa.String(length=30), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "role")

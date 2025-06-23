"""Add server default now() to created_at columns

Revision ID: e20e3e3531c7
Revises: db38a70c4d6a
Create Date: 2025-06-20 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e20e3e3531c7"
down_revision = "db38a70c4d6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    # Update existing NULL values to current timestamp to satisfy NOT NULL constraint
    op.execute("UPDATE sources SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE clusters SET created_at = NOW() WHERE created_at IS NULL")

    # Set server default of NOW() on created_at columns
    op.alter_column(
        "sources",
        "created_at",
        server_default=sa.text("NOW()"),
        existing_type=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "clusters",
        "created_at",
        server_default=sa.text("NOW()"),
        existing_type=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert the migration."""
    # Remove server default
    op.alter_column(
        "sources",
        "created_at",
        server_default=None,
        existing_type=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "clusters",
        "created_at",
        server_default=None,
        existing_type=sa.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )

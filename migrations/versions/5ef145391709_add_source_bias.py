"""add_source_bias

Revision ID: 5ef145391709
Revises: 5ee3f3458fd1
Create Date: 2025-06-23 14:45:55.102496

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "5ef145391709"
down_revision = "5ee3f3458fd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto extension is available for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create source_bias table
    op.create_table(
        "source_bias",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("bias_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("bias_label", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("bias_label IN ('left','center','right','unknown')"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_source_bias_bias_label"), "source_bias", ["bias_label"], unique=False
    )
    op.create_index(
        op.f("ix_source_bias_bias_score"), "source_bias", ["bias_score"], unique=False
    )

    # Add nullable foreign key column to sources table
    op.add_column("sources", sa.Column("bias_id", UUID(as_uuid=True), nullable=True))

    # Create foreign key constraint
    op.create_foreign_key(None, "sources", "source_bias", ["bias_id"], ["id"])


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint("fk_sources_source_bias_id", "sources", type_="foreignkey")

    # Drop foreign key column from sources table
    op.drop_column("sources", "bias_id")

    # Drop indexes
    op.drop_index("ix_source_bias_bias_label", "source_bias")
    op.drop_index("ix_source_bias_bias_score", "source_bias")

    # Drop source_bias table
    op.drop_table("source_bias")

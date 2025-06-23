from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:  # noqa: D401
    """Create initial schema."""
    # sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sources_platform", "sources", ["platform"])
    op.create_index("ix_sources_created_at", "sources", ["created_at"])
    op.create_index(
        "ix_sources_platform_created_at",
        "sources",
        ["platform", "created_at"],
        unique=False,
    )

    # embeddings table
    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vector", sa.LargeBinary(), nullable=False),
    )
    op.create_index("ix_embeddings_source_id", "embeddings", ["source_id"])

    # clusters table
    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_clusters_created_at", "clusters", ["created_at"])

    # narratives table
    op.create_table(
        "narratives",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "cluster_id",
            sa.Integer(),
            sa.ForeignKey("clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "conflicting_with",
            sa.Integer(),
            sa.ForeignKey("narratives.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_narratives_cluster_id", "narratives", ["cluster_id"])


def downgrade() -> None:  # noqa: D401
    """Drop all tables."""
    op.drop_index("ix_narratives_cluster_id", table_name="narratives")
    op.drop_table("narratives")

    op.drop_index("ix_clusters_created_at", table_name="clusters")
    op.drop_table("clusters")

    op.drop_index("ix_embeddings_source_id", table_name="embeddings")
    op.drop_table("embeddings")

    op.drop_index("ix_sources_platform_created_at", table_name="sources")
    op.drop_index("ix_sources_created_at", table_name="sources")
    op.drop_index("ix_sources_platform", table_name="sources")
    op.drop_table("sources")

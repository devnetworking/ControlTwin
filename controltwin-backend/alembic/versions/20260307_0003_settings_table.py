"""Add settings table

Revision ID: 20260307_0003_settings_table
Revises: 20250301_0002_seed_data
Create Date: 2026-03-07 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260307_0003_settings_table"
down_revision = "0002_seed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUM may already exist if created by a failed previous attempt
    op.execute("DO $$ BEGIN CREATE TYPE setting_scope AS ENUM ('global','user','site'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    setting_scope_enum = postgresql.ENUM("global", "user", "site", name="setting_scope", create_type=False)

    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("scope", setting_scope_enum, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", "scope", "user_id", "site_id", name="uq_settings_key_scope_user_site"),
    )
    op.create_index(op.f("ix_settings_key"), "settings", ["key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_settings_key"), table_name="settings")
    op.drop_table("settings")
    setting_scope_enum = postgresql.ENUM("global", "user", "site", name="setting_scope")
    setting_scope_enum.drop(op.get_bind(), checkfirst=True)

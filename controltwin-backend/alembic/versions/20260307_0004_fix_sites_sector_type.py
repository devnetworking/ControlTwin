"""Fix sites.sector type alignment

Revision ID: 20260307_0004_fix_sites_sector
Revises: 20260307_0003_settings_table
Create Date: 2026-03-07 00:00:01
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260307_0004_fix_sites_sector"
down_revision = "20260307_0003_settings_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert ENUM -> VARCHAR while preserving data and enforcing allowed values.
    op.execute(
        """
        ALTER TABLE sites
        ALTER COLUMN sector TYPE VARCHAR(30)
        USING sector::text;
        """
    )

    # Recreate check constraint to match initial schema contract.
    op.execute("ALTER TABLE sites DROP CONSTRAINT IF EXISTS ck_sites_sector;")
    op.execute(
        """
        ALTER TABLE sites
        ADD CONSTRAINT ck_sites_sector
        CHECK (sector IN ('electricity','oil','gas','water','manufacturing','generic'));
        """
    )

    op.execute("ALTER TABLE sites ALTER COLUMN sector SET DEFAULT 'generic';")


def downgrade() -> None:
    # Best-effort rollback to enum type used by ORM naming.
    op.execute("DO $$ BEGIN CREATE TYPE sector AS ENUM ('electricity','oil','gas','water','manufacturing','generic'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("ALTER TABLE sites DROP CONSTRAINT IF EXISTS ck_sites_sector;")
    op.execute(
        """
        ALTER TABLE sites
        ALTER COLUMN sector TYPE sector
        USING sector::sector;
        """
    )
    op.execute("ALTER TABLE sites ALTER COLUMN sector SET DEFAULT 'generic';")

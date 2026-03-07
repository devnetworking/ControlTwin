"""Initial schema — all ControlTwin tables

Revision ID: 0001_initial
Revises:
Create Date: 2025-03-01 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            role VARCHAR(20) NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMPTZ,
            last_login TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_users_role CHECK (
                role IN ('super_admin','admin','ot_analyst','ot_operator','viewer','readonly')
            )
        );
        """
    )
    op.execute("CREATE INDEX ix_users_username ON users (username);")
    op.execute("CREATE INDEX ix_users_email ON users (email);")

    op.execute(
        """
        CREATE TABLE sites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            location VARCHAR(255),
            sector VARCHAR(30) NOT NULL DEFAULT 'generic',
            timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_sites_sector CHECK (
                sector IN ('electricity','oil','gas','water','manufacturing','generic')
            )
        );
        """
    )
    op.execute("CREATE INDEX ix_sites_name ON sites (name);")

    op.execute(
        """
        CREATE TABLE assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES sites(id) ON DELETE RESTRICT,
            parent_id UUID REFERENCES assets(id) ON DELETE SET NULL,
            name VARCHAR(100) NOT NULL,
            tag VARCHAR(50) NOT NULL,
            description TEXT,
            asset_type VARCHAR(30) NOT NULL,
            protocol VARCHAR(30) NOT NULL DEFAULT 'other',
            ip_address VARCHAR(45),
            port INTEGER,
            vendor VARCHAR(100),
            model VARCHAR(100),
            firmware_version VARCHAR(50),
            purdue_level INTEGER NOT NULL DEFAULT 1,
            criticality VARCHAR(10) NOT NULL DEFAULT 'medium',
            status VARCHAR(15) NOT NULL DEFAULT 'unknown',
            last_seen TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_assets_site_tag UNIQUE (site_id, tag),
            CONSTRAINT ck_assets_asset_type CHECK (
                asset_type IN (
                    'plc','rtu','hmi','scada_server','historian',
                    'sensor','actuator','ied','gateway','switch','turbine',
                    'transformer','pump','valve','meter'
                )
            ),
            CONSTRAINT ck_assets_protocol CHECK (
                protocol IN (
                    'modbus_tcp','modbus_rtu','opcua','dnp3','iec61850',
                    'iccp','ethernetip','profinet','bacnet','mqtt','other'
                )
            ),
            CONSTRAINT ck_assets_port CHECK (port IS NULL OR (port > 0 AND port <= 65535)),
            CONSTRAINT ck_assets_purdue_level CHECK (purdue_level >= 0 AND purdue_level <= 4),
            CONSTRAINT ck_assets_criticality CHECK (criticality IN ('critical','high','medium','low')),
            CONSTRAINT ck_assets_status CHECK (status IN ('online','offline','degraded','maintenance','unknown'))
        );
        """
    )
    op.execute("CREATE INDEX ix_assets_tag ON assets (tag);")
    op.execute("CREATE INDEX ix_assets_site_id ON assets (site_id);")
    op.execute("CREATE INDEX ix_assets_status ON assets (status);")

    op.execute(
        """
        CREATE TABLE data_points (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            tag VARCHAR(50) NOT NULL,
            data_type VARCHAR(10) NOT NULL DEFAULT 'float',
            unit VARCHAR(20),
            engineering_low DOUBLE PRECISION,
            engineering_high DOUBLE PRECISION,
            alarm_low_low DOUBLE PRECISION,
            alarm_low DOUBLE PRECISION,
            alarm_high DOUBLE PRECISION,
            alarm_high_high DOUBLE PRECISION,
            sample_interval_ms INTEGER NOT NULL DEFAULT 1000,
            is_writable BOOLEAN NOT NULL DEFAULT FALSE,
            last_value VARCHAR(255),
            last_updated TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_data_points_asset_tag UNIQUE (asset_id, tag),
            CONSTRAINT ck_data_points_data_type CHECK (
                data_type IN ('float','integer','boolean','string','enum')
            )
        );
        """
    )
    op.execute("CREATE INDEX ix_data_points_asset_id ON data_points (asset_id);")
    op.execute("CREATE INDEX ix_data_points_tag ON data_points (tag);")

    op.execute(
        """
        CREATE TABLE alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES sites(id) ON DELETE RESTRICT,
            asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            severity VARCHAR(10) NOT NULL DEFAULT 'medium',
            category VARCHAR(30) NOT NULL DEFAULT 'manual',
            mitre_technique_id VARCHAR(10),
            mitre_technique_name VARCHAR(255),
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            acknowledged_at TIMESTAMPTZ,
            resolved_at TIMESTAMPTZ,
            acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
            raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            CONSTRAINT ck_alerts_severity CHECK (
                severity IN ('critical','high','medium','low','info')
            ),
            CONSTRAINT ck_alerts_category CHECK (
                category IN (
                    'threshold_breach','anomaly_ml','communication_loss',
                    'unauthorized_command','config_change','replay_attack',
                    'dos_attempt','range_violation','sequence_violation','manual'
                )
            ),
            CONSTRAINT ck_alerts_status CHECK (
                status IN ('open','acknowledged','investigating','resolved','false_positive')
            )
        );
        """
    )
    op.execute("CREATE INDEX ix_alerts_site_id ON alerts (site_id);")
    op.execute("CREATE INDEX ix_alerts_asset_id ON alerts (asset_id);")
    op.execute("CREATE INDEX ix_alerts_severity ON alerts (severity);")
    op.execute("CREATE INDEX ix_alerts_status ON alerts (status);")
    op.execute("CREATE INDEX ix_alerts_triggered_at ON alerts (triggered_at);")

    op.execute(
        """
        CREATE TABLE collectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id UUID NOT NULL REFERENCES sites(id) ON DELETE RESTRICT,
            name VARCHAR(100) NOT NULL,
            protocol VARCHAR(30) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            poll_interval_ms INTEGER NOT NULL DEFAULT 1000,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            status VARCHAR(15) NOT NULL DEFAULT 'stopped',
            last_heartbeat TIMESTAMPTZ,
            last_error TEXT,
            points_collected_total BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_collectors_protocol CHECK (
                protocol IN ('modbus_tcp','opcua','dnp3','mqtt','iec61850')
            ),
            CONSTRAINT ck_collectors_port CHECK (port > 0 AND port <= 65535),
            CONSTRAINT ck_collectors_status CHECK (
                status IN ('running','stopped','error','connecting')
            )
        );
        """
    )
    op.execute("CREATE INDEX ix_collectors_site_id ON collectors (site_id);")
    op.execute("CREATE INDEX ix_collectors_status ON collectors (status);")

    op.execute(
        """
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(255),
            ip_address VARCHAR(45),
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);")
    op.execute("CREATE INDEX ix_audit_logs_action ON audit_logs (action);")
    op.execute("CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);")
    op.execute("CREATE INDEX ix_audit_logs_resource_type ON audit_logs (resource_type);")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )

    for table in ("users", "sites", "assets", "collectors"):
        op.execute(
            f"""
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
        )


def downgrade() -> None:
    for table in ("users", "sites", "assets", "collectors"):
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")

    op.execute("DROP TABLE IF EXISTS audit_logs;")
    op.execute("DROP TABLE IF EXISTS collectors;")
    op.execute("DROP TABLE IF EXISTS alerts;")
    op.execute("DROP TABLE IF EXISTS data_points;")
    op.execute("DROP TABLE IF EXISTS assets;")
    op.execute("DROP TABLE IF EXISTS sites;")
    op.execute("DROP TABLE IF EXISTS users;")

    op.execute('DROP EXTENSION IF EXISTS pg_trgm;')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')

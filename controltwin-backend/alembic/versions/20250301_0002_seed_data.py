"""Seed demo data for ControlTwin development

Revision ID: 0002_seed
Revises: 0001_initial
Create Date: 2025-03-01 01:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_seed"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
        VALUES
          ('admin', 'admin@controltwin.io', '$2b$12$placeholder_hash_for_dev_only_not_for_production_use_xx', 'Admin ControlTwin', 'super_admin', TRUE),
          ('operator1', 'operator1@controltwin.io', '$2b$12$placeholder_hash_for_dev_only_not_for_production_use_xx', 'Opérateur 1', 'ot_operator', TRUE),
          ('analyst1', 'analyst1@controltwin.io', '$2b$12$placeholder_hash_for_dev_only_not_for_production_use_xx', 'Analyste 1', 'ot_analyst', TRUE),
          ('viewer1', 'viewer1@controltwin.io', '$2b$12$placeholder_hash_for_dev_only_not_for_production_use_xx', 'Viewer 1', 'viewer', TRUE),
          ('readonly1', 'readonly1@controltwin.io', '$2b$12$placeholder_hash_for_dev_only_not_for_production_use_xx', 'ReadOnly 1', 'readonly', TRUE)
        ON CONFLICT (username) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO sites (name, description, location, sector, timezone, metadata)
        VALUES
          ('Centrale Électrique Nord', 'Site de production électrique principal', 'Montreal, QC', 'electricity', 'America/Toronto', '{}'::jsonb),
          ('Pipeline Gazier Est', 'Infrastructure de transport gazier', 'Quebec City, QC', 'gas', 'America/Toronto', '{}'::jsonb),
          ('Sous-station Haute Tension', 'Sous-station de distribution HT', 'Laval, QC', 'electricity', 'America/Toronto', '{}'::jsonb)
        ON CONFLICT DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO assets (
            site_id, name, tag, asset_type, protocol, ip_address, port, purdue_level, criticality, status, metadata
        )
        SELECT s.id, v.name, v.tag, v.asset_type, v.protocol, v.ip_address, v.port, v.purdue_level, v.criticality, v.status, '{}'::jsonb
        FROM (
            VALUES
            ('Centrale Électrique Nord', 'PLC-001', 'PLC-001', 'plc', 'modbus_tcp', '192.168.10.10', 502, 1, 'critical', 'online'),
            ('Centrale Électrique Nord', 'PLC-002', 'PLC-002', 'plc', 'modbus_tcp', '192.168.10.11', 502, 1, 'critical', 'online'),
            ('Centrale Électrique Nord', 'HMI-001', 'HMI-001', 'hmi', 'opcua', '192.168.10.20', 4840, 2, 'high', 'online'),
            ('Centrale Électrique Nord', 'SCADA-001', 'SCADA-001', 'scada_server', 'opcua', '192.168.10.30', 4840, 3, 'critical', 'online'),
            ('Centrale Électrique Nord', 'TURB-001', 'TURB-001', 'turbine', 'modbus_tcp', '192.168.10.40', 502, 0, 'critical', 'online'),
            ('Centrale Électrique Nord', 'TURB-002', 'TURB-002', 'turbine', 'modbus_tcp', '192.168.10.41', 502, 0, 'critical', 'degraded'),
            ('Centrale Électrique Nord', 'TRANS-001', 'TRANS-001', 'transformer', 'modbus_tcp', '192.168.10.50', 502, 0, 'critical', 'online'),
            ('Centrale Électrique Nord', 'METER-001', 'METER-001', 'meter', 'modbus_tcp', '192.168.10.60', 502, 1, 'medium', 'online'),

            ('Pipeline Gazier Est', 'RTU-001', 'RTU-001', 'rtu', 'modbus_tcp', '10.0.1.10', 502, 1, 'critical', 'online'),
            ('Pipeline Gazier Est', 'RTU-002', 'RTU-002', 'rtu', 'dnp3', '10.0.1.11', 20000, 1, 'critical', 'offline'),
            ('Pipeline Gazier Est', 'PUMP-001', 'PUMP-001', 'pump', 'modbus_tcp', '10.0.1.20', 502, 0, 'high', 'online'),
            ('Pipeline Gazier Est', 'VALVE-001', 'VALVE-001', 'valve', 'modbus_tcp', '10.0.1.30', 502, 0, 'high', 'online'),
            ('Pipeline Gazier Est', 'HIST-001', 'HIST-001', 'historian', 'opcua', '10.0.1.100', 4840, 3, 'medium', 'online'),

            ('Sous-station Haute Tension', 'IED-001', 'IED-001', 'ied', 'iec61850', '172.16.0.10', 102, 1, 'critical', 'online'),
            ('Sous-station Haute Tension', 'IED-002', 'IED-002', 'ied', 'iec61850', '172.16.0.11', 102, 1, 'critical', 'online'),
            ('Sous-station Haute Tension', 'SWITCH-001', 'SWITCH-001', 'switch', 'other', '172.16.0.100', NULL, 2, 'medium', 'online'),
            ('Sous-station Haute Tension', 'GATEWAY-001', 'GATEWAY-001', 'gateway', 'mqtt', '172.16.0.200', 1883, 2, 'high', 'online')
        ) AS v(site_name, name, tag, asset_type, protocol, ip_address, port, purdue_level, criticality, status)
        JOIN sites s ON s.name = v.site_name
        ON CONFLICT (site_id, tag) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO data_points (
            asset_id, name, tag, data_type, unit,
            engineering_low, engineering_high, alarm_high, alarm_high_high,
            is_writable, metadata
        )
        SELECT a.id, v.name, v.tag, v.data_type, v.unit,
               v.eng_low, v.eng_high, v.alarm_high, v.alarm_hh, FALSE, '{}'::jsonb
        FROM (
            VALUES
            ('PLC-001', 'temperature_1', 'TEMP_001', 'float', '°C', -10.0, 150.0, 120.0, 140.0),
            ('PLC-001', 'pressure_1', 'PRESS_001', 'float', 'bar', 0.0, 20.0, 18.0, 19.5),
            ('PLC-001', 'run_status', 'STATUS_001', 'boolean', NULL, NULL, NULL, NULL, NULL),
            ('PLC-001', 'motor_speed', 'SPEED_001', 'float', 'rpm', 0.0, 3600.0, 3400.0, NULL),

            ('TURB-001', 'turbine_temp', 'TURB_TEMP', 'float', '°C', 0.0, 600.0, 550.0, 580.0),
            ('TURB-001', 'turbine_speed', 'TURB_SPEED', 'float', 'rpm', 0.0, 3000.0, 2900.0, NULL),
            ('TURB-001', 'active_power', 'TURB_POWER', 'float', 'MW', 0.0, 500.0, NULL, NULL),
            ('TURB-001', 'vibration', 'TURB_VIB', 'float', 'mm/s', 0.0, 10.0, 7.0, 9.0),

            ('PUMP-001', 'flow_rate', 'PUMP_FLOW', 'float', 'm³/h', 0.0, 1000.0, 900.0, NULL),
            ('PUMP-001', 'outlet_pressure', 'PUMP_PRESS', 'float', 'bar', 0.0, 80.0, 75.0, 78.0),
            ('PUMP-001', 'bearing_temp', 'PUMP_TEMP', 'float', '°C', 0.0, 100.0, 85.0, 95.0),
            ('PUMP-001', 'pump_status', 'PUMP_STATUS', 'boolean', NULL, NULL, NULL, NULL, NULL)
        ) AS v(asset_tag, name, tag, data_type, unit, eng_low, eng_high, alarm_high, alarm_hh)
        JOIN assets a ON a.tag = v.asset_tag
        ON CONFLICT (asset_id, tag) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO collectors (
            site_id, name, protocol, host, port, config, poll_interval_ms, status
        )
        SELECT s.id, v.name, v.protocol, v.host, v.port, '{}'::jsonb, v.poll_interval_ms, v.status
        FROM (
            VALUES
            ('Centrale Électrique Nord', 'Modbus Collector Nord', 'modbus_tcp', '192.168.10.10', 502, 1000, 'running'),
            ('Centrale Électrique Nord', 'OPC-UA Collector Nord', 'opcua', '192.168.10.30', 4840, 500, 'stopped')
        ) AS v(site_name, name, protocol, host, port, poll_interval_ms, status)
        JOIN sites s ON s.name = v.site_name;
        """
    )

    op.execute(
        """
        WITH admin_user AS (
            SELECT id FROM users WHERE username = 'admin' LIMIT 1
        )
        INSERT INTO alerts (
            site_id, asset_id, title, description, severity, category,
            mitre_technique_id, mitre_technique_name, status, acknowledged_by,
            raw_data, metadata
        )
        SELECT
            s.id,
            a.id,
            v.title,
            v.description,
            v.severity,
            v.category,
            v.mitre_technique_id,
            v.mitre_technique_name,
            v.status,
            CASE WHEN v.status = 'acknowledged' THEN (SELECT id FROM admin_user) ELSE NULL END,
            '{}'::jsonb,
            '{}'::jsonb
        FROM (
            VALUES
            ('Centrale Électrique Nord', 'TURB-002', 'TURB-002 Vibration dépassement critique', 'Vibration anormale au-dessus du seuil HH', 'critical', 'threshold_breach', 'T0801', 'Damage to Property', 'open'),
            ('Pipeline Gazier Est', 'RTU-002', 'RTU-002 Communication perdue', 'Perte de communication depuis 5 minutes', 'high', 'communication_loss', 'T0827', 'Loss of Control', 'acknowledged'),
            ('Centrale Électrique Nord', 'PLC-001', 'PLC-001 Anomalie détectée sur TEMP_001', 'Déviation détectée par modèle ML', 'medium', 'anomaly_ml', 'T0801', 'Damage to Property', 'open'),
            ('Centrale Électrique Nord', 'SCADA-001', 'SCADA-001 Changement de configuration détecté', 'Modification de configuration hors fenêtre', 'low', 'config_change', 'T0836', 'Modify Program', 'resolved'),
            ('Centrale Électrique Nord', 'TURB-001', 'Maintenance planifiée TURB-001', 'Intervention maintenance préventive', 'info', 'manual', NULL, NULL, 'open')
        ) AS v(site_name, asset_tag, title, description, severity, category, mitre_technique_id, mitre_technique_name, status)
        JOIN sites s ON s.name = v.site_name
        LEFT JOIN assets a ON a.tag = v.asset_tag;
        """
    )

    op.execute(
        """
        WITH admin_user AS (
            SELECT id FROM users WHERE username = 'admin' LIMIT 1
        ),
        one_alert AS (
            SELECT id FROM alerts ORDER BY triggered_at DESC LIMIT 1
        )
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, ip_address, details)
        VALUES
          ((SELECT id FROM admin_user), 'user_login', 'user', (SELECT id::text FROM admin_user), '127.0.0.1', '{"username":"admin"}'::jsonb),
          ((SELECT id FROM admin_user), 'asset_created', 'asset', (SELECT id::text FROM (SELECT id FROM assets WHERE tag = 'PLC-001' LIMIT 1) a), '127.0.0.1', '{"tag":"PLC-001"}'::jsonb),
          ((SELECT id FROM admin_user), 'alert_acknowledged', 'alert', (SELECT id::text FROM one_alert), '127.0.0.1', '{}'::jsonb);
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM audit_logs WHERE action IN ('user_login','asset_created','alert_acknowledged');")
    op.execute(
        """
        DELETE FROM alerts
        WHERE title IN (
            'TURB-002 Vibration dépassement critique',
            'RTU-002 Communication perdue',
            'PLC-001 Anomalie détectée sur TEMP_001',
            'SCADA-001 Changement de configuration détecté',
            'Maintenance planifiée TURB-001'
        );
        """
    )
    op.execute(
        """
        DELETE FROM data_points
        WHERE tag IN (
            'TEMP_001','PRESS_001','STATUS_001','SPEED_001',
            'TURB_TEMP','TURB_SPEED','TURB_POWER','TURB_VIB',
            'PUMP_FLOW','PUMP_PRESS','PUMP_TEMP','PUMP_STATUS'
        );
        """
    )
    op.execute(
        """
        DELETE FROM assets
        WHERE tag IN (
            'PLC-001','PLC-002','HMI-001','SCADA-001','TURB-001','TURB-002','TRANS-001','METER-001',
            'RTU-001','RTU-002','PUMP-001','VALVE-001','HIST-001',
            'IED-001','IED-002','SWITCH-001','GATEWAY-001'
        );
        """
    )
    op.execute("DELETE FROM collectors WHERE name IN ('Modbus Collector Nord','OPC-UA Collector Nord');")
    op.execute(
        """
        DELETE FROM sites
        WHERE name IN ('Centrale Électrique Nord','Pipeline Gazier Est','Sous-station Haute Tension');
        """
    )
    op.execute(
        """
        DELETE FROM users
        WHERE username IN ('admin','operator1','analyst1','viewer1','readonly1');
        """
    )

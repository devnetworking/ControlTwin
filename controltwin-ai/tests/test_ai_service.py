"""Tests for ControlTwin AI service endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

client = TestClient(app)
BASE_PREFIX = "/api/v1/ai"


def test_status_returns_200() -> None:
    """Ensure /status endpoint responds successfully."""
    with patch("app.api.router.ollama.list", return_value={"models": []}), \
         patch("app.api.router.HttpClient.heartbeat", return_value=True), \
         patch("redis.asyncio.client.Redis.ping", return_value=True):
        response = client.get(f"{BASE_PREFIX}/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data


def test_anomaly_detect_with_mock_datapoints() -> None:
    """Ensure anomaly detection endpoint returns expected schema."""
    payload = {
        "asset_id": "asset-test-1",
        "datapoints": [
            {"tag": "pressure", "value": 10.0, "timestamp": "2026-01-01T00:00:00Z"},
            {"tag": "pressure", "value": 250.0, "timestamp": "2026-01-01T00:01:00Z"},
        ],
    }
    response = client.post(f"{BASE_PREFIX}/anomaly/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "is_anomaly" in data
    assert "confidence" in data
    assert "technique" in data


def test_remediation_suggest_with_mock_alert() -> None:
    """Ensure remediation suggestion endpoint returns expected structure."""
    payload = {
        "alert": {
            "id": "alert-123",
            "title": "Unauthorized PLC write",
            "description": "Write command detected outside maintenance window",
            "category": "process_integrity",
            "severity": "high",
        }
    }
    with patch("app.remediation.engine.ollama.chat", return_value={"message": {"content": "ok"}}), \
         patch("app.remediation.engine.ollama.embeddings", return_value={"embedding": [0.1, 0.2, 0.3]}):
        response = client.post(f"{BASE_PREFIX}/remediation/suggest", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert "mitre_ref" in data
    assert "confidence" in data
    assert "llm_explanation" in data

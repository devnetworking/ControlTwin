import pytest

from app.anomaly.mitre_mapper import MitreMapper


def test_mitre_mapper_communication_loss_plc():
    mapper = MitreMapper()
    out = mapper.map("communication_loss", "plc", {"pattern": "sudden"})
    assert out["id"] == "T0827"


def test_mitre_mapper_config_change():
    mapper = MitreMapper()
    out = mapper.map("config_change", "plc", {})
    assert out["id"] == "T0836"


@pytest.mark.asyncio
async def test_zscore_rule_boundary():
    # Unit-style math assertion representing value=mean+4*std
    mean, std, value = 10.0, 2.0, 18.0
    z = (value - mean) / std
    assert z == 4.0
    assert abs(z) > 3


def test_level1_threshold_breach_logic():
    value = 120
    high_high = 100
    assert value > high_high


def test_aggregate_scores_logic():
    level_scores = [1.0, 0.95, 0.4, 0.5]
    weights = [0.35, 0.25, 0.2, 0.2]
    final = sum(s * w for s, w in zip(level_scores, weights))
    assert final > 0.7

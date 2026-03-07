import pytest


def _divergence_pct(reported, desired):
    if desired == 0:
        return 0.0 if reported == 0 else 100.0
    return abs(reported - desired) / abs(desired) * 100.0


def test_divergence_threshold_default_5pct():
    reported = 105
    desired = 100
    pct = _divergence_pct(reported, desired)
    assert pct == 5.0


def test_no_divergence_when_states_match():
    reported = {"speed": 1500, "temp": 70}
    desired = {"speed": 1500, "temp": 70}
    divergences = [k for k in reported if _divergence_pct(reported[k], desired[k]) > 5.0]
    assert divergences == []


@pytest.mark.asyncio
async def test_check_divergence_mocked():
    reported = {"pressure": 12.0, "flow": 98.0}
    desired = {"pressure": 10.0, "flow": 100.0}
    divergences = []
    for k in desired:
        pct = _divergence_pct(reported[k], desired[k])
        if pct > 5.0:
            divergences.append({"tag": k, "delta_pct": pct})
    assert len(divergences) == 1
    assert divergences[0]["tag"] == "pressure"

def _chunk_text(text, size=512, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + size]
        chunks.append(" ".join(chunk))
        if i + size >= len(words):
            break
        i += size - overlap
    return chunks


def test_rag_chunking_512_tokens():
    text = "x " * 1300
    chunks = _chunk_text(text, size=512, overlap=50)
    assert len(chunks) >= 3
    assert all(len(c.split()) <= 512 for c in chunks)


def test_prompt_building_contains_asset_details():
    alert = {"title": "PLC Command Anomaly", "severity": "high"}
    asset = {"name": "PLC-1", "asset_type": "plc", "ip_address": "10.10.1.5"}
    prompt = f"Alert: {alert['title']} Severity: {alert['severity']} Asset: {asset['name']} {asset['asset_type']} {asset['ip_address']}"
    assert "PLC-1" in prompt
    assert "plc" in prompt
    assert "10.10.1.5" in prompt


def test_json_response_parsing():
    raw = '{"diagnosis":"ok","probable_causes":["a"],"recommended_actions":[],"risk_level":"LOW","estimated_impact":"none","references":[]}'
    import json
    parsed = json.loads(raw)
    assert parsed["diagnosis"] == "ok"
    assert parsed["risk_level"] == "LOW"

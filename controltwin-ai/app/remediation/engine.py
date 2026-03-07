from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import ollama
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger
from app.remediation.rag import RAGRetriever


class RemediationEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.remediation")
        self.rag = RAGRetriever()
        self.engine = create_async_engine(self.settings.postgres_dsn, future=True, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS remediation_suggestions (
                    id SERIAL PRIMARY KEY,
                    suggestion_id VARCHAR(128) UNIQUE NOT NULL,
                    alert_id VARCHAR(128) NOT NULL,
                    asset_id VARCHAR(128) NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS remediation_feedback (
                    id SERIAL PRIMARY KEY,
                    suggestion_id VARCHAR(128) NOT NULL,
                    was_helpful BOOLEAN,
                    applied_action TEXT,
                    outcome TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """))

    async def suggest(self, alert_id: str, asset_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        start = time.perf_counter()

        alert = await self._fetch_backend(f"/alerts/{alert_id}")
        asset = await self._fetch_backend(f"/assets/{asset_id}")
        anomaly_summary = await self._fetch_anomaly_summary(asset_id)
        rag_chunks = await self.rag.retrieve(f"{alert.get('title', '')} {asset.get('asset_type', '')}", n_results=5)
        rag_context = "\n".join([f"- {c['content'][:400]}" for c in rag_chunks])

        prompt = f"""
You are a cybersecurity expert in Industrial Control Systems (ICS/OT).

ALERT:
- Title: {alert.get("title")}
- Category: {alert.get("category")}
- Severity: {alert.get("severity")}
- MITRE Technique: {alert.get("mitre_technique_id")} - {alert.get("mitre_technique_name")}
- Triggered: {alert.get("triggered_at")}

AFFECTED ASSET:
- Name: {asset.get("name")}, Tag: {asset.get("tag")}
- Type: {asset.get("asset_type")}, Protocol: {asset.get("protocol")}
- IP: {asset.get("ip_address")}, Purdue Level: {asset.get("purdue_level")}
- Criticality: {asset.get("criticality")}

RECENT ANOMALY HISTORY (last 24h):
{anomaly_summary}

RELEVANT KNOWLEDGE BASE:
{rag_context}

Respond with a JSON object:
{{
  "diagnosis": "...",
  "probable_causes": ["...", "...", "..."],
  "recommended_actions": [
    {{"action": "...", "priority": "immediate|short_term|long_term", "risk": "low|medium|high"}}
  ],
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "estimated_impact": "...",
  "references": ["IEC standard or MITRE technique referenced"]
}}

CRITICAL: Never suggest automated writes to ICS equipment.
All actions must require human validation before execution.
""".strip()

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        try:
            resp = ollama.chat(
                model=self.settings.ollama_model_mistral,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},
            )
            raw = resp.get("message", {}).get("content", "{}")
            parsed = self._safe_parse_json(raw)
        except Exception:
            parsed = {
                "error": "LLM unavailable",
                "fallback": "rule-based suggestion",
                "diagnosis": "Manual investigation required due to local LLM unavailability.",
                "probable_causes": ["Sensor drift", "Network latency", "Unauthorized configuration change"],
                "recommended_actions": [
                    {"action": "Validate PLC/HMI setpoints against historian", "priority": "immediate", "risk": "low"},
                    {"action": "Inspect network path and packet integrity", "priority": "short_term", "risk": "medium"},
                ],
                "risk_level": "MEDIUM",
                "estimated_impact": "Potential process instability if unresolved.",
                "references": ["MITRE ICS"],
            }

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        suggestion_id = f"sug_{int(time.time() * 1000)}"
        payload = {
            "suggestion_id": suggestion_id,
            "diagnosis": parsed.get("diagnosis"),
            "probable_causes": parsed.get("probable_causes", []),
            "recommended_actions": parsed.get("recommended_actions", []),
            "risk_level": parsed.get("risk_level", "MEDIUM"),
            "estimated_impact": parsed.get("estimated_impact"),
            "references": parsed.get("references", []),
            "generated_by": f"ollama/{self.settings.ollama_model_mistral}",
            "kb_sources_used": [c["metadata"].get("doc_id") for c in rag_chunks if c.get("metadata")],
            "processing_time_ms": elapsed_ms,
            "model_version": self.settings.ollama_model_mistral,
            "confidence": 0.75,
            "safety_notice": "suggestions_only_no_auto_execution",
        }

        async with self.session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO remediation_suggestions (suggestion_id, alert_id, asset_id, payload)
                    VALUES (:sid, :aid, :asset, CAST(:payload AS JSONB))
                """),
                {"sid": suggestion_id, "aid": alert_id, "asset": asset_id, "payload": json.dumps(payload)},
            )
            await session.commit()

        self.logger.info(
            "remediation suggestion generated",
            extra={
                "event": "llm_call",
                "model": self.settings.ollama_model_mistral,
                "prompt_hash": prompt_hash,
                "response_time_ms": elapsed_ms,
                "tokens_used": 0,
                "alert_id": alert_id,
                "asset_id": asset_id,
            },
        )
        return payload

    async def add_feedback(self, suggestion_id: str, was_helpful: bool, applied_action: str, outcome: str) -> dict[str, Any]:
        async with self.session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO remediation_feedback (suggestion_id, was_helpful, applied_action, outcome)
                    VALUES (:s, :h, :a, :o)
                """),
                {"s": suggestion_id, "h": was_helpful, "a": applied_action, "o": outcome},
            )
            await session.commit()
        return {"status": "ok", "suggestion_id": suggestion_id}

    async def history(self, alert_id: str) -> list[dict[str, Any]]:
        async with self.session_factory() as session:
            res = await session.execute(
                text("SELECT suggestion_id, payload, created_at FROM remediation_suggestions WHERE alert_id=:a ORDER BY created_at DESC"),
                {"a": alert_id},
            )
            rows = res.fetchall()
        return [{"suggestion_id": r[0], **(r[1] or {}), "created_at": r[2].isoformat() if r[2] else None} for r in rows]

    async def _fetch_backend(self, suffix: str) -> dict[str, Any]:
        url = f"{self.settings.backend_base_url}{suffix}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url)
                r.raise_for_status()
                return r.json()
        except Exception:
            return {}

    async def _fetch_anomaly_summary(self, asset_id: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"http://localhost:8001/api/v1/ai/anomaly/history/{asset_id}?hours=24")
                if r.status_code == 200:
                    data = r.json()
                    return json.dumps(data, ensure_ascii=False)[:3000]
        except Exception:
            pass
        return "No recent anomaly history available."

    @staticmethod
    def _safe_parse_json(raw: str) -> dict[str, Any]:
        raw = raw.strip()
        try:
            return json.loads(raw)
        except Exception:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start:end + 1])
                except Exception:
                    pass
        return {"diagnosis": raw[:300], "probable_causes": [], "recommended_actions": [], "risk_level": "MEDIUM", "estimated_impact": "", "references": []}

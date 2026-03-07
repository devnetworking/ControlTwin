from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import ollama

from app.core.config import get_settings
from app.core.logging import get_logger


class ScenarioGenerator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.scenario-generator")

    async def generate(self, natural_language_prompt: str, asset: dict[str, Any], twin_state: dict[str, Any]) -> dict[str, Any]:
        prompt = f"""
Convert this simulation request into structured parameters for an ICS simulation.

Request: {natural_language_prompt}
Asset: {asset.get("name")} ({asset.get("asset_type")})
Current state: {twin_state.get("reported_state")}

Respond ONLY with valid JSON:
{{
  "parameter_overrides": {{"tag_name": 0}},
  "failure_conditions": [{{"tag": "...", "threshold": 0, "direction": "above|below"}}],
  "cascade_rules": [{{"trigger_asset": "...", "affected_asset": "...", "delay_minutes": 1}}],
  "duration_hours": 24,
  "n_iterations": 1000
}}
""".strip()

        ph = hashlib.sha256(prompt.encode()).hexdigest()
        start = time.perf_counter()
        try:
            resp = ollama.chat(
                model=self.settings.ollama_model_mistral,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},
            )
            content = resp.get("message", {}).get("content", "{}")
            data = self._parse_json(content)
        except Exception:
            data = {
                "error": "LLM unavailable",
                "fallback": "rule-based suggestion",
                "parameter_overrides": {},
                "failure_conditions": [],
                "cascade_rules": [],
                "duration_hours": 24,
                "n_iterations": 1000,
            }

        self.logger.info(
            "scenario generation complete",
            extra={
                "event": "llm_call",
                "prompt_hash": ph,
                "model": self.settings.ollama_model_mistral,
                "response_time_ms": int((time.perf_counter() - start) * 1000),
                "tokens_used": 0,
            },
        )
        return data

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except Exception:
            s, e = content.find("{"), content.rfind("}")
            if s != -1 and e != -1 and e > s:
                try:
                    return json.loads(content[s:e + 1])
                except Exception:
                    pass
        return {
            "parameter_overrides": {},
            "failure_conditions": [],
            "cascade_rules": [],
            "duration_hours": 24,
            "n_iterations": 1000,
        }

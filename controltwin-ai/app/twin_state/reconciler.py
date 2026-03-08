import hashlib
import json
import time
from typing import Any

import ollama

from app.core.config import get_settings
from app.core.logging import get_logger


class LLMReconciler:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.reconciler")

    async def explain_divergence(self, asset: dict[str, Any], divergences: list[dict[str, Any]], context: list[dict[str, Any]]) -> str:
        lines = []
        for d in divergences:
            lines.append(
                f"- {d.get('tag')}: desired={d.get('desired')}, reported={d.get('reported')}, "
                f"delta={d.get('delta_pct', 0):.2f}%, duration={d.get('duration_minutes', 0):.1f} min"
            )
        context_values = "\n".join([json.dumps(v, ensure_ascii=False) for v in context[:10]])

        prompt = f"""
You are an ICS/SCADA expert analyzing a Digital Twin divergence.

Asset: {asset.get("name", "unknown")} ({asset.get("asset_type", "unknown")}) at site {asset.get("site_name", "unknown")}
Protocol: {asset.get("protocol", "unknown")}, IP: {asset.get("ip_address", "unknown")}
Purdue Level: {asset.get("purdue_level", "unknown")}

Divergences detected:
{chr(10).join(lines)}

Last 10 sensor values for context:
{context_values}

Provide:
1. Most probable root cause (1-2 sentences, technical, OT-specific)
2. Recommended immediate actions (max 3 bullet points)
3. Risk level: LOW / MEDIUM / HIGH / CRITICAL

Respond in the same language as the asset's site timezone country.
Be concise and technical. No disclaimers.
""".strip()

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        start = time.perf_counter()
        try:
            response = ollama.chat(
                model=self.settings.ollama_model_mistral,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            text = response.get("message", {}).get("content", "").strip()
            self.logger.info(
                "llm divergence explanation generated",
                extra={
                    "event": "llm_call",
                    "model": self.settings.ollama_model_mistral,
                    "prompt_hash": prompt_hash,
                    "response_time_ms": elapsed_ms,
                    "tokens_used": 0,
                },
            )
            return text or "No explanation generated."
        except Exception:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self.logger.exception(
                "ollama unavailable",
                extra={
                    "event": "llm_call_failed",
                    "model": self.settings.ollama_model_mistral,
                    "prompt_hash": prompt_hash,
                    "response_time_ms": elapsed_ms,
                    "tokens_used": 0,
                },
            )
            fallback = {
                "error": "LLM unavailable",
                "fallback": "rule-based suggestion: verify sensor calibration, communication quality, and setpoint propagation path.",
            }
            return json.dumps(fallback, ensure_ascii=False)

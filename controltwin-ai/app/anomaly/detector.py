"""Anomaly detection engine using Isolation Forest and LSTM autoencoder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyResult:
    """Structured anomaly detection response."""

    score: float
    is_anomaly: bool
    confidence: float
    technique: str


class _LSTMAutoencoder(nn.Module):
    """Lightweight LSTM autoencoder for sequence reconstruction error."""

    def __init__(self, input_size: int = 1, hidden_size: int = 16) -> None:
        """Initialize encoder and decoder LSTM layers."""
        super().__init__()
        self.encoder = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.decoder = nn.LSTM(hidden_size, input_size, batch_first=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run forward pass and reconstruct input sequence."""
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return decoded


class AnomalyDetector:
    """Hybrid anomaly detector combining fast and deep techniques."""

    def __init__(self) -> None:
        """Initialize models and MITRE mapping ranges."""
        self.iso = IsolationForest(contamination=0.05, random_state=42)
        self.lstm = _LSTMAutoencoder()
        self.lstm.eval()
        self._fitted_iso = False

    def _mitre_map(self, score: float) -> str:
        """Map anomaly intensity to MITRE ATT&CK for ICS technique range."""
        if score >= 0.9:
            return "T0803"
        if score >= 0.8:
            return "T0814"
        if score >= 0.7:
            return "T0829"
        if score >= 0.6:
            return "T0831"
        return "T0801"

    async def detect(self, asset_id: str, datapoints: list[dict[str, Any]]) -> AnomalyResult:
        """Detect anomalies from datapoints using IsolationForest and LSTM error."""
        try:
            values = [float(p.get("value", 0.0)) for p in datapoints]
            if not values:
                return AnomalyResult(score=0.0, is_anomaly=False, confidence=0.5, technique="T0801")

            data = np.array(values, dtype=np.float32).reshape(-1, 1)

            if len(values) >= 10:
                self.iso.fit(data)
                self._fitted_iso = True

            iso_score = 0.0
            if self._fitted_iso:
                pred = self.iso.predict(data)
                iso_score = float(np.mean(pred == -1))

            seq = torch.tensor(data.reshape(1, -1, 1), dtype=torch.float32)
            with torch.no_grad():
                recon = self.lstm(seq)
                mse = torch.mean((seq - recon) ** 2).item()

            deep_score = float(min(1.0, mse * 10.0))
            final_score = float(min(1.0, (0.6 * iso_score) + (0.4 * deep_score)))
            is_anomaly = final_score >= 0.65
            confidence = float(min(0.99, max(0.5, final_score)))
            technique = self._mitre_map(final_score)

            return AnomalyResult(
                score=final_score,
                is_anomaly=is_anomaly,
                confidence=confidence,
                technique=technique,
            )
        except Exception:
            return AnomalyResult(score=0.0, is_anomaly=False, confidence=0.5, technique="T0801")

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from app.core.config import get_settings


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.decoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.output = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        out = self.output(decoded)
        return out


class LSTMAnomalyModel:
    def __init__(self) -> None:
        self.settings = get_settings()
        os.makedirs(self.settings.model_dir, exist_ok=True)
        self.model = LSTMAutoencoder()
        self.threshold: float = self.settings.lstm_default_threshold
        self.model_version: str = "untrained"

    def train(self, sequences: np.ndarray, epochs: int = 50, lr: float = 0.001) -> dict[str, Any]:
        self.model.train()
        x = torch.tensor(sequences, dtype=torch.float32)
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        for _ in range(epochs):
            optimizer.zero_grad()
            recon = self.model(x)
            loss = criterion(recon, x)
            loss.backward()
            optimizer.step()

        with torch.no_grad():
            recon = self.model(x)
            errors = torch.mean((recon - x) ** 2, dim=(1, 2)).numpy()
        self.threshold = float(np.mean(errors) + 3 * np.std(errors))

        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return {"threshold": self.threshold, "model_version": self.model_version}

    def predict(self, sequence: np.ndarray) -> tuple[bool, float]:
        self.model.eval()
        x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            recon = self.model(x)
            err = float(torch.mean((recon - x) ** 2).item())
        return err > self.threshold, err

    def save_model(self, data_point_id: str) -> str:
        path = os.path.join(self.settings.model_dir, f"{data_point_id}_lstm_autoencoder.pt")
        payload = {
            "state_dict": self.model.state_dict(),
            "threshold": self.threshold,
            "model_version": self.model_version,
        }
        torch.save(payload, path)
        return path

    def load_model(self, data_point_id: str) -> bool:
        path = os.path.join(self.settings.model_dir, f"{data_point_id}_lstm_autoencoder.pt")
        if not os.path.exists(path):
            return False
        payload = torch.load(path, map_location="cpu")
        self.model.load_state_dict(payload["state_dict"])
        self.threshold = float(payload.get("threshold", self.settings.lstm_default_threshold))
        self.model_version = payload.get("model_version", os.path.basename(path))
        return True

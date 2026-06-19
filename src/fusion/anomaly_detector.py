"""Autoencoder-based anomaly detector for fused thermal features."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


class ThermalAutoencoder(nn.Module):
    def __init__(self, input_dim: int = 12, latent_dim: int = 4) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out: torch.Tensor = self.decoder(self.encoder(x))
        return out


class AnomalyDetector:
    def __init__(
        self,
        input_dim: int = 12,
        model_path: str | None = None,
        threshold: float = 0.05,
    ) -> None:
        self.model = ThermalAutoencoder(input_dim=input_dim)
        if model_path and Path(model_path).exists():
            self.model.load_state_dict(
                torch.load(model_path, map_location="cpu", weights_only=True)
            )
        self.model.eval()
        self.threshold = threshold

    def score(self, features: np.ndarray) -> float:
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            recon = self.model(x)
        return float(nn.functional.mse_loss(recon, x).item())

    def predict(self, features: np.ndarray) -> bool:
        return self.score(features) > self.threshold

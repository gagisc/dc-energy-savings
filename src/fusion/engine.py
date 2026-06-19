"""Thermal + contact sensor fusion engine."""

from __future__ import annotations

import numpy as np
import pandas as pd


class FusionEngine:
    def __init__(
        self,
        frame_percentiles: list[int] | None = None,
        hotspot_threshold: float = 9500.0,
    ) -> None:
        self.frame_percentiles = frame_percentiles or [50, 75, 90, 95, 99]
        self.hotspot_threshold = hotspot_threshold

    def extract_frame_features(self, frame: np.ndarray) -> dict:
        flat = frame.ravel().astype(float)
        feat = {
            "frame_mean": float(np.mean(flat)),
            "frame_std": float(np.std(flat)),
            "frame_max": float(np.max(flat)),
            "hotspot_fraction": float(np.mean(flat > self.hotspot_threshold)),
        }
        for p in self.frame_percentiles:
            feat[f"frame_p{p}"] = float(np.percentile(flat, p))
        return feat

    def fuse(self, frame_features: dict, sensor_readings: list) -> dict:
        fused = dict(frame_features)
        temps = [r["temp_c"] for r in sensor_readings if "temp_c" in r]
        if temps:
            fused.update(
                {
                    "ds18b20_mean": float(np.mean(temps)),
                    "ds18b20_max": float(np.max(temps)),
                    "ds18b20_std": float(np.std(temps)),
                }
            )
        return fused

    def to_series(self, fused: dict) -> pd.Series:
        return pd.Series(fused)

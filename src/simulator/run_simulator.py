"""
Synthetic data generator — produces thermal PNG frames + sensor CSV + fused CSV.

Usage: python src/simulator/run_simulator.py --n-frames 200
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]


def gen_frame(rng: np.random.Generator, h: int = 240, w: int = 320) -> np.ndarray:
    frame = rng.normal(8000, 200, (h, w)).astype(np.float32)
    if rng.random() < 0.08:
        cx, cy = int(rng.integers(60, w - 60)), int(rng.integers(60, h - 60))
        yy, xx = np.ogrid[:h, :w]
        frame[(xx - cx) ** 2 + (yy - cy) ** 2 < 35**2] += rng.integers(600, 1800)
    return np.clip(frame, 0, 65535).astype(np.uint16)


def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
    norm = (frame.astype(np.float32) / 65535.0 * 255).astype(np.uint8)
    return np.stack(
        [
            norm,
            (norm * 0.4).astype(np.uint8),
            np.clip(255 - norm.astype(np.int32), 0, 255).astype(np.uint8),
        ],
        axis=-1,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-frames", type=int, default=100)
    ap.add_argument("--n-sensors", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default="data/samples")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    out = Path(args.out_dir)
    frames_dir = out / "thermal_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    sids = [f"28-SIM{i:04X}" for i in range(args.n_sensors)]
    sensor_rows, fused_rows = [], []
    t0 = time.time()
    for i in range(args.n_frames):
        ts = t0 + i * 5
        frame = gen_frame(rng)
        if Image:
            Image.fromarray(frame_to_rgb(frame), "RGB").save(frames_dir / f"frame_{i:05d}.png")
        temps: list[float] = []
        for sid in sids:
            temp = 24.0 + rng.normal(0, 0.5) + (rng.uniform(2, 6) if rng.random() < 0.04 else 0)
            temp = round(float(temp), 2)
            sensor_rows.append({"timestamp": ts, "device_id": sid, "temp_c": temp})
            temps.append(temp)
        flat = frame.ravel().astype(float)
        fused_rows.append(
            {
                "timestamp": ts,
                "frame_mean": np.mean(flat),
                "frame_std": np.std(flat),
                "frame_max": np.max(flat),
                "frame_p90": np.percentile(flat, 90),
                "frame_p99": np.percentile(flat, 99),
                "hotspot_fraction": np.mean(flat > 9500),
                "ds18b20_mean": np.mean(temps),
                "ds18b20_max": np.max(temps),
                "ds18b20_std": np.std(temps),
            }
        )
    with open(out / "sensor_readings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "device_id", "temp_c"])
        w.writeheader()
        w.writerows(sensor_rows)
    with open(out / "fused_features.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fused_rows[0].keys()))
        w.writeheader()
        w.writerows(fused_rows)
    print(f"Done — {args.n_frames} frames + CSVs written to {out}/")


if __name__ == "__main__":
    main()

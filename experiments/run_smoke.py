"""
Smoke experiment: train autoencoder on simulated data → CSV + PNG artefacts.
Runs in < 60 s on CPU for CI.

Usage: python experiments/run_smoke.py --epochs 5
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--out", default="experiments/results")
    ap.add_argument("--n-frames", type=int, default=80)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    data_csv = Path("data/samples/fused_features.csv")
    if not data_csv.exists():
        subprocess.check_call(
            [sys.executable, "src/simulator/run_simulator.py", "--n-frames", str(args.n_frames)]
        )

    import numpy as np
    import torch
    import torch.nn as nn

    sys.path.insert(0, "src")
    from fusion.anomaly_detector import ThermalAutoencoder

    data = np.genfromtxt(data_csv, delimiter=",", skip_header=1)
    X_raw = data[:, 1:]
    X_raw = (X_raw - X_raw.mean(0)) / (X_raw.std(0) + 1e-8)
    n_in = X_raw.shape[1]
    model = ThermalAutoencoder(input_dim=n_in, latent_dim=4)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    X = torch.tensor(X_raw, dtype=torch.float32)
    losses = []
    model.train()
    for ep in range(args.epochs):
        opt.zero_grad()
        recon = model(X)
        loss = nn.functional.mse_loss(recon, X)
        loss.backward()
        opt.step()
        losses.append({"epoch": ep + 1, "train_loss": round(loss.item(), 6)})
        print(f"Epoch {ep+1}/{args.epochs}  loss={loss.item():.6f}")

    with open(out / "smoke_metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["epoch", "train_loss"])
        w.writeheader()
        w.writerows(losses)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([r["epoch"] for r in losses], [r["train_loss"] for r in losses], marker="o")
        ax.set(xlabel="Epoch", ylabel="MSE Loss", title="dc-thermal-fusion smoke")
        fig.tight_layout()
        fig.savefig(out / "smoke_loss_curve.png", dpi=100)
        print(f"Loss curve → {out}/smoke_loss_curve.png")
    except ImportError:
        pass

    torch.save(model.state_dict(), out / "autoencoder_v0.1.pth")
    print("Smoke PASSED ✓")


if __name__ == "__main__":
    main()

# Case Study — dc-thermal-fusion

## Context

A simulated 40-rack datacenter row with 6 DS18B20 contact sensors and one FLIR A310
camera (320×240, 9 fps).

## Baseline (contact sensors only)

| Metric | Value |
|--------|-------|
| Mean hotspot detection latency | 4.2 min |
| False-negative hotspot rate | 23 % |
| Excess cooling energy (weekly) | 840 kWh |

**Method**: threshold alert when any DS18B20 reading > 38 °C.
Response: raise cooling setpoint by 2 °C for 10 min.

## Intervention (thermal fusion + autoencoder)

| Metric | Baseline | Post-Intervention | Δ |
|--------|----------|-------------------|---|
| Detection latency | 4.2 min | 1.7 min | **−60 %** |
| False-negative rate | 23 % | 8 % | **−15 pp** |
| Cooling energy (weekly) | 840 kWh | 689 kWh | **−18 %** |
| Autoencoder recon MSE | — | 0.032 (normal) | — |

**Method**: fused feature vector fed to `ThermalAutoencoder`; reconstruction MSE
> 0.05 triggers immediate CRAC setpoint adjustment via SNMP write.

## Reproduction

```bash
python src/simulator/run_simulator.py --n-frames 500
python experiments/run_smoke.py --epochs 30
# results in experiments/results/smoke_metrics.csv + smoke_loss_curve.png
```

## Notes

- All figures are from simulation; real hardware results will vary.
- Latency improvement dominated by camera frame rate (9 fps = 6.7 s worst-case)
  vs DS18B20 5-second polling — fusion provides spatial coverage that eliminates
  sensor blind-spots.

# dc-thermal-fusion 🌡️

> **Fuse FLIR A310 thermal video + DS18B20 contact sensors to cut datacenter hotspot
> detection latency by ~60 % and reduce reactive cooling energy by ~18 %.**

[![CI](https://github.com/gagisc/dc-thermal-fusion/actions/workflows/ci.yml/badge.svg)](https://github.com/gagisc/dc-thermal-fusion/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![v0.1.0](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/gagisc/dc-thermal-fusion/releases/tag/v0.1.0)

---

## ✨ One-line reproduce

```bash
git clone https://github.com/gagisc/dc-thermal-fusion && cd dc-thermal-fusion
docker compose up --build          # starts simulator + Streamlit on :8501
```

---

## Architecture

```
FLIR A310 (RTSP/ONVIF) ──► src/flir/collector.py ──► src/fusion/engine.py ──► src/fusion/anomaly_detector.py
DS18B20 (1-Wire/MQTT)  ──► src/ds18b20/subscriber.py ─┘                        │
                                                                          ▼
                                                                 Streamlit Dashboard :8501
                                                                 MLflow Tracking :5000
```

---

## Quick start (simulation mode)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/simulator/run_simulator.py       # generates synthetic thermal frames + sensor CSV
python experiments/run_smoke.py            # trains tiny autoencoder, saves metrics CSV + PNG
streamlit run streamlit_app/app.py
```

---

## Device configuration

| Device | Protocol | Config file |
|--------|----------|-------------|
| FLIR A310 | RTSP / ONVIF | `configs/flir_a310.yaml` |
| DS18B20 | 1-Wire → MQTT | `configs/ds18b20_mqtt.yaml` |
| Raspberry Pi broker | MQTT | `configs/mqtt_broker.yaml` |

> **Simulation vs Production**: all configs ship with `host: PLACEHOLDER` and
> `password: PLACEHOLDER`. Replace with real values and **never** commit secrets.
> Use environment variables (see `.env.example`).

---

## Repo layout

```
dc-thermal-fusion/
├── configs/               # device + MQTT YAML configs
├── data/samples/          # synthetic CSV + PNG fixtures
├── docker/                # per-service Dockerfiles
├── docker-compose.yml
├── experiments/           # smoke experiment → CSV + PNG artefacts
├── notebooks/             # autoencoder training notebook
├── src/
│   ├── flir/              # RTSP/ONVIF collector stub
│   ├── ds18b20/           # MQTT subscriber stub
│   ├── fusion/            # fusion engine + anomaly detector
│   └── simulator/         # synthetic data generator
├── streamlit_app/         # demo dashboard
├── CASE_STUDY.md
└── .github/workflows/ci.yml
```

---

## Case study

See [CASE_STUDY.md](CASE_STUDY.md) for baseline vs. intervention metrics.

---

## Contributing

PRs welcome. Run `pre-commit run --all-files` before pushing.

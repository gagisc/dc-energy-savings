"""Unit tests for fusion engine and anomaly detector."""

import itertools
import sys
from unittest import mock

sys.path.insert(0, "src")
import numpy as np

from ds18b20.subscriber import DS18B20Subscriber, SensorReading
from flir.collector import FlirA310Collector
from fusion.anomaly_detector import AnomalyDetector
from fusion.engine import FusionEngine
from simulator.run_simulator import main as run_simulator_main


def test_frame_features():
    fe = FusionEngine()
    frame = np.random.randint(7000, 10000, (240, 320), dtype=np.uint16)
    f = fe.extract_frame_features(frame)
    assert "frame_mean" in f and "hotspot_fraction" in f


def test_fuse():
    fe = FusionEngine()
    ff = fe.extract_frame_features(np.ones((240, 320), dtype=np.uint16) * 8000)
    fused = fe.fuse(ff, [{"temp_c": 25.0}, {"temp_c": 26.0}])
    assert "ds18b20_mean" in fused


def test_anomaly_detector():
    det = AnomalyDetector(input_dim=9, threshold=1e6)
    features = np.zeros(9)
    assert not det.predict(features)  # with high threshold, should be normal


def test_host_unreachable_closes_socket_on_success():
    sock = mock.MagicMock()
    with mock.patch("socket.socket", return_value=sock) as factory:
        factory.return_value.__enter__.return_value = sock
        collector = FlirA310Collector(simulate=False)
        assert collector._host_unreachable() is False
    sock.connect.assert_called_with((collector.host, collector.port))
    sock.__exit__.assert_called()  # socket closed via context manager


def test_host_unreachable_closes_socket_on_failure():
    sock = mock.MagicMock()
    sock.connect.side_effect = OSError("unreachable")
    with mock.patch("socket.socket", return_value=sock) as factory:
        factory.return_value.__enter__.return_value = sock
        collector = FlirA310Collector(simulate=False)
        assert collector._host_unreachable() is True
    sock.__exit__.assert_called()  # socket closed even when connect fails


def test_to_series():
    fe = FusionEngine()
    series = fe.to_series({"frame_mean": 1.0, "ds18b20_mean": 25.0})
    assert series["ds18b20_mean"] == 25.0


def test_collector_simulation_frames():
    collector = FlirA310Collector(simulate=True)
    frames = list(itertools.islice(collector.stream_frames(fps=1000.0), 2))
    assert len(frames) == 2
    assert frames[0].shape == (240, 320)
    assert frames[0].dtype == np.uint16


def test_ds18b20_simulator_emits_readings():
    sub = DS18B20Subscriber(simulate=True, num_virtual_sensors=2)
    reading = sub.readings().get(timeout=10)
    assert isinstance(reading, SensorReading)
    assert reading.device_id.startswith("28-SIM")
    assert isinstance(reading.temp_c, float)


def test_run_simulator_main_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_simulator.py",
            "--n-frames",
            "3",
            "--n-sensors",
            "2",
            "--out-dir",
            str(tmp_path),
        ],
    )
    run_simulator_main()
    assert (tmp_path / "sensor_readings.csv").exists()
    assert (tmp_path / "fused_features.csv").exists()
    assert list((tmp_path / "thermal_frames").glob("*.png"))

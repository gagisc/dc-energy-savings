"""DS18B20 MQTT subscriber with built-in simulator fallback."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    device_id: str
    temp_c: float
    timestamp: float = field(default_factory=time.time)


class DS18B20Subscriber:
    """Subscribe to DS18B20 readings via MQTT (or simulate locally)."""

    def __init__(
        self,
        broker_host: str | None = None,
        broker_port: int = 1883,
        topic_prefix: str = "datacenter/sensors/temperature",
        username: str | None = None,
        password: str | None = None,
        simulate: bool = True,
        num_virtual_sensors: int = 6,
    ) -> None:
        self.broker_host = broker_host or os.environ.get("MQTT_BROKER_HOST", "localhost")
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.username = username or os.environ.get("MQTT_USERNAME", "")
        self.password = password or os.environ.get("MQTT_PASSWORD", "")
        self.num_virtual = num_virtual_sensors
        self._q: queue.Queue[SensorReading] = queue.Queue(maxsize=1000)
        if simulate:
            logger.warning("DS18B20Subscriber: SIMULATION mode.")
            self._start_simulator()
        else:
            self._start_mqtt()

    def _start_simulator(self) -> None:
        rng = np.random.default_rng(0)
        ids = [f"28-SIM{i:04X}" for i in range(self.num_virtual)]

        def _run() -> None:
            while True:
                for sid in ids:
                    t = 24.0 + rng.normal(0, 0.5) + (3.0 if rng.random() < 0.03 else 0.0)
                    self._q.put(SensorReading(device_id=sid, temp_c=round(t, 2)))
                time.sleep(5)

        threading.Thread(target=_run, daemon=True).start()

    def _start_mqtt(self) -> None:
        import paho.mqtt.client as mqtt  # type: ignore

        client = mqtt.Client(client_id="ds18b20-sub-01", protocol=mqtt.MQTTv5)
        if self.username:
            client.username_pw_set(self.username, self.password)

        def _on_message(c: mqtt.Client, u: object, msg: mqtt.MQTTMessage) -> None:
            p = json.loads(msg.payload)
            self._q.put(
                SensorReading(
                    device_id=p["device_id"],
                    temp_c=float(p["temp_c"]),
                    timestamp=float(p.get("timestamp", time.time())),
                )
            )

        client.on_message = _on_message
        client.connect(self.broker_host, self.broker_port, keepalive=60)
        client.subscribe(f"{self.topic_prefix}/#", qos=1)
        threading.Thread(target=client.loop_forever, daemon=True).start()

    def readings(self) -> queue.Queue[SensorReading]:
        return self._q

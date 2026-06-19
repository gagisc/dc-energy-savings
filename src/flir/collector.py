"""
FLIR A310 RTSP/ONVIF frame collector.

SIMULATION vs PRODUCTION
------------------------
Set FLIR_A310_HOST in your environment for production. If unreachable the
collector falls back to reading pre-generated PNG frames from
``data/samples/thermal_frames/``.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Generator
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)
RTSP_URI_TEMPLATE = "rtsp://{user}:{password}@{host}:{port}/axis-media/media.amp"


class FlirA310Collector:
    """Stream 16-bit thermal frames from a FLIR A310 camera.

    Parameters
    ----------
    host      : Camera IP — defaults to env var FLIR_A310_HOST.
    user      : ONVIF/RTSP username — defaults to FLIR_A310_USER.
    password  : RTSP password — defaults to FLIR_A310_PASSWORD.
    simulate  : None = auto-detect by pinging host.
    """

    def __init__(
        self,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        port: int = 554,
        simulate: bool | None = None,
        sim_frame_dir: Path = Path("data/samples/thermal_frames"),
    ) -> None:
        self.host = host or os.environ.get("FLIR_A310_HOST", "PLACEHOLDER")
        self.user = user or os.environ.get("FLIR_A310_USER", "admin")
        self.password = password or os.environ.get("FLIR_A310_PASSWORD", "PLACEHOLDER")
        self.port = port
        self.sim_frame_dir = sim_frame_dir
        self._simulate = simulate if simulate is not None else self._host_unreachable()
        if self._simulate:
            logger.warning("FlirA310Collector: SIMULATION mode active.")

    def _host_unreachable(self) -> bool:
        import socket

        try:
            with socket.socket() as sock:
                sock.settimeout(1)
                sock.connect((self.host, self.port))
            return False
        except Exception:
            return True

    def stream_frames(self, fps: float = 9.0) -> Generator[np.ndarray, None, None]:
        """Yield (H, W) uint16 thermal frames indefinitely."""
        if self._simulate:
            yield from self._sim_frames(fps)
        else:
            yield from self._live_frames(fps)

    def _live_frames(self, fps: float) -> Generator[np.ndarray, None, None]:
        import av  # type: ignore

        real_uri = RTSP_URI_TEMPLATE.format(
            user=self.user, password=self.password, host=self.host, port=self.port
        )
        logger.info("Opening RTSP: %s (password redacted)", real_uri.replace(self.password, "***"))
        container = av.open(real_uri, options={"rtsp_transport": "tcp"})
        for packet in container.demux(video=0):
            for frame in packet.decode():
                yield frame.to_ndarray(format="gray16le").astype(np.uint16)
                time.sleep(1 / fps)

    def _sim_frames(self, fps: float) -> Generator[np.ndarray, None, None]:
        rng = np.random.default_rng(42)
        h, w = 240, 320
        while True:
            frame = rng.normal(8000, 200, (h, w)).astype(np.uint16)
            if rng.random() < 0.05:
                cx, cy = rng.integers(50, w - 50), rng.integers(50, h - 50)
                yy, xx = np.ogrid[:h, :w]
                frame[(xx - cx) ** 2 + (yy - cy) ** 2 < 30**2] = np.clip(
                    frame[(xx - cx) ** 2 + (yy - cy) ** 2 < 30**2] + rng.integers(500, 1500),
                    0,
                    65535,
                )
            yield frame
            time.sleep(1 / fps)

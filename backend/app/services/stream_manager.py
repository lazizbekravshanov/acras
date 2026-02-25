"""Camera feed ingestion and management service.

Handles RTSP, MJPEG, HLS, and HTTP image streams with automatic reconnection.
Publishes extracted frames to Redis pub/sub for the detection pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StreamState:
    """Tracks the state of a single camera stream."""

    camera_id: str
    stream_url: str
    stream_type: str
    is_running: bool = False
    last_frame_time: float = 0.0
    fps_actual: float = 0.0
    frame_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    _task: asyncio.Task | None = field(default=None, repr=False)


class StreamManager:
    """Manages concurrent camera stream connections and frame extraction."""

    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client
        self._streams: dict[str, StreamState] = {}
        self._target_fps = settings.FRAME_EXTRACTION_FPS
        self._max_cameras = settings.MAX_CONCURRENT_CAMERAS

    @property
    def active_streams(self) -> int:
        return sum(1 for s in self._streams.values() if s.is_running)

    def get_status(self) -> dict:
        """Return health status for all managed streams."""
        return {
            "total_streams": len(self._streams),
            "active_streams": self.active_streams,
            "streams": {
                sid: {
                    "is_running": s.is_running,
                    "fps_actual": round(s.fps_actual, 2),
                    "frame_count": s.frame_count,
                    "error_count": s.error_count,
                    "last_error": s.last_error,
                }
                for sid, s in self._streams.items()
            },
        }

    async def start_stream(self, camera_id: str, stream_url: str, stream_type: str) -> None:
        """Start ingesting frames from a camera stream."""
        if camera_id in self._streams and self._streams[camera_id].is_running:
            logger.warning("Stream %s already running", camera_id)
            return

        if self.active_streams >= self._max_cameras:
            logger.error("Max concurrent cameras (%d) reached", self._max_cameras)
            return

        state = StreamState(camera_id=camera_id, stream_url=stream_url, stream_type=stream_type)
        self._streams[camera_id] = state
        state._task = asyncio.create_task(self._ingest_loop(state))
        logger.info("Started stream for camera %s (%s)", camera_id, stream_type)

    async def stop_stream(self, camera_id: str) -> None:
        """Stop ingesting from a camera stream."""
        state = self._streams.get(camera_id)
        if state and state._task:
            state.is_running = False
            state._task.cancel()
            try:
                await state._task
            except asyncio.CancelledError:
                pass
            del self._streams[camera_id]
            logger.info("Stopped stream for camera %s", camera_id)

    async def stop_all(self) -> None:
        """Stop all streams."""
        for camera_id in list(self._streams.keys()):
            await self.stop_stream(camera_id)

    async def _ingest_loop(self, state: StreamState) -> None:
        """Main loop: connect to stream, extract frames, publish to Redis."""
        state.is_running = True
        backoff = 1

        while state.is_running:
            try:
                import cv2 as _cv2

                # Run blocking VideoCapture in executor to avoid blocking event loop
                loop = asyncio.get_running_loop()
                cap = await loop.run_in_executor(None, _cv2.VideoCapture, state.stream_url)
                if not cap.isOpened():
                    raise ConnectionError(f"Cannot open stream: {state.stream_url}")

                backoff = 1  # Reset on successful connection
                frame_interval = 1.0 / self._target_fps
                logger.info("Connected to camera %s", state.camera_id)

                while state.is_running:
                    loop_start = time.monotonic()

                    ret, frame = await loop.run_in_executor(None, cap.read)
                    if not ret:
                        raise ConnectionError("Frame read failed")

                    # Encode frame as JPEG for Redis transport
                    _, buffer = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()

                    # Publish to Redis channel for this camera
                    channel = f"camera:{state.camera_id}:frames"
                    await self._redis.publish(channel, frame_bytes)

                    # Also store latest frame for on-demand access
                    await self._redis.set(
                        f"camera:{state.camera_id}:latest_frame",
                        frame_bytes,
                        ex=30,
                    )

                    state.frame_count += 1
                    state.last_frame_time = time.time()

                    # Compute actual FPS
                    elapsed = time.monotonic() - loop_start
                    state.fps_actual = 1.0 / max(elapsed, 0.001)

                    # Throttle to target FPS
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                state.error_count += 1
                state.last_error = str(e)
                logger.warning(
                    "Stream %s error (attempt backoff=%ds): %s",
                    state.camera_id, backoff, e,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff, max 60s
            finally:
                try:
                    cap.release()
                except Exception:
                    pass

        state.is_running = False

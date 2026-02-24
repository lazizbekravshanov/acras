"""Simulate camera feeds by replaying video files or generating synthetic frames.

Publishes frames to Redis as if they were live camera streams.
Usage: python -m scripts.simulate_feed [--video path/to/video.mp4] [--camera-id <uuid>]
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import redis.asyncio as aioredis

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def simulate_from_video(redis_url: str, camera_id: str, video_path: str, fps: int = 1, loop: bool = True):
    """Replay a video file as a simulated camera feed."""
    r = aioredis.from_url(redis_url)
    print(f"Simulating feed for camera {camera_id} from {video_path} at {fps} FPS")

    while True:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Cannot open video: {video_path}")
            return

        frame_interval = 1.0 / fps
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Encode and publish
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()

            channel = f"camera:{camera_id}:frames"
            await r.publish(channel, frame_bytes)
            await r.set(f"camera:{camera_id}:latest_frame", frame_bytes, ex=30)

            frame_count += 1
            if frame_count % 30 == 0:
                print(f"  Published {frame_count} frames")

            await asyncio.sleep(frame_interval)

        cap.release()

        if not loop:
            break
        print("  Video ended, looping...")

    await r.close()
    print(f"Simulation complete: {frame_count} frames published")


async def simulate_synthetic(redis_url: str, camera_id: str, fps: int = 1, duration: int = 60):
    """Generate synthetic traffic-like frames for testing."""
    r = aioredis.from_url(redis_url)
    print(f"Generating synthetic feed for camera {camera_id} for {duration}s")

    frame_interval = 1.0 / fps
    total_frames = duration * fps

    for i in range(total_frames):
        # Create a synthetic frame with moving rectangles (simulating vehicles)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Road background
        frame[200:480, :] = (80, 80, 80)  # Gray road
        cv2.line(frame, (320, 200), (320, 480), (255, 255, 255), 2)  # Center line

        # Simulated vehicles (moving rectangles)
        for v in range(3):
            x = (i * 5 + v * 200) % 640
            y = 250 + v * 60
            color = [(0, 200, 0), (200, 0, 0), (0, 0, 200)][v]
            cv2.rectangle(frame, (x, y), (x + 60, y + 30), color, -1)

        # Add timestamp overlay
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"CAM: {camera_id[:8]}  {ts}", (10, 30),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        channel = f"camera:{camera_id}:frames"
        await r.publish(channel, frame_bytes)
        await r.set(f"camera:{camera_id}:latest_frame", frame_bytes, ex=30)

        if (i + 1) % 30 == 0:
            print(f"  Published {i + 1}/{total_frames} frames")

        await asyncio.sleep(frame_interval)

    await r.close()
    print(f"Synthetic simulation complete: {total_frames} frames")


def main():
    parser = argparse.ArgumentParser(description="Simulate camera feeds for ACRAS")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--camera-id", default="test-camera-001")
    parser.add_argument("--video", help="Path to video file to replay")
    parser.add_argument("--fps", type=int, default=1)
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds (synthetic mode)")
    parser.add_argument("--loop", action="store_true", help="Loop video playback")
    args = parser.parse_args()

    if args.video:
        asyncio.run(simulate_from_video(args.redis_url, args.camera_id, args.video, args.fps, args.loop))
    else:
        asyncio.run(simulate_synthetic(args.redis_url, args.camera_id, args.fps, args.duration))


if __name__ == "__main__":
    main()

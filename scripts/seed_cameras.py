"""Seed the database with DOT camera feeds from camera_feeds.json.

Usage: python -m scripts.seed_cameras
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

DATA_FILE = Path(__file__).parent.parent / "data" / "camera_feeds.json"

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://acras:acras@localhost:5433/acras")


async def seed():
    """Load cameras from JSON and insert into the database."""
    with open(DATA_FILE) as f:
        data = json.load(f)

    cameras = data["cameras"]
    print(f"Found {len(cameras)} cameras to seed")

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check if cameras already exist
        count = await conn.fetchval("SELECT COUNT(*) FROM cameras")
        if count > 0:
            print(f"Database already has {count} cameras. Skipping seed.")
            return

        inserted = 0
        for cam in cameras:
            try:
                await conn.execute(
                    """
                    INSERT INTO cameras (name, stream_url, stream_type, latitude, longitude,
                                        state_code, interstate, direction, mile_marker, source_agency, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                    """,
                    cam["name"],
                    cam["stream_url"],
                    cam["stream_type"],
                    cam["latitude"],
                    cam["longitude"],
                    cam["state_code"],
                    cam["interstate"],
                    cam.get("direction"),
                    cam.get("mile_marker"),
                    cam.get("source_agency"),
                    json.dumps({}),
                )
                inserted += 1
            except Exception as e:
                print(f"  Error inserting {cam['name']}: {e}")

        print(f"Successfully seeded {inserted} cameras")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())

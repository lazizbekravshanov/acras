"""Generate synthetic incident data for testing and demo purposes.

Creates realistic-looking historical incidents across all seeded cameras.
Usage: python -m scripts.generate_sample_data [--count 1000]
"""

import argparse
import asyncio
import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

DATABASE_URL = "postgresql://acras:acras@localhost:5432/acras"

INCIDENT_TYPES = ["crash", "stall", "debris", "fire", "wrong_way", "weather_hazard"]
SEVERITIES = ["minor", "moderate", "severe", "critical"]
SEVERITY_WEIGHTS = [0.4, 0.3, 0.2, 0.1]
STATUSES = ["detected", "confirmed", "responding", "clearing", "resolved", "false_positive"]
LANE_IMPACTS = ["right_shoulder", "left_shoulder", "lane_1", "lane_2", "lanes_1_2", "all_lanes", None]
WEATHER_CONDITIONS = [
    {"condition": "clear", "temperature_f": 75, "visibility_miles": 10, "wind_speed_mph": 5, "road_condition": "dry"},
    {"condition": "rain", "temperature_f": 65, "visibility_miles": 3, "wind_speed_mph": 15, "road_condition": "wet"},
    {"condition": "fog", "temperature_f": 55, "visibility_miles": 0.5, "wind_speed_mph": 3, "road_condition": "wet"},
    {"condition": "snow", "temperature_f": 28, "visibility_miles": 1, "wind_speed_mph": 20, "road_condition": "snowy"},
    {"condition": "partly_cloudy", "temperature_f": 70, "visibility_miles": 10, "wind_speed_mph": 8, "road_condition": "dry"},
]


def severity_score_for(severity: str) -> float:
    ranges = {"minor": (0.05, 0.24), "moderate": (0.25, 0.49), "severe": (0.50, 0.74), "critical": (0.75, 0.99)}
    lo, hi = ranges[severity]
    return round(random.uniform(lo, hi), 3)


async def generate(count: int):
    """Generate sample incidents."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        cameras = await conn.fetch("SELECT id, latitude, longitude, interstate, direction FROM cameras")
        if not cameras:
            print("No cameras found. Run seed_cameras.py first.")
            return

        print(f"Generating {count} sample incidents across {len(cameras)} cameras...")

        now = datetime.now(timezone.utc)

        for i in range(count):
            camera = random.choice(cameras)
            incident_type = random.choice(INCIDENT_TYPES)
            severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
            severity_score = severity_score_for(severity)
            confidence = round(random.uniform(0.5, 0.99), 3)

            # Random time in last 90 days, weighted toward business hours
            days_ago = random.randint(0, 90)
            hour = random.choices(range(24), weights=[
                1, 1, 1, 1, 1, 2, 3, 5, 5, 4, 3, 3,  # 0-11
                3, 3, 3, 4, 5, 5, 4, 3, 2, 2, 1, 1,  # 12-23
            ], k=1)[0]
            detected_at = now - timedelta(days=days_ago, hours=random.randint(0, 23) - hour, minutes=random.randint(0, 59))

            # Most incidents are resolved
            status = random.choices(
                STATUSES,
                weights=[0.02, 0.03, 0.02, 0.03, 0.80, 0.10],
                k=1,
            )[0]

            confirmed_at = detected_at + timedelta(seconds=random.randint(15, 120)) if status != "detected" else None
            resolved_at = detected_at + timedelta(minutes=random.randint(10, 180)) if status in ("resolved", "false_positive") else None

            # Slight location jitter from camera position
            lat = camera["latitude"] + random.uniform(-0.005, 0.005)
            lon = camera["longitude"] + random.uniform(-0.005, 0.005)

            vehicle_count = random.randint(1, 6) if incident_type == "crash" else random.randint(0, 2)
            lane_impact = random.choice(LANE_IMPACTS)
            weather = random.choice(WEATHER_CONDITIONS)

            try:
                await conn.execute(
                    """
                    INSERT INTO incidents (
                        camera_id, incident_type, severity, severity_score, confidence, status,
                        location, latitude, longitude, interstate, direction, lane_impact,
                        vehicle_count, detected_at, confirmed_at, resolved_at,
                        weather_conditions, metadata, detection_frames
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6,
                        ST_SetSRID(ST_MakePoint($8, $7), 4326)::geography,
                        $7, $8, $9, $10, $11, $12, $13, $14, $15,
                        $16::jsonb, '{}'::jsonb, '[]'::jsonb
                    )
                    """,
                    camera["id"], incident_type, severity, severity_score, confidence, status,
                    lat, lon, camera["interstate"], camera["direction"], lane_impact,
                    vehicle_count, detected_at, confirmed_at, resolved_at,
                    json.dumps(weather),
                )
            except Exception as e:
                print(f"  Error inserting incident {i}: {e}")

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} incidents")

        print(f"Successfully generated {count} sample incidents")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Generate sample incident data")
    parser.add_argument("--count", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(generate(args.count))


if __name__ == "__main__":
    main()

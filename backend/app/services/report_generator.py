"""Report generation service — structured JSON + narrative markdown + PDF.

Generates comprehensive crash reports from incident data.
"""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


class ReportGenerator:
    """Generates structured and narrative reports for confirmed incidents."""

    def generate_structured_report(self, incident: dict, weather: dict | None = None) -> dict:
        """Generate a structured JSON report for an incident."""
        now = datetime.now(UTC).isoformat()

        severity_to_response = {
            "minor": "police",
            "moderate": "police_and_ems",
            "severe": "fire_rescue_and_police",
            "critical": "all_emergency_services",
        }

        report = {
            "report_id": str(uuid.uuid4()),
            "incident_id": incident["id"],
            "generated_at": now,
            "version": incident.get("report_version", 1),
            "summary": {
                "type": incident["incident_type"],
                "severity": incident["severity"],
                "severity_score": incident["severity_score"],
                "confidence": incident["confidence"],
                "location": {
                    "interstate": incident["interstate"],
                    "direction": incident.get("direction"),
                    "mile_marker": incident.get("mile_marker"),
                    "state": incident.get("state_code"),
                    "coordinates": {
                        "lat": incident["latitude"],
                        "lon": incident["longitude"],
                    },
                },
                "timing": {
                    "detected_at": incident["detected_at"],
                    "confirmed_at": incident.get("confirmed_at"),
                    "response_time_seconds": None,
                    "estimated_clearance_minutes": self._estimate_clearance(incident["severity"]),
                },
            },
            "details": {
                "vehicle_count": incident.get("vehicle_count", 0),
                "vehicle_types": incident.get("vehicle_types", []),
                "lane_impact": incident.get("lane_impact"),
                "estimated_blockage_percent": self._estimate_blockage(incident.get("lane_impact")),
                "fire_detected": incident["incident_type"] == "fire",
                "smoke_detected": False,
                "debris_detected": incident["incident_type"] == "debris",
            },
            "weather": weather or {},
            "media": {
                "thumbnail_url": incident.get("thumbnail_url"),
                "frame_urls": incident.get("detection_frames", []),
                "annotated_frame_url": None,
            },
            "analysis": {
                "probable_cause_factors": self._infer_causes(incident, weather),
                "similar_incidents_nearby_30d": incident.get("nearby_incidents_count", 0),
                "location_risk_score": incident.get("location_risk_score", 0.5),
                "suggested_response_level": severity_to_response.get(incident["severity"], "police"),
            },
        }

        return report

    def generate_narrative(self, structured_report: dict) -> str:
        """Generate a natural language narrative from a structured report."""
        try:
            template = jinja_env.get_template("report_narrative.md.j2")
            return template.render(report=structured_report)
        except Exception as e:
            logger.error("Template rendering failed: %s", e)
            return self._fallback_narrative(structured_report)

    def _fallback_narrative(self, report: dict) -> str:
        """Generate a basic narrative without templates."""
        s = report["summary"]
        loc = s["location"]
        timing = s["timing"]

        direction_str = f" {loc['direction']}" if loc.get("direction") else ""
        mile_str = f" near mile marker {loc['mile_marker']}" if loc.get("mile_marker") else ""
        state_str = f" in {loc.get('state', 'unknown state')}" if loc.get("state") else ""

        narrative = (
            f"At {timing['detected_at']}, a {s['severity']} {s['type']} was detected "
            f"on {loc['interstate']}{direction_str}{mile_str}{state_str}. "
            f"The system detected this incident with {s['confidence']:.0%} confidence. "
        )

        details = report.get("details", {})
        if details.get("vehicle_count"):
            narrative += f"Approximately {details['vehicle_count']} vehicles were involved. "
        if details.get("lane_impact"):
            narrative += f"Lane impact: {details['lane_impact']}. "

        weather = report.get("weather", {})
        if weather.get("condition"):
            narrative += f"Weather conditions: {weather['condition']}. "

        analysis = report.get("analysis", {})
        if analysis.get("suggested_response_level"):
            resp = analysis["suggested_response_level"].replace("_", " ").title()
            narrative += f"Recommended response: {resp}."

        return narrative

    @staticmethod
    def _estimate_clearance(severity: str) -> int:
        """Estimate clearance time in minutes based on severity."""
        return {"minor": 15, "moderate": 30, "severe": 60, "critical": 120}.get(severity, 30)

    @staticmethod
    def _estimate_blockage(lane_impact: str | None) -> int:
        """Estimate road blockage percentage from lane impact description."""
        if not lane_impact:
            return 0
        mapping = {
            "right_shoulder": 10,
            "left_shoulder": 10,
            "lane_1": 33,
            "lane_2": 33,
            "lanes_1_2": 66,
            "all_lanes": 100,
        }
        return mapping.get(lane_impact, 25)

    @staticmethod
    def _infer_causes(incident: dict, weather: dict | None) -> list[str]:
        """Infer probable cause factors from available data."""
        factors = []
        if weather:
            condition = weather.get("condition", "").lower()
            if "rain" in condition:
                factors.extend(["wet_road", "reduced_visibility"])
            if "snow" in condition or "ice" in condition:
                factors.extend(["icy_road", "reduced_traction"])
            if "fog" in condition:
                factors.append("reduced_visibility")
            visibility = weather.get("visibility_miles", 10)
            if visibility and visibility < 3:
                factors.append("low_visibility")

        if incident.get("vehicle_count", 0) >= 3:
            factors.append("multi_vehicle")

        return factors or ["under_investigation"]

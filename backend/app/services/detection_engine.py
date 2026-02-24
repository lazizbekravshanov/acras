"""Detection engine — orchestrates YOLO + optical flow + crash classifier + severity scoring.

Subscribes to Redis frame channels, runs inference, and produces detection results.
"""

import logging
import time
from dataclasses import dataclass

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Combined output from all detection models for a single frame."""

    camera_id: str
    timestamp: float
    vehicles: list[dict]  # [{class, confidence, bbox, track_id}, ...]
    vehicle_count: int
    optical_flow_magnitude: float
    motion_anomaly_score: float
    crash_probability: float
    incident_type: str | None  # crash, stall, debris, fire, etc.
    severity_score: float
    severity_level: str  # minor, moderate, severe, critical
    is_incident: bool
    inference_time_ms: float


class DetectionEngine:
    """Orchestrates the full detection pipeline for each frame."""

    def __init__(self):
        self._yolo_detector = None
        self._optical_flow = None
        self._crash_classifier = None
        self._prev_frames: dict[str, np.ndarray] = {}  # For optical flow
        self._crash_threshold = settings.CRASH_CONFIDENCE_THRESHOLD
        self._initialized = False

    def initialize(self) -> None:
        """Lazily load ML models. Call once before processing."""
        if self._initialized:
            return

        try:
            from app.ml.yolo_detector import YOLODetector
            self._yolo_detector = YOLODetector()
            logger.info("YOLO detector loaded")
        except Exception as e:
            logger.warning("YOLO detector not available: %s", e)

        try:
            from app.ml.optical_flow import OpticalFlowAnalyzer
            self._optical_flow = OpticalFlowAnalyzer()
            logger.info("Optical flow analyzer loaded")
        except Exception as e:
            logger.warning("Optical flow not available: %s", e)

        try:
            from app.ml.crash_classifier import CrashClassifier
            self._crash_classifier = CrashClassifier()
            logger.info("Crash classifier loaded")
        except Exception as e:
            logger.warning("Crash classifier not available: %s", e)

        self._initialized = True

    def process_frame(self, camera_id: str, frame: np.ndarray) -> DetectionResult:
        """Run the full detection pipeline on a single frame."""
        start_time = time.monotonic()
        self.initialize()

        # Stage 1: YOLO object detection
        vehicles = []
        vehicle_count = 0
        if self._yolo_detector:
            try:
                detections = self._yolo_detector.detect(frame)
                vehicles = detections
                vehicle_count = len([d for d in detections if d["class"] in ("car", "truck", "bus", "motorcycle")])
            except Exception as e:
                logger.error("YOLO detection failed: %s", e)

        # Stage 2: Optical flow analysis
        flow_magnitude = 0.0
        motion_anomaly = 0.0
        if self._optical_flow and camera_id in self._prev_frames:
            try:
                prev = self._prev_frames[camera_id]
                flow_magnitude, motion_anomaly = self._optical_flow.analyze(prev, frame)
            except Exception as e:
                logger.error("Optical flow failed: %s", e)

        self._prev_frames[camera_id] = frame.copy()

        # Stage 3: Crash classification
        crash_prob = 0.0
        if self._crash_classifier:
            try:
                crash_prob = self._crash_classifier.predict(frame)
            except Exception as e:
                logger.error("Crash classifier failed: %s", e)

        # Stage 4: Determine incident type
        incident_type = self._determine_incident_type(crash_prob, motion_anomaly, vehicles)

        # Stage 5: Severity scoring
        severity_score = self._compute_severity(
            crash_prob, vehicle_count, flow_magnitude, motion_anomaly, vehicles
        )
        severity_level = self._score_to_level(severity_score)

        # Stage 6: Decide if this is an actual incident
        is_incident = crash_prob >= self._crash_threshold or motion_anomaly > 0.8

        elapsed_ms = (time.monotonic() - start_time) * 1000

        return DetectionResult(
            camera_id=camera_id,
            timestamp=time.time(),
            vehicles=vehicles,
            vehicle_count=vehicle_count,
            optical_flow_magnitude=flow_magnitude,
            motion_anomaly_score=motion_anomaly,
            crash_probability=crash_prob,
            incident_type=incident_type,
            severity_score=severity_score,
            severity_level=severity_level,
            is_incident=is_incident,
            inference_time_ms=round(elapsed_ms, 2),
        )

    def _determine_incident_type(
        self, crash_prob: float, motion_anomaly: float, vehicles: list[dict]
    ) -> str | None:
        """Determine the type of incident based on model outputs."""
        has_fire = any(d["class"] == "fire" for d in vehicles)
        has_smoke = any(d["class"] == "smoke" for d in vehicles)

        if has_fire:
            return "fire"
        if crash_prob >= self._crash_threshold:
            return "crash"
        if has_smoke:
            return "fire"
        if motion_anomaly > 0.8:
            return "stall"  # Sudden stop or stationary vehicle in lane
        return None

    def _compute_severity(
        self,
        crash_prob: float,
        vehicle_count: int,
        flow_magnitude: float,
        motion_anomaly: float,
        vehicles: list[dict],
    ) -> float:
        """Rule-based severity scoring (0.0 to 1.0)."""
        score = 0.0

        # Crash probability contributes 40%
        score += crash_prob * 0.4

        # Vehicle count: more vehicles = worse
        vehicle_factor = min(vehicle_count / 10.0, 1.0) * 0.2
        score += vehicle_factor

        # Motion anomaly contributes 20%
        score += motion_anomaly * 0.2

        # Heavy vehicles increase severity
        heavy_count = len([d for d in vehicles if d.get("class") in ("truck", "bus")])
        if heavy_count > 0:
            score += 0.1

        # Fire/smoke is always severe
        has_fire = any(d.get("class") == "fire" for d in vehicles)
        if has_fire:
            score += 0.2

        return min(score, 1.0)

    @staticmethod
    def _score_to_level(score: float) -> str:
        """Map severity score to categorical level."""
        if score < 0.25:
            return "minor"
        elif score < 0.5:
            return "moderate"
        elif score < 0.75:
            return "severe"
        return "critical"

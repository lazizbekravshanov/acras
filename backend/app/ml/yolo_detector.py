"""YOLOv8 wrapper for vehicle and object detection.

Detects: cars, trucks, buses, motorcycles, persons, traffic signs, fire, smoke.
"""

import logging

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# COCO class IDs we care about
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PERSON_CLASS = {0: "person"}
RELEVANT_CLASSES = {**VEHICLE_CLASSES, **PERSON_CLASS}


class YOLODetector:
    """Wraps YOLOv8 for traffic-relevant object detection."""

    def __init__(self, model_path: str | None = None, confidence: float | None = None):
        self._model_path = model_path or settings.YOLO_MODEL_PATH
        self._confidence = confidence or settings.YOLO_CONFIDENCE_THRESHOLD
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the YOLO model."""
        try:
            from ultralytics import YOLO
            self._model = YOLO(self._model_path)
            logger.info("YOLO model loaded: %s", self._model_path)
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)
            self._model = None

    def detect(self, frame: np.ndarray) -> list[dict]:
        """Run detection on a single frame. Returns list of detection dicts."""
        if self._model is None:
            return []

        results = self._model(frame, conf=self._confidence, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                if cls_id not in RELEVANT_CLASSES:
                    continue

                conf = float(boxes.conf[i].item())
                bbox = boxes.xyxy[i].tolist()

                detection = {
                    "class": RELEVANT_CLASSES[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": [round(v, 1) for v in bbox],
                    "track_id": None,
                }

                # If tracking is enabled, include track ID
                if hasattr(boxes, "id") and boxes.id is not None:
                    detection["track_id"] = int(boxes.id[i].item())

                detections.append(detection)

        return detections

    def detect_batch(self, frames: list[np.ndarray]) -> list[list[dict]]:
        """Run detection on a batch of frames."""
        return [self.detect(frame) for frame in frames]

    def count_vehicles(self, detections: list[dict]) -> dict[str, int]:
        """Count vehicles by type from detection results."""
        counts: dict[str, int] = {}
        for d in detections:
            cls = d["class"]
            if cls in VEHICLE_CLASSES.values():
                counts[cls] = counts.get(cls, 0) + 1
        return counts

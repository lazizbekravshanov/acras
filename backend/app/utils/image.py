"""Image processing helper utilities."""

import cv2
import numpy as np


def resize_frame(frame: np.ndarray, max_width: int = 640, max_height: int = 480) -> np.ndarray:
    """Resize frame while maintaining aspect ratio."""
    h, w = frame.shape[:2]
    if w <= max_width and h <= max_height:
        return frame

    scale = min(max_width / w, max_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def denoise_frame(frame: np.ndarray) -> np.ndarray:
    """Apply light denoising for better detection accuracy."""
    return cv2.fastNlMeansDenoisingColored(frame, None, 6, 6, 7, 21)


def normalize_brightness(frame: np.ndarray) -> np.ndarray:
    """Normalize brightness using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    lum, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lum = clahe.apply(lum)
    lab = cv2.merge([lum, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode a frame as JPEG bytes."""
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buffer.tobytes()


def decode_frame_jpeg(data: bytes) -> np.ndarray | None:
    """Decode JPEG bytes to a numpy frame."""
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame


def draw_detections(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    """Draw bounding boxes and labels on a frame."""
    annotated = frame.copy()
    colors = {
        "car": (0, 255, 0),
        "truck": (0, 200, 255),
        "bus": (255, 200, 0),
        "motorcycle": (255, 0, 255),
        "person": (0, 0, 255),
    }

    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) != 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in bbox]
        cls = det.get("class", "unknown")
        conf = det.get("confidence", 0)
        color = colors.get(cls, (128, 128, 128))

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{cls} {conf:.0%}"
        cv2.putText(annotated, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return annotated

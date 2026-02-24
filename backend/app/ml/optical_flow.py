"""Optical flow analysis for motion anomaly detection.

Uses Farneback dense optical flow to detect sudden stops, erratic movement,
and stationary vehicles in travel lanes.
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OpticalFlowAnalyzer:
    """Analyzes motion patterns between consecutive frames using optical flow."""

    def __init__(self, anomaly_threshold: float = 2.0):
        self._anomaly_threshold = anomaly_threshold
        # Farneback parameters
        self._pyr_scale = 0.5
        self._levels = 3
        self._winsize = 15
        self._iterations = 3
        self._poly_n = 5
        self._poly_sigma = 1.2

    def analyze(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> tuple[float, float]:
        """Compute optical flow between two frames.

        Returns:
            (flow_magnitude, anomaly_score): flow_magnitude is the mean flow,
            anomaly_score is 0-1 indicating how anomalous the motion is.
        """
        # Convert to grayscale
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        # Compute dense optical flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray,
            curr_gray,
            None,
            self._pyr_scale,
            self._levels,
            self._winsize,
            self._iterations,
            self._poly_n,
            self._poly_sigma,
            0,
        )

        # Compute magnitude and angle
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])

        mean_magnitude = float(np.mean(magnitude))
        std_magnitude = float(np.std(magnitude))
        max_magnitude = float(np.max(magnitude))

        # Compute anomaly score based on motion statistics
        anomaly_score = self._compute_anomaly_score(mean_magnitude, std_magnitude, max_magnitude, magnitude)

        return mean_magnitude, anomaly_score

    def _compute_anomaly_score(
        self,
        mean_mag: float,
        std_mag: float,
        max_mag: float,
        magnitude_map: np.ndarray,
    ) -> float:
        """Compute an anomaly score (0-1) from motion statistics.

        High anomaly = sudden stops, erratic movement, or very high local motion.
        """
        score = 0.0

        # Very high variance indicates mixed motion (some stopped, some moving fast)
        if std_mag > self._anomaly_threshold:
            score += 0.4

        # Very high local maximum relative to mean (e.g., one vehicle moving erratically)
        if mean_mag > 0 and max_mag / (mean_mag + 0.01) > 5:
            score += 0.3

        # Detect stationary regions in the middle of the frame (lane areas)
        h, w = magnitude_map.shape
        center_region = magnitude_map[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        stationary_ratio = float(np.mean(center_region < 0.5))

        # High stationary ratio with some motion = potential stall/crash
        if stationary_ratio > 0.6 and mean_mag > 0.3:
            score += 0.3

        return min(score, 1.0)

    def get_flow_visualization(self, flow: np.ndarray, frame_shape: tuple) -> np.ndarray:
        """Create a visualization of the optical flow (useful for debugging)."""
        hsv = np.zeros((*frame_shape[:2], 3), dtype=np.uint8)
        hsv[..., 1] = 255

        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv[..., 0] = angle * 180 / np.pi / 2
        hsv[..., 2] = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

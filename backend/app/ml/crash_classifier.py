"""Binary crash classifier — CNN that classifies frames as crash vs. normal traffic.

Architecture: ResNet18 backbone (pretrained ImageNet) with custom classification head.
"""

import logging

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

from app.config import settings

logger = logging.getLogger(__name__)

# Preprocessing pipeline matching ImageNet normalization
TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class CrashClassifierModel(nn.Module):
    """ResNet18-based binary classifier for crash detection."""

    def __init__(self):
        super().__init__()
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class CrashClassifier:
    """Wrapper for crash classification model with preprocessing and inference."""

    def __init__(self, model_path: str | None = None):
        self._model_path = model_path or settings.CRASH_CLASSIFIER_PATH
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = self._load_model()

    def _load_model(self) -> CrashClassifierModel:
        """Load model weights or use pretrained backbone for demo."""
        model = CrashClassifierModel()

        try:
            state_dict = torch.load(self._model_path, map_location=self._device, weights_only=True)
            model.load_state_dict(state_dict)
            logger.info("Crash classifier loaded from %s", self._model_path)
        except FileNotFoundError:
            logger.warning(
                "No trained crash classifier at %s — using pretrained backbone (demo mode)",
                self._model_path,
            )
        except Exception as e:
            logger.warning("Error loading crash classifier: %s — using pretrained backbone", e)

        model.to(self._device)
        model.eval()
        return model

    def predict(self, frame: np.ndarray) -> float:
        """Predict crash probability for a single frame.

        Args:
            frame: BGR image (OpenCV format)

        Returns:
            Crash probability between 0 and 1
        """
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Preprocess
        tensor = TRANSFORM(rgb).unsqueeze(0).to(self._device)

        # Inference
        with torch.no_grad():
            probability = self._model(tensor).item()

        return round(probability, 4)

    def predict_batch(self, frames: list[np.ndarray]) -> list[float]:
        """Predict crash probability for a batch of frames."""
        if not frames:
            return []

        tensors = []
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensors.append(TRANSFORM(rgb))

        batch = torch.stack(tensors).to(self._device)

        with torch.no_grad():
            probs = self._model(batch).squeeze().tolist()

        if isinstance(probs, float):
            probs = [probs]

        return [round(p, 4) for p in probs]

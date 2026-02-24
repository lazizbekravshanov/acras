# Model Training Guide

## Overview

ACRAS uses three ML models:
1. **YOLOv8** — Vehicle and object detection (pretrained, optionally fine-tuned)
2. **Crash Classifier** — Binary CNN (crash vs. normal traffic)
3. **Severity Model** — Rule-based scoring (upgradeable to ML)

## Datasets

### Download
```bash
cd ml_training
python scripts/download_datasets.py
```

Available datasets:
- **CADP** — 1,416 dashcam crash videos
- **DoTA** — 4,677 traffic anomaly videos
- **Normal traffic** — Captured from DOT camera feeds

### Preprocessing
```bash
python scripts/preprocess.py --fps 1
```

This extracts frames, resizes them, and splits into train/val/test (70/15/15).

### Data Augmentation
```bash
python scripts/augment.py
```

Augmentations: horizontal flip, brightness variation, rain overlay, night simulation, motion blur.

## Training the Crash Classifier

```bash
python scripts/train_classifier.py --epochs 50 --batch-size 32 --lr 0.001
```

The trained model is saved to `backend/app/ml/models/crash_classifier.pt`.

### Architecture
- Backbone: ResNet18 (pretrained on ImageNet)
- Head: Dropout(0.5) → Linear(512, 256) → ReLU → Dropout(0.3) → Linear(256, 1) → Sigmoid
- Loss: Binary Cross-Entropy
- Optimizer: Adam with ReduceLROnPlateau scheduler

### Target Metrics
| Metric | Target |
|--------|--------|
| F1 Score | > 0.80 |
| False Positive Rate | < 0.05 |
| Recall | > 0.90 |

## Evaluation

```bash
python scripts/evaluate.py --model backend/app/ml/models/crash_classifier.pt
```

## Fine-tuning YOLOv8

```bash
yolo train model=yolov8s.pt data=configs/yolo_finetune.yaml epochs=100 batch=16
```

## Exporting Models

For production deployment, export to ONNX:
```python
import torch
model = torch.load("crash_classifier.pt")
torch.onnx.export(model, dummy_input, "crash_classifier.onnx")
```

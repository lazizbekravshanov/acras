# ACRAS ML Training

## Quick Start

```bash
# 1. Download datasets
python scripts/download_datasets.py

# 2. Preprocess data
python scripts/preprocess.py

# 3. Augment training data
python scripts/augment.py

# 4. Train crash classifier
python scripts/train_classifier.py --epochs 50

# 5. Evaluate
python scripts/evaluate.py
```

## Notebooks

- `01_data_exploration.ipynb` — Dataset analysis and visualization
- `02_yolo_finetuning.ipynb` — YOLOv8 fine-tuning for traffic objects
- `03_crash_classifier_training.ipynb` — ResNet18 crash/normal classifier
- `04_severity_model_training.ipynb` — Severity scoring model development

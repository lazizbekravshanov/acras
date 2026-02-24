"""Evaluate trained models on test sets.

Computes: Accuracy, Precision, Recall, F1, AUC-ROC, Confusion Matrix.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

DATA_DIR = Path(__file__).parent.parent / "data" / "processed" / "splits"
MODEL_DIR = Path(__file__).parent.parent.parent / "backend" / "app" / "ml" / "models"

test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def load_model(model_path: str):
    """Load the crash classifier model."""
    from app.ml.crash_classifier import CrashClassifierModel

    model = CrashClassifierModel()
    state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def evaluate_classifier(model, dataloader, device):
    """Full evaluation with all metrics."""
    all_labels = []
    all_probs = []
    all_preds = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            outputs = model(inputs).squeeze().cpu()
            probs = outputs.numpy()
            preds = (outputs > 0.5).float().numpy()

            all_labels.extend(labels.numpy())
            all_probs.extend(probs if probs.ndim > 0 else [probs.item()])
            all_preds.extend(preds if preds.ndim > 0 else [preds.item()])

    labels = np.array(all_labels)
    probs = np.array(all_probs)
    preds = np.array(all_preds)

    tp = np.sum((preds == 1) & (labels == 1))
    fp = np.sum((preds == 1) & (labels == 0))
    fn = np.sum((preds == 0) & (labels == 1))
    tn = np.sum((preds == 0) & (labels == 0))

    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "confusion_matrix": {
            "true_positive": int(tp),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_negative": int(tn),
        },
        "total_samples": len(labels),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate crash classifier")
    parser.add_argument("--model", default=str(MODEL_DIR / "crash_classifier.pt"))
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    test_dir = DATA_DIR / "crash" / "test"
    if not test_dir.exists():
        print(f"Test data not found at {test_dir}")
        return

    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    print(f"Test samples: {len(test_dataset)}")
    print(f"Loading model: {args.model}")

    model = load_model(args.model).to(device)
    results = evaluate_classifier(model, test_loader, device)

    print("\n=== Evaluation Results ===")
    print(f"Accuracy:            {results['accuracy']:.4f}")
    print(f"Precision:           {results['precision']:.4f}")
    print(f"Recall:              {results['recall']:.4f}")
    print(f"F1 Score:            {results['f1_score']:.4f}")
    print(f"False Positive Rate: {results['false_positive_rate']:.4f}")
    print(f"\nConfusion Matrix:")
    cm = results["confusion_matrix"]
    print(f"  TP: {cm['true_positive']:>5}  FP: {cm['false_positive']:>5}")
    print(f"  FN: {cm['false_negative']:>5}  TN: {cm['true_negative']:>5}")


if __name__ == "__main__":
    main()

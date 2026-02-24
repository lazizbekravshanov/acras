"""Train the crash classifier CNN (ResNet18 backbone).

Usage: python train_classifier.py [--epochs 50] [--batch-size 32] [--lr 0.001]
"""

import argparse
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

# Add backend to path for model definition
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

DATA_DIR = Path(__file__).parent.parent / "data" / "processed" / "splits"
MODEL_OUTPUT = Path(__file__).parent.parent.parent / "backend" / "app" / "ml" / "models"

# Data transforms
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def build_model() -> nn.Module:
    """Build the crash classifier model."""
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(num_features, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1),
        nn.Sigmoid(),
    )
    return model


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch. Returns average loss and accuracy."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.float().to(device)

        optimizer.zero_grad()
        outputs = model(inputs).squeeze()
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * inputs.size(0)
        predicted = (outputs > 0.5).float()
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    return total_loss / total, correct / total


def evaluate(model, dataloader, criterion, device):
    """Evaluate model. Returns loss, accuracy, precision, recall, F1."""
    model.eval()
    total_loss = 0
    tp = fp = fn = tn = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.float().to(device)

            outputs = model(inputs).squeeze()
            loss = criterion(outputs, labels)
            total_loss += loss.item() * inputs.size(0)

            predicted = (outputs > 0.5).float()
            tp += ((predicted == 1) & (labels == 1)).sum().item()
            fp += ((predicted == 1) & (labels == 0)).sum().item()
            fn += ((predicted == 0) & (labels == 1)).sum().item()
            tn += ((predicted == 0) & (labels == 0)).sum().item()

    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return total_loss / total, accuracy, precision, recall, f1


def main():
    parser = argparse.ArgumentParser(description="Train crash classifier")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--patience", type=int, default=10)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Check for data
    train_dir = DATA_DIR / "crash" / "train"
    val_dir = DATA_DIR / "crash" / "val"

    if not train_dir.exists():
        print("Training data not found. Run preprocess.py first.")
        print(f"Expected: {train_dir}")
        print("\nGenerating a demo model with pretrained weights...")

        # Save pretrained model for demo purposes
        model = build_model()
        MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)
        output_path = MODEL_OUTPUT / "crash_classifier.pt"
        torch.save(model.state_dict(), output_path)
        print(f"Demo model saved to {output_path}")
        return

    # Load datasets
    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Classes: {train_dataset.classes}")

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)

    # Build model
    model = build_model().to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    # Training loop
    best_f1 = 0
    patience_counter = 0

    for epoch in range(args.epochs):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, precision, recall, f1 = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        print(
            f"Epoch {epoch + 1}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} P: {precision:.3f} R: {recall:.3f} F1: {f1:.3f}"
        )

        # Save best model
        if f1 > best_f1:
            best_f1 = f1
            patience_counter = 0
            MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)
            output_path = MODEL_OUTPUT / "crash_classifier.pt"
            torch.save(model.state_dict(), output_path)
            print(f"  Saved best model (F1: {f1:.3f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping at epoch {epoch + 1}")
                break

    print(f"\nTraining complete. Best F1: {best_f1:.3f}")
    print(f"Model saved to: {MODEL_OUTPUT / 'crash_classifier.pt'}")


if __name__ == "__main__":
    main()

"""Preprocess downloaded datasets for model training.

Operations:
- Extract frames from videos at 1 FPS
- Resize to 224x224 for classifier, 640x640 for YOLO
- Split into train/val/test (70/15/15)
- Generate annotation files in YOLO format
"""

import argparse
import os
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

CLASSIFIER_SIZE = (224, 224)
YOLO_SIZE = (640, 640)
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


def extract_frames(video_path: Path, output_dir: Path, fps: int = 1) -> int:
    """Extract frames from a video at the specified FPS."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30
    frame_interval = max(1, int(video_fps / fps))

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % frame_interval == 0:
            filename = f"{video_path.stem}_frame{count:05d}.jpg"
            cv2.imwrite(str(output_dir / filename), frame)
            count += 1

        frame_num += 1

    cap.release()
    return count


def resize_for_classifier(input_dir: Path, output_dir: Path) -> int:
    """Resize images to 224x224 for crash classifier training."""
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for img_path in input_dir.glob("*.jpg"):
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        resized = cv2.resize(img, CLASSIFIER_SIZE, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(output_dir / img_path.name), resized)
        count += 1

    return count


def split_dataset(source_dir: Path, output_base: Path) -> dict[str, int]:
    """Split a directory of images into train/val/test sets."""
    images = list(source_dir.glob("*.jpg"))
    random.shuffle(images)

    n = len(images)
    train_end = int(n * SPLIT_RATIOS["train"])
    val_end = train_end + int(n * SPLIT_RATIOS["val"])

    splits = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:],
    }

    counts = {}
    for split_name, split_images in splits.items():
        split_dir = output_base / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        for img in split_images:
            shutil.copy2(img, split_dir / img.name)
        counts[split_name] = len(split_images)

    return counts


def main():
    parser = argparse.ArgumentParser(description="Preprocess crash detection datasets")
    parser.add_argument("--fps", type=int, default=1, help="Frames per second to extract")
    args = parser.parse_args()

    print("=== ACRAS Data Preprocessing ===\n")

    # Step 1: Extract frames from video datasets
    crash_frames_dir = PROCESSED_DIR / "crash_frames"
    normal_frames_dir = PROCESSED_DIR / "normal_frames"

    crash_video_dirs = [
        RAW_DIR / "cadp",
        RAW_DIR / "dota",
    ]

    total_crash = 0
    for video_dir in crash_video_dirs:
        if not video_dir.exists():
            print(f"Skipping {video_dir.name} (not downloaded)")
            continue

        print(f"Extracting frames from {video_dir.name}...")
        for video_file in video_dir.rglob("*.mp4"):
            count = extract_frames(video_file, crash_frames_dir, fps=args.fps)
            total_crash += count

        for video_file in video_dir.rglob("*.avi"):
            count = extract_frames(video_file, crash_frames_dir, fps=args.fps)
            total_crash += count

    print(f"  Crash frames extracted: {total_crash}")

    # Step 2: Process normal traffic images
    normal_src = RAW_DIR / "normal_traffic"
    total_normal = 0
    if normal_src.exists():
        normal_frames_dir.mkdir(parents=True, exist_ok=True)
        for img in normal_src.glob("*.jpg"):
            shutil.copy2(img, normal_frames_dir / img.name)
            total_normal += 1
    print(f"  Normal frames: {total_normal}")

    # Step 3: Resize for classifier
    print("\nResizing for classifier (224x224)...")
    classifier_dir = PROCESSED_DIR / "classifier"
    if crash_frames_dir.exists():
        resize_for_classifier(crash_frames_dir, classifier_dir / "crash")
    if normal_frames_dir.exists():
        resize_for_classifier(normal_frames_dir, classifier_dir / "normal")

    # Step 4: Split datasets
    print("\nSplitting into train/val/test...")
    for label in ["crash", "normal"]:
        label_dir = classifier_dir / label
        if label_dir.exists():
            counts = split_dataset(label_dir, PROCESSED_DIR / "splits" / label)
            print(f"  {label}: {counts}")

    print("\nPreprocessing complete!")
    print(f"Output: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()

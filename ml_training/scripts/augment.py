"""Data augmentation for crash detection training.

Augmentations: horizontal flip, brightness/contrast, rain overlay, night simulation,
Gaussian noise, motion blur.
"""

import argparse
import random
from pathlib import Path

import cv2
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"


def add_rain(image: np.ndarray, intensity: float = 0.5) -> np.ndarray:
    """Add synthetic rain streaks to an image."""
    result = image.copy()
    h, w = result.shape[:2]
    num_drops = int(500 * intensity)

    for _ in range(num_drops):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        length = random.randint(10, 30)
        cv2.line(result, (x, y), (x + random.randint(-2, 2), y + length), (200, 200, 200), 1)

    # Slight blur to blend
    result = cv2.addWeighted(result, 0.85, cv2.GaussianBlur(result, (3, 3), 0), 0.15, 0)
    return result


def simulate_night(image: np.ndarray, darkness: float = 0.5) -> np.ndarray:
    """Simulate nighttime by reducing brightness and adding noise."""
    dark = (image * (1 - darkness * 0.7)).astype(np.uint8)
    # Add noise
    noise = np.random.normal(0, 10, dark.shape).astype(np.int16)
    noisy = np.clip(dark.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def add_motion_blur(image: np.ndarray, kernel_size: int = 15) -> np.ndarray:
    """Add horizontal motion blur."""
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
    kernel /= kernel_size
    return cv2.filter2D(image, -1, kernel)


def augment_image(image: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """Apply multiple augmentations to a single image."""
    augmented = []

    # Horizontal flip
    augmented.append(("flip", cv2.flip(image, 1)))

    # Brightness variations
    bright = cv2.convertScaleAbs(image, alpha=1.3, beta=20)
    augmented.append(("bright", bright))
    dark = cv2.convertScaleAbs(image, alpha=0.7, beta=-20)
    augmented.append(("dark", dark))

    # Rain overlay
    augmented.append(("rain", add_rain(image, intensity=0.6)))

    # Night simulation
    augmented.append(("night", simulate_night(image, darkness=0.6)))

    # Motion blur
    augmented.append(("blur", add_motion_blur(image, kernel_size=11)))

    return augmented


def main():
    parser = argparse.ArgumentParser(description="Augment training images")
    parser.add_argument("--input", default=str(DATA_DIR / "classifier" / "crash"))
    parser.add_argument("--output", default=str(DATA_DIR / "classifier" / "crash_augmented"))
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return

    images = list(input_dir.glob("*.jpg"))
    print(f"Found {len(images)} images to augment")

    total = 0
    for img_path in images:
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        # Copy original
        cv2.imwrite(str(output_dir / img_path.name), image)
        total += 1

        # Generate augmentations
        for suffix, aug_img in augment_image(image):
            aug_name = f"{img_path.stem}_{suffix}.jpg"
            cv2.imwrite(str(output_dir / aug_name), aug_img)
            total += 1

    print(f"Generated {total} images (original + augmented)")


if __name__ == "__main__":
    main()

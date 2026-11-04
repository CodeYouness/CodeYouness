"""Prep a portrait for ASCII conversion.

1. Remove the background (rembg if installed, otherwise flood-fill from the
   borders on flat/solid backgrounds such as a studio colour).
2. Boost local contrast with CLAHE so the face gets real highlights/shadows.
3. Save grayscale + subject mask (alpha) -> `source-prepped.png`.

Usage: python scripts/prep_photo.py source-photo.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def subject_mask(rgb: np.ndarray) -> np.ndarray:
    """Return a 0..1 float mask, 1 = subject."""
    try:
        from rembg import remove  # optional, heavy

        out = remove(Image.fromarray(rgb))
        return np.asarray(out)[:, :, 3].astype(np.float32) / 255.0
    except ImportError:
        pass
    # Fallback: flood-fill similar colours connected to the image border.
    h, w = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ff = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    for x, y in [(0, 0), (w - 1, 0), (0, h // 2), (w - 1, h // 2), (w // 2, 0)]:
        cv2.floodFill(bgr, ff, (x, y), 0, (40, 40, 40), (40, 40, 40), flags)
    bg = ff[1:-1, 1:-1] > 0
    bg = cv2.morphologyEx(bg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = 1.0 - bg.astype(np.float32)
    return cv2.GaussianBlur(mask, (5, 5), 0)


def main(src: str) -> None:
    rgb = np.asarray(Image.open(src).convert("RGB"))
    mask = subject_mask(rgb)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)
    # Keep the mask as alpha: the ASCII step maps background -> blank.
    la = np.dstack([gray.clip(0, 255), mask * 255.0]).astype(np.uint8)
    Image.fromarray(la, "LA").save(ROOT / "source-prepped.png")
    print("wrote source-prepped.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "source-photo.png"))

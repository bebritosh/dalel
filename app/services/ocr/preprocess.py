"""Image preprocessing for OCR: EXIF rotation, grayscale, contrast boost."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def preprocess_image(file_path: Path) -> Image.Image:
    """Open an image and apply orientation fix, grayscale and autocontrast."""
    image = Image.open(file_path)
    image = ImageOps.exif_transpose(image)  # honor EXIF orientation
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return image

"""Image preprocessing for OCR: EXIF rotation, grayscale, contrast boost."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

UPSCALE_BELOW_WIDTH = 1200


def preprocess_image(file_path: Path) -> Image.Image:
    """Open an image and apply orientation fix, grayscale and autocontrast."""
    image = Image.open(file_path)
    image = ImageOps.exif_transpose(image)  # honor EXIF orientation
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    # Upscale small images: Tesseract works best on ~30px x-height text, and
    # small-font / blurred receipts lose characters at native size.
    if image.width < UPSCALE_BELOW_WIDTH:
        image = image.resize((int(image.width * 1.5), int(image.height * 1.5)), Image.LANCZOS)
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return image

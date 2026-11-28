"""Photo-quality checks (Pillow): resolution, blur, exposure, EXIF date."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from tests.conftest import create_case
from tests.test_pipeline import _upload


def _png(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _jpg_with_exif_date(exif_date: str) -> bytes:
    """A small, flat, dark JPEG carrying an EXIF DateTime (YYYY:MM:DD HH:MM:SS)."""
    image = Image.new("RGB", (120, 120), (20, 20, 20))
    exif = Image.Exif()
    exif[0x0132] = exif_date  # DateTime
    buf = BytesIO()
    image.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def _good_photo() -> bytes:
    """Large, sharp, mid-brightness image: should raise no findings."""
    image = Image.new("RGB", (1000, 1000), (128, 128, 128))
    draw = ImageDraw.Draw(image)
    for x in range(0, 1000, 40):
        draw.line([(x, 0), (x, 1000)], fill=(0, 0, 0), width=3)
        draw.line([(0, x), (1000, x)], fill=(255, 255, 255), width=3)
    return _png(image)


def _upload_photo(client, case_id, token, name, content, mime):
    return client.post(
        f"/cases/{case_id}/documents",
        headers={"X-Case-Token": token},
        data={"kind": "photo"},
        files={"file": (name, content, mime)},
    )


def test_small_blurry_dark_photo_flags_p1_p2_p3(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    small_flat = Image.new("RGB", (100, 100), (20, 20, 20))  # tiny, flat, dark
    assert _upload_photo(client, case_id, token, "bad.png", _png(small_flat), "image/png").status_code == 201
    codes = {c["code"] for c in client.get(f"/cases/{case_id}/checks", headers=h).json()}
    assert {"P1", "P2", "P3"} <= codes


def test_good_photo_has_no_photo_findings(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    assert _upload_photo(client, case_id, token, "good.png", _good_photo(), "image/png").status_code == 201
    codes = {c["code"] for c in client.get(f"/cases/{case_id}/checks", headers=h).json()}
    assert not ({"P1", "P2", "P3", "P4"} & codes)


def test_exif_date_before_purchase_flags_p4(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    # Extraction gives purchase_date 2026-11-05 for the demo receipt.
    _upload(client, case_id, token, "receipt.png", "receipt", "image/png")
    client.post(f"/cases/{case_id}/extract", headers=h)
    # Photo taken in 2020, before the purchase → P4 (needs review, not blocking).
    _upload_photo(client, case_id, token, "old.jpg", _jpg_with_exif_date("2020:01:01 10:00:00"), "image/jpeg")
    checks = client.get(f"/cases/{case_id}/checks", headers=h).json()
    p4 = [c for c in checks if c["code"] == "P4"]
    assert p4 and p4[0]["severity"] == "warning"


def test_photo_checks_are_warnings_only(client):
    """Photo findings never carry error severity, so they never block export."""
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    _upload_photo(client, case_id, token, "bad.png", _png(Image.new("RGB", (100, 100), (20, 20, 20))), "image/png")
    photo_checks = [c for c in client.get(f"/cases/{case_id}/checks", headers=h).json() if c["code"].startswith("P")]
    assert photo_checks
    assert all(c["severity"] == "warning" for c in photo_checks)

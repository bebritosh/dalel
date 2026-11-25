"""Photo-quality checks on defect images (Pillow only).

Checks: resolution (P1), blur via edge-variance (P2), exposure (P3) and EXIF
capture date vs purchase date (P4). All findings are warnings — they inform the
user and never block export. Defect recognition is explicitly out of scope: we
only judge whether the photo is usable, not what it shows.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from PIL import Image, ImageFilter, ImageOps, ImageStat
from sqlmodel import Session, select

from app.models import Document, DocumentKind, Fact
from app.schemas.checks import CheckResult
from app.services.extract.normalize import normalize_date

_RULES_PATH = Path("rules/validation.yaml")
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_EXIF_DATETIME_ORIGINAL = 0x9003
_EXIF_IFD = 0x8769


def _load_rules() -> dict[str, dict]:
    data = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
    return {rule["id"]: rule for rule in data.get("rules", [])}


def _blur_variance(gray: Image.Image) -> float:
    """Variance of the edge image: low variance ≈ few edges ≈ blurry."""
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).var[0])


def _exif_date(image: Image.Image) -> date | None:
    try:
        exif = image.getexif()
        ifd = exif.get_ifd(_EXIF_IFD)
        raw = ifd.get(_EXIF_DATETIME_ORIGINAL) or exif.get(0x0132)
    except (AttributeError, OSError, ValueError):
        return None
    if not raw:
        return None
    # EXIF format: "YYYY:MM:DD HH:MM:SS".
    return normalize_date(str(raw).split(" ")[0].replace(":", "-"))


def check_photos(session: Session, case_id: int) -> list[CheckResult]:
    """Return photo-quality findings for a case's defect photos."""
    rules = _load_rules()
    photos = session.exec(
        select(Document).where(
            Document.case_id == case_id, Document.kind == DocumentKind.photo
        )
    ).all()
    if not photos:
        return []

    pdate_fact = session.exec(
        select(Fact).where(Fact.case_id == case_id, Fact.field == "purchase_date")
    ).first()
    purchase_date = normalize_date(pdate_fact.value) if pdate_fact and pdate_fact.value else None

    results: list[CheckResult] = []

    def mk(code: str, doc_id: int) -> CheckResult:
        rule = rules[code]
        return CheckResult(
            code=code, severity=rule["severity"], message=rule["message"],
            document_ids=[doc_id],
        )

    for doc in photos:
        path = Path(doc.stored_path)
        if path.suffix.lower() not in _IMAGE_SUFFIXES or not path.exists():
            continue  # non-image evidence (e.g. mp4 video) is not analysed
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                exif_day = _exif_date(image)
                gray = ImageOps.grayscale(image)
                width, height = gray.size
                blur_var = _blur_variance(gray)
                brightness = float(ImageStat.Stat(gray).mean[0])
        except OSError:
            continue  # unreadable image — not a photo-quality finding

        p1 = rules["P1"]
        if min(width, height) < p1["min_side"]:
            results.append(mk("P1", doc.id))
        if blur_var < rules["P2"]["blur_var_min"]:
            results.append(mk("P2", doc.id))
        p3 = rules["P3"]
        if brightness < p3["brightness_min"] or brightness > p3["brightness_max"]:
            results.append(mk("P3", doc.id))
        if purchase_date and exif_day and exif_day < purchase_date:
            results.append(mk("P4", doc.id))

    return results

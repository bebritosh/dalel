"""The backend-free demo ships the real claim text and a real DOCX."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.make_mock_exports import CLAIM_TS, PUBLIC, claim_ts, demo_exports


def test_mock_claim_text_matches_backend():
    out = demo_exports()
    assert CLAIM_TS.read_text(encoding="utf-8") == claim_ts(out["text"]), (
        "frontend/src/mock/claimText.ts is stale: run scripts/make_mock_exports.py"
    )


def test_mock_docx_is_a_real_docx():
    path = PUBLIC / "pretenziya_demo.docx"
    assert zipfile.is_zipfile(path)
    with zipfile.ZipFile(path) as z:
        assert "word/document.xml" in z.namelist()
    assert Path(PUBLIC / "pretenziya_demo.docx").stat().st_size > 10_000

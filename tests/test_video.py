"""mp4 defect video is accepted as evidence (kind=photo) and resolves M3."""

from __future__ import annotations

from tests.conftest import create_case


def _m3_resolved(client, case_id, h) -> bool:
    items = client.get(f"/cases/{case_id}/missing", headers=h).json()
    return next(i for i in items if i["rule_id"] == "M3")["resolved"]


def test_mp4_upload_accepted_and_resolves_m3(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    assert _m3_resolved(client, case_id, h) is False

    # Minimal mp4 header bytes; content is never analysed, only stored.
    mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
    up = client.post(
        f"/cases/{case_id}/documents",
        headers=h,
        data={"kind": "photo"},
        files={"file": ("defect.mp4", mp4, "video/mp4")},
    )
    assert up.status_code == 201
    assert up.json()["mime_type"] == "video/mp4"
    assert _m3_resolved(client, case_id, h) is True


def test_mp4_does_not_break_photo_checks(client):
    """Photo-quality checks skip the video without error."""
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
    client.post(
        f"/cases/{case_id}/documents",
        headers=h,
        data={"kind": "photo"},
        files={"file": ("defect.mp4", mp4, "video/mp4")},
    )
    resp = client.get(f"/cases/{case_id}/checks", headers=h)
    assert resp.status_code == 200
    assert not [c for c in resp.json() if c["code"].startswith("P")]

"""Keep the frontend dictionaries in sync with each other and with the backend.

There is no JS test runner in the project, so these checks read the .ts/.tsx
sources as text:
- ru/en/kk dictionaries have the same keys (no untranslated key in one language);
- every missing-evidence rule (rules/missing_evidence.yaml) has localized
  title/why/fix, and the RU text equals the server text;
- every event description the backend writes starts with a label that the
  Timeline component knows how to localize.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "frontend" / "src" / "i18n"
_ENTRY_RE = re.compile(r'^\s*("(?:[^"\\]|\\.)+"|[A-Za-z_]\w*)\s*:\s*"((?:[^"\\]|\\.)*)",?\s*$')


def _dict(lang: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (I18N / f"{lang}.ts").read_text(encoding="utf-8").splitlines():
        m = _ENTRY_RE.match(line)
        if m:
            out[m.group(1).strip('"')] = m.group(2).replace('\\"', '"')
    return out


def test_dictionaries_have_same_keys() -> None:
    ru, en, kk = _dict("ru"), _dict("en"), _dict("kk")
    assert len(ru) > 50
    assert set(ru) == set(en), set(ru) ^ set(en)
    assert set(ru) == set(kk), set(ru) ^ set(kk)


def test_missing_rules_are_localized() -> None:
    rules = yaml.safe_load((ROOT / "rules" / "missing_evidence.yaml").read_text(encoding="utf-8"))
    ru, en, kk = _dict("ru"), _dict("en"), _dict("kk")
    for rule in rules["rules"]:
        for part in ("title", "why", "fix"):
            key = f"missing.{rule['id']}.{part}"
            assert key in en and key in kk, key
            assert ru.get(key) == rule[part], f"{key}: RU text differs from the YAML"


def test_backend_event_labels_are_known_to_timeline() -> None:
    timeline = (ROOT / "frontend" / "src" / "components" / "Timeline.tsx").read_text(encoding="utf-8")
    block = re.search(r"RU_LABELS[^{]*\{(.*?)\};", timeline, re.S)
    assert block, "RU_LABELS not found in Timeline.tsx"
    known = set(re.findall(r'"([^"]+)":\s*"\w+"', block.group(1)))

    sources = [ROOT / "app" / "services" / "chat.py", ROOT / "app" / "services" / "timeline.py"]
    labels = set()
    for src in sources:
        for m in re.finditer(r'description=f?"([^"«]+?)(?::\s*«|")', src.read_text(encoding="utf-8")):
            labels.add(m.group(1))
    assert labels, "no event descriptions found in the backend"
    assert labels <= known, f"labels missing in Timeline.tsx RU_LABELS: {labels - known}"

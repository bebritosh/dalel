"""Extraction orchestration: OCR -> LLM provider -> grounded Facts."""

from __future__ import annotations

from sqlmodel import Session, select

from app.core.config import settings
from app.models import Case, CaseStatus, Document, DocumentKind, Fact, OcrLine
from app.services.extract.base import LlmProvider
from app.services.extract.fixture_provider import FixtureProvider
from app.services.extract.grounding import is_grounded
from app.services.extract.live_provider import LiveProvider
from app.services.extract.schema import ExtractedField, ExtractionResult
from app.services.ocr import run_ocr


def get_provider() -> LlmProvider:
    """Return the configured extraction provider (fixture by default)."""
    if settings.llm_mode == "live":
        return LiveProvider()
    return FixtureProvider()


def _make_scalar_fact(
    case_id: int,
    document_id: int,
    field: str,
    extracted: ExtractedField,
    lines_by_id: dict[int, OcrLine],
) -> Fact:
    grounded = is_grounded(field, extracted.value, extracted.line_ids, lines_by_id)
    confidence = extracted.confidence if grounded else min(extracted.confidence, 0.3)
    return Fact(
        case_id=case_id,
        field=field,
        value=extracted.value,
        confidence=confidence,
        document_id=document_id,
        line_ids=list(extracted.line_ids),
        grounded=grounded,
        needs_review=not grounded,
        confirmed_by_user=False,
    )


def _facts_from_result(
    case_id: int,
    document_id: int,
    result: ExtractionResult,
    lines_by_id: dict[int, OcrLine],
) -> list[Fact]:
    facts: list[Fact] = []
    fields = result.fields
    for name in ("seller_name", "purchase_date", "total_amount", "currency"):
        extracted = getattr(fields, name)
        if extracted is not None:
            facts.append(
                _make_scalar_fact(case_id, document_id, name, extracted, lines_by_id)
            )
    for idx, item in enumerate(fields.items, start=1):
        grounded = is_grounded("item", item.name, item.line_ids, lines_by_id)
        facts.append(
            Fact(
                case_id=case_id,
                field=f"item_{idx}",
                value=item.name,
                confidence=0.8 if grounded else 0.3,
                document_id=document_id,
                line_ids=list(item.line_ids),
                grounded=grounded,
                needs_review=not grounded,
            )
        )
        if item.price:
            price_grounded = is_grounded(
                "price", item.price, item.line_ids, lines_by_id
            )
            facts.append(
                Fact(
                    case_id=case_id,
                    field=f"item_{idx}_price",
                    value=item.price,
                    confidence=0.8 if price_grounded else 0.3,
                    document_id=document_id,
                    line_ids=list(item.line_ids),
                    grounded=price_grounded,
                    needs_review=not price_grounded,
                )
            )
    for name in result.unreadable:
        facts.append(
            Fact(
                case_id=case_id,
                field=name,
                value="",
                confidence=0.0,
                document_id=document_id,
                line_ids=[],
                needs_review=True,
            )
        )
    return facts


def run_extraction(session: Session, case: Case) -> list[Fact]:
    """Run OCR + extraction for a case's receipts and persist grounded Facts.

    Idempotent: if facts already exist for the case, they are returned as-is.
    """
    existing = session.exec(select(Fact).where(Fact.case_id == case.id)).all()
    if existing:
        return list(existing)

    provider = get_provider()
    receipts = session.exec(
        select(Document).where(
            Document.case_id == case.id, Document.kind == DocumentKind.receipt
        )
    ).all()

    created: list[Fact] = []
    for doc in receipts:
        lines = run_ocr(session, doc)
        lines_by_id = {line.line_no: line for line in lines}
        result = provider.extract(doc.sha256, lines)
        for fact in _facts_from_result(case.id, doc.id, result, lines_by_id):
            session.add(fact)
            created.append(fact)

    case.status = CaseStatus.extracted
    session.add(case)
    session.commit()
    for fact in created:
        session.refresh(fact)
    return created

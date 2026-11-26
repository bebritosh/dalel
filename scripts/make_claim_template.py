"""Generate templates/claim.docx with docxtpl placeholders.

Run once to (re)create the template:
    python scripts/make_claim_template.py

The produced .docx is a plain Word file a lawyer can edit. Static text is kept
free of digits so the output guard only ever sees grounded values.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path("templates/claim.docx")


def _setup_page(doc: Document) -> None:
    """A4, standard margins for Kazakhstan business letters, Times New Roman 14."""
    for section in doc.sections:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)
        section.top_margin = section.bottom_margin = Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    # East-Asian/complex-script fallbacks so Word does not swap the font.
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), "Times New Roman")
    pf = normal.paragraph_format
    pf.space_after = Pt(0)
    pf.line_spacing = 1.15


def _heading(doc: Document, text: str) -> None:
    run = doc.add_paragraph().add_run(text)
    run.bold = True


def build() -> None:
    doc = Document()
    _setup_page(doc)

    title = doc.add_paragraph()
    run = title.add_run("ПРЕТЕНЗИЯ")
    run.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("Кому: {{ seller }}")
    doc.add_paragraph(
        "От кого: [ФИО заявителя], [адрес заявителя], [контактные данные]"
    )
    doc.add_paragraph("")
    doc.add_paragraph(
        "Я приобрёл(а) у продавца {{ seller }} товар: {{ item_desc }}. "
        "Дата покупки: {{ purchase_date }}. "
        "Стоимость товара составила {{ amount }} {{ currency }}."
    )
    doc.add_paragraph(
        "В процессе эксплуатации в товаре обнаружился недостаток, "
        "товар оказался ненадлежащего качества."
    )
    doc.add_paragraph("")
    _heading(doc, "Хронология обращения:")
    doc.add_paragraph("— {{ purchase_date }}: покупка товара.")
    # {%p ... %} tags remove their own paragraph: no empty lines when absent.
    doc.add_paragraph("{%p if contact_date %}")
    doc.add_paragraph("— {{ contact_date }}: обращение к продавцу.")
    doc.add_paragraph("{%p endif %}")
    doc.add_paragraph("{%p if refusal_date %}")
    doc.add_paragraph(
        "— {{ refusal_date }}: продавец отказал в удовлетворении требования."
    )
    doc.add_paragraph("{%p endif %}")
    doc.add_paragraph("")
    _heading(doc, "Требование:")
    doc.add_paragraph(
        "{% if remedy_citation %}На основании {{ remedy_citation }} прошу"
        "{% else %}Прошу{% endif %} расторгнуть договор купли-продажи и вернуть "
        "уплаченную за товар денежную сумму {{ amount }} {{ currency }}."
    )
    doc.add_paragraph("{%p if term_citation %}")
    doc.add_paragraph(
        "Ответ на претензию прошу дать в письменной форме в течение десяти "
        "календарных дней со дня её получения ({{ term_citation }})."
    )
    doc.add_paragraph("{%p endif %}")
    doc.add_paragraph("")
    _heading(doc, "Приложения:")
    doc.add_paragraph("— копия чека;")
    doc.add_paragraph("— экспорт переписки с продавцом.")
    doc.add_paragraph("")
    _heading(doc, "Правовое обоснование:")
    doc.add_paragraph("{%p for ref in legal %}")
    doc.add_paragraph("— {{ ref.citation }}: {{ ref.text }}.")
    doc.add_paragraph("{%p endfor %}")
    doc.add_paragraph("")
    doc.add_paragraph("[ФИО заявителя], подпись, дата.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()

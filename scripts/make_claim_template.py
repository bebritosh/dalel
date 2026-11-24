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

OUT = Path("templates/claim.docx")


def build() -> None:
    doc = Document()

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
    doc.add_paragraph("Хронология обращения:")
    doc.add_paragraph("— {{ purchase_date }}: покупка товара.")
    doc.add_paragraph(
        "{% if contact_date %}— {{ contact_date }}: обращение к продавцу.{% endif %}"
    )
    doc.add_paragraph(
        "{% if refusal_date %}— {{ refusal_date }}: продавец отказал "
        "в удовлетворении требования.{% endif %}"
    )
    doc.add_paragraph("")
    doc.add_paragraph("Требование:")
    doc.add_paragraph(
        "Прошу вернуть уплаченную за товар денежную сумму "
        "{{ amount }} {{ currency }}."
    )
    doc.add_paragraph("")
    doc.add_paragraph("Приложения:")
    doc.add_paragraph("— копия чека;")
    doc.add_paragraph("— экспорт переписки с продавцом.")
    doc.add_paragraph("")
    doc.add_paragraph("Правовое обоснование:")
    doc.add_paragraph("{%p for ref in legal %}")
    doc.add_paragraph("— {{ ref.title }}: [норма уточняется юристом].")
    doc.add_paragraph("{%p endfor %}")
    doc.add_paragraph("")
    doc.add_paragraph("[ФИО заявителя], подпись, дата.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()

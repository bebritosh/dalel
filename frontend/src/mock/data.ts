// Fully synthetic mock data for VITE_API_MODE=mock (no backend needed).
import type {
  CaseDetail,
  CheckResult,
  Fact,
  MissingItem,
  OcrLine,
  TimelineEvent,
} from "../api/types";

export const RECEIPT_NATURAL = { width: 760, height: 1040 };

// bbox: [x, top, width, height] in the SVG's 760x1040 coordinate space.
export const mockLines: OcrLine[] = [
  ["ТОО «Пример Электроникс»", 48, 48, 420, 44],
  ["г. Алматы, пр. Абая 150", 48, 120, 360, 44],
  ["Чек № 000123", 48, 192, 220, 44],
  ["Дата: 05.11.2026 14:32", 48, 264, 360, 44],
  ["Кассир: Иванова А.", 48, 336, 300, 44],
  ["--------------------------------", 48, 408, 520, 44],
  ["Смартфон X 128GB", 48, 480, 300, 44],
  ["1 шт x 249 990,00", 48, 552, 300, 44],
  ["--------------------------------", 48, 624, 520, 44],
  ["ИТОГО: 249 990,00 KZT", 48, 696, 380, 44],
  ["Оплата: карта", 48, 768, 220, 44],
  ["Спасибо за покупку!", 48, 840, 320, 44],
].map(([text, x, top, w, h], i) => ({
  id: i + 1,
  line_no: i,
  text: text as string,
  bbox_x: x as number,
  bbox_y: top as number,
  bbox_w: w as number,
  bbox_h: h as number,
  page: 0,
}));

function fact(
  id: number,
  field: string,
  value: string,
  line_ids: number[],
  grounded: boolean,
  confirmed = false,
): Fact {
  return {
    id,
    field,
    value,
    confidence: grounded ? 0.9 : 0.2,
    document_id: 1,
    line_ids,
    grounded,
    needs_review: !grounded,
    confirmed_by_user: confirmed,
  };
}

export const mockFacts: Fact[] = [
  fact(1, "seller_name", "ТОО «Пример Электроникс»", [0], true),
  fact(2, "purchase_date", "2026-11-05", [3], true),
  fact(3, "total_amount", "249990.00", [9], true),
  fact(4, "currency", "KZT", [9], true),
  fact(5, "item_1", "Смартфон X 128GB", [6, 7], true),
  fact(6, "item_1_price", "249990.00", [6, 7], true),
  fact(7, "warranty_period", "", [], false),
];

export const mockEvents: TimelineEvent[] = [
  {
    id: 1,
    date: "2026-11-05",
    kind: "purchase",
    description: "Покупка товара по чеку",
    document_id: 1,
    needs_review: true,
  },
  {
    id: 2,
    date: "2026-11-06",
    kind: "contact",
    description: "Первое обращение к продавцу: «экран мигает и сильно греется»",
    document_id: 2,
    needs_review: true,
  },
  {
    id: 3,
    date: "2026-11-09",
    kind: "refusal",
    description: "Отказ продавца: «вернуть деньги не можем, случай не гарантийный»",
    document_id: 2,
    needs_review: true,
  },
];

export const mockMissing: MissingItem[] = [
  {
    rule_id: "M1",
    title: "Нет данных о гарантии",
    why: "Гарантийный срок усиливает требование и влияет на права покупателя.",
    fix: "Загрузите гарантийный талон или найдите срок гарантии на чеке/упаковке.",
    resolved: false,
  },
  {
    rule_id: "M2",
    title: "Нет даты первого обращения к продавцу",
    why: "С даты обращения отсчитывается срок ответа продавца.",
    fix: "Добавьте экспорт переписки, где видно первое обращение.",
    resolved: true,
  },
  {
    rule_id: "M3",
    title: "Нет фото или видео дефекта",
    why: "Доказательство дефекта подтверждает некачественность товара.",
    fix: "Загрузите фото или видео, где виден дефект.",
    resolved: false,
  },
  {
    rule_id: "M4",
    title: "Нет письменного отказа продавца",
    why: "Письменный отказ подтверждает, что спор не решён добровольно.",
    fix: "Добавьте переписку с отказом продавца.",
    resolved: true,
  },
  {
    rule_id: "M5",
    title: "Чек нечитаем или поля не распознаны",
    why: "Без читаемого чека нельзя подтвердить покупку и сумму.",
    fix: "Загрузите более чёткое фото чека или введите поля вручную.",
    resolved: true,
  },
];

export const mockChecks: CheckResult[] = [];

export const mockClaimText = [
  "ПРЕТЕНЗИЯ",
  "",
  "Кому: ТОО «Пример Электроникс»",
  "От кого: [ФИО заявителя], [адрес заявителя], [контактные данные]",
  "",
  "Я приобрёл(а) у продавца ТОО «Пример Электроникс» товар: Смартфон X 128GB. " +
    "Дата покупки: 05.11.2026. Стоимость товара составила 249 990,00 KZT.",
  "В процессе эксплуатации в товаре обнаружился недостаток, товар оказался ненадлежащего качества.",
  "",
  "Хронология обращения:",
  "— 05.11.2026: покупка товара.",
  "— 06.11.2026: обращение к продавцу.",
  "— 09.11.2026: продавец отказал в удовлетворении требования.",
  "",
  "Требование:",
  "Прошу вернуть уплаченную за товар денежную сумму 249 990,00 KZT.",
  "",
  "Приложения:",
  "— копия чека;",
  "— экспорт переписки с продавцом.",
  "",
  "Правовое обоснование:",
  "— Право на товар надлежащего качества: [норма уточняется юристом].",
  "— Права потребителя при обнаружении недостатков товара: [норма уточняется юристом].",
  "— Срок рассмотрения требования продавцом: [норма уточняется юристом].",
  "",
  "[ФИО заявителя], подпись, дата.",
].join("\n");

export const mockCase: CaseDetail = {
  id: 1,
  status: "extracted",
  claim_type: "defective_goods",
  created_at: new Date().toISOString(),
  response_deadline: null,
  documents: [
    {
      id: 1,
      case_id: 1,
      kind: "receipt",
      sha256: "mock",
      mime_type: "image/svg+xml",
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      case_id: 1,
      kind: "chat",
      sha256: "mock2",
      mime_type: "text/plain",
      created_at: new Date().toISOString(),
    },
  ],
  facts: mockFacts,
  receipt_document_id: 1,
};

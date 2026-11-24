// Formatting helpers that mirror the backend's claim rendering.

export function fieldLabel(
  field: string,
  t: (k: string) => string,
): string {
  if (field.startsWith("item_") && field.endsWith("_price")) {
    return t("field.price");
  }
  if (field.startsWith("item_")) {
    const idx = field.slice("item_".length);
    return `${t("field.item")} ${idx}`;
  }
  const known = t(`field.${field}`);
  return known === `field.${field}` ? field : known;
}

// "249990.00" -> "249 990,00"
export function fmtAmount(value: string): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return value;
  const [whole, frac] = num.toFixed(2).split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${grouped},${frac}`;
}

// "2026-11-05" -> "05.11.2026"
export function fmtDate(iso: string | null): string {
  if (!iso) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  return `${m[3]}.${m[2]}.${m[1]}`;
}

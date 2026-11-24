import { useEffect, useRef, useState } from "react";
import type { OcrLine } from "../api/types";
import { useI18n } from "../i18n";

interface Props {
  imageUrl: string;
  lines: OcrLine[];
  selectedLineIds: number[];
  naturalWidth?: number;
  naturalHeight?: number;
}

export function ReceiptViewer({
  imageUrl,
  lines,
  selectedLineIds,
  naturalWidth,
  naturalHeight,
}: Props) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const [nat, setNat] = useState({
    w: naturalWidth ?? 0,
    h: naturalHeight ?? 0,
  });
  const [scale, setScale] = useState(1);

  function fit() {
    const c = containerRef.current;
    if (c && nat.w > 0) setScale((c.clientWidth - 24) / nat.w);
  }

  useEffect(() => {
    if (nat.w > 0 && scale === 1) fit();
  }, [nat.w]);

  // Scroll the first selected box into view.
  useEffect(() => {
    if (!selectedLineIds.length) return;
    const first = lines.find((l) => selectedLineIds.includes(l.line_no));
    const c = containerRef.current;
    if (first && c) {
      c.scrollTo({ top: Math.max(0, first.bbox_y * scale - 60), behavior: "smooth" });
    }
  }, [selectedLineIds, lines, scale]);

  const selected = lines.filter((l) => selectedLineIds.includes(l.line_no));

  return (
    <div className="rounded-card border border-border bg-surface">
      <div className="flex items-center gap-2 border-b border-border p-2">
        <button
          type="button"
          aria-label={t("receipt.zoomOut")}
          onClick={() => setScale((s) => Math.max(0.2, s - 0.2))}
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-bg"
        >
          −
        </button>
        <button
          type="button"
          aria-label={t("receipt.zoomIn")}
          onClick={() => setScale((s) => Math.min(3, s + 0.2))}
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-bg"
        >
          +
        </button>
        <button
          type="button"
          onClick={fit}
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-bg"
        >
          {t("receipt.fit")}
        </button>
      </div>

      <div
        ref={containerRef}
        className="relative max-h-[70vh] overflow-auto p-3"
      >
        {!selected.length && (
          <p className="mb-2 text-sm text-muted">{t("receipt.hint")}</p>
        )}
        <div
          className="relative"
          style={{ width: nat.w ? nat.w * scale : "100%" }}
        >
          <img
            src={imageUrl}
            alt="Чек"
            className="block w-full select-none"
            onLoad={(e) => {
              const img = e.currentTarget;
              if (!nat.w && img.naturalWidth) {
                setNat({ w: img.naturalWidth, h: img.naturalHeight });
              }
            }}
          />
          {nat.w > 0 && (
            <svg
              className="pointer-events-none absolute left-0 top-0"
              width={nat.w * scale}
              height={nat.h * scale}
              viewBox={`0 0 ${nat.w} ${nat.h}`}
            >
              {selected.map((l) => (
                <rect
                  key={l.id}
                  x={l.bbox_x}
                  y={l.bbox_y}
                  width={l.bbox_w}
                  height={l.bbox_h}
                  fill="var(--color-highlight)"
                  fillOpacity="0.45"
                  stroke="var(--color-highlight-border)"
                  strokeWidth="2"
                  rx="4"
                />
              ))}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}

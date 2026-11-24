import { Fragment } from "react";

export interface ClaimToken {
  match: string; // the exact substring to make clickable
  lineIds: number[]; // receipt OCR line numbers to highlight
}

interface Props {
  text: string;
  tokens: ClaimToken[];
  activeMatch: string | null;
  onSelect: (token: ClaimToken) => void;
}

interface Segment {
  text: string;
  token?: ClaimToken;
}

function segmentLine(line: string, tokens: ClaimToken[]): Segment[] {
  const segments: Segment[] = [];
  let i = 0;
  while (i < line.length) {
    let best: { index: number; token: ClaimToken } | null = null;
    for (const tk of tokens) {
      if (!tk.match) continue;
      const idx = line.indexOf(tk.match, i);
      if (idx !== -1 && (best === null || idx < best.index)) {
        best = { index: idx, token: tk };
      }
    }
    if (!best) {
      segments.push({ text: line.slice(i) });
      break;
    }
    if (best.index > i) segments.push({ text: line.slice(i, best.index) });
    segments.push({ text: best.token.match, token: best.token });
    i = best.index + best.token.match.length;
  }
  return segments;
}

export function ClaimText({ text, tokens, activeMatch, onSelect }: Props) {
  const lines = text.split("\n");
  return (
    <div className="whitespace-pre-wrap text-[15px] leading-7 text-text">
      {lines.map((line, li) => (
        <Fragment key={li}>
          {segmentLine(line, tokens).map((seg, si) =>
            seg.token ? (
              <button
                key={si}
                type="button"
                onClick={() => onSelect(seg.token!)}
                aria-label={`${seg.text}, показать в чеке`}
                title={`line_ids: ${seg.token.lineIds.join(", ")}`}
                className={`tabular cursor-pointer rounded-sm underline decoration-dotted decoration-accent underline-offset-4 hover:bg-highlight/40 ${
                  activeMatch === seg.text ? "bg-highlight/60" : ""
                }`}
              >
                {seg.text}
              </button>
            ) : (
              <span key={si}>{seg.text}</span>
            ),
          )}
          {"\n"}
        </Fragment>
      ))}
    </div>
  );
}

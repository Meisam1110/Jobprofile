/** Chart primitives following the dataviz method: thin marks, rounded data
 * ends, recessive grid, hover tooltips, text in ink tokens (never series
 * color), sequential single-hue ramp for magnitude. */
import { ReactNode, useState } from "react";
import { SEQUENTIAL, SERIES } from "../api";

export function StatTile({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: string; tone?: "good" | "warning" | "critical" }) {
  const toneClass = tone === "critical" ? "text-status-critical" : tone === "warning" ? "text-amber-700" : tone === "good" ? "text-green-800" : "text-ink";
  return (
    <div className="card p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</div>
      <div className={`mt-1 text-3xl font-bold ${toneClass}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-ink-muted">{hint}</div>}
    </div>
  );
}

/** Horizontal bar list — magnitude across categories (single series → one hue). */
export function BarList({ data, color = SERIES[0], maxRows = 12, onClick }: {
  data: { name: string; count: number }[];
  color?: string;
  maxRows?: number;
  onClick?: (name: string) => void;
}) {
  const rows = data.slice(0, maxRows);
  const max = Math.max(...rows.map((r) => r.count), 1);
  return (
    <div className="space-y-1.5">
      {rows.map((r) => (
        <button
          key={r.name}
          className="group flex w-full items-center gap-2 text-left"
          onClick={() => onClick?.(r.name)}
          title={`${r.name}: ${r.count}`}
        >
          <div className="w-44 truncate text-xs text-ink-secondary">{r.name}</div>
          <div className="relative h-4 flex-1 rounded bg-plane">
            <div
              className="absolute inset-y-0 left-0 rounded group-hover:opacity-80"
              style={{ width: `${(r.count / max) * 100}%`, backgroundColor: color, minWidth: 2 }}
            />
          </div>
          <div className="w-10 text-right text-xs tabular-nums text-ink-secondary">{r.count}</div>
        </button>
      ))}
    </div>
  );
}

/** Grade distribution — ordered columns, one hue (grades are ordinal). */
export function ColumnChart({ data, order }: { data: Record<string, number>; order: string[] }) {
  const [hover, setHover] = useState<string | null>(null);
  const entries = order.filter((k) => data[k] !== undefined).map((k) => ({ key: k, value: data[k] }));
  const max = Math.max(...entries.map((e) => e.value), 1);
  return (
    <div className="flex h-40 items-end gap-3 px-1">
      {entries.map((e, i) => (
        <div key={e.key} className="relative flex flex-1 flex-col items-center gap-1" onMouseEnter={() => setHover(e.key)} onMouseLeave={() => setHover(null)}>
          {hover === e.key && (
            <div className="absolute -top-7 rounded bg-brand-ink px-2 py-0.5 text-xs text-white">{e.value}</div>
          )}
          <div
            className="w-full max-w-12 rounded-t"
            style={{
              height: `${Math.max((e.value / max) * 128, 3)}px`,
              backgroundColor: SEQUENTIAL[Math.min(2 + i, SEQUENTIAL.length - 1)],
            }}
          />
          <div className="text-xs font-medium text-ink-secondary">{e.key}</div>
        </div>
      ))}
    </div>
  );
}

/** Job-family × grade heat map — sequential ramp, hover tooltip per cell. */
export function HeatMap({ grades, rows }: { grades: string[]; rows: Record<string, number | string>[] }) {
  const max = Math.max(...rows.flatMap((r) => grades.map((g) => Number(r[g] ?? 0))), 1);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="pb-1 pr-2 text-left font-semibold text-ink-muted">Job family</th>
            {grades.map((g) => (
              <th key={g} className="w-10 pb-1 text-center font-semibold text-ink-muted">{g}</th>
            ))}
            <th className="w-12 pb-1 text-right font-semibold text-ink-muted">Total</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={String(r.family)}>
              <td className="max-w-52 truncate py-0.5 pr-2 text-ink-secondary">{String(r.family)}</td>
              {grades.map((g) => {
                const value = Number(r[g] ?? 0);
                const step = value === 0 ? -1 : Math.min(Math.floor((value / max) * (SEQUENTIAL.length - 1)) + 1, SEQUENTIAL.length - 1);
                return (
                  <td key={g} className="p-0.5">
                    <div
                      className="flex h-6 items-center justify-center rounded"
                      style={{ backgroundColor: step < 0 ? "var(--plane)" : SEQUENTIAL[step] }}
                      title={`${r.family} · Level ${g}: ${value} profile${value === 1 ? "" : "s"}`}
                    >
                      {value > 0 && (
                        <span className={step >= 3 ? "text-white" : "text-ink"} style={{ fontSize: 10 }}>{value}</span>
                      )}
                    </div>
                  </td>
                );
              })}
              <td className="py-0.5 text-right tabular-nums text-ink-secondary">{String(r.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Donut for status share (few categories, fixed slot order). */
export function Donut({ data, size = 140 }: { data: { name: string; count: number }[]; size?: number }) {
  const total = data.reduce((s, d) => s + d.count, 0) || 1;
  let acc = 0;
  const radius = size / 2 - 8;
  const cx = size / 2;
  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} role="img" aria-label="Distribution">
        {data.map((d, i) => {
          const start = (acc / total) * 2 * Math.PI - Math.PI / 2;
          acc += d.count;
          const end = (acc / total) * 2 * Math.PI - Math.PI / 2;
          const large = end - start > Math.PI ? 1 : 0;
          const x1 = cx + radius * Math.cos(start), y1 = cx + radius * Math.sin(start);
          const x2 = cx + radius * Math.cos(end), y2 = cx + radius * Math.sin(end);
          return (
            <path
              key={d.name}
              d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`}
              fill="none"
              stroke={SERIES[i % SERIES.length]}
              strokeWidth={14}
            >
              <title>{`${d.name}: ${d.count}`}</title>
            </path>
          );
        })}
        <text x={cx} y={cx} textAnchor="middle" dominantBaseline="central" className="fill-ink text-xl font-bold">
          {total}
        </text>
      </svg>
      <div className="space-y-1 text-xs">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: SERIES[i % SERIES.length] }} />
            <span className="text-ink-secondary">{d.name}</span>
            <span className="tabular-nums text-ink-muted">{d.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

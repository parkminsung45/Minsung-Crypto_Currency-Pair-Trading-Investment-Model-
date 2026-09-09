"use client";

import { useMemo } from "react";
import { useCssVars } from "@/hooks/useCssVar";
import { SERIES, type HistoryRecord } from "@/lib/types";

const SERIES_VARS = SERIES.map((s) => s.cssVar);

/** 도넛 옆 비중 리스트 범례 (원본 weightsDonutLegend()) */
export function WeightsDonutLegend({ latest }: { latest: HistoryRecord }) {
  const colors = useCssVars(["--text-muted", ...SERIES_VARS]);

  const rows = useMemo(
    () =>
      SERIES.map((s) => ({ ...s, weight: latest.weights[s.key] ?? 0 }))
        .filter((s) => Math.abs(s.weight) > 0.0005)
        .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight)),
    [latest],
  );

  return (
    <div className="grid grid-cols-2 gap-x-8 gap-y-2">
      {rows.map((r) => (
        <div key={r.key} className="flex items-center gap-[7px] whitespace-nowrap text-[13px]">
          <span
            className="h-2.5 w-2.5 flex-none rounded-[3px]"
            style={{ background: r.weight < 0 ? colors["--text-muted"] : colors[r.cssVar] }}
          />
          <span style={{ color: "var(--text-primary)" }}>
            {r.label}
            {r.weight < 0 ? " (숏)" : ""}
          </span>
          <span className="ml-0.5 tabular-nums" style={{ color: "var(--text-secondary)" }}>
            {(r.weight * 100).toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}

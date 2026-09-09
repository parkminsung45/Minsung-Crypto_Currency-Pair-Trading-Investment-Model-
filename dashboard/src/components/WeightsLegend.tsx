"use client";

import { useCssVars } from "@/hooks/useCssVar";
import { SERIES } from "@/lib/types";

const SERIES_VARS = SERIES.map((s) => s.cssVar);

/** 목표 비중 추이 차트 아래 범례 (원본 weightsLegend()) */
export function WeightsLegend() {
  const colors = useCssVars(SERIES_VARS);
  return (
    <div className="mt-2 flex flex-wrap gap-3.5 text-xs" style={{ color: "var(--text-secondary)" }}>
      {SERIES.map((s) => (
        <span key={s.key} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 flex-none rounded-[3px]" style={{ background: colors[s.cssVar] }} />
          <span>{s.label}</span>
        </span>
      ))}
    </div>
  );
}

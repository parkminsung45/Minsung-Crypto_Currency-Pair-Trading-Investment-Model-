"use client";

import { WeightsDonut } from "./WeightsDonut";
import { WeightsDonutLegend } from "./WeightsDonutLegend";
import type { TooltipState } from "@/lib/chart-utils";
import type { HistoryRecord } from "@/lib/types";

/** 도넛 + 옆 범례를 가로로 배치 (원본 donutCard()) */
export function DonutCard({
  latest,
  onHover,
}: {
  latest: HistoryRecord;
  onHover: (state: TooltipState | null) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-8">
      <WeightsDonut latest={latest} onHover={onHover} />
      <WeightsDonutLegend latest={latest} />
    </div>
  );
}

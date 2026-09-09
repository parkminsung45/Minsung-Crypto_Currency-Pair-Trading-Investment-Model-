"use client";

import { useCssVars } from "@/hooks/useCssVar";
import { PAIR_COLORS, type TrainingCurves } from "@/lib/types";

/** 학습 곡선 아래 범례 (원본 trainingCurveLegend()) */
export function TrainingCurveLegend({ curves }: { curves: TrainingCurves }) {
  const colors = useCssVars(PAIR_COLORS);
  const pairNames = Object.keys(curves);

  return (
    <div className="mt-2 flex flex-wrap gap-3.5 text-xs" style={{ color: "var(--text-secondary)" }}>
      {pairNames.map((pair, i) => {
        const episodes = curves[pair];
        const first = episodes[0].reward;
        const last = episodes[episodes.length - 1].reward;
        return (
          <span key={pair} className="inline-flex items-center gap-1.5">
            <span
              className="h-2.5 w-2.5 flex-none rounded-[3px]"
              style={{ background: colors[PAIR_COLORS[i % PAIR_COLORS.length]] }}
            />
            <span>
              {pair} — 에피소드 보상 {first.toFixed(0)} → {last.toFixed(0)}
            </span>
          </span>
        );
      })}
    </div>
  );
}

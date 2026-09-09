"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMemo } from "react";
import { ChartFrame } from "./ChartFrame";
import { M, niceTicks } from "@/lib/chart-utils";
import { useCssVars } from "@/hooks/useCssVar";
import { PAIR_COLORS, type TrainingCurves } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 220;

/** 페어별 학습 곡선(에피소드 보상) 라인차트 (원본 trainingCurveChart()) */
export function TrainingCurveChart({ curves }: { curves: TrainingCurves }) {
  const reduceMotion = useReducedMotion();
  const colors = useCssVars(["--grid", "--text-muted", ...PAIR_COLORS]);

  const geo = useMemo(() => {
    const pairNames = Object.keys(curves);
    const allRewards = pairNames.flatMap((p) => curves[p].map((e) => e.reward));
    const maxEp = Math.max(...pairNames.map((p) => curves[p].length), 0);
    if (allRewards.length === 0 || maxEp < 2) return null;

    const lo = Math.min(0, ...allRewards);
    const hi = Math.max(...allRewards);
    const pad = (hi - lo) * 0.1 || 1;
    const y = (v: number) => M.top + (HEIGHT - M.top - M.bottom) * (1 - (v - (lo - pad)) / (hi - lo + pad * 2));
    const x = (i: number) => M.left + (WIDTH - M.left - M.right) * (i / (maxEp - 1));
    const ticks = niceTicks(lo - pad, hi + pad).map((v) => ({ value: v, y: y(v) }));
    const xLabels = Array.from({ length: Math.min(maxEp, 6) }, (_, k) => {
      const ep = Math.round((k / Math.min(maxEp - 1, 5)) * (maxEp - 1));
      return { x: x(ep), text: "ep " + (ep + 1) };
    });
    return { pairNames, y, x, ticks, xLabels };
  }, [curves]);

  if (!geo) {
    return (
      <div className="py-6 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
        학습 곡선 데이터가 없습니다.
      </div>
    );
  }
  if (!colors["--grid"]) {
    return <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="block w-full h-auto" />;
  }

  const { pairNames, y, x, ticks, xLabels } = geo;

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" className="block w-full h-auto">
      <ChartFrame
        width={WIDTH}
        height={HEIGHT}
        yTicks={ticks}
        yFmt={(v) => v.toFixed(0)}
        xLabels={xLabels}
        colors={{ grid: colors["--grid"], muted: colors["--text-muted"] }}
      />
      {pairNames.map((pair, i) => {
        const color = colors[PAIR_COLORS[i % PAIR_COLORS.length]];
        const episodes = curves[pair];
        const pts = episodes.map((e, idx) => `${x(idx)},${y(e.reward)}`).join(" ");
        const last = episodes[episodes.length - 1];
        return (
          <g key={pair}>
            <motion.polyline
              points={pts}
              fill="none"
              stroke={color}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
              initial={reduceMotion ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.9, delay: reduceMotion ? 0 : i * 0.12, ease: [0.16, 1, 0.3, 1] }}
            />
            <circle cx={x(episodes.length - 1)} cy={y(last.reward)} r={3.5} fill={color} />
          </g>
        );
      })}
    </svg>
  );
}

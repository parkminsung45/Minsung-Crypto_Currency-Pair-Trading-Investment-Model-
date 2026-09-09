"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMemo, useState } from "react";
import { ChartFrame, HatchPatternDefs } from "./ChartFrame";
import { M, pickXLabels, xPositions, type TooltipState } from "@/lib/chart-utils";
import { useCssVars } from "@/hooks/useCssVar";
import { SERIES, type HistoryRecord } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 240;

const SERIES_VARS = SERIES.map((s) => s.cssVar);

/**
 * 목표 비중 추이 — 100% 스택 컬럼 (원본 weightsChart()).
 * weights 절대값 합으로 정규화해 숏(음수) 다리가 있어도 항상 100%로 채우고,
 * 숏 세그먼트는 빗금 패턴으로 구분한다.
 */
export function WeightsChart({
  history,
  onHover,
}: {
  history: HistoryRecord[];
  onHover: (state: TooltipState | null) => void;
}) {
  const reduceMotion = useReducedMotion();
  const colors = useCssVars(["--grid", "--text-muted", "--surface", "--text-primary", "--text-muted", ...SERIES_VARS]);
  const [hoverKey, setHoverKey] = useState<string | null>(null);

  const geo = useMemo(() => {
    const xs = xPositions(history.length, WIDTH);
    const slot = (WIDTH - M.left - M.right) / (history.length || 1);
    const barW = Math.min(24, Math.max(6, slot - 2));
    const plotH = HEIGHT - M.top - M.bottom;
    const y = (frac: number) => M.top + plotH * frac;
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({ value: (1 - f) * 100, y: y(f) }));
    return { xs, slot, barW, plotH, y, ticks };
  }, [history]);

  if (history.length === 0 || !colors["--surface"]) {
    return <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="block w-full h-auto" />;
  }

  const { xs, barW, plotH, y, ticks } = geo;

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" className="block w-full h-auto">
      <HatchPatternDefs surface={colors["--surface"]} ink={colors["--text-primary"]} />
      <ChartFrame
        width={WIDTH}
        height={HEIGHT}
        yTicks={ticks}
        yFmt={(v) => v + "%"}
        xLabels={pickXLabels(history, xs)}
        colors={{ grid: colors["--grid"], muted: colors["--text-muted"] }}
      />
      {history.map((h, i) => {
        const total = SERIES.reduce((sum, s) => sum + Math.abs(h.weights[s.key] ?? 0), 0) || 1;
        let acc = 0;
        const x0 = xs[i] - barW / 2;
        return (
          <g key={h.date + i}>
            {SERIES.map((s) => {
              const raw = h.weights[s.key] ?? 0;
              const frac = Math.abs(raw) / total;
              if (frac <= 0) return null;
              const segTop = y(acc);
              const segH = Math.max(plotH * frac - 2, 1);
              const color = raw < 0 ? "url(#short-hatch)" : colors[s.cssVar];
              const rowKey = `${i}-${s.key}`;
              acc += frac;
              return (
                <motion.rect
                  key={rowKey}
                  x={x0}
                  y={segTop}
                  width={barW}
                  height={segH}
                  rx={2}
                  fill={color}
                  opacity={hoverKey === rowKey ? 0.8 : 1}
                  initial={reduceMotion ? false : { scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{
                    duration: 0.5,
                    delay: reduceMotion ? 0 : Math.min(i * 0.012, 0.4),
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  style={{ transformOrigin: `${xs[i]}px ${HEIGHT - M.bottom}px` }}
                  onPointerMove={(e) => {
                    setHoverKey(rowKey);
                    onHover({
                      x: e.clientX,
                      y: e.clientY,
                      dateText: h.date,
                      rows: SERIES.filter((t) => (h.weights[t.key] ?? 0) !== 0).map((t) => ({
                        color: (h.weights[t.key] ?? 0) < 0 ? colors["--text-muted"] : colors[t.cssVar],
                        value: ((h.weights[t.key] ?? 0) * 100).toFixed(1) + "%",
                        name: t.label + (t.key === s.key ? " ◀" : ""),
                      })),
                    });
                  }}
                  onPointerLeave={() => {
                    setHoverKey(null);
                    onHover(null);
                  }}
                />
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

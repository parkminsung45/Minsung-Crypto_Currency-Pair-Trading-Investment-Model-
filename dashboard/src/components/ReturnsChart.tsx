"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMemo, useState } from "react";
import { ChartFrame } from "./ChartFrame";
import { M, fmtKrw, fmtPct, niceTicks, pickXLabels, xPositions, type TooltipState } from "@/lib/chart-utils";
import { useCssVars } from "@/hooks/useCssVar";
import type { HistoryRecord } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 220;

/** 일간 수익률 다이버징 바 (원본 returnsChart()) — 0 기준선 위/아래 양/음 색상 */
export function ReturnsChart({
  history,
  onHover,
}: {
  history: HistoryRecord[];
  onHover: (state: TooltipState | null) => void;
}) {
  const reduceMotion = useReducedMotion();
  const colors = useCssVars(["--grid", "--text-muted", "--baseline", "--pos", "--neg"]);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const points = useMemo(() => history.filter((h) => h.daily_return_pct != null), [history]);

  const geo = useMemo(() => {
    if (points.length === 0) return null;
    const rets = points.map((h) => h.daily_return_pct as number);
    const maxAbs = Math.max(...rets.map(Math.abs), 0.5);
    const lo = -maxAbs * 1.2;
    const hi = maxAbs * 1.2;
    const y = (v: number) => M.top + (HEIGHT - M.top - M.bottom) * (1 - (v - lo) / (hi - lo));
    const xs = xPositions(points.length, WIDTH);
    const slot = (WIDTH - M.left - M.right) / points.length;
    const barW = Math.min(24, Math.max(4, slot - 2));
    const ticks = niceTicks(lo, hi).map((v) => ({ value: v, y: y(v) }));
    return { y, xs, slot, barW, ticks };
  }, [points]);

  if (points.length === 0) {
    return (
      <div className="text-xs" style={{ color: "var(--text-muted)" }}>
        일간 수익률은 기록이 2일 이상 쌓이면 표시됩니다 (첫날은 전일 기준이 없습니다).
      </div>
    );
  }
  if (!geo || !colors["--pos"]) {
    return <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="block w-full h-auto" />;
  }

  const { y, xs, slot, barW, ticks } = geo;

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" className="block w-full h-auto">
      <ChartFrame
        width={WIDTH}
        height={HEIGHT}
        yTicks={ticks}
        yFmt={(v) => v + "%"}
        xLabels={pickXLabels(points, xs)}
        colors={{ grid: colors["--grid"], muted: colors["--text-muted"] }}
      />
      <line
        x1={M.left}
        x2={WIDTH - M.right}
        y1={y(0)}
        y2={y(0)}
        stroke={colors["--baseline"]}
        strokeWidth={1}
      />
      {points.map((h, i) => {
        const v = h.daily_return_pct as number;
        const positive = v >= 0;
        const color = positive ? colors["--pos"] : colors["--neg"];
        const top = positive ? y(v) : y(0);
        const barH = Math.max(Math.abs(y(v) - y(0)), 1.5);
        const r = Math.min(4, barW / 2, barH);
        const x0 = xs[i] - barW / 2;
        const d = positive
          ? `M ${x0} ${top + barH} L ${x0} ${top + r} Q ${x0} ${top} ${x0 + r} ${top} L ${x0 + barW - r} ${top} Q ${x0 + barW} ${top} ${x0 + barW} ${top + r} L ${x0 + barW} ${top + barH} Z`
          : `M ${x0} ${top} L ${x0 + barW} ${top} L ${x0 + barW} ${top + barH - r} Q ${x0 + barW} ${top + barH} ${x0 + barW - r} ${top + barH} L ${x0 + r} ${top + barH} Q ${x0} ${top + barH} ${x0} ${top + barH - r} Z`;
        const isHover = hoverIdx === i;
        return (
          <g key={h.date + i}>
            <motion.path
              d={d}
              fill={color}
              opacity={isHover ? 0.8 : 1}
              initial={reduceMotion ? false : { scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.5, delay: reduceMotion ? 0 : Math.min(i * 0.012, 0.4), ease: [0.16, 1, 0.3, 1] }}
              style={{ transformOrigin: `${xs[i]}px ${y(0)}px` }}
            />
            <rect
              x={xs[i] - slot / 2}
              y={M.top}
              width={slot}
              height={HEIGHT - M.top - M.bottom}
              fill="transparent"
              onPointerMove={(e) => {
                setHoverIdx(i);
                onHover({
                  x: e.clientX,
                  y: e.clientY,
                  dateText: h.date,
                  rows: [
                    { color, value: fmtPct(v), name: "일간 수익률" },
                    { color: "transparent", value: fmtKrw(h.portfolio_value), name: "포트폴리오 가치" },
                  ],
                });
              }}
              onPointerLeave={() => {
                setHoverIdx(null);
                onHover(null);
              }}
            />
          </g>
        );
      })}
    </svg>
  );
}

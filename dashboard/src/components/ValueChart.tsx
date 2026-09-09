"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMemo, useRef, useState } from "react";
import { ChartFrame } from "./ChartFrame";
import { M, fmtKrw, fmtPct, niceTicks, pickXLabels, xPositions, type TooltipState } from "@/lib/chart-utils";
import { useCssVars } from "@/hooks/useCssVar";
import type { HistoryRecord } from "@/lib/types";

const WIDTH = 1040;
const HEIGHT = 260;

/** 포트폴리오 가치 추이 — 단일 시리즈 라인 + 영역 채우기 (원본 valueChart()) */
export function ValueChart({
  history,
  onHover,
}: {
  history: HistoryRecord[];
  onHover: (state: TooltipState | null) => void;
}) {
  const reduceMotion = useReducedMotion();
  const colors = useCssVars(["--grid", "--text-muted", "--pos", "--surface", "--baseline", "--text-primary"]);
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const geo = useMemo(() => {
    const values = history.map((h) => h.portfolio_value);
    const vMin = Math.min(...values);
    const vMax = Math.max(...values);
    const pad = (vMax - vMin) * 0.15 || vMax * 0.02 || 1;
    const lo = vMin - pad;
    const hi = vMax + pad;
    const y = (v: number) => M.top + (HEIGHT - M.top - M.bottom) * (1 - (v - lo) / (hi - lo));
    const xs = xPositions(history.length, WIDTH);
    const ticks = niceTicks(lo, hi).map((v) => ({ value: v, y: y(v) }));
    return { y, xs, ticks };
  }, [history]);

  if (history.length === 0 || !colors["--pos"]) {
    return <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="block w-full h-auto" />;
  }

  const { y, xs, ticks } = geo;
  const last = history[history.length - 1];
  const endX = xs[xs.length - 1];
  const endY = y(last.portfolio_value);
  const pts = history.map((h, i) => `${xs[i]},${y(h.portfolio_value)}`).join(" ");
  const area = `${M.left},${HEIGHT - M.bottom} ${pts} ${xs[xs.length - 1]},${HEIGHT - M.bottom}`;

  const handleMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let best = 0;
    for (let i = 1; i < xs.length; i++) if (Math.abs(xs[i] - px) < Math.abs(xs[best] - px)) best = i;
    setHoverIdx(best);
    const h = history[best];
    const rows = [{ color: colors["--pos"], value: fmtKrw(h.portfolio_value), name: "포트폴리오 가치" }];
    if (h.daily_return_pct != null) {
      rows.push({ color: "transparent", value: fmtPct(h.daily_return_pct), name: "일간 수익률" });
    }
    onHover({ x: e.clientX, y: e.clientY, dateText: h.date, rows });
  };
  const handleLeave = () => {
    setHoverIdx(null);
    onHover(null);
  };

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      className="block w-full h-auto"
      onPointerMove={handleMove}
      onPointerLeave={handleLeave}
    >
      <ChartFrame
        width={WIDTH}
        height={HEIGHT}
        yTicks={ticks}
        yFmt={(v) => "₩" + v.toLocaleString("ko-KR")}
        xLabels={pickXLabels(history, xs)}
        colors={{ grid: colors["--grid"], muted: colors["--text-muted"] }}
      />
      {history.length > 1 && (
        <>
          <motion.polygon
            points={area}
            fill={colors["--pos"]}
            opacity={0.1}
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 0.1 }}
            transition={{ duration: 0.6 }}
          />
          <motion.polyline
            points={pts}
            fill="none"
            stroke={colors["--pos"]}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            initial={reduceMotion ? false : { pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          />
        </>
      )}
      <circle cx={endX} cy={endY} r={6} fill={colors["--surface"]} />
      <circle cx={endX} cy={endY} r={4} fill={colors["--pos"]} />
      <text
        x={endX - 10}
        y={endY - 12 < M.top + 10 ? endY + 20 : endY - 12}
        textAnchor="end"
        fontSize={12}
        fontWeight={650}
        fill={colors["--text-primary"]}
      >
        {fmtKrw(last.portfolio_value)}
      </text>

      {hoverIdx != null && (
        <>
          <line
            x1={xs[hoverIdx]}
            x2={xs[hoverIdx]}
            y1={M.top}
            y2={HEIGHT - M.bottom}
            stroke={colors["--baseline"]}
            strokeWidth={1}
          />
          <circle cx={xs[hoverIdx]} cy={y(history[hoverIdx].portfolio_value)} r={6} fill={colors["--surface"]} />
          <circle cx={xs[hoverIdx]} cy={y(history[hoverIdx].portfolio_value)} r={4} fill={colors["--pos"]} />
        </>
      )}
    </svg>
  );
}

"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMemo, useState } from "react";
import { HatchPatternDefs } from "./ChartFrame";
import { fmtKrw, type TooltipState } from "@/lib/chart-utils";
import { useCssVars } from "@/hooks/useCssVar";
import { SERIES, type HistoryRecord } from "@/lib/types";

const SERIES_VARS = SERIES.map((s) => s.cssVar);
const DONUT_SIZE = 168;
const DONUT_R = 58;
const DONUT_STROKE = 22;

/** 오늘의 포트폴리오 구성 도넛 (원본 weightsDonut()) */
export function WeightsDonut({
  latest,
  onHover,
}: {
  latest: HistoryRecord;
  onHover: (state: TooltipState | null) => void;
}) {
  const reduceMotion = useReducedMotion();
  const colors = useCssVars(["--surface", "--text-primary", "--text-muted", ...SERIES_VARS]);
  const [hoverKey, setHoverKey] = useState<string | null>(null);

  const size = DONUT_SIZE;
  const cx = size / 2;
  const cy = size / 2;
  const r = DONUT_R;
  const stroke = DONUT_STROKE;
  const circumference = 2 * Math.PI * r;
  const gapDeg = 3;

  const slices = useMemo(() => {
    const total = SERIES.reduce((sum, s) => sum + Math.abs(latest.weights[s.key] ?? 0), 0) || 1;
    const withWeights = SERIES.map((s) => ({
      ...s,
      raw: latest.weights[s.key] ?? 0,
      weight: Math.abs(latest.weights[s.key] ?? 0) / total,
    })).filter((s) => s.weight > 0.0005);

    return withWeights.reduce<Array<(typeof withWeights)[number] & { angleStart: number }>>((acc, s) => {
      const angleStart = acc.length > 0 ? acc[acc.length - 1].angleStart + acc[acc.length - 1].weight * 360 : 0;
      acc.push({ ...s, angleStart });
      return acc;
    }, []);
  }, [latest]);

  if (!colors["--surface"]) {
    return <svg viewBox={`0 0 ${size} ${size}`} style={{ width: size, height: size, flex: "none" }} />;
  }

  return (
    <svg viewBox={`0 0 ${size} ${size}`} role="img" style={{ width: size, height: size, flex: "none" }}>
      <HatchPatternDefs surface={colors["--surface"]} ink={colors["--text-primary"]} />
      <g transform={`rotate(-90 ${cx} ${cy})`}>
        {slices.map((s) => {
          const sweepDeg = s.weight * 360;
          const drawDeg = Math.max(sweepDeg - gapDeg, sweepDeg * 0.35);
          const dash = (drawDeg / 360) * circumference;
          const offset = -((s.angleStart / 360) * circumference);
          const color = s.raw < 0 ? "url(#short-hatch)" : colors[s.cssVar];
          const isHover = hoverKey === s.key;
          return (
            <motion.circle
              key={s.key}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={isHover ? stroke + 3 : stroke}
              strokeDashoffset={offset}
              initial={reduceMotion ? false : { strokeDasharray: `0 ${circumference}` }}
              animate={{ strokeDasharray: `${dash} ${circumference - dash}` }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              onPointerMove={(e) => {
                setHoverKey(s.key);
                onHover({
                  x: e.clientX,
                  y: e.clientY,
                  dateText: latest.date,
                  rows: [
                    {
                      color: s.raw < 0 ? colors["--text-muted"] : color,
                      value: (s.raw * 100).toFixed(1) + "%",
                      name: s.label + (s.raw < 0 ? " (숏)" : ""),
                    },
                  ],
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
      <text x={cx} y={cy + 5} textAnchor="middle" fontSize={14} fontWeight={650} fill={colors["--text-primary"]}>
        {fmtKrw(latest.portfolio_value)}
      </text>
    </svg>
  );
}

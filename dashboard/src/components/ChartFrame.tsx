"use client";

import { M, type Tick, type XLabel } from "@/lib/chart-utils";

interface ChartFrameProps {
  width: number;
  height: number;
  yTicks: Tick[];
  yFmt: (v: number) => string;
  xLabels: XLabel[];
  colors: { grid: string; muted: string };
}

/** 그리드 라인 + 축 라벨 (원본 chartFrame()) — 각 차트가 이 위에 데이터 마크를 그린다 */
export function ChartFrame({ width, height, yTicks, yFmt, xLabels, colors }: ChartFrameProps) {
  return (
    <>
      {yTicks.map((t, i) => (
        <line
          key={`grid-${i}`}
          x1={M.left}
          x2={width - M.right}
          y1={t.y}
          y2={t.y}
          stroke={colors.grid}
          strokeWidth={1}
        />
      ))}
      {yTicks.map((t, i) => (
        <text
          key={`ylabel-${i}`}
          x={M.left - 8}
          y={t.y + 4}
          textAnchor="end"
          fontSize={11}
          fill={colors.muted}
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {yFmt(t.value)}
        </text>
      ))}
      {xLabels.map((l, i) => (
        <text key={`xlabel-${i}`} x={l.x} y={height - 6} textAnchor="middle" fontSize={11} fill={colors.muted}>
          {l.text}
        </text>
      ))}
    </>
  );
}

/** 숏 포지션 표시용 빗금 패턴 defs (원본 ensureHatchPattern()) */
export function HatchPatternDefs({ surface, ink }: { surface: string; ink: string }) {
  return (
    <defs>
      <pattern id="short-hatch" width={6} height={6} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width={6} height={6} fill={surface} />
        <line x1={0} y1={0} x2={0} y2={6} stroke={ink} strokeWidth={2} opacity={0.35} />
      </pattern>
    </defs>
  );
}

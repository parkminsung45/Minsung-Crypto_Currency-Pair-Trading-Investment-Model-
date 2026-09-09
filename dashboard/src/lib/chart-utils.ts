// 원본 vanilla 대시보드(index.html)의 SVG 차트 헬퍼를 TS로 포팅.
// 차트 라이브러리 없이 순수 SVG 좌표 계산만 담당 — 렌더링은 각 컴포넌트에서.

import type { HistoryRecord } from "./types";

export const M = { top: 16, right: 56, bottom: 26, left: 64 };

export interface Tick {
  value: number;
  y: number;
}

export interface XLabel {
  x: number;
  text: string;
}

/** "예쁜" 눈금 값 배열 계산 (원본 niceTicks 그대로 포팅) */
export function niceTicks(min: number, max: number, count = 4): number[] {
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const span = max - min;
  const step = Math.pow(10, Math.floor(Math.log10(span / count)));
  const err = span / count / step;
  const mult = err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
  const s = step * mult;
  const ticks: number[] = [];
  for (let v = Math.ceil(min / s) * s; v <= max + s * 1e-9; v += s) {
    ticks.push(+v.toFixed(10));
  }
  return ticks;
}

/** N개 데이터 포인트를 플롯 폭에 균등 배치한 x좌표 배열 */
export function xPositions(n: number, width: number): number[] {
  const inner = width - M.left - M.right;
  if (n === 1) return [M.left + inner / 2];
  return Array.from({ length: n }, (_, i) => M.left + (inner * i) / (n - 1));
}

/** x축 라벨을 데이터 개수에 따라 축약 선택 (원본 pickXLabels) */
export function pickXLabels(history: HistoryRecord[], xs: number[]): XLabel[] {
  const n = history.length;
  if (n === 0) return [];
  const idxs =
    n <= 6
      ? history.map((_, i) => i)
      : [0, Math.round((n - 1) * 0.25), Math.round((n - 1) * 0.5), Math.round((n - 1) * 0.75), n - 1];
  return [...new Set(idxs)].map((i) => ({ x: xs[i], text: history[i].date.slice(5, 10) }));
}

export const fmtKrw = (v: number) => "₩" + Math.round(v).toLocaleString("ko-KR");
export const fmtPct = (v: number, digits = 2) => (v > 0 ? "+" : "") + v.toFixed(digits) + "%";

export interface TooltipRow {
  color: string;
  value: string;
  name: string;
}

export interface TooltipState {
  x: number;
  y: number;
  dateText: string;
  rows: TooltipRow[];
}

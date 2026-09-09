"use client";

import { KpiTile } from "./KpiTile";
import { fmtKrw, fmtPct } from "@/lib/chart-utils";
import type { HistoryRecord } from "@/lib/types";

/** KPI 티커 테이프 — 하나의 컨테이너를 세로 구분선으로 나눈 가로 연결형 (원본 kpiRow() 재구성) */
export function KpiRow({ history }: { history: HistoryRecord[] }) {
  const latest = history[history.length - 1];
  const first = history[0];
  const cum = (latest.portfolio_value / first.portfolio_value - 1) * 100;

  return (
    <div
      className="ticker-tape flex flex-wrap overflow-hidden rounded-xl border px-5 transition-shadow duration-200"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <KpiTile
        label="포트폴리오 가치"
        value={fmtKrw(latest.portfolio_value)}
        deltaText={latest.daily_return_pct != null ? fmtPct(latest.daily_return_pct) + " 전 기록 대비" : "첫 기록"}
        deltaDir={latest.daily_return_pct == null ? null : latest.daily_return_pct >= 0 ? "up" : "down"}
        delay={0}
      />
      <KpiTile
        label="누적 수익률"
        value={fmtPct(cum)}
        deltaText={first.date + " 이후"}
        deltaDir={cum === 0 ? null : cum > 0 ? "up" : "down"}
        delay={0.05}
      />
      <KpiTile label="기록된 실행" value={String(history.length) + "회"} deltaText="선택한 기간 기준" delay={0.1} />
      <KpiTile
        label="현금 비중"
        value={((latest.weights.CASH ?? 0) * 100).toFixed(1) + "%"}
        deltaText={latest.date + " 목표 비중"}
        delay={0.15}
      />
    </div>
  );
}

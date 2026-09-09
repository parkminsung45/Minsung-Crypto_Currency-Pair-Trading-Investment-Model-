"use client";

import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { Card } from "./Card";
import { CollapsibleCard } from "./CollapsibleCard";
import { ChartTooltip } from "./ChartTooltip";
import { DashboardHeader } from "./DashboardHeader";
import { DashboardFooter } from "./DashboardFooter";
import { DonutCard } from "./DonutCard";
import { EmptyState } from "./EmptyState";
import { HistoryTable } from "./HistoryTable";
import { KpiRow } from "./KpiRow";
import { ModelInfoCard } from "./ModelInfoCard";
import { RangeFilter } from "./RangeFilter";
import { ReturnsChart } from "./ReturnsChart";
import { ValueChart } from "./ValueChart";
import { WeightsChart } from "./WeightsChart";
import { WeightsLegend } from "./WeightsLegend";
import { useHistoryData } from "@/hooks/useHistoryData";
import type { TooltipState } from "@/lib/chart-utils";
import { RANGES, type RangeDef } from "@/lib/types";

export function Dashboard() {
  const { fullHistory, loadError, trainingCurves } = useHistoryData();
  const [activeRange, setActiveRange] = useState<RangeDef["key"]>("all");
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const [modelInfoExpanded, setModelInfoExpanded] = useState(true);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const sliced = useMemo(() => {
    if (!fullHistory) return null;
    const range = RANGES.find((r) => r.key === activeRange);
    if (!range || !isFinite(range.days)) return fullHistory;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - range.days);
    const iso = cutoff.toISOString().slice(0, 10);
    return fullHistory.filter((h) => h.date >= iso);
  }, [fullHistory, activeRange]);

  // ---- 헤더 상태 계산 ----
  let statusText = "불러오는 중…";
  let statusVariant: "loading" | "dry" | "live" | "empty" | "error" = "loading";
  let lastUpdatedText = "";

  if (loadError) {
    statusText = "로드 실패";
    statusVariant = "error";
  } else if (fullHistory !== null) {
    if (fullHistory.length === 0) {
      statusText = "기록 없음";
      statusVariant = "empty";
    } else {
      const latest = fullHistory[fullHistory.length - 1];
      statusText = latest.dry_run ? "드라이런 모드" : "실거래 모드";
      statusVariant = latest.dry_run ? "dry" : "live";
      lastUpdatedText = "마지막 기록: " + latest.date;
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1080px] px-4 pb-12 pt-6 sm:px-4">
      <DashboardHeader statusText={statusText} statusVariant={statusVariant} lastUpdatedText={lastUpdatedText} />

      {loadError && (
        <EmptyState>데이터를 불러오지 못했습니다: {loadError} — 60초 후 자동 재시도합니다.</EmptyState>
      )}

      {!loadError && fullHistory === null && (
        <div className="py-16 text-center text-sm" style={{ color: "var(--text-muted)" }}>
          불러오는 중…
        </div>
      )}

      {!loadError && fullHistory !== null && fullHistory.length === 0 && (
        <EmptyState>
          <div>아직 기록된 실행이 없습니다.</div>
          <div className="mt-1">
            백테스트 또는 페이퍼 트레이딩 실행 후{" "}
            <code
              className="rounded-md border px-1.5 py-px text-[12.5px]"
              style={{ background: "var(--page)", borderColor: "var(--border)" }}
            >
              dashboard/data/history.json
            </code>{" "}
            을 갱신해 push하면 자동으로 채워집니다.
          </div>
        </EmptyState>
      )}

      {!loadError && fullHistory !== null && fullHistory.length > 0 && sliced && (
        <>
          <RangeFilter active={activeRange} onChange={setActiveRange} />

          {sliced.length === 0 ? (
            <EmptyState>선택한 기간에 기록이 없습니다.</EmptyState>
          ) : (
            <motion.div layout className="flex flex-col gap-4">
              <KpiRow history={sliced} />

              <Card
                title="오늘의 포트폴리오 구성"
                desc={`${sliced[sliced.length - 1].date} 기준 종목별 목표 비중`}
                delay={0.05}
              >
                <DonutCard latest={sliced[sliced.length - 1]} onHover={setTooltip} />
              </Card>

              <Card title="포트폴리오 가치 추이" desc="매 실행 시점의 계좌 평가액 (KRW)" delay={0.1}>
                <ValueChart history={sliced} onHover={setTooltip} />
              </Card>

              <Card title="일간 수익률" desc="직전 기록 대비 변화율 — 위 파랑, 아래 빨강" delay={0.15}>
                <ReturnsChart history={sliced} onHover={setTooltip} />
              </Card>

              <Card
                title="목표 비중 추이"
                desc="모델이 산출한 종목별 목표 비중 (100% 스택)"
                delay={0.2}
                extra={<WeightsLegend />}
              >
                <WeightsChart history={sliced} onHover={setTooltip} />
              </Card>

              <CollapsibleCard
                title="RL 모델"
                desc="어떤 알고리즘으로, 무엇을 보고 학습하는지"
                expanded={modelInfoExpanded}
                onToggle={() => setModelInfoExpanded((v) => !v)}
                delay={0.25}
              >
                <ModelInfoCard curves={trainingCurves} />
              </CollapsibleCard>

              <CollapsibleCard
                title="전체 기록"
                desc="모든 값의 표 형태 원본 (최신순) — 행을 클릭하면 판단 근거를 볼 수 있습니다"
                count={sliced.length}
                expanded={historyExpanded}
                onToggle={() => setHistoryExpanded((v) => !v)}
                delay={0.3}
              >
                <HistoryTable history={sliced} />
              </CollapsibleCard>
            </motion.div>
          )}
        </>
      )}

      <DashboardFooter />
      <ChartTooltip state={tooltip} />
    </div>
  );
}

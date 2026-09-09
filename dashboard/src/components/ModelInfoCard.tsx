"use client";

import { TrainingCurveChart } from "./TrainingCurveChart";
import { TrainingCurveLegend } from "./TrainingCurveLegend";
import type { TrainingCurves } from "@/lib/types";

const INFO_ITEMS: { title: string; body: string }[] = [
  {
    title: "관측(State)",
    body: "스프레드 z-score, 스프레드 변화량, 현재 포지션(유지/롱/숏), 미실현손익 근사값, 보유 스텝 수 — 5차원 벡터",
  },
  {
    title: "행동(Action)",
    body: "4가지 이산 행동 중 하나: 유지(HOLD), 롱 진입(ENTER_LONG), 숏 진입(ENTER_SHORT), 청산(EXIT)",
  },
  {
    title: "보상(Reward)",
    body:
      "스텝별 미실현손익 변화분(delta) — 진입·청산 시 수수료(0.05%)를 차감. 포지션 진입 후 " +
      "최소 120분은 청산 신호를 무시하고, 최대 240분이 지나면 강제 청산 — 진단 결과 평균회귀 " +
      "신호가 60분 이내엔 거의 없고 120~480분에 강해지는 것을 반영",
  },
  {
    title: "학습 데이터",
    body:
      "업비트 1분봉 최근 180일, 스프레드는 240분 롤링 윈도우로 헤지비율(OLS)과 z-score 계산 — " +
      "한 에피소드가 데이터 전체(약 25만 스텝)를 관통",
  },
];

const CAVEAT_TEXT =
  "참고: 처음 30일 데이터로 학습했을 때는 모델이 z-score와 반대 방향(평균회귀가 아닌 " +
  "역방향)으로 수렴하는 문제가 실제로 있었습니다. 진단해보니 진입 임계치(|z|>2) 근처, " +
  "60분 이내에는 평균회귀 신호가 거의 없고(상관관계 ≈ 0) 120~480분 구간에서만 뚜렷하게 " +
  '나타났습니다(상관관계 최대 -0.40) — 즉 데이터 부족이 아니라 진입/보유 시점이 신호와 ' +
  "어긋난 것이었습니다. 180일 데이터 + 최소/최대 보유시간 제약으로 재학습한 결과 방향성은 " +
  '바로잡혔습니다. 아래 "전체 기록" 표의 각 행을 펼치면 그 시점 판단 근거(z-score, 액션별 ' +
  "확률, 교과서적 방향과의 일치 여부)를 그대로 확인할 수 있습니다.";

/** RL 모델 설명 카드 본문 (원본 modelInfoBody()) */
export function ModelInfoCard({ curves }: { curves: TrainingCurves | null }) {
  const maxEpisodes = curves ? Math.max(0, ...Object.values(curves).map((e) => e.length)) : 0;
  const showCurve = !!curves && Object.keys(curves).length > 0 && maxEpisodes >= 2;

  return (
    <div className="mt-1 flex flex-col gap-4">
      <div>
        <p className="text-[12.5px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          각 페어(예: BTC/ETH)마다 독립된 PPO(Proximal Policy Optimization) 정책을 학습해 1시간마다
          페이퍼 트레이딩을 실행합니다. 알고리즘: Stable-Baselines3 PPO, MLP 정책망.
        </p>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-2.5">
        {INFO_ITEMS.map((item) => (
          <div
            key={item.title}
            className="rounded-lg border px-3 py-2.5"
            style={{ background: "var(--page)", borderColor: "var(--border)" }}
          >
            <div className="mb-1 text-[11.5px] font-semibold" style={{ color: "var(--text-secondary)" }}>
              {item.title}
            </div>
            <div className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {item.body}
            </div>
          </div>
        ))}
      </div>

      <div
        className="rounded-lg border px-3 py-2.5 text-xs leading-relaxed"
        style={{ background: "var(--page)", borderColor: "var(--border)", color: "var(--text-secondary)" }}
      >
        {CAVEAT_TEXT}
      </div>

      {showCurve && curves && (
        <div>
          <h3 className="mb-1 text-[13px] font-semibold">학습 곡선 (에피소드별 누적 보상)</h3>
          <div className="mb-2.5 text-xs" style={{ color: "var(--text-muted)" }}>
            우상향할수록 학습 중 정책이 개선되고 있다는 뜻 — 절대값 자체의 손익 의미보다는 추세를 본다.
          </div>
          <TrainingCurveChart curves={curves} />
          <TrainingCurveLegend curves={curves} />
        </div>
      )}
    </div>
  );
}

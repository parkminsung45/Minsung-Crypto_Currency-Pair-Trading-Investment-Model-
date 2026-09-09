// 데이터 shape — dashboard/data/history.json, training_curves.json
// 원본(vanilla) 대시보드 index.html의 런타임 동작을 그대로 따르되 타입을 붙인다.
// 과거 레코드는 필드가 느슨하므로(예: weights에 XRP/SOL이 없거나, actions 키가
// "KRW-BTC" 같은 원시 심볼이거나 값이 "BUY"/"SELL"일 수 있음) 대부분을 옵셔널/문자열로 둔다.

export type ActionKey = "HOLD" | "ENTER_LONG" | "ENTER_SHORT" | "EXIT";

export interface Weights {
  BTC?: number;
  ETH?: number;
  XRP?: number;
  SOL?: number;
  CASH?: number;
  [key: string]: number | undefined;
}

export interface ActionProbs {
  HOLD?: number;
  ENTER_LONG?: number;
  ENTER_SHORT?: number;
  EXIT?: number;
  [key: string]: number | undefined;
}

export interface PairReasoning {
  explanation: string;
  spread_zscore: number;
  spread_change: number;
  chosen_action: string;
  action_probs: ActionProbs;
  unrealized_pnl_obs?: number;
}

export interface HistoryRecord {
  date: string; // "YYYY-MM-DD" 또는 전체 ISO 타임스탬프 — 표시시 slice로 다룸
  portfolio_value: number;
  daily_return_pct: number | null;
  weights: Weights;
  actions?: Record<string, string>; // 값이 "HOLD"/"ENTER_LONG"/... 또는 과거 레코드는 "BUY"/"SELL"
  reasoning?: Record<string, PairReasoning>;
  dry_run: boolean;
}

export interface TrainingEpisode {
  episode: number;
  reward: number;
  length: number;
}

export type TrainingCurves = Record<string, TrainingEpisode[]>;

export interface SeriesDef {
  key: "BTC" | "ETH" | "XRP" | "SOL" | "CASH";
  label: string;
  cssVar: string;
}

export const SERIES: SeriesDef[] = [
  { key: "BTC", label: "BTC", cssVar: "--s-btc" },
  { key: "ETH", label: "ETH", cssVar: "--s-eth" },
  { key: "XRP", label: "XRP", cssVar: "--s-xrp" },
  { key: "SOL", label: "SOL", cssVar: "--s-sol" },
  { key: "CASH", label: "현금(KRW)", cssVar: "--s-cash" },
];

export interface RangeDef {
  key: "all" | "7d" | "30d" | "90d";
  label: string;
  days: number;
}

export const RANGES: RangeDef[] = [
  { key: "all", label: "전체", days: Infinity },
  { key: "7d", label: "최근 7일", days: 7 },
  { key: "30d", label: "최근 30일", days: 30 },
  { key: "90d", label: "최근 90일", days: 90 },
];

export const ACTION_LABELS_KO: Record<string, string> = {
  HOLD: "유지",
  ENTER_LONG: "롱 진입",
  ENTER_SHORT: "숏 진입",
  EXIT: "청산",
};

export const PAIR_COLORS = ["--s-btc", "--s-xrp", "--s-eth", "--s-sol"];

"use client";

import { useEffect, useRef, useState } from "react";
import type { HistoryRecord, TrainingCurves } from "@/lib/types";

const DATA_URL =
  "https://raw.githubusercontent.com/parkminsung45/Minsung-Crypto_Currency-Pair-Trading-Investment-Model-/main/dashboard/data/history.json";
const TRAINING_CURVES_URL =
  "https://raw.githubusercontent.com/parkminsung45/Minsung-Crypto_Currency-Pair-Trading-Investment-Model-/main/dashboard/data/training_curves.json";
const REFRESH_MS = 60_000;

async function fetchHistory(): Promise<HistoryRecord[]> {
  const res = await fetch(DATA_URL + "?t=" + Date.now(), { cache: "no-store" });
  if (res.status === 404) return [];
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

async function fetchTrainingCurves(): Promise<TrainingCurves> {
  try {
    const res = await fetch(TRAINING_CURVES_URL);
    if (!res.ok) return {};
    const data = await res.json();
    return data && typeof data === "object" ? data : {};
  } catch {
    return {}; // 학습 곡선은 부가 정보 — 실패해도 나머지 대시보드는 정상 표시
  }
}

export interface HistoryDataState {
  fullHistory: HistoryRecord[] | null; // null = 아직 로드 전, [] = 데이터 없음
  loadError: string | null;
  trainingCurves: TrainingCurves | null; // 최초 1회만 로드
  isRefreshing: boolean;
}

/** history.json 60초 폴링 + training_curves.json 최초 1회 로드 (원본 refresh()/즉시실행 IIFE 대응) */
export function useHistoryData(): HistoryDataState {
  const [fullHistory, setFullHistory] = useState<HistoryRecord[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [trainingCurves, setTrainingCurves] = useState<TrainingCurves | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const fullHistoryRef = useRef<HistoryRecord[] | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchTrainingCurves().then((curves) => {
      if (!cancelled) setTrainingCurves(curves);
    });

    async function refresh() {
      setIsRefreshing(true);
      try {
        const data = await fetchHistory();
        if (cancelled) return;
        fullHistoryRef.current = data;
        setFullHistory(data);
        setLoadError(null);
      } catch (err) {
        if (cancelled) return;
        // 이미 데이터가 있으면 이전 렌더를 유지한다 (스켈레톤/깜빡임 없음)
        if (fullHistoryRef.current === null) {
          setLoadError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setIsRefreshing(false);
      }
    }

    refresh();
    const interval = setInterval(refresh, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return { fullHistory, loadError, trainingCurves, isRefreshing };
}

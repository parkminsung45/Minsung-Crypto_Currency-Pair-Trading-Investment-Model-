"use client";

import { motion } from "motion/react";
import { ThemeToggle } from "./ThemeToggle";

interface DashboardHeaderProps {
  statusText: string;
  statusVariant: "loading" | "dry" | "live" | "empty" | "error";
  lastUpdatedText: string;
}

/** 헤더 — 제목, 상태뱃지(펄스 도트 포함), 마지막 업데이트, GitHub 링크, 테마 토글 */
export function DashboardHeader({ statusText, statusVariant, lastUpdatedText }: DashboardHeaderProps) {
  // live/dry 모두 "동작 중" 상태이므로 민트 펄스 뱃지, 나머지(로딩/빈/에러)는 중립색 고정 뱃지
  const isActive = statusVariant === "live" || statusVariant === "dry";
  const dotColor = statusVariant === "live" ? "var(--down)" : "var(--up)";

  return (
    <header className="mb-5 flex items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold">Reinforced Learning based Crypto Currency Trading</h1>
        <div
          className="mt-1 flex flex-wrap items-center gap-2.5 text-[13px]"
          style={{ color: "var(--text-secondary)" }}
        >
          <motion.span
            key={statusText}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.25 }}
            className="mono inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs"
            style={
              isActive
                ? {
                    borderColor: `color-mix(in srgb, ${dotColor} 30%, transparent)`,
                    background: `color-mix(in srgb, ${dotColor} 8%, transparent)`,
                    color: dotColor,
                    fontWeight: 600,
                  }
                : {
                    borderColor: "var(--border)",
                    color: "var(--text-secondary)",
                    fontWeight: 400,
                  }
            }
          >
            {isActive && (
              <span className="pulse-dot" style={{ background: dotColor, boxShadow: `0 0 8px ${dotColor}` }} />
            )}
            {statusText}
          </motion.span>
          {lastUpdatedText && <span>{lastUpdatedText}</span>}
          <a
            href="https://github.com/parkminsung45/Minsung-Crypto_Currency-Pair-Trading-Investment-Model-"
            target="_blank"
            rel="noopener noreferrer"
            className="underline-offset-2 hover:underline"
            style={{ color: "var(--text-secondary)" }}
          >
            GitHub 저장소
          </a>
        </div>
      </div>
      <ThemeToggle />
    </header>
  );
}

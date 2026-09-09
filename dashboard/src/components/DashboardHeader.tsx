"use client";

import { motion } from "motion/react";

interface DashboardHeaderProps {
  statusText: string;
  statusVariant: "loading" | "dry" | "live" | "empty" | "error";
  lastUpdatedText: string;
}

/** 헤더 — 제목, 상태뱃지, 마지막 업데이트, GitHub 링크 */
export function DashboardHeader({ statusText, statusVariant, lastUpdatedText }: DashboardHeaderProps) {
  const badgeColor = statusVariant === "live" ? "var(--down)" : "var(--text-secondary)";

  return (
    <header className="mb-5">
      <h1 className="text-xl font-semibold">Reinforced Learning based Crypto Currency Trading</h1>
      <div className="mt-1 flex flex-wrap items-center gap-2.5 text-[13px]" style={{ color: "var(--text-secondary)" }}>
        <motion.span
          key={statusText}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.25 }}
          className="inline-block rounded-full border px-2 py-0.5 text-xs"
          style={{
            borderColor: "var(--border)",
            color: badgeColor,
            fontWeight: statusVariant === "live" ? 600 : 400,
          }}
        >
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
    </header>
  );
}

"use client";

import { motion, useReducedMotion } from "motion/react";

interface KpiTileProps {
  label: string;
  value: string;
  deltaText?: string | null;
  deltaDir?: "up" | "down" | null;
  delay?: number;
}

/** 티커 테이프 세그먼트 하나 (원본 kpiRow()의 tile() → 티커 아이템으로 재구성) */
export function KpiTile({ label, value, deltaText, deltaDir, delay = 0 }: KpiTileProps) {
  const reduceMotion = useReducedMotion();
  const valueColor = deltaDir === "up" ? "var(--up)" : deltaDir === "down" ? "var(--down)" : "var(--text-primary)";
  const deltaColor = deltaDir === "up" ? "var(--up)" : deltaDir === "down" ? "var(--down)" : "var(--text-muted)";

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.16, 1, 0.3, 1] }}
      className="min-w-[150px] flex-1 border-r px-5 py-4 first:pl-0 last:border-r-0 last:pr-0"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="text-[11px]" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <motion.div
        key={value}
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="mono mt-1.5 text-2xl font-semibold"
        style={{ color: valueColor }}
      >
        {value}
      </motion.div>
      {deltaText != null && (
        <div className="mono mt-0.5 text-xs" style={{ color: deltaColor }}>
          {deltaText}
        </div>
      )}
    </motion.div>
  );
}

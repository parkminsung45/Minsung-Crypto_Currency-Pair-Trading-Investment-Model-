"use client";

import { motion, useReducedMotion } from "motion/react";

interface KpiTileProps {
  label: string;
  value: string;
  deltaText?: string | null;
  deltaDir?: "up" | "down" | null;
  delay?: number;
}

/** KPI 타일 하나 (원본 kpiRow()의 tile()) */
export function KpiTile({ label, value, deltaText, deltaDir, delay = 0 }: KpiTileProps) {
  const reduceMotion = useReducedMotion();
  const deltaColor = deltaDir === "up" ? "var(--up)" : deltaDir === "down" ? "var(--down)" : "var(--text-muted)";

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={reduceMotion ? undefined : { y: -3 }}
      className="rounded-xl border px-4 py-3.5"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
        {label}
      </div>
      <motion.div
        key={value}
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="mt-1 text-[26px] font-semibold tabular-nums"
      >
        {value}
      </motion.div>
      {deltaText != null && (
        <div className="mt-0.5 text-xs" style={{ color: deltaColor }}>
          {deltaText}
        </div>
      )}
    </motion.div>
  );
}

"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

interface CardProps {
  title: string;
  desc?: string;
  extra?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
}

/** 정적 카드 — 값 차트/도넛/일간 수익률 등 접이식이 아닌 카드용 (원본 card()) */
export function Card({ title, desc, extra, children, className = "", delay = 0 }: CardProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={reduceMotion ? undefined : { y: -3, boxShadow: "var(--shadow-card-hover)" }}
      className={`card-surface rounded-xl border p-4 ${className}`}
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <h2 className="text-sm font-semibold">{title}</h2>
      {desc && (
        <div className="mb-2.5 mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
          {desc}
        </div>
      )}
      <div className={desc ? "w-full" : "mt-2 w-full"}>{children}</div>
      {extra}
    </motion.div>
  );
}

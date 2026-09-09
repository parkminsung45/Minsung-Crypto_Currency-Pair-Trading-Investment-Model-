"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

interface CollapsibleCardProps {
  title: string;
  desc: string;
  count?: number | null;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
  delay?: number;
}

/** 헤더 클릭으로 접고 펼치는 카드 (원본 collapsibleCard()) — RL 모델 설명, 전체 기록 표에 사용 */
export function CollapsibleCard({
  title,
  desc,
  count,
  expanded,
  onToggle,
  children,
  delay = 0,
}: CollapsibleCardProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={reduceMotion ? undefined : { y: -3 }}
      className="rounded-xl border p-4"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <button
        type="button"
        aria-expanded={expanded}
        onClick={onToggle}
        className="flex w-full cursor-pointer items-center justify-between gap-2 bg-transparent p-0 text-left font-inherit group"
      >
        <h2 className="text-sm font-semibold transition-colors group-hover:opacity-80">
          {count == null ? title : `${title} (${count}건)`}
        </h2>
        <motion.span
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          className="flex-none text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          ▸
        </motion.span>
      </button>
      <div className={expanded ? "mb-2.5 mt-0.5 text-xs" : "mt-0.5 text-xs"} style={{ color: "var(--text-muted)" }}>
        {desc}
      </div>
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="body"
            initial={reduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            style={{ overflow: "hidden" }}
          >
            <div className="w-full">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

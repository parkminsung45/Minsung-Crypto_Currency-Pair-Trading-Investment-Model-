"use client";

import { AnimatePresence, motion } from "motion/react";
import type { TooltipState } from "@/lib/chart-utils";

/**
 * 원본의 #tooltip (position: fixed, pointer-events: none) 대응.
 * 차트 컴포넌트들이 포인터 위치를 계산해 이 컴포넌트에 상태로 전달한다.
 */
export function ChartTooltip({ state }: { state: TooltipState | null }) {
  return (
    <AnimatePresence>
      {state && (
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.96 }}
          transition={{ duration: 0.12 }}
          className="fixed z-50 min-w-[130px] rounded-lg border px-2.5 py-2 text-xs shadow-lg pointer-events-none"
          style={{
            left: Math.min(state.x + 14, (typeof window !== "undefined" ? window.innerWidth : 2000) - 160),
            top: Math.min(state.y + 14, (typeof window !== "undefined" ? window.innerHeight : 2000) - 120),
            background: "var(--surface)",
            borderColor: "var(--border)",
            boxShadow: "0 4px 16px rgba(0,0,0,0.16)",
            color: "var(--text-primary)",
          }}
        >
          <div className="mb-1" style={{ color: "var(--text-muted)" }}>
            {state.dateText}
          </div>
          {state.rows.map((r, i) => (
            <div key={i} className="mt-0.5 flex items-center gap-1.5">
              <span className="h-[3px] w-2.5 flex-none rounded-sm" style={{ background: r.color }} />
              <span className="font-semibold">{r.value}</span>
              <span style={{ color: "var(--text-secondary)" }}>{r.name}</span>
            </div>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

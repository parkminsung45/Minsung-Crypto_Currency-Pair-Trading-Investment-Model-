"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { fmtKrw, fmtPct } from "@/lib/chart-utils";
import { ACTION_LABELS_KO, SERIES, type HistoryRecord, type PairReasoning } from "@/lib/types";

const PROB_ORDER = ["HOLD", "ENTER_LONG", "ENTER_SHORT", "EXIT"] as const;

function ReasoningDetail({ reasoning }: { reasoning: Record<string, PairReasoning> }) {
  return (
    <div className="flex flex-col gap-3.5 whitespace-normal px-4 py-3">
      {Object.entries(reasoning).map(([pair, r]) => (
        <div key={pair}>
          <div className="mb-1 text-xs font-semibold">{pair}</div>
          <div className="mb-1.5 text-[12.5px] leading-normal" style={{ color: "var(--text-secondary)" }}>
            {r.explanation}
          </div>
          <div className="mb-2 flex gap-3 text-[11.5px] tabular-nums" style={{ color: "var(--text-muted)" }}>
            <span>z-score {r.spread_zscore.toFixed(2)}</span>
            <span>변화량 {r.spread_change.toFixed(3)}</span>
            <span>선택: {ACTION_LABELS_KO[r.chosen_action] ?? r.chosen_action}</span>
          </div>
          <div className="flex max-w-[420px] flex-col gap-1">
            {PROB_ORDER.map((key) => {
              const p = r.action_probs[key] ?? 0;
              const chosen = key === r.chosen_action;
              return (
                <div
                  key={key}
                  className="grid items-center gap-2 text-[11px]"
                  style={{ gridTemplateColumns: "56px 1fr 34px", color: "var(--text-muted)" }}
                >
                  <span>{ACTION_LABELS_KO[key]}</span>
                  <div className="h-1.5 overflow-hidden rounded" style={{ background: "var(--page)" }}>
                    <motion.div
                      className="h-full rounded"
                      style={{ background: chosen ? "var(--pos)" : "var(--baseline)" }}
                      initial={{ width: 0 }}
                      animate={{ width: (p * 100).toFixed(1) + "%" }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                  <span className="text-right tabular-nums">{(p * 100).toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

const CELL = "whitespace-nowrap border-b px-2 py-1.5 text-right";

function TableRow({ h }: { h: HistoryRecord }) {
  const [open, setOpen] = useState(false);
  const hasReasoning = !!(h.reasoning && Object.keys(h.reasoning).length > 0);
  const ret = h.daily_return_pct;
  const acts = Object.entries(h.actions ?? {})
    .filter(([, a]) => a !== "HOLD")
    .map(([sym, a]) => sym + " " + a);
  const colCount = 4 + SERIES.length + 2;
  const borderStyle = { borderColor: "var(--grid)" };

  return (
    <>
      <tr
        className={hasReasoning ? "cursor-pointer transition-colors hover:[background:var(--page)]" : ""}
        onClick={hasReasoning ? () => setOpen((v) => !v) : undefined}
      >
        <td className={`${CELL} w-4 pr-0.5 text-left`} style={{ ...borderStyle, color: "var(--text-muted)" }}>
          {hasReasoning ? (open ? "▾" : "▸") : ""}
        </td>
        <td className={CELL} style={borderStyle}>
          {h.date}
        </td>
        <td className={`${CELL} tabular-nums`} style={borderStyle}>
          {fmtKrw(h.portfolio_value)}
        </td>
        <td
          className={`${CELL} tabular-nums`}
          style={{ ...borderStyle, color: ret == null ? "var(--text-primary)" : ret >= 0 ? "var(--up)" : "var(--down)" }}
        >
          {ret == null ? "–" : fmtPct(ret)}
        </td>
        {SERIES.map((s) => (
          <td key={s.key} className={`${CELL} tabular-nums`} style={borderStyle}>
            {((h.weights[s.key] ?? 0) * 100).toFixed(1)}%
          </td>
        ))}
        <td className={CELL} style={borderStyle}>
          {acts.length ? acts.join(", ") : "전체 HOLD"}
        </td>
        <td className={CELL} style={borderStyle}>
          {h.dry_run ? "드라이런" : "실거래"}
        </td>
      </tr>
      {hasReasoning && (
        <tr>
          <td colSpan={colCount} className="border-b p-0" style={borderStyle}>
            <AnimatePresence initial={false}>
              {open && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                  style={{ overflow: "hidden" }}
                >
                  <ReasoningDetail reasoning={h.reasoning as Record<string, PairReasoning>} />
                </motion.div>
              )}
            </AnimatePresence>
          </td>
        </tr>
      )}
    </>
  );
}

/** 전체 기록 표 (원본 historyTable()) — 최신순, reasoning 있는 행은 클릭시 펼쳐짐 */
export function HistoryTable({ history }: { history: HistoryRecord[] }) {
  const cols = ["", "날짜", "가치", "일간 수익률", ...SERIES.map((s) => s.label), "주문", "모드"];
  const reversed = [...history].reverse();

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[12.5px]">
        <thead>
          <tr>
            {cols.map((c, i) => (
              <th
                key={i}
                className={`whitespace-nowrap border-b px-2 py-1.5 font-semibold ${i === 0 ? "text-left" : "text-right"}`}
                style={{ borderColor: "var(--grid)", color: "var(--text-secondary)" }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {reversed.map((h, i) => (
            <TableRow key={h.date + i} h={h} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

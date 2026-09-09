"use client";

import { RANGES, type RangeDef } from "@/lib/types";

/** 기간 필터 버튼 행 (전체/7일/30일/90일) — 원본 filters */
export function RangeFilter({
  active,
  onChange,
}: {
  active: RangeDef["key"];
  onChange: (key: RangeDef["key"]) => void;
}) {
  return (
    <div className="mb-4 flex flex-wrap gap-1.5">
      {RANGES.map((r) => {
        const pressed = r.key === active;
        return (
          <button
            key={r.key}
            type="button"
            aria-pressed={pressed}
            onClick={() => onChange(r.key)}
            className="cursor-pointer rounded-lg border px-3 py-1.5 text-[13px] transition-colors"
            style={{
              background: "var(--surface)",
              borderColor: pressed ? "var(--baseline)" : "var(--border)",
              color: pressed ? "var(--text-primary)" : "var(--text-secondary)",
              fontWeight: pressed ? 650 : 400,
            }}
          >
            {r.label}
          </button>
        );
      })}
    </div>
  );
}

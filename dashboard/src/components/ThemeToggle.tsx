"use client";

import { motion } from "motion/react";
import { useEffect, useState } from "react";

type Theme = "dark" | "light";

function readInitialTheme(): Theme {
  if (typeof document === "undefined") return "dark";
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "light" ? "light" : "dark";
}

/** 헤더 우측 다크/라이트 테마 토글 (기본값 다크) — localStorage에 저장하고 data-theme 속성 전환 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");

  // 마운트 시 실제 적용된 테마로 동기화 (layout.tsx의 인라인 스크립트가 이미 속성을 설정해둠)
  useEffect(() => {
    setTheme(readInitialTheme());
  }, []);

  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      // localStorage 접근 불가(프라이빗 모드 등) — 이번 세션 동안만 토글 유지
    }
  };

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "라이트 모드로 전환" : "다크 모드로 전환"}
      title={isDark ? "라이트 모드로 전환" : "다크 모드로 전환"}
      className="inline-flex h-7 w-7 flex-none cursor-pointer items-center justify-center rounded-full border transition-colors"
      style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--text-secondary)" }}
    >
      <motion.span
        key={theme}
        initial={{ opacity: 0, rotate: -90, scale: 0.6 }}
        animate={{ opacity: 1, rotate: 0, scale: 1 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        className="flex items-center justify-center"
      >
        {isDark ? (
          // 달 아이콘 (다크 상태 — 클릭하면 라이트로)
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : (
          // 해 아이콘 (라이트 상태 — 클릭하면 다크로)
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.8" />
            <path
              d="M12 2.5v2.2M12 19.3v2.2M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
        )}
      </motion.span>
    </button>
  );
}

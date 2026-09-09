"use client";

import { useMemo, useSyncExternalStore } from "react";

// 시스템 다크모드 전환 + 수동 테마 토글(data-theme 속성 변경) 둘 다 구독해야
// 차트 색상이 즉시 재계산된다.
function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  const mql = window.matchMedia("(prefers-color-scheme: dark)");
  mql.addEventListener("change", callback);

  const observer = new MutationObserver(callback);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  return () => {
    mql.removeEventListener("change", callback);
    observer.disconnect();
  };
}

// 다크모드 전환이 있을 때마다 값이 바뀌었다고 보고 — 실제 CSS 값은 getSnapshot에서 매번 새로 읽는다.
function getSnapshot() {
  if (typeof window === "undefined") return "";
  const explicit = document.documentElement.getAttribute("data-theme");
  const system = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  return explicit ?? system;
}
function getServerSnapshot() {
  return "";
}

/**
 * :root에 정의된 CSS 커스텀 프로퍼티(팔레트) 값을 읽어온다.
 * 라이트/다크 전환(prefers-color-scheme change) 또는 수동 토글(data-theme 속성) 시
 * 재계산되도록 useSyncExternalStore로 구독.
 * 원본의 cssColor(v) = getComputedStyle(document.documentElement).getPropertyValue(v).trim() 에 대응.
 */
export function useCssVars(vars: string[]): Record<string, string> {
  const scheme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  return useMemo(() => {
    if (typeof window === "undefined") {
      return Object.fromEntries(vars.map((v) => [v, ""]));
    }
    const styles = getComputedStyle(document.documentElement);
    return Object.fromEntries(vars.map((v) => [v, styles.getPropertyValue(v).trim()]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vars, scheme]);
}

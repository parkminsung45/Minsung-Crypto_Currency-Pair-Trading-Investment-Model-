/** 푸터 — 원본 footer 그대로 */
export function DashboardFooter() {
  return (
    <footer className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
      데이터: 저장소의{" "}
      <code
        className="rounded-md border px-1.5 py-px text-[12.5px]"
        style={{ background: "var(--page)", borderColor: "var(--border)" }}
      >
        dashboard/data/history.json
      </code>{" "}
      — 백테스트/페이퍼 트레이딩 실행이 갱신하며, push되면 이 페이지가 자동 반영합니다 (60초마다
      재조회, GitHub raw 캐시로 수 분 지연 가능).
      <div className="mt-1.5">Made by Minsung</div>
    </footer>
  );
}

/** 데이터 없음 / 로드 실패 상태 (원본 render()의 empty 처리) */
export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-4 py-12 text-center text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
      {children}
    </div>
  );
}

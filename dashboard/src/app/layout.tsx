import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reinforced Learning based Crypto Currency Trading",
  description: "암호화폐 페어 트레이딩 강화학습 모델 대시보드",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

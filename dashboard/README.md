강화학습 기반 암호화폐 페어 트레이딩 대시보드 (Next.js + Tailwind + motion).

배포: https://upbit-spread-rl-dashboard.vercel.app

## 데이터

빌드에 데이터를 포함하지 않습니다. 클라이언트에서 GitHub raw로 직접 fetch합니다:

- `data/history.json` — 60초 폴링
- `data/training_curves.json` — 최초 1회 로드

`data/*.json`은 `.github/workflows/paper_trading.yml`이 매시간 자동 커밋·push하며 갱신합니다. 코드를 수정할 때 이 폴더는 건드리지 마세요.

## 로컬 개발

```bash
npm install
npm run dev
```

## 빌드

```bash
npm run build
```

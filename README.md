# upbit-spread-rl

업비트(Upbit) Open API 기반, 스프레드 전략을 학습하는 강화학습(RL) 자동매매 프로젝트.

전체 아키텍처, 전략 설계, 로드맵은 [DESIGN.md](DESIGN.md)를 참고한다.

**대시보드**: [upbit-spread-rl-dashboard.vercel.app](https://upbit-spread-rl-dashboard.vercel.app) — 포트폴리오 가치, 누적수익률, 종목 비중을 확인한다. 아직 실행 이력이 없어 현재는 "기록 없음" 상태.

## 전략

1. **페어 스프레드**: 상관관계 높은 두 코인(예: BTC/ETH) 로그가격 비율의 평균회귀를 노리는 통계적 차익거래.
2. **호가 스프레드**: 오더북 bid-ask 스프레드를 이용한 마켓메이킹/유동성 공급.

## 현재 상태

프로젝트 스캐폴딩 단계. 데이터 수집·환경·PPO 학습 파이프라인의 뼈대가 동작하며(단위테스트 통과), 아직 실제 대량 데이터 학습·백테스트·실거래 연동은 진행 전.

- [x] 데이터 수집: 업비트 REST 캔들 백필(`data/candle_fetcher.py`), WebSocket 오더북/체결 스트림(`data/orderbook_stream.py`)
- [x] 피처: 페어 스프레드 z-score(`features/pair_spread.py`), 호가 스프레드/임밸런스(`features/quote_spread.py`)
- [x] Gym 환경: `PairSpreadEnv`, `QuoteSpreadEnv`
- [x] PPO 학습 래퍼(`agents/train.py`)
- [x] 실행 계층: `PaperBroker`, `LiveBroker`, `RiskGuard`
- [x] 대시보드 골격 배포(Vercel, `dashboard/`) — `dashboard/data/history.json`을 GitHub raw로 fetch
- [ ] 대량 과거 데이터 수집 및 백테스트/워크포워드 검증
- [ ] 페이퍼 트레이딩 운영
- [ ] 실거래 전환

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 사용법

### 1. 과거 데이터 수집

```bash
python scripts/collect_candles.py --market KRW-BTC --days 30
python scripts/collect_candles.py --market KRW-ETH --days 30
```

### 2. 페어 스프레드 PPO 학습

```bash
python scripts/train_pair_spread.py --market-a KRW-BTC --market-b KRW-ETH --days 30
```

### 3. 테스트

```bash
pytest tests/ -v
```

## 실거래 관련 주의사항

- `.env.example`을 `.env`로 복사 후 `UPBIT_ACCESS_KEY`/`UPBIT_SECRET_KEY`를 채운다. `.env`는 git에 커밋되지 않는다.
- `LiveBroker`는 실제 주문을 발생시킨다. `RiskGuard` 없이 직접 호출하지 않는다.
- 실거래 전 반드시 백테스트 → 워크포워드 검증 → 페이퍼 트레이딩(최소 2~4주) 단계를 거친다. 자세한 내용은 DESIGN.md 7절 참고.

## 디렉토리 구조

```
src/upbit_spread_rl/
├── data/        # 업비트 REST/WS 수집, 저장
├── features/    # 스프레드/호가 피처 계산
├── envs/        # Gymnasium 커스텀 환경
├── agents/      # PPO 학습 래퍼
├── execution/   # Broker(Paper/Live), RiskGuard
└── utils/       # 설정, 레이트리밋
scripts/         # 실행 진입점
configs/         # YAML 설정
```

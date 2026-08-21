# upbit-spread-rl 설계 문서

업비트(Upbit) API 기반, 스프레드 전략을 학습하는 강화학습(RL) 자동매매 시스템.

## 1. 목표와 범위

- 전략 두 가지를 하나의 프로젝트에서 다룬다.
  1. **페어 스프레드(Pair Spread)**: 상관관계 높은 두 코인(예: BTC-ETH) 가격 비율의 평균회귀를 노리는 통계적 차익거래.
  2. **호가 스프레드(Quote Spread / Market Making)**: 단일 코인 오더북의 bid-ask 스프레드를 이용해 양방향 지정가를 걸어 유동성을 공급하고 스프레드 수익을 취하는 전략.
- 최종 목표는 업비트 Open API 주문 연동을 통한 **실거래 자동매매**. 단계적으로: 데이터 수집 → 백테스트 → 페이퍼 트레이딩(모의) → 소액 실거래 → 확장.
- 기존 "Minsung Investment Model"(미국 주식 전용) 저장소와는 완전히 분리된 별도 프로젝트. 코드/데이터/자격증명 공유 없음.

## 2. 왜 RL인가 / 왜 이 구조인가

두 전략은 "언제 진입/청산할지"와 "어떤 가격에 호가를 낼지"를 동시에 결정해야 하는 순차적 의사결정 문제이고, 거래비용(수수료·슬리피지)과 재고 리스크(inventory risk)가 보상에 비선형적으로 얽혀 있어 규칙 기반보다 RL로 정책을 학습하는 편이 적합하다고 판단했다. 다만 RL은 과최적화와 리워드 해킹에 취약하므로, 반드시 **워크포워드 검증 + 페이퍼 트레이딩 기간**을 거친 뒤에만 실거래로 넘어간다.

## 3. 전체 아키텍처

```
                     ┌─────────────────────┐
                     │   Upbit Open API     │
                     │  REST (과거/주문)     │
                     │  WebSocket (실시간)   │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  data/ (수집 계층)     │
                     │  - candle_fetcher     │
                     │  - orderbook_stream   │
                     │  - trade_stream       │
                     │  - storage (parquet)  │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ features/ (피처 계층) │
                     │  - pair_spread_feat   │
                     │  - quote_spread_feat  │
                     │  - normalizer         │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │  envs/ (Gym 환경)     │
                     │  - PairSpreadEnv      │
                     │  - QuoteSpreadEnv     │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ agents/ (RL 학습)     │
                     │  - PPO (SB3)          │
                     │  - train / eval       │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ execution/ (실행 계층)│
                     │  - paper_broker       │
                     │  - live_broker (Upbit)│
                     │  - risk_guard         │
                     └───────────────────────┘
```

각 계층은 인터페이스로 분리한다. 예를 들어 `execution`의 `paper_broker`와 `live_broker`는 동일한 `Broker` 프로토콜을 구현하므로, 학습된 정책을 바꾸지 않고 페이퍼→실거래 전환이 가능하다.

## 4. 전략별 설계

### 4.1 페어 스프레드 (PairSpreadEnv)

- **유니버스**: 상관관계/공적분(cointegration) 검정을 통과한 코인 페어(초기: BTC/ETH, 이후 확장).
- **스프레드 정의**: `spread_t = log(price_A_t) - beta * log(price_B_t)`, beta는 롤링 OLS 또는 칼만필터로 추정.
- **상태(state)**: 스프레드의 z-score, 스프레드 변화율, 각 코인 개별 모멘텀/변동성, 현재 포지션(롱/숏/중립), 미실현 손익, 보유시간.
- **행동(action)**: `{롱 스프레드 진입, 숏 스프레드 진입, 청산, 유지}` — 초기엔 이산(discrete) 액션으로 시작, 추후 포지션 사이즈까지 연속 액션으로 확장 검토.
- **보상(reward)**: 실현 손익 - 수수료(업비트 0.05%) - 슬리피지 페널티, 스프레드가 과도하게 벌어진 채 오래 보유 시 리스크 페널티 추가.
- **에피소드**: 고정 길이 윈도우(예: 1일)로 분할하거나 연속 스트림에서 랜덤 시작점 샘플링.

### 4.2 호가 스프레드 (QuoteSpreadEnv)

- **대상**: 유동성 충분한 단일 마켓(예: KRW-BTC).
- **상태**: 오더북 상위 N호가(bid/ask 가격·수량), 최근 체결 임밸런스, 현재 재고(inventory), 스프레드 폭 추이.
- **행동**: 매수호가/매도호가를 현재 mid 대비 몇 틱 offset에 걸지 결정 (연속 액션 2개: bid_offset, ask_offset), 또는 이산화된 offset 후보 중 선택.
- **보상**: 체결된 스프레드 수익 - 재고 리스크 페널티(재고가 한쪽으로 쌓이면 패널티 증가) - 수수료.
- **핵심 리스크**: 역선택(adverse selection) — 가격이 급변할 때 한쪽만 체결되는 상황. 재고 한도(inventory cap)와 즉시 헤지 로직을 환경 제약으로 반영.

### 4.3 두 전략의 관계

MVP는 두 환경을 독립적으로 학습/평가한다. 이후 포트폴리오 레벨에서 두 정책의 자본 배분을 조정하는 상위 컨트롤러(선택적, 3단계 이후 과제)를 고려한다.

## 5. 데이터 계층

- **과거 데이터**: 업비트 REST `/v1/candles/*` (분/일봉), `/v1/trades/ticks`(체결)로 백필. Parquet으로 `data/raw/`에 저장, 날짜/마켓별 파티셔닝.
- **실시간 데이터**: 업비트 WebSocket(`wss://api.upbit.com/websocket/v1`)으로 `orderbook`, `trade` 타입 구독. 재연결/백오프 로직 필수(업비트 WS는 유휴 연결을 끊음).
- **레이트리밋**: 업비트 REST는 IP당 초당 요청 제한이 있음(그룹별 상이). `utils/rate_limiter.py`로 토큰버킷 구현.
- **저장 포맷**: Parquet + 스키마 고정(pyarrow). raw → processed(피처 계산 완료) 2단계.

## 6. 실행/리스크 계층 (실거래 전환 대비)

- `Broker` 프로토콜: `get_balance()`, `place_order()`, `cancel_order()`, `get_open_orders()`.
- `PaperBroker`: 시뮬레이션 체결(오더북 스냅샷 기반 체결 가정, 수수료 반영).
- `LiveBroker`: 업비트 Open API 주문 엔드포인트(JWT 인증, `pyjwt` + API 키/시크릿). API 키는 `.env`로 관리, 저장소에 커밋 금지.
- `RiskGuard`: 일일 손실 한도, 최대 포지션 크기, 연속 손실 시 자동 중단(kill switch) — 실거래 진입 전 필수 게이트.

## 7. 검증 파이프라인

1. **백테스트**: 과거 데이터로 환경 재생, 학습된 정책 평가. Look-ahead bias 방지(피처 계산 시 미래 데이터 참조 금지).
2. **워크포워드**: 시간 순으로 train/validation 윈도우를 순차 이동하며 재학습·평가, 특정 구간 과최적화 방지.
3. **페이퍼 트레이딩**: 실시간 데이터로 실제 주문 없이 PaperBroker로 일정 기간(최소 2~4주 권장) 운영, 실거래 지표(체결률, 슬리피지)와 백테스트 지표 비교.
4. **소액 실거래**: RiskGuard 하에 최소 단위로 실거래 시작, 점진적 확대.

## 8. 기술 스택

- Python 3.11, `gymnasium`(커스텀 Env), `stable-baselines3`(PPO), `torch`
- `pandas`/`pyarrow`(데이터), `websockets`/`httpx`(업비트 연동), `pyjwt`(인증)
- `pydantic`(설정/스키마 검증), `pytest`(테스트)
- 설정은 `configs/*.yaml` + `pydantic-settings`로 관리

## 9. 디렉토리 구조

```
upbit-spread-rl/
├── src/upbit_spread_rl/
│   ├── data/           # 업비트 REST/WS 수집, 저장
│   ├── features/       # 스프레드/호가 피처 계산
│   ├── envs/            # Gymnasium 커스텀 환경
│   ├── agents/          # PPO 학습/평가 래퍼
│   ├── execution/       # PaperBroker, LiveBroker, RiskGuard
│   └── utils/           # 설정, 레이트리밋, 로깅
├── scripts/              # 실행 진입점 (수집/학습/백테스트/실거래)
├── configs/              # YAML 설정
├── data/{raw,processed}/
├── models/               # 학습된 정책 체크포인트
├── logs/
├── tests/
└── notebooks/
```

## 10. 로드맵 (단계별)

| 단계 | 내용 | 산출물 |
|---|---|---|
| 0 | 스캐폴딩, 설정/로깅 기반 | 본 저장소 골격 |
| 1 | 업비트 REST 과거 데이터 수집 | `data/raw` parquet |
| 2 | WebSocket 실시간 수집 | 오더북/체결 스트림 저장 |
| 3 | 피처 엔지니어링 (페어/호가) | `features/*` |
| 4 | Gym 환경 구현 (페어 → 호가 순) | `envs/*` + 단위테스트 |
| 5 | PPO 학습 파이프라인 | `agents/train.py`, `models/*.zip` |
| 6 | 백테스트/워크포워드 평가 | `scripts/backtest.py`, 리포트 |
| 7 | PaperBroker 페이퍼 트레이딩 | 실시간 모의 운영 로그 |
| 8 | LiveBroker + RiskGuard | 소액 실거래 |

## 11. 미해결 질문 / 다음 결정 필요 사항

- 페어 스프레드 유니버스를 몇 개 페어로 시작할지 (BTC/ETH 단일 vs 다중)
- 호가 스프레드 대상 마켓 (KRW-BTC만 vs 복수)
- 캔들 주기(1분/3분/5분) 및 재학습 주기
- RiskGuard의 구체적 손실 한도 수치는 실거래 직전에 별도 논의

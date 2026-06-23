# 졸라맨 축구 예측기 MVP

Next.js + TypeScript + TailwindCSS + Phaser.js 프론트엔드와 FastAPI + PostgreSQL + SQLAlchemy 백엔드로 만든 분석/시각화 전용 MVP입니다.

> 주의: 이 앱은 Betman 구매, 결제, 로그인 자동화 또는 베팅 자동 구매 기능을 포함하지 않습니다. 경기 데이터 수집은 `MockMatchProvider` 인터페이스 구현으로 시작하며, 추후 합법적으로 사용 가능한 스포츠 데이터 API provider를 연결할 수 있습니다.

## 기능

- `/matches`: 경기 목록, 팀/대회/마감시간/배당률 표시
- `/matches/[id]`: 경기 상세, 분석 시작, 30초 졸라맨 축구 시뮬레이션, 결과 표시
- REST API
  - `GET /api/matches`
  - `GET /api/matches/{id}`
  - `POST /api/matches/{id}/predict`
  - `GET /api/predictions/{id}`
  - `GET /api/predictions/{id}/simulation-events`
- Mock team stats 기반 승/무/패 확률, 예상 스코어, 팀 스타일 생성
- 예측 결과 기반 30초 simulation event timeline 생성

## 프로젝트 구조

```text
.
├── backend/              # FastAPI + SQLAlchemy
├── frontend/             # Next.js + TypeScript + TailwindCSS + Phaser.js
├── docker-compose.yml    # PostgreSQL + API + Web
└── .env.example
```

## 로컬 실행

### Docker Compose 권장

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000/matches
- Backend docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 백엔드만 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

앱 시작 시 seed data가 자동 생성됩니다.

### 프론트엔드만 실행

```bash
cd frontend
npm install
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` 기본값은 `http://localhost:8000`입니다.

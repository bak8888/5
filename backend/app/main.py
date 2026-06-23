from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db
from .models import Match, Prediction, SimulationEvent, Team, TeamStats
from .prediction import build_events, predict_match
from .providers import MockMatchProvider
from .schemas import MatchOut, PredictionOut, SimulationEventOut

app = FastAPI(title="졸라맨 축구 예측기 API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

TEAM_STATS = {
    "서울 졸라FC": (.78, .64, .72, "high_pressing"), "부산 스틱맨즈": (.62, .58, .55, "counter_attack"),
    "레드 라인즈": (.83, .69, .8, "possession"), "블루 서클스": (.58, .61, .52, "low_block"),
    "마드리드 막대": (.7, .66, .64, "possession"), "카탈루냐 드리블": (.74, .6, .69, "high_pressing"),
}

def seed(db: Session):
    if db.query(Match).first():
        return
    teams = {}
    for name, (attack, defense, form, style) in TEAM_STATS.items():
        team = Team(name=name, league="Mock League")
        db.add(team); db.flush()
        db.add(TeamStats(team_id=team.id, attack=attack, defense=defense, recent_form=form, team_style=style))
        teams[name] = team
    for item in MockMatchProvider().matches():
        h, d, a = item["odds"]
        db.add(Match(competition=item["competition"], cutoff_time=item["cutoff_time"], home_team_id=teams[item["home"]].id, away_team_id=teams[item["away"]].id, home_odds=h, draw_odds=d, away_odds=a))
    db.commit()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed(db)
    finally:
        db.close()

@app.get("/api/matches", response_model=list[MatchOut])
def get_matches(db: Session = Depends(get_db)):
    return db.query(Match).options(joinedload(Match.home_team), joinedload(Match.away_team)).order_by(Match.cutoff_time).all()

@app.get("/api/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).options(joinedload(Match.home_team), joinedload(Match.away_team)).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match not found")
    return match

@app.post("/api/matches/{match_id}/predict", response_model=PredictionOut)
def create_prediction(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).options(joinedload(Match.home_team).joinedload(Team.stats), joinedload(Match.away_team).joinedload(Team.stats)).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match not found")
    prediction = predict_match(match)
    db.add(prediction); db.commit(); db.refresh(prediction)
    for event in build_events(prediction):
        db.add(event)
    db.commit(); db.refresh(prediction)
    return prediction

@app.get("/api/predictions/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = db.get(Prediction, prediction_id)
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    return prediction

@app.get("/api/predictions/{prediction_id}/simulation-events", response_model=list[SimulationEventOut])
def get_simulation_events(prediction_id: int, db: Session = Depends(get_db)):
    if not db.get(Prediction, prediction_id):
        raise HTTPException(404, "Prediction not found")
    return db.query(SimulationEvent).filter(SimulationEvent.prediction_id == prediction_id).order_by(SimulationEvent.second).all()

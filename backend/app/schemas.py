from datetime import datetime
from pydantic import BaseModel

class TeamOut(BaseModel):
    id: int
    name: str
    league: str
    model_config = {"from_attributes": True}

class MatchOut(BaseModel):
    id: int
    competition: str
    cutoff_time: datetime
    home_odds: float
    draw_odds: float
    away_odds: float
    home_team: TeamOut
    away_team: TeamOut
    model_config = {"from_attributes": True}

class PredictionOut(BaseModel):
    id: int
    match_id: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    expected_home_goals: float
    expected_away_goals: float
    predicted_home_goals: int
    predicted_away_goals: int
    confidence: float
    home_style: str
    away_style: str
    summary: str
    homeWinProb: float
    drawProb: float
    awayWinProb: float
    expectedHomeGoals: float
    expectedAwayGoals: float
    predictedHomeScore: int
    predictedAwayScore: int
    explanation: str
    homeStyle: str
    awayStyle: str
    created_at: datetime
    model_config = {"from_attributes": True}

class SimulationEventOut(BaseModel):
    id: int
    prediction_id: int
    second: int
    event_type: str
    team_side: str
    x: float
    y: float
    description: str
    model_config = {"from_attributes": True}

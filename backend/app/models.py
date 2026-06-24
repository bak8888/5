from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    league: Mapped[str] = mapped_column(String(120))
    stats: Mapped["TeamStats"] = relationship(back_populates="team", uselist=False)

class TeamStats(Base):
    __tablename__ = "team_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), unique=True)
    attack: Mapped[float] = mapped_column(Float)
    defense: Mapped[float] = mapped_column(Float)
    recent_form: Mapped[float] = mapped_column(Float)
    recent_5_points: Mapped[int] = mapped_column(Integer, default=7)
    recent_10_avg_goals_for: Mapped[float] = mapped_column(Float, default=1.4)
    recent_10_avg_goals_against: Mapped[float] = mapped_column(Float, default=1.2)
    home_record_score: Mapped[float] = mapped_column(Float, default=0.55)
    away_record_score: Mapped[float] = mapped_column(Float, default=0.45)
    h2h_score: Mapped[float] = mapped_column(Float, default=0.5)
    home_advantage: Mapped[float] = mapped_column(Float, default=0.08)
    team_style: Mapped[str] = mapped_column(String(40))
    team: Mapped[Team] = relationship(back_populates="stats")

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    competition: Mapped[str] = mapped_column(String(120))
    cutoff_time: Mapped[datetime] = mapped_column(DateTime)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    home_odds: Mapped[float] = mapped_column(Float)
    draw_odds: Mapped[float] = mapped_column(Float)
    away_odds: Mapped[float] = mapped_column(Float)
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    home_win_probability: Mapped[float] = mapped_column(Float)
    draw_probability: Mapped[float] = mapped_column(Float)
    away_win_probability: Mapped[float] = mapped_column(Float)
    expected_home_goals: Mapped[float] = mapped_column(Float, default=0.0)
    expected_away_goals: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_home_goals: Mapped[int] = mapped_column(Integer)
    predicted_away_goals: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    home_style: Mapped[str] = mapped_column(String(40))
    away_style: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    match: Mapped[Match] = relationship()
    events: Mapped[list["SimulationEvent"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")

    @property
    def homeWinProb(self) -> float:
        return self.home_win_probability

    @property
    def drawProb(self) -> float:
        return self.draw_probability

    @property
    def awayWinProb(self) -> float:
        return self.away_win_probability

    @property
    def expectedHomeGoals(self) -> float:
        return self.expected_home_goals

    @property
    def expectedAwayGoals(self) -> float:
        return self.expected_away_goals

    @property
    def predictedHomeScore(self) -> int:
        return self.predicted_home_goals

    @property
    def predictedAwayScore(self) -> int:
        return self.predicted_away_goals

    @property
    def explanation(self) -> str:
        return self.summary

    @property
    def homeStyle(self) -> str:
        return self.home_style

    @property
    def awayStyle(self) -> str:
        return self.away_style

class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"))
    second: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40))
    team_side: Mapped[str] = mapped_column(String(10))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(300))
    prediction: Mapped[Prediction] = relationship(back_populates="events")

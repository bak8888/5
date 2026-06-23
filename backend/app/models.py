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
    predicted_home_goals: Mapped[int] = mapped_column(Integer)
    predicted_away_goals: Mapped[int] = mapped_column(Integer)
    home_style: Mapped[str] = mapped_column(String(40))
    away_style: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    match: Mapped[Match] = relationship()
    events: Mapped[list["SimulationEvent"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")

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

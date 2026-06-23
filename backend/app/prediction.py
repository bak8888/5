import math
from dataclasses import dataclass
from .models import Match, Prediction, SimulationEvent

EVENTS = ["build_up", "press", "counter_attack", "pass", "shot", "save", "goal", "miss"]

@dataclass(frozen=True)
class TeamPredictionStats:
    recent_5_points: int
    recent_10_avg_goals_for: float
    recent_10_avg_goals_against: float
    venue_record_score: float
    h2h_score: float
    attack_score: float
    defense_score: float
    recent_form_score: float
    style: str

@dataclass(frozen=True)
class OddsInput:
    home: float
    draw: float
    away: float

@dataclass(frozen=True)
class MatchContext:
    competition: str
    neutral_h2h_score: float = 0.5
    home_advantage: float = 0.06

@dataclass(frozen=True)
class PredictionEngineInput:
    home_team_stats: TeamPredictionStats
    away_team_stats: TeamPredictionStats
    odds: OddsInput
    match_context: MatchContext

@dataclass(frozen=True)
class PredictionEngineOutput:
    homeWinProb: float
    drawProb: float
    awayWinProb: float
    expectedHomeGoals: float
    expectedAwayGoals: float
    predictedHomeScore: int
    predictedAwayScore: int
    confidence: float
    explanation: str
    homeStyle: str
    awayStyle: str

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))

def _normalize(values: list[float]) -> list[float]:
    safe_values = [max(value, 0.0001) for value in values]
    total = sum(safe_values)
    return [value / total for value in safe_values]

def _implied_probabilities(odds: OddsInput) -> tuple[float, float, float]:
    home, draw, away = _normalize([1 / odds.home, 1 / odds.draw, 1 / odds.away])
    return home, draw, away

def _team_stats_from_orm(stats, *, venue: str) -> TeamPredictionStats:
    return TeamPredictionStats(
        recent_5_points=stats.recent_5_points,
        recent_10_avg_goals_for=stats.recent_10_avg_goals_for,
        recent_10_avg_goals_against=stats.recent_10_avg_goals_against,
        venue_record_score=stats.home_record_score if venue == "home" else stats.away_record_score,
        h2h_score=stats.h2h_score,
        attack_score=stats.attack,
        defense_score=stats.defense,
        recent_form_score=stats.recent_form,
        style=stats.team_style,
    )

def _build_engine_input(match: Match) -> PredictionEngineInput:
    return PredictionEngineInput(
        home_team_stats=_team_stats_from_orm(match.home_team.stats, venue="home"),
        away_team_stats=_team_stats_from_orm(match.away_team.stats, venue="away"),
        odds=OddsInput(home=match.home_odds, draw=match.draw_odds, away=match.away_odds),
        match_context=MatchContext(competition=match.competition),
    )

def run_prediction_engine(engine_input: PredictionEngineInput) -> PredictionEngineOutput:
    home = engine_input.home_team_stats
    away = engine_input.away_team_stats
    market_home, market_draw, market_away = _implied_probabilities(engine_input.odds)

    home_recent_points_score = _clamp(home.recent_5_points / 15)
    away_recent_points_score = _clamp(away.recent_5_points / 15)
    home_goal_balance = _clamp((home.recent_10_avg_goals_for - away.recent_10_avg_goals_against + 2.5) / 5)
    away_goal_balance = _clamp((away.recent_10_avg_goals_for - home.recent_10_avg_goals_against + 2.5) / 5)
    h2h_home = _clamp((home.h2h_score + (1 - away.h2h_score)) / 2)
    h2h_away = 1 - h2h_home

    home_strength = (
        home.attack_score * 0.2
        + home.defense_score * 0.12
        + home.recent_form_score * 0.14
        + home_recent_points_score * 0.12
        + home_goal_balance * 0.12
        + home.venue_record_score * 0.1
        + h2h_home * 0.08
        + market_home * 0.12
        + engine_input.match_context.home_advantage
    )
    away_strength = (
        away.attack_score * 0.2
        + away.defense_score * 0.12
        + away.recent_form_score * 0.14
        + away_recent_points_score * 0.12
        + away_goal_balance * 0.12
        + away.venue_record_score * 0.1
        + h2h_away * 0.08
        + market_away * 0.12
    )
    draw_strength = (
        0.2
        + market_draw * 0.28
        + (1 - abs(home_strength - away_strength)) * 0.22
        + (1 - abs(home.recent_10_avg_goals_for - away.recent_10_avg_goals_for) / 3) * 0.1
    )

    home_prob, draw_prob, away_prob = _normalize([home_strength, draw_strength, away_strength])
    rounded_home = round(home_prob, 4)
    rounded_draw = round(draw_prob, 4)
    rounded_away = round(1 - rounded_home - rounded_draw, 4)

    expected_home_goals = max(0.2, 0.35 + home.recent_10_avg_goals_for * 0.48 + (1 - away.defense_score) * 0.55 + home_prob * 0.75)
    expected_away_goals = max(0.2, 0.28 + away.recent_10_avg_goals_for * 0.48 + (1 - home.defense_score) * 0.55 + away_prob * 0.75)
    predicted_home_score = max(0, round(expected_home_goals))
    predicted_away_score = max(0, round(expected_away_goals))

    edge = max(rounded_home, rounded_draw, rounded_away) - min(rounded_home, rounded_draw, rounded_away)
    market_alignment = 1 - (abs(rounded_home - market_home) + abs(rounded_draw - market_draw) + abs(rounded_away - market_away)) / 2
    confidence = round(_clamp(edge * 0.65 + market_alignment * 0.35), 4)

    explanation = (
        "예측 모델 기준으로 최근 5경기 승점, 최근 10경기 평균 득점/실점, 홈·원정 성적, "
        "상대전적, 배당률 implied probability, 공격력·수비력·최근폼 점수를 함께 반영했습니다. "
        f"홈 승률 {rounded_home * 100:.1f}%, 무승부 {rounded_draw * 100:.1f}%, 원정 승률 {rounded_away * 100:.1f}%로 계산되며, "
        f"예상 득점은 홈 {expected_home_goals:.2f}, 원정 {expected_away_goals:.2f}입니다. "
        "이 결과는 분석 모델의 추정치이며 경기 결과를 단정하지 않습니다."
    )

    return PredictionEngineOutput(
        homeWinProb=rounded_home,
        drawProb=rounded_draw,
        awayWinProb=rounded_away,
        expectedHomeGoals=round(expected_home_goals, 3),
        expectedAwayGoals=round(expected_away_goals, 3),
        predictedHomeScore=predicted_home_score,
        predictedAwayScore=predicted_away_score,
        confidence=confidence,
        explanation=explanation,
        homeStyle=home.style,
        awayStyle=away.style,
    )

def predict_match(match: Match) -> Prediction:
    result = run_prediction_engine(_build_engine_input(match))
    return Prediction(
        match_id=match.id,
        home_win_probability=result.homeWinProb,
        draw_probability=result.drawProb,
        away_win_probability=result.awayWinProb,
        expected_home_goals=result.expectedHomeGoals,
        expected_away_goals=result.expectedAwayGoals,
        predicted_home_goals=result.predictedHomeScore,
        predicted_away_goals=result.predictedAwayScore,
        confidence=result.confidence,
        home_style=result.homeStyle,
        away_style=result.awayStyle,
        summary=result.explanation,
    )

def _style_event(style: str, fallback: str, tick: int) -> str:
    if style == "possession" and tick % 2 == 0:
        return "pass"
    if style == "high_pressing" and tick % 3 == 1:
        return "press"
    if style == "counter_attack" and tick % 4 == 2:
        return "counter_attack"
    return fallback

def build_events(prediction: Prediction) -> list[SimulationEvent]:
    events = []
    goal_seconds = [12, 24, 28][: prediction.predicted_home_goals + prediction.predicted_away_goals]
    shot_seconds = {9, 18, 27}
    save_seconds = {15, 21}
    home_goals_left = prediction.predicted_home_goals
    for tick, second in enumerate(range(0, 31, 3)):
        side = "home" if math.sin(second + prediction.id) >= 0 else "away"
        active_style = prediction.home_style if side == "home" else prediction.away_style
        et = _style_event(active_style, EVENTS[tick % (len(EVENTS) - 1)], tick)
        if second in shot_seconds:
            et = "shot"
        if second in save_seconds:
            et = "save"
        if second in goal_seconds:
            if home_goals_left > 0:
                side, home_goals_left = "home", home_goals_left - 1
            else:
                side = "away"
            et = "goal"
        x = 18 + (second * 2.1 if side == "home" else 64 - second * 1.5) % 66
        y = 18 + abs(math.sin(second / 4)) * 44
        events.append(SimulationEvent(prediction_id=prediction.id, second=second, event_type=et, team_side=side, x=round(x,1), y=round(y,1), description=f"{second}초: {side} {et}"))
    return events

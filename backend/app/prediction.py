import math
from .models import Match, Prediction, SimulationEvent

EVENTS = ["build_up", "press", "counter_attack", "pass", "shot", "save", "goal", "miss"]

def _normalize(values):
    total = sum(values)
    return [v / total for v in values]

def predict_match(match: Match) -> Prediction:
    hs, aw = match.home_team.stats, match.away_team.stats
    market = _normalize([1 / match.home_odds, 1 / match.draw_odds, 1 / match.away_odds])
    home_power = hs.attack * 0.34 + (1 - aw.defense) * 0.22 + hs.recent_form * 0.18 + hs.home_advantage + market[0] * 0.18
    away_power = aw.attack * 0.34 + (1 - hs.defense) * 0.22 + aw.recent_form * 0.18 + market[2] * 0.18
    draw_power = 0.38 - abs(home_power - away_power) * 0.22 + market[1] * 0.35
    hp, dp, ap = _normalize([max(home_power, .05), max(draw_power, .05), max(away_power, .05)])
    home_xg = max(0.2, 0.65 + hs.attack * 1.35 - aw.defense * .55 + hs.home_advantage + hp * .55)
    away_xg = max(0.2, 0.55 + aw.attack * 1.25 - hs.defense * .55 + ap * .55)
    hg, ag = round(home_xg), round(away_xg)
    return Prediction(
        match_id=match.id,
        home_win_probability=round(hp, 4), draw_probability=round(dp, 4), away_win_probability=round(ap, 4),
        predicted_home_goals=hg, predicted_away_goals=ag,
        home_style=hs.team_style, away_style=aw.team_style,
        summary=f"{match.home_team.name}는 {hs.team_style}, {match.away_team.name}는 {aw.team_style} 성향입니다. 예상 스코어는 {hg}-{ag}입니다.",
    )

def build_events(prediction: Prediction) -> list[SimulationEvent]:
    events = []
    goal_seconds = [12, 24, 28][: prediction.predicted_home_goals + prediction.predicted_away_goals]
    home_goals_left = prediction.predicted_home_goals
    for second in range(0, 31, 3):
        side = "home" if math.sin(second + prediction.id) >= 0 else "away"
        et = EVENTS[(second // 3) % (len(EVENTS) - 1)]
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

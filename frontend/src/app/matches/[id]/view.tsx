'use client';

import { useCallback, useState } from 'react';
import StickmanSimulation from '@/components/StickmanSimulation';

type Match = {
  id: number;
  competition: string;
  home_team: { name: string };
  away_team: { name: string };
  home_odds: number;
  draw_odds: number;
  away_odds: number;
};

type Prediction = {
  id: number;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  predicted_home_goals: number;
  predicted_away_goals: number;
  home_style: string;
  away_style: string;
  summary: string;
};

export default function MatchDetail({ match, api }: { match: Match; api: string }) {
  const [prediction, setPrediction] = useState<Prediction>();
  const [events, setEvents] = useState<Parameters<typeof StickmanSimulation>[0]['events']>([]);
  const [done, setDone] = useState(false);

  async function run() {
    setDone(false);
    const nextPrediction = await fetch(`${api}/api/matches/${match.id}/predict`, { method: 'POST' }).then(response => response.json());
    setPrediction(nextPrediction);
    const nextEvents = await fetch(`${api}/api/predictions/${nextPrediction.id}/simulation-events`).then(response => response.json());
    setEvents(nextEvents);
  }

  const handleSimulationEnd = useCallback(() => setDone(true), []);

  return (
    <main className="mx-auto max-w-5xl p-8">
      <a href="/matches" className="text-emerald-300">← 목록</a>
      <h1 className="mt-4 text-3xl font-bold">{match.home_team.name} vs {match.away_team.name}</h1>
      <p className="mt-2 text-slate-300">{match.competition} · 배당률 {match.home_odds}/{match.draw_odds}/{match.away_odds}</p>
      <button onClick={run} className="mt-6 rounded-xl bg-emerald-400 px-6 py-3 font-bold text-slate-950">분석 시작</button>

      {prediction && (
        <section className="mt-8 rounded-2xl bg-slate-900 p-5">
          <h2 className="text-xl font-bold">분석 결과 요약</h2>
          <p className="mt-2 text-slate-300">{prediction.summary}</p>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <b>홈 {(prediction.home_win_probability * 100).toFixed(1)}%</b>
            <b>무 {(prediction.draw_probability * 100).toFixed(1)}%</b>
            <b>원정 {(prediction.away_win_probability * 100).toFixed(1)}%</b>
          </div>
          <p className="mt-3 text-sm text-slate-400">스타일: {prediction.home_style} vs {prediction.away_style}</p>
        </section>
      )}

      {prediction && events.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-xl font-bold">30초 졸라맨 축구 시뮬레이션</h2>
          <StickmanSimulation
            events={events}
            homeStyle={prediction.home_style}
            awayStyle={prediction.away_style}
            onSimulationEnd={handleSimulationEnd}
          />
        </section>
      )}

      {prediction && done && (
        <section className="mt-8 rounded-2xl border border-yellow-300 bg-yellow-950 p-6">
          <h2 className="text-2xl font-bold">최종 예측 결과</h2>
          <p className="mt-2 text-3xl">
            {match.home_team.name} {prediction.predicted_home_goals} - {prediction.predicted_away_goals} {match.away_team.name}
          </p>
        </section>
      )}
    </main>
  );
}

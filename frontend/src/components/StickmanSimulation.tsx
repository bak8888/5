'use client';

import { useEffect, useRef, useState } from 'react';
import type * as Phaser from 'phaser';

type SimulationEvent = {
  second: number;
  event_type: 'build_up' | 'press' | 'counter_attack' | 'pass' | 'shot' | 'save' | 'goal' | 'miss';
  team_side: 'home' | 'away';
  x: number;
  y: number;
  description: string;
};

type TeamStyle = 'high_pressing' | 'possession' | 'counter_attack' | 'low_block' | string;

type StickmanSimulationProps = {
  events: SimulationEvent[];
  homeStyle: TeamStyle;
  awayStyle: TeamStyle;
  onSimulationEnd: () => void;
};

type PhaserModule = typeof import('phaser');

type PlayerSprite = {
  body: Phaser.GameObjects.Container;
  role: 'keeper' | 'defender' | 'midfielder' | 'forward';
  side: 'home' | 'away';
  baseX: number;
  baseY: number;
};

const WIDTH = 800;
const HEIGHT = 450;
const PITCH = { left: 40, right: 760, top: 42, bottom: 418, midY: 225 };

function scaleX(percent: number) {
  return PITCH.left + (PITCH.right - PITCH.left) * (percent / 100);
}

function scaleY(percent: number) {
  return PITCH.top + (PITCH.bottom - PITCH.top) * (percent / 100);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function formation(side: 'home' | 'away', style: TeamStyle) {
  const home = side === 'home';
  if (style === 'low_block') {
    return [
      { role: 'keeper' as const, x: home ? 74 : 726, y: 225 },
      { role: 'defender' as const, x: home ? 132 : 668, y: 130 },
      { role: 'defender' as const, x: home ? 145 : 655, y: 320 },
      { role: 'midfielder' as const, x: home ? 210 : 590, y: 190 },
      { role: 'forward' as const, x: home ? 250 : 550, y: 270 },
    ];
  }
  if (style === 'high_pressing') {
    return [
      { role: 'keeper' as const, x: home ? 82 : 718, y: 225 },
      { role: 'defender' as const, x: home ? 245 : 555, y: 125 },
      { role: 'defender' as const, x: home ? 250 : 550, y: 320 },
      { role: 'midfielder' as const, x: home ? 385 : 415, y: 180 },
      { role: 'forward' as const, x: home ? 500 : 300, y: 265 },
    ];
  }
  if (style === 'possession') {
    return [
      { role: 'keeper' as const, x: home ? 82 : 718, y: 225 },
      { role: 'defender' as const, x: home ? 195 : 605, y: 135 },
      { role: 'defender' as const, x: home ? 205 : 595, y: 315 },
      { role: 'midfielder' as const, x: home ? 340 : 460, y: 205 },
      { role: 'forward' as const, x: home ? 455 : 345, y: 270 },
    ];
  }
  return [
    { role: 'keeper' as const, x: home ? 82 : 718, y: 225 },
    { role: 'defender' as const, x: home ? 175 : 625, y: 130 },
    { role: 'defender' as const, x: home ? 178 : 622, y: 320 },
    { role: 'midfielder' as const, x: home ? 315 : 485, y: 205 },
    { role: 'forward' as const, x: home ? 455 : 345, y: 255 },
  ];
}

function createStickman(scene: Phaser.Scene, x: number, y: number, color: number, label: string) {
  const head = scene.add.circle(0, -16, 7, color).setStrokeStyle(2, 0xffffff);
  const torso = scene.add.line(0, 0, 0, -8, 0, 12, 0xffffff).setLineWidth(3);
  const arms = scene.add.line(0, 0, -12, 0, 12, 0, 0xffffff).setLineWidth(3);
  const leftLeg = scene.add.line(0, 0, 0, 12, -10, 25, 0xffffff).setLineWidth(3);
  const rightLeg = scene.add.line(0, 0, 0, 12, 10, 25, 0xffffff).setLineWidth(3);
  const number = scene.add.text(-4, -7, label, { fontSize: '10px', color: '#ffffff' });
  return scene.add.container(x, y, [head, torso, arms, leftLeg, rightLeg, number]);
}

export default function StickmanSimulation({ events, homeStyle, awayStyle, onSimulationEnd }: StickmanSimulationProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [label, setLabel] = useState('킥오프 준비');

  useEffect(() => {
    let game: Phaser.Game | undefined;
    let ended = false;

    import('phaser').then((PhaserRuntime: PhaserModule) => {
      if (!ref.current) return;

      const config: Phaser.Types.Core.GameConfig = {
        type: PhaserRuntime.AUTO,
        parent: ref.current,
        width: WIDTH,
        height: HEIGHT,
        backgroundColor: '#15803d',
        scene: {
          create() {
            const scene = this as Phaser.Scene;
            let homeScore = 0;
            let awayScore = 0;
            const players: PlayerSprite[] = [];

            scene.add.rectangle(400, 225, 720, 376, 0x15803d).setStrokeStyle(3, 0xffffff);
            scene.add.circle(400, 225, 58).setStrokeStyle(2, 0xffffff);
            scene.add.line(400, 225, 400, 42, 400, 418, 0xffffff).setLineWidth(2);
            scene.add.rectangle(40, 225, 34, 128).setStrokeStyle(3, 0xffffff);
            scene.add.rectangle(760, 225, 34, 128).setStrokeStyle(3, 0xffffff);
            scene.add.rectangle(400, 24, 400, 34, 0x0f172a, 0.9);

            const timerText = scene.add.text(20, 10, '0s', { fontSize: '20px', color: '#d1fae5' });
            const scoreText = scene.add.text(330, 9, 'HOME 0 : 0 AWAY', { fontSize: '20px', color: '#ffffff' });
            const eventText = scene.add.text(560, 10, 'Ready', { fontSize: '16px', color: '#fde68a' });
            const ball = scene.add.circle(400, 225, 8, 0xffffff).setStrokeStyle(2, 0x111827);
            const trail = scene.add.graphics();

            formation('home', homeStyle).forEach((spot, idx) => {
              players.push({ body: createStickman(scene, spot.x, spot.y, 0x2563eb, `${idx + 1}`), role: spot.role, side: 'home', baseX: spot.x, baseY: spot.y });
            });
            formation('away', awayStyle).forEach((spot, idx) => {
              players.push({ body: createStickman(scene, spot.x, spot.y, 0xef4444, `${idx + 1}`), role: spot.role, side: 'away', baseX: spot.x, baseY: spot.y });
            });

            const moveTeamShape = (event: SimulationEvent, targetX: number, targetY: number) => {
              const attacking = players.filter(player => player.side === event.team_side);
              const defending = players.filter(player => player.side !== event.team_side);
              const attackDirection = event.team_side === 'home' ? 1 : -1;
              const attackStyle = event.team_side === 'home' ? homeStyle : awayStyle;
              const defenseStyle = event.team_side === 'home' ? awayStyle : homeStyle;

              attacking.forEach((player, idx) => {
                const pressingBoost = attackStyle === 'high_pressing' ? 62 : 24;
                const passCompactness = attackStyle === 'possession' ? 0.45 : 1;
                const counterBoost = event.event_type === 'counter_attack' ? 115 : 0;
                const roleOffset = player.role === 'keeper' ? -80 : player.role === 'defender' ? -38 : player.role === 'midfielder' ? 0 : 42;
                const nextX = clamp(targetX - attackDirection * roleOffset + attackDirection * pressingBoost + attackDirection * counterBoost, 55, 745);
                const nextY = clamp(targetY + (idx - 2) * 28 * passCompactness, 78, 372);
                scene.tweens.add({ targets: player.body, x: nextX, y: nextY, duration: event.event_type === 'counter_attack' ? 420 : 760, ease: 'Sine.easeInOut' });
              });

              defending.forEach((player, idx) => {
                const blockLine = defenseStyle === 'low_block' ? (player.side === 'home' ? 150 : 650) : targetX - attackDirection * 90;
                const pressureLine = defenseStyle === 'high_pressing' ? targetX + attackDirection * 34 : blockLine;
                scene.tweens.add({
                  targets: player.body,
                  x: clamp(player.role === 'keeper' ? player.baseX : pressureLine + (idx - 2) * 10, 55, 745),
                  y: clamp(targetY + (idx - 2) * 38, 80, 370),
                  duration: 700,
                  ease: 'Sine.easeInOut',
                });
              });
            };

            const drawShotTrail = (fromX: number, fromY: number, toX: number, toY: number, color = 0xfacc15) => {
              trail.clear();
              trail.lineStyle(4, color, 0.9);
              trail.beginPath();
              trail.moveTo(fromX, fromY);
              trail.lineTo((fromX + toX) / 2, Math.min(fromY, toY) - 44);
              trail.lineTo(toX, toY);
              trail.strokePath();
              scene.time.delayedCall(700, () => trail.clear());
            };

            const animateEvent = (event: SimulationEvent) => {
              const eventX = scaleX(event.x);
              const eventY = scaleY(event.y);
              const attackDirection = event.team_side === 'home' ? 1 : -1;
              const goalX = event.team_side === 'home' ? 780 : 20;
              const keeper = players.find(player => player.side !== event.team_side && player.role === 'keeper');
              const shortPass = (event.team_side === 'home' ? homeStyle : awayStyle) === 'possession';

              setLabel(event.description);
              timerText.setText(`${event.second}s`);
              eventText.setText(event.event_type.replace('_', ' ').toUpperCase());
              moveTeamShape(event, eventX, eventY);

              if (event.event_type === 'shot' || event.event_type === 'miss') {
                const targetY = event.event_type === 'miss' ? eventY + 72 : PITCH.midY;
                drawShotTrail(ball.x, ball.y, goalX, targetY);
                scene.tweens.add({ targets: ball, x: goalX - attackDirection * 24, y: targetY, duration: 650, ease: 'Cubic.easeOut' });
                return;
              }

              if (event.event_type === 'save') {
                const saveX = event.team_side === 'home' ? 730 : 70;
                drawShotTrail(ball.x, ball.y, saveX, PITCH.midY, 0x93c5fd);
                scene.tweens.add({ targets: ball, x: saveX, y: PITCH.midY, duration: 520, ease: 'Cubic.easeOut' });
                if (keeper) {
                  scene.tweens.add({ targets: keeper.body, x: saveX, y: PITCH.midY, angle: event.team_side === 'home' ? -18 : 18, duration: 260, yoyo: true });
                }
                return;
              }

              if (event.event_type === 'goal') {
                drawShotTrail(ball.x, ball.y, goalX, PITCH.midY, 0xfbbf24);
                scene.tweens.add({ targets: ball, x: goalX, y: PITCH.midY, scale: 0.75, duration: 720, ease: 'Cubic.easeIn' });
                if (event.team_side === 'home') homeScore += 1;
                else awayScore += 1;
                scoreText.setText(`HOME ${homeScore} : ${awayScore} AWAY`);
                scene.cameras.main.flash(220, 250, 204, 21);
                return;
              }

              if (event.event_type === 'counter_attack') {
                const breakX = clamp(eventX + attackDirection * 190, 70, 730);
                scene.tweens.add({ targets: ball, x: breakX, y: eventY, duration: 360, ease: 'Expo.easeOut' });
                return;
              }

              if (event.event_type === 'pass' && shortPass) {
                const passX = clamp(eventX + attackDirection * 45, 70, 730);
                scene.tweens.add({ targets: ball, x: eventX, y: eventY, duration: 250, ease: 'Sine.easeInOut' });
                scene.tweens.add({ targets: ball, x: passX, y: eventY + 28, duration: 260, delay: 260, ease: 'Sine.easeInOut' });
                scene.tweens.add({ targets: ball, x: passX + attackDirection * 38, y: eventY - 18, duration: 260, delay: 540, ease: 'Sine.easeInOut' });
                return;
              }

              scene.tweens.add({ targets: ball, x: eventX, y: eventY, duration: event.event_type === 'press' ? 430 : 720, ease: 'Sine.easeInOut' });
            };

            events.forEach(event => {
              scene.time.delayedCall(event.second * 1000, () => animateEvent(event));
            });

            scene.time.delayedCall(30000, () => {
              timerText.setText('30s');
              if (!ended) {
                ended = true;
                onSimulationEnd();
              }
            });
          },
        },
      };

      game = new PhaserRuntime.Game(config);
    });

    return () => {
      ended = true;
      game?.destroy(true);
    };
  }, [awayStyle, events, homeStyle, onSimulationEnd]);

  return (
    <div>
      <div ref={ref} className="overflow-hidden rounded-2xl border border-emerald-300" />
      <p className="mt-3 rounded bg-slate-800 p-3 text-emerald-200">{label}</p>
    </div>
  );
}

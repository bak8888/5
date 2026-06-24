import MatchDetail from './view';
const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; const match = await fetch(`${API}/api/matches/${id}`, { cache:'no-store' }).then(r=>r.json()); return <MatchDetail match={match} api={API} />; }

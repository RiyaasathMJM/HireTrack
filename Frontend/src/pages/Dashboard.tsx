// ── pages/Dashboard.tsx ───────────────────────────────────────────────────────

import { useEffect, useState } from 'react';
import {
  BarChart3,
  Users,
  Briefcase,
  TrendingUp,
  Star,
  Clock,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import TopBar from '../components/layout/TopBar';
import MatchScoreBar from '../components/ui/MatchScoreBar';
import StageTag from '../components/ui/StageTag';
import Spinner from '../components/ui/Spinner';
import candidatesApi from '../api/candidates';
import jobsApi from '../api/jobs';
import type { Candidate, JobDescription, PipelineStage } from '../types';

const STAGE_COLORS: Record<PipelineStage, string> = {
  applied:   '#6366f1',
  screening: '#f59e0b',
  interview: '#3b82f6',
  offer:     '#10b981',
  rejected:  '#ef4444',
};

const STAGES: PipelineStage[] = ['applied', 'screening', 'interview', 'offer', 'rejected'];

export default function Dashboard() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      candidatesApi.list(),
      jobsApi.list(),
    ]).then(([cRes, jRes]) => {
      setCandidates(cRes.data);
      setJobs(jRes.data);
    }).finally(() => setLoading(false));
  }, []);

  const stageData = STAGES.map(stage => ({
    name: stage.charAt(0).toUpperCase() + stage.slice(1),
    count: candidates.filter(c => c.stage === stage).length,
    fill: STAGE_COLORS[stage],
  }));

  const pieData = stageData.filter(d => d.count > 0);

  const avgScore = candidates.length
    ? Math.round(candidates.reduce((s, c) => s + c.match_score, 0) / candidates.length)
    : 0;

  const topCandidates = [...candidates]
    .sort((a, b) => b.match_score - a.match_score)
    .slice(0, 5);

  const avgStarRating = candidates.length
    ? (candidates.reduce((s, c) => s + c.star_rating, 0) / candidates.length).toFixed(1)
    : '—';

  const recentCandidates = [...candidates]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 4);

  if (loading) {
    return (
      <div className="page">
        <TopBar title="Dashboard" subtitle="Overview of your hiring pipeline" />
        <div className="page-content">
          <Spinner label="Loading dashboard…" size={40} />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <TopBar title="Dashboard" subtitle="Overview of your hiring pipeline" />
      <div className="page-content">

        {/* Stat Cards */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-icon stat-icon--purple">
              <Users size={22} />
            </div>
            <div className="stat-body">
              <p className="stat-value">{candidates.length}</p>
              <p className="stat-label">Total Candidates</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon stat-icon--blue">
              <Briefcase size={22} />
            </div>
            <div className="stat-body">
              <p className="stat-value">{jobs.length}</p>
              <p className="stat-label">Job Descriptions</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon stat-icon--green">
              <TrendingUp size={22} />
            </div>
            <div className="stat-body">
              <p className="stat-value">{avgScore}%</p>
              <p className="stat-label">Avg Match Score</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon stat-icon--amber">
              <Star size={22} />
            </div>
            <div className="stat-body">
              <p className="stat-value">{avgStarRating}</p>
              <p className="stat-label">Avg Star Rating</p>
            </div>
          </div>
        </div>

        {/* Charts row */}
        <div className="dashboard-charts">
          <div className="card chart-card">
            <div className="card-header">
              <BarChart3 size={18} className="card-header-icon" />
              <h2 className="card-title">Candidates by Stage</h2>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stageData} margin={{ top: 8, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 10,
                    color: 'var(--text)',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {stageData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card chart-card">
            <div className="card-header">
              <TrendingUp size={18} className="card-header-icon" />
              <h2 className="card-title">Stage Distribution</h2>
            </div>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="count"
                    nameKey="name"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: 'var(--surface)',
                      border: '1px solid var(--border)',
                      borderRadius: 10,
                      color: 'var(--text)',
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-empty">No data yet</div>
            )}
          </div>
        </div>

        {/* Bottom row */}
        <div className="dashboard-bottom">
          {/* Top Candidates by score */}
          <div className="card">
            <div className="card-header">
              <TrendingUp size={18} className="card-header-icon" />
              <h2 className="card-title">Top Candidates</h2>
            </div>
            {topCandidates.length === 0 ? (
              <p className="text-muted">No candidates yet.</p>
            ) : (
              <ul className="top-candidates-list">
                {topCandidates.map(c => (
                  <li key={c.id} className="top-candidate-row">
                    <div className="top-candidate-avatar">
                      {c.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="top-candidate-info">
                      <p className="top-candidate-name">{c.name || 'Unknown'}</p>
                      <StageTag stage={c.stage} />
                    </div>
                    <MatchScoreBar score={c.match_score} showLabel />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Recently added */}
          <div className="card">
            <div className="card-header">
              <Clock size={18} className="card-header-icon" />
              <h2 className="card-title">Recently Added</h2>
            </div>
            {recentCandidates.length === 0 ? (
              <p className="text-muted">No candidates yet.</p>
            ) : (
              <ul className="recent-list">
                {recentCandidates.map(c => (
                  <li key={c.id} className="recent-row">
                    <div className="recent-avatar">
                      {c.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="recent-info">
                      <p className="recent-name">{c.name || 'Unknown'}</p>
                      <p className="recent-email">{c.email || '—'}</p>
                    </div>
                    <p className="recent-date">
                      {new Date(c.created_at).toLocaleDateString()}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

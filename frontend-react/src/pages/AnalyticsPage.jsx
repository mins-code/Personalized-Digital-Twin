import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { getDashboardStats } from '../api';
import { useAuth } from '../contexts/AuthContext';
import NoiseOverlay from '../components/NoiseOverlay';
import { Link } from 'react-router-dom';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

function StatCard({ icon, label, value, sub, accent }) {
  return (
    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      <span style={{ fontSize: '1.4rem' }}>{icon}</span>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ fontSize: '1.9rem', fontWeight: 700, color: accent || 'var(--text-primary)', lineHeight: 1 }}>{value}</span>
      {sub && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{sub}</span>}
    </div>
  );
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getDashboardStats()
      .then(d => setStats(d))
      .catch(e => setError(e?.response?.data?.error || 'Failed to load analytics data.'))
      .finally(() => setLoading(false));
  }, []);

  const scores = stats?.scores || [];
  const labels = stats?.labels || [];

  const totalLogs = scores.length;
  const avgRetention = totalLogs > 0 ? (scores.reduce((a, b) => a + b, 0) / totalLogs).toFixed(1) : null;
  const trend = totalLogs >= 2
    ? scores[scores.length - 1] - scores[0] > 0 ? 'up' : scores[scores.length - 1] - scores[0] < 0 ? 'down' : 'flat'
    : 'flat';
  const best = totalLogs > 0 ? Math.max(...scores).toFixed(1) : null;
  const latest = totalLogs > 0 ? scores[scores.length - 1].toFixed(1) : null;

  const lineData = {
    labels,
    datasets: [{
      label: 'Retention Score',
      data: scores,
      borderColor: 'var(--accent)',
      backgroundColor: 'rgba(180,145,90,0.12)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: 'var(--accent)',
    }],
  };

  const lineOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: { label: ctx => `${ctx.parsed.y.toFixed(1)} retention` },
      },
    },
    scales: {
      x: {
        ticks: { color: 'rgba(255,255,255,0.4)', maxTicksLimit: 8 },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        min: 0, max: 100,
        ticks: { color: 'rgba(255,255,255,0.4)', callback: v => `${v}%` },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
  };

  // Distribution bar chart — bin scores into ranges
  const bins = [0, 20, 40, 60, 80, 100];
  const binLabels = ['0–20', '20–40', '40–60', '60–80', '80–100'];
  const binCounts = binLabels.map((_, i) =>
    scores.filter(s => s >= bins[i] && s < bins[i + 1]).length
  );
  // include 100 in last bucket
  if (scores.includes(100)) binCounts[4]++;

  const barData = {
    labels: binLabels,
    datasets: [{
      label: 'Sessions',
      data: binCounts,
      backgroundColor: [
        'rgba(248,113,113,0.6)',
        'rgba(251,191,36,0.6)',
        'rgba(180,145,90,0.6)',
        'rgba(96,165,250,0.6)',
        'rgba(74,222,128,0.6)',
      ],
      borderRadius: 6,
    }],
  };

  const barOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: 'rgba(255,255,255,0.4)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: {
        beginAtZero: true,
        ticks: { color: 'rgba(255,255,255,0.4)', stepSize: 1 },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
  };

  return (
    <div className="page-main">
      <NoiseOverlay />
      <div className="ambient-bg" />

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2.5rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 className="newsreader" style={{ fontSize: '2.1rem', marginBottom: '0.3rem', color: 'var(--text-primary)' }}>
              Progress Analytics
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.93rem', margin: 0 }}>
              {user?.student_id ? `${user.student_id} · ` : ''}Retention trends and study performance overview
            </p>
          </div>
          <Link to="/log" className="glow-button" style={{ textDecoration: 'none', fontSize: '0.88rem', padding: '0.55rem 1.25rem' }}>
            + Log Study Session
          </Link>
        </div>

        {/* Loading */}
        {loading && (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>⏳</div>
            Loading analytics…
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
            <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>
            <Link to="/log" className="glow-button" style={{ textDecoration: 'none', fontSize: '0.88rem' }}>
              Log Your First Session
            </Link>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && totalLogs === 0 && (
          <div className="glass-panel" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📊</div>
            <h2 className="newsreader" style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>No data yet</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.92rem' }}>
              Log at least one study session to see your retention analytics.
            </p>
            <Link to="/log" className="glow-button" style={{ textDecoration: 'none' }}>
              Log First Session
            </Link>
          </div>
        )}

        {/* Main analytics */}
        {!loading && !error && totalLogs > 0 && (
          <>
            {/* Summary stat cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              <StatCard icon="📋" label="Total Sessions" value={totalLogs} sub="study logs recorded" />
              <StatCard
                icon="🧠"
                label="Avg Retention"
                value={`${avgRetention}%`}
                sub="across all sessions"
                accent={avgRetention >= 75 ? '#4ade80' : avgRetention >= 50 ? 'var(--accent)' : '#f87171'}
              />
              <StatCard
                icon="🏆"
                label="Best Session"
                value={`${best}%`}
                sub="peak performance"
                accent="#4ade80"
              />
              <StatCard
                icon="📈"
                label="Latest"
                value={`${latest}%`}
                sub="most recent log"
                accent={trend === 'up' ? '#4ade80' : trend === 'down' ? '#f87171' : 'var(--accent)'}
              />
              <StatCard
                icon={trend === 'up' ? '🚀' : trend === 'down' ? '📉' : '➡️'}
                label="Trend"
                value={trend === 'up' ? 'Improving' : trend === 'down' ? 'Declining' : 'Stable'}
                sub="first vs latest"
                accent={trend === 'up' ? '#4ade80' : trend === 'down' ? '#f87171' : 'rgba(255,255,255,0.6)'}
              />
            </div>

            {/* Retention over time */}
            <div className="glass-panel" style={{ padding: '1.75rem 2rem', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                Retention Score Over Time
              </h3>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginBottom: '1.25rem', marginTop: 0 }}>
                Your logged retention scores, session by session.
              </p>
              <Line data={lineData} options={lineOptions} />
            </div>

            {/* Distribution */}
            <div className="glass-panel" style={{ padding: '1.75rem 2rem', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
                Score Distribution
              </h3>
              <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginBottom: '1.25rem', marginTop: 0 }}>
                How often your retention score falls in each range.
              </p>
              <Bar data={barData} options={barOptions} />
            </div>

            {/* Insight callout */}
            <div className="glass-panel" style={{ padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <span style={{ fontSize: '1.4rem', flexShrink: 0 }}>💡</span>
              <div>
                <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  <strong style={{ color: 'var(--accent)' }}>Improve accuracy:</strong>{' '}
                  CogniSync's retention model retrains as you log more sessions. For best predictions, log consistently
                  and take quizzes after studying. Use the{' '}
                  <Link to="/simulator" style={{ color: 'var(--accent)' }}>What-If Simulator</Link>{' '}
                  to find your optimal study conditions.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}


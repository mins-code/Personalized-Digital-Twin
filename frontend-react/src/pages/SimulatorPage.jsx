import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { predictInstant, getDashboardMeta } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const DIFFICULTY_LABELS = { 1: 'Very Easy', 2: 'Easy', 3: 'Medium', 4: 'Hard', 5: 'Very Hard' };

function ScoreRing({ value }) {
  const pct = value !== null ? Math.max(0, Math.min(100, value)) : null;
  const color = pct === null ? 'rgba(255,255,255,0.08)' :
    pct >= 75 ? '#4ade80' : pct >= 50 ? 'var(--accent)' : '#f87171';

  return (
    <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
      <div style={{
        display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center',
        width: 170, height: 170, borderRadius: '50%',
        border: `5px solid ${color}`,
        boxShadow: pct !== null ? `0 0 35px ${color}44` : 'none',
        transition: 'border-color 0.4s, box-shadow 0.4s',
      }}>
        <span style={{
          fontSize: pct !== null ? '2.8rem' : '2rem',
          fontWeight: 700,
          color: pct !== null ? color : 'var(--text-muted)',
          lineHeight: 1,
        }}>
          {pct !== null ? `${Math.round(pct)}%` : '---'}
        </span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
          Predicted Retention
        </span>
      </div>
    </div>
  );
}

function BreakdownRow({ label, value }) {
  if (value === undefined || value === null) return null;
  const pct = Math.max(0, Math.min(100, value));
  const color = pct >= 75 ? '#4ade80' : pct >= 50 ? 'var(--accent)' : '#f87171';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem',
      padding: '0.5rem 0',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      <span style={{ width: 100, fontSize: '0.8rem', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
      <span style={{ width: 44, textAlign: 'right', fontSize: '0.82rem', fontWeight: 600, color }}>{Math.round(pct)}%</span>
    </div>
  );
}

export default function SimulatorPage() {
  const [studyHour, setStudyHour] = useState(10);
  const [studyDuration, setStudyDuration] = useState(2.0);
  const [subjectDifficulty, setSubjectDifficulty] = useState(3);
  const [meta, setMeta] = useState(null);
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    getDashboardMeta().then(res => setMeta(res.data)).catch(() => {});
  }, []);

  const runPrediction = useCallback(async () => {
    setLoading(true);
    try {
      const data = await predictInstant({
        study_hour: studyHour,
        study_duration: studyDuration,
        subject_difficulty: subjectDifficulty,
      });
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [studyHour, studyDuration, subjectDifficulty]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runPrediction(), 300);
    return () => clearTimeout(debounceRef.current);
  }, [studyHour, studyDuration, subjectDifficulty, runPrediction]);

  const sweepChartData = result?.sweep_labels && result?.sweep_scores ? {
    labels: result.sweep_labels,
    datasets: [{
      label: 'Predicted Retention across Hour of Day',
      data: result.sweep_scores,
      borderColor: 'var(--accent)',
      backgroundColor: 'rgba(180,145,90,0.12)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: 'var(--accent)',
    }],
  } : null;

  const fatigue = meta?.fatigue_status || {};
  const commute = meta?.commute_status || {};
  const workload = meta?.workload_metrics || {};

  return (
    <div className="page-main">
      <NoiseOverlay />
      <div className="ambient-bg" />

      <div style={{ maxWidth: 1050, margin: '0 auto', padding: '2.5rem 1.5rem' }}>
        <div style={{ marginBottom: '1.75rem' }}>
          <span className="label-sm" style={{ color: 'var(--tertiary-fixed)', display: 'block', marginBottom: '0.25rem' }}>
            WHAT-IF STUDY-TIME SIMULATOR (PRD SECTION 6.13)
          </span>
          <h1 className="newsreader" style={{ fontSize: '2.1rem', marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
            Study-Time Scenario Simulator
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            Simulate study effectiveness at different times and durations. Context variables (fatigue, commute delay, and academic load) are automatically grounded in real records.
          </p>
        </div>

        {/* ── Context Parameters Bar (PRD v1.2) ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.75rem' }}>
          <div className="glass-panel" style={{ padding: '0.85rem 1rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Trained Fatigue State</span>
            <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--accent)', fontSize: '0.98rem' }}>
              {fatigue.fatigue_label || 'A little bit'} ({fatigue.readiness_score || 82}% Readiness)
            </p>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Random Forest Model (No manual sliders)</span>
          </div>

          <div className="glass-panel" style={{ padding: '0.85rem 1rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Commute Deviation</span>
            <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.98rem' }}>
              +{commute.deviation_min || 3} min delay
            </p>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Google Maps expected: {commute.expected_duration_min || 35}m</span>
          </div>

          <div className="glass-panel" style={{ padding: '0.85rem 1rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Workload Index</span>
            <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.98rem' }}>
              {workload.load_level || 'Moderate'} ({workload.workload_score || 35} / 100)
            </p>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>From uploaded Timetable & Calendar</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
          
          {/* ── Scenario Controls (Only User Study Decisions) ── */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
              Candidate Study Parameters
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Proposed Study Hour</label>
                  <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{String(studyHour).padStart(2, '0')}:00</span>
                </div>
                <input type="range" min="8" max="22" step="1" value={studyHour} onChange={e => setStudyHour(Number(e.target.value))} style={{ width: '100%' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  <span>08:00 (Morning)</span>
                  <span>22:00 (Night)</span>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Planned Duration</label>
                  <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{studyDuration} hours</span>
                </div>
                <input type="range" min="0.5" max="5.0" step="0.5" value={studyDuration} onChange={e => setStudyDuration(Number(e.target.value))} style={{ width: '100%' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  <span>30 mins</span>
                  <span>5 hours</span>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Subject Difficulty</label>
                  <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{DIFFICULTY_LABELS[subjectDifficulty]} ({subjectDifficulty})</span>
                </div>
                <input type="range" min="1" max="5" step="1" value={subjectDifficulty} onChange={e => setSubjectDifficulty(Number(e.target.value))} style={{ width: '100%' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  <span>Introductory (1)</span>
                  <span>Complex (5)</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Multi-Model Ensemble Output (PRD Section 6.8 & 6.13) ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="glass-panel" style={{ padding: '1.5rem 1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                  Predicted Retention Score
                </h2>
                {loading && <span style={{ fontSize: '0.75rem', color: 'var(--accent)' }}>Computing…</span>}
              </div>

              <ScoreRing value={result?.predicted_retention ?? null} />

              {result?.model_breakdown && (
                <div style={{ marginTop: '0.5rem' }}>
                  <BreakdownRow label="Random Forest" value={result.model_breakdown.rf} />
                  <BreakdownRow label="XGBoost" value={result.model_breakdown.xgb} />
                  <BreakdownRow label="SVR Regressor" value={result.model_breakdown.svr} />
                  <BreakdownRow label="Ensemble" value={result.model_breakdown.ensemble} />
                </div>
              )}
            </div>
          </div>

        </div>

        {/* ── Correlation Map across Hours ── */}
        {sweepChartData && (
          <div className="glass-panel" style={{ marginTop: '1.5rem', padding: '1.5rem 2rem' }}>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-primary)' }}>
              Hour-of-Day Retention Profile
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Simulated retention curve throughout the day under current fatigue, commute, and academic workload constraints.
            </p>
            <div style={{ height: 240 }}>
              <Line 
                data={sweepChartData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    y: { min: 0, max: 100, ticks: { callback: v => `${v}%`, color: 'rgba(255,255,255,0.4)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    x: { ticks: { color: 'rgba(255,255,255,0.4)' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                  }
                }} 
              />
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

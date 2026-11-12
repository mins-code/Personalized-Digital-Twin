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
import { predictInstant } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const DIFFICULTY_LABELS = { 1: 'Very Easy', 2: 'Easy', 3: 'Medium', 4: 'Hard', 5: 'Very Hard' };

const SLIDERS = [
  { key: 'sleep_hours',       label: 'Sleep Hours',         min: 3,   max: 12,  step: 0.5, default: 7.0,  unit: 'hrs' },
  { key: 'energy_score',      label: 'Energy Level',        min: 1,   max: 5,   step: 1,   default: 3,    unit: '' },
  { key: 'study_hour',        label: 'Study Start Hour',    min: 0,   max: 23,  step: 1,   default: 10,   unit: '' },
  { key: 'study_duration',    label: 'Study Duration',      min: 0.5, max: 5.0, step: 0.5, default: 2.0,  unit: 'hrs' },
  { key: 'subject_difficulty',label: 'Subject Difficulty',  min: 1,   max: 5,   step: 1,   default: 3,    unit: '' },
];

function formatValue(key, val) {
  if (key === 'study_hour') return `${String(val).padStart(2, '0')}:00`;
  if (key === 'subject_difficulty') return `${DIFFICULTY_LABELS[val] || val} (${val})`;
  if (key === 'sleep_hours' || key === 'study_duration') return `${val} hrs`;
  return `${val}`;
}

function ScoreRing({ value }) {
  const pct = value !== null ? Math.max(0, Math.min(100, value)) : null;
  const color = pct === null ? 'rgba(255,255,255,0.08)' :
    pct >= 75 ? '#4ade80' : pct >= 50 ? 'var(--accent)' : '#f87171';

  return (
    <div style={{ textAlign: 'center', padding: '2rem 0 1.5rem' }}>
      <div style={{
        display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center',
        width: 180, height: 180, borderRadius: '50%',
        border: `6px solid ${color}`,
        boxShadow: pct !== null ? `0 0 40px ${color}55, 0 0 80px ${color}22` : 'none',
        transition: 'border-color 0.4s, box-shadow 0.4s',
        position: 'relative',
      }}>
        <span style={{
          fontSize: pct !== null ? '3rem' : '2rem',
          fontWeight: 700,
          color: pct !== null ? color : 'var(--text-muted)',
          lineHeight: 1,
          letterSpacing: '-1px',
          transition: 'color 0.4s',
        }}>
          {pct !== null ? `${Math.round(pct)}` : '---'}
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
          {pct !== null ? '% retention' : 'adjust sliders'}
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
    <div className="breakdown-row" style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem',
      padding: '0.55rem 0',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      <span style={{ width: 80, fontSize: '0.82rem', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
      <span style={{ width: 44, textAlign: 'right', fontSize: '0.85rem', fontWeight: 600, color }}>{Math.round(pct)}%</span>
    </div>
  );
}

export default function SimulatorPage() {
  const [inputs, setInputs] = useState(() =>
    Object.fromEntries(SLIDERS.map(s => [s.key, s.default]))
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const debounceRef = useRef(null);
  const abortRef = useRef(null);

  const runPrediction = useCallback(async (vals) => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();
    setLoading(true);
    setError('');
    try {
      const data = await predictInstant({
        sleep_hours: vals.sleep_hours,
        energy_score: vals.energy_score,
        study_hour: vals.study_hour,
        study_duration: vals.study_duration,
        subject_difficulty: vals.subject_difficulty,
        // mood_score not collected per PRD — omit or send neutral placeholder
      });
      setResult(data);
    } catch (e) {
      if (e.name !== 'CanceledError' && e.name !== 'AbortError') {
        setError(e?.response?.data?.error || 'Prediction failed. Is the backend running?');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounce on input change
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runPrediction(inputs), 350);
    return () => clearTimeout(debounceRef.current);
  }, [inputs, runPrediction]);

  const handleSlider = (key, val) => setInputs(prev => ({ ...prev, [key]: Number(val) }));

  const sweepChartData = result?.sweep_labels && result?.sweep_scores ? {
    labels: result.sweep_labels,
    datasets: [{
      label: 'Predicted Retention (%)',
      data: result.sweep_scores,
      borderColor: 'var(--accent)',
      backgroundColor: 'rgba(180,145,90,0.12)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointBackgroundColor: 'var(--accent)',
    }],
  } : null;

  const sweepChartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => `${Math.round(ctx.parsed.y)}% retention`,
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Sleep Hours', color: 'rgba(255,255,255,0.4)', font: { size: 11 } },
        ticks: { color: 'rgba(255,255,255,0.4)' },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        min: 0, max: 100,
        title: { display: true, text: 'Retention %', color: 'rgba(255,255,255,0.4)', font: { size: 11 } },
        ticks: { color: 'rgba(255,255,255,0.4)', callback: v => `${v}%` },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
    },
  };

  const breakdown = result?.model_breakdown || {};
  const retentionValue = result?.predicted_retention ?? null;

  return (
    <div className="page-main">
      <NoiseOverlay />
      <div className="ambient-bg" />

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2.5rem 1.5rem' }}>
        <h1 className="newsreader" style={{ fontSize: '2.1rem', marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
          What-If Simulator
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.93rem', marginBottom: '2rem' }}>
          Adjust environmental variables to explore how different study conditions affect your predicted retention score.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* LEFT: Controls */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.75rem', color: 'var(--text-primary)' }}>
              Environmental Controls
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {SLIDERS.map(s => (
                <div key={s.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <label style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      {s.label}
                    </label>
                    <span style={{
                      fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent)',
                      minWidth: 90, textAlign: 'right',
                    }}>
                      {formatValue(s.key, inputs[s.key])}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={s.min} max={s.max} step={s.step}
                    value={inputs[s.key]}
                    onChange={e => handleSlider(s.key, e.target.value)}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    <span>{formatValue(s.key, s.min)}</span>
                    <span>{formatValue(s.key, s.max)}</span>
                  </div>
                </div>
              ))}
            </div>

            {error && (
              <div style={{
                marginTop: '1.5rem', padding: '0.75rem 1rem',
                background: 'rgba(248,113,113,0.1)', borderRadius: 8,
                border: '1px solid rgba(248,113,113,0.3)',
                fontSize: '0.85rem', color: '#f87171',
              }}>
                {error}
              </div>
            )}

            <p style={{
              marginTop: '1.5rem', fontSize: '0.78rem', color: 'var(--text-muted)',
              lineHeight: 1.5, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem',
            }}>
              Predictions update automatically as you adjust the sliders.
              Results are generated by CogniSync's ensemble model (RF + XGB + SVR).
            </p>
          </div>

          {/* RIGHT: Retention readout + breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Score ring */}
            <div className="glass-panel" style={{ padding: '1.5rem 2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                  Predicted Retention
                </h2>
                {loading && (
                  <span style={{ fontSize: '0.78rem', color: 'var(--accent)', animation: 'pulse-glow 1s infinite' }}>
                    Computing…
                  </span>
                )}
              </div>
              <ScoreRing value={retentionValue} />

              {retentionValue !== null && (
                <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
                  {retentionValue >= 75
                    ? '🟢 Excellent conditions for learning'
                    : retentionValue >= 55
                    ? '🟡 Moderate retention expected'
                    : '🔴 Consider adjusting your conditions'}
                </p>
              )}
            </div>

            {/* Model breakdown */}
            {result && (
              <div className="glass-panel" style={{ padding: '1.5rem 1.75rem' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-primary)' }}>
                  Model Breakdown
                </h3>
                <BreakdownRow label="Random Forest" value={breakdown.rf} />
                <BreakdownRow label="XGBoost" value={breakdown.xgb} />
                <BreakdownRow label="SVR" value={breakdown.svr} />
                <BreakdownRow label="Ensemble" value={breakdown.ensemble} />
                {breakdown.uncertainty !== undefined && (
                  <p style={{ marginTop: '0.85rem', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    <span style={{ color: 'var(--accent)' }}>Uncertainty: </span>
                    ±{(breakdown.uncertainty * 100).toFixed(1)}% — based on model agreement
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sleep / Retention sweep chart */}
        {sweepChartData && (
          <div className="glass-panel" style={{ marginTop: '1.5rem', padding: '1.75rem 2rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.25rem', color: 'var(--text-primary)' }}>
              Sleep / Retention Correlation Map
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '1.25rem', marginTop: 0 }}>
              Predicted retention across the full range of sleep hours, holding other controls fixed.
            </p>
            <Line data={sweepChartData} options={sweepChartOptions} />
          </div>
        )}
      </div>
    </div>
  );
}


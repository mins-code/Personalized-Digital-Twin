import { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getDashboardStats, getDashboardMeta, uploadSyllabus, listSyllabuses, deleteSyllabus, deleteSingleSyllabus } from '../api';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import NoiseOverlay from '../components/NoiseOverlay';
import LoadingSpinner from '../components/LoadingSpinner';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const API_BASE = process.env.REACT_APP_API_BASE_URL || '';

export default function DashboardPage() {
  const { user } = useAuth();
  const [meta, setMeta]           = useState({ student_id: '', best_time: '10:00', log_count: 0, progress_percentage: 0, shap_path: '' });
  const [chartData, setChartData] = useState(null);
  const [syllabuses, setSyllabuses] = useState([]);
  const [uploading, setUploading]   = useState(false);
  const [uploadMsg, setUploadMsg]   = useState('');
  const [metaLoading, setMetaLoading] = useState(true);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Fetch chart data
    getDashboardStats().then(res => {
      setChartData({
        labels: res.data.labels,
        datasets: [{
          label: 'Predicted Retention',
          data: res.data.scores,
          borderColor: '#45501f',
          backgroundColor: 'rgba(69, 80, 31, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#d7c3b0',
          pointBorderColor: '#11140e',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.4,
        }],
      });
    }).catch(() => {});

    // Fetch meta (best_time, log_count, shap_path)
    getDashboardMeta().then(res => {
      const d = res.data;
      setMeta({
        student_id: d.student_id || user?.student_id || '',
        best_time: d.best_time || '10:00',
        log_count: d.log_count ?? 0,
        progress_percentage: d.progress_percentage ?? 0,
        shap_path: d.shap_path || '',
      });
    }).finally(() => setMetaLoading(false));

    fetchSyllabuses();
  }, []);

  const fetchSyllabuses = () => {
    listSyllabuses().then(res => setSyllabuses(res.data.syllabuses || [])).catch(() => {});
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg('');
    try {
      const res = await uploadSyllabus(file);
      setUploadMsg(res.data.message || 'Synced successfully.');
      fetchSyllabuses();
    } catch (err) {
      setUploadMsg(err?.response?.data?.error || 'Upload failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteSingle = async (filename) => {
    if (!window.confirm(`Delete ${filename}?`)) return;
    try {
      await deleteSingleSyllabus(filename);
      fetchSyllabuses();
    } catch (err) {
      alert('Delete failed.');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Clear all uploaded syllabuses from memory? This cannot be undone.')) return;
    try {
      await deleteSyllabus();
      setSyllabuses([]);
    } catch (err) {
      alert('Failed to clear memory.');
    }
  };

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    scales: {
      x: {
        grid: { color: 'rgba(69,71,66,0.2)' },
        ticks: { color: '#90918b', font: { family: 'Manrope', size: 11 } },
      },
      y: {
        min: 0, max: 100,
        grid: { color: 'rgba(69,71,66,0.2)' },
        ticks: { color: '#90918b', font: { family: 'Manrope', size: 11 }, callback: v => `${v}%` },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(40,43,36,0.9)',
        titleColor: '#f4dfcb', bodyColor: '#c6c7c0',
        callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(1)}%` },
      },
    },
  };

  const { log_count, progress_percentage, shap_path, best_time, student_id } = meta;
  const displayStudentId = student_id || user?.student_id || '';

  return (
    <div className="page-container ambient-bg">
      <NoiseOverlay />
      <main className="page-main">

        {/* Welcome banner */}
        <div className="mb-8">
          <div className="glass-panel" style={{ borderRadius: 'var(--radius-lg)', padding: '1rem 1.5rem', textAlign: 'center' }}>
            <p style={{ fontFamily: 'Newsreader, serif', fontSize: '1.25rem', fontStyle: 'italic', color: 'var(--tertiary-fixed)', letterSpacing: '0.03em' }}>
              Welcome back{displayStudentId ? `, ${displayStudentId}` : ''}!
            </p>
          </div>
        </div>

        <div className="grid-12">

          {/* ── Hero: Best Study Window ── */}
          <div className="col-8 glass-panel card">
            <div style={{
              position: 'absolute', top: 0, right: 0, width: '16rem', height: '16rem',
              background: 'rgba(69,80,31,0.2)', borderRadius: '50%', filter: 'blur(60px)',
              transform: 'translate(25%, -25%)',
            }} />
            <h2 style={{
              fontFamily: 'Newsreader, serif', fontSize: 'clamp(1.75rem, 3vw, 2.75rem)',
              color: 'var(--primary)', marginBottom: '1.5rem', position: 'relative', zIndex: 1, lineHeight: 1.3,
            }}>
              Your Digital Twin predicts your peak retention today will be at{' '}
              <span className="pulse-text" style={{ color: 'var(--tertiary-fixed)' }}>
                {metaLoading ? '...' : best_time}
              </span>.
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', position: 'relative', zIndex: 1, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '2rem', color: 'var(--secondary-fixed)' }}>psychology</span>
                <div>
                  <p className="label-sm">Model Confidence</p>
                  <p style={{ color: 'var(--secondary-fixed)', fontSize: '1.125rem', marginTop: '0.25rem' }}>92% Confidence</p>
                </div>
              </div>

              {meta?.fatigue_status && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '2rem', color: 'var(--tertiary-fixed)' }}>bedtime</span>
                  <div>
                    <p className="label-sm">Cognitive Fatigue (RF)</p>
                    <p style={{ color: 'var(--tertiary-fixed)', fontSize: '1.125rem', marginTop: '0.25rem' }}>
                      {meta.fatigue_status.fatigue_label}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── Retraining Progress ── */}
          <div className="col-4 glass-panel card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="material-symbols-outlined" style={{ color: 'var(--tertiary)', fontSize: '1.5rem' }}>model_training</span>
                <span className="label-sm">Twin Status</span>
              </div>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.5rem', color: 'var(--primary)', marginTop: '1rem' }}>
                Retraining Progress
              </h3>
              <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                Every 14 logs refines your cognitive twin's accuracy.
              </p>
            </div>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--on-surface-variant)', marginBottom: '0.5rem' }}>
                <span>{log_count} Logs</span>
                <span>14 Logs</span>
              </div>
              <div style={{
                width: '100%', background: 'rgba(51,54,47,0.5)', height: '0.75rem',
                borderRadius: '9999px', overflow: 'hidden', border: '1px solid rgba(69,71,66,0.2)',
              }}>
                <div className="progress-bar-inner" style={{
                  width: `${progress_percentage}%`,
                  height: '100%', borderRadius: '9999px',
                  background: 'var(--secondary-container)',
                  position: 'relative', overflow: 'hidden',
                }}>
                  <div className="shimmer" style={{
                    position: 'absolute', inset: 0,
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                  }} />
                </div>
              </div>
            </div>
          </div>

          {/* ── Digital Identity (SHAP) ── */}
          <div className="col-5 glass-panel card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.5rem', color: 'var(--primary)' }}>Digital Identity</h3>
              <span className="label-sm">Feature Drivers</span>
            </div>
            <div style={{
              flex: 1, background: 'rgba(51,54,47,0.3)', borderRadius: 'var(--radius-xl)',
              border: '1px solid rgba(69,71,66,0.3)', display: 'flex', alignItems: 'center',
              justifyContent: 'center', padding: '1rem', overflow: 'hidden', minHeight: '200px',
            }}>
              {shap_path ? (
                <img
                  src={`${API_BASE}/static/${shap_path}`}
                  alt="SHAP Feature Importance"
                  style={{ width: '100%', height: 'auto', objectFit: 'contain', opacity: 0.9, mixBlendMode: 'screen', filter: 'contrast(1.25)' }}
                  onError={e => { e.target.style.mixBlendMode = 'normal'; e.target.src = 'https://via.placeholder.com/400x300/11140e/c6c7c0?text=Model+Initializing...'; }}
                />
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--on-surface-variant)' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '3rem', display: 'block', marginBottom: '0.5rem' }}>scatter_plot</span>
                  <p className="label-sm">Model initializing…</p>
                </div>
              )}
            </div>
          </div>

          {/* ── Weekly Pulse Chart ── */}
          <div className="col-7 glass-panel card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.5rem', color: 'var(--primary)' }}>Weekly Pulse</h3>
              <span className="label-sm">Retention Trend</span>
            </div>
            <div style={{ flex: 1, minHeight: '250px', position: 'relative' }}>
              {chartData
                ? <Line data={chartData} options={chartOptions} />
                : <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                    <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.875rem' }}>
                      No study logs yet. Add your first log to see the trend.
                    </p>
                  </div>
              }
            </div>
          </div>

          {/* ── Neural Knowledge Sync (Syllabus Upload) ── */}
          <div className="col-12 glass-panel card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.5rem', color: 'var(--primary)' }}>Neural Knowledge Sync</h3>
              <span className="label-sm" id="sync-status">
                {syllabuses.length > 0 ? `${syllabuses.length} syllabus${syllabuses.length > 1 ? 'es' : ''} synced` : 'No Syllabus Synced'}
              </span>
            </div>

            {/* Dropzone */}
            <div className="dropzone">
              <input
                type="file"
                accept=".pdf"
                ref={fileInputRef}
                onChange={handleFileUpload}
                disabled={uploading}
              />
              {uploading ? (
                <>
                  <span className="material-symbols-outlined spin" style={{ fontSize: '2.5rem', color: 'var(--secondary-fixed)', marginBottom: '0.5rem' }}>sync</span>
                  <p style={{ color: 'var(--secondary-fixed)', fontSize: '0.875rem' }}>Syncing…</p>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '2.5rem', color: 'var(--on-surface-variant)', marginBottom: '0.5rem' }}>cloud_upload</span>
                  <p style={{ color: 'var(--on-surface-variant)' }}>Drag and drop PDFs here, or click to browse</p>
                  <p style={{ color: 'var(--outline)', fontSize: '0.75rem', marginTop: '0.5rem' }}>Only .pdf files are supported</p>
                </>
              )}
            </div>

            {uploadMsg && (
              <div style={{
                marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: 'var(--radius-lg)',
                background: 'rgba(69,80,31,0.2)', border: '1px solid rgba(219,233,169,0.3)',
                color: 'var(--secondary-fixed)', fontSize: '0.875rem', textAlign: 'center',
              }}>
                <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', marginRight: '0.5rem' }}>check_circle</span>
                {uploadMsg}
              </div>
            )}

            {/* Syllabus list */}
            <div style={{ marginTop: '1.5rem' }}>
              <p className="label-sm" style={{ marginBottom: '1rem' }}>Ingested Knowledge Base</p>
              {syllabuses.length === 0 ? (
                <p style={{ color: 'var(--outline)', fontSize: '0.875rem', fontStyle: 'italic' }}>No syllabuses uploaded yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {syllabuses.map(s => (
                    <div key={s.filename} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.75rem 1rem', borderRadius: 'var(--radius-lg)',
                      background: 'rgba(40,43,36,0.4)', border: '1px solid rgba(69,71,66,0.3)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span className="material-symbols-outlined" style={{ color: 'var(--tertiary)' }}>description</span>
                        <span style={{ color: 'var(--primary)', fontSize: '0.875rem' }}>{s.display_name}</span>
                      </div>
                      <button
                        onClick={() => handleDeleteSingle(s.filename)}
                        style={{
                          background: 'transparent', border: 'none',
                          color: 'var(--outline)', cursor: 'pointer', transition: 'color 0.2s',
                          display: 'flex', alignItems: 'center',
                        }}
                        onMouseOver={e => e.currentTarget.style.color = 'var(--error)'}
                        onMouseOut={e => e.currentTarget.style.color = 'var(--outline)'}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: '1.25rem' }}>delete</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Clear all */}
            {syllabuses.length > 0 && (
              <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  onClick={handleClearAll}
                  style={{
                    padding: '0.5rem 1rem', background: 'transparent', cursor: 'pointer',
                    color: 'var(--error)', fontSize: '0.75rem', letterSpacing: '0.15em',
                    textTransform: 'uppercase', fontWeight: 600, border: '1px solid rgba(255,180,171,0.5)',
                    borderRadius: '9999px', transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: '0.5rem',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '1.125rem' }}>delete_forever</span>
                  Clear All Memory
                </button>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}


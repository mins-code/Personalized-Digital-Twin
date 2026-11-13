import { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  getDashboardStats, 
  getDashboardMeta, 
  uploadSyllabus, 
  uploadSchedulePDF,
  listSyllabuses, 
  deleteSyllabus, 
  deleteSingleSyllabus 
} from '../api';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import NoiseOverlay from '../components/NoiseOverlay';
import LoadingSpinner from '../components/LoadingSpinner';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function DashboardPage() {
  const { user } = useAuth();
  const [meta, setMeta]           = useState(null);
  const [chartData, setChartData] = useState(null);
  const [syllabuses, setSyllabuses] = useState([]);
  const [uploading, setUploading]   = useState(false);
  const [uploadMsg, setUploadMsg]   = useState('');
  const [loading, setLoading]       = useState(true);
  
  const scheduleInputRef = useRef(null);
  const syllabusInputRef = useRef(null);

  const fetchDashboardData = () => {
    Promise.all([getDashboardStats(), getDashboardMeta(), listSyllabuses()])
      .then(([statsRes, metaRes, sylRes]) => {
        setChartData({
          labels: statsRes.data.labels,
          datasets: [{
            label: 'Predicted Retention (%)',
            data: statsRes.data.scores,
            borderColor: '#b4915a',
            backgroundColor: 'rgba(180, 145, 90, 0.12)',
            borderWidth: 3,
            pointBackgroundColor: '#f4dfcb',
            pointBorderColor: '#11140e',
            pointBorderWidth: 2,
            pointRadius: 5,
            fill: true,
            tension: 0.4,
          }],
        });
        setMeta(metaRes.data);
        setSyllabuses(sylRes.data.syllabuses || []);
      })
      .catch((err) => console.error("Error loading dashboard data:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleScheduleUpload = async (e, category) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg('');
    try {
      await uploadSchedulePDF(file, category);
      setUploadMsg(`Successfully uploaded and parsed ${category}!`);
      fetchDashboardData();
    } catch (err) {
      setUploadMsg(err?.response?.data?.error || 'Failed to upload schedule.');
    } finally {
      setUploading(false);
    }
  };

  const handleSyllabusUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg('');
    try {
      await uploadSyllabus(file);
      setUploadMsg('Study material indexed successfully!');
      fetchDashboardData();
    } catch (err) {
      setUploadMsg(err?.response?.data?.error || 'Failed to upload study material.');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container ambient-bg flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const {
    best_time,
    log_count,
    progress_percentage,
    fatigue_status,
    workload_metrics,
    commute_status,
    recommended_windows,
  } = meta || {};

  return (
    <div className="page-container ambient-bg">
      <NoiseOverlay />
      <main className="page-main">

        {/* ── Welcome Header ── */}
        <div style={{ marginBottom: '2rem' }}>
          <div className="glass-panel" style={{ borderRadius: 'var(--radius-lg)', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <p style={{ fontFamily: 'Newsreader, serif', fontSize: '1.25rem', fontStyle: 'italic', color: 'var(--tertiary-fixed)', margin: 0 }}>
              Welcome back, {user?.student_id || meta?.student_id || 'Student'}
            </p>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button 
                className="glow-button" 
                style={{ padding: '0.45rem 1rem', fontSize: '0.8rem' }}
                onClick={() => scheduleInputRef.current?.click()}
                disabled={uploading}
              >
                + Upload Timetable / Calendar PDF
              </button>
              <input 
                type="file" 
                ref={scheduleInputRef} 
                style={{ display: 'none' }} 
                accept=".pdf" 
                onChange={(e) => handleScheduleUpload(e, 'timetable')} 
              />
            </div>
          </div>
          {uploadMsg && (
            <p style={{ fontSize: '0.85rem', color: '#4ade80', marginTop: '0.5rem', textAlign: 'right' }}>{uploadMsg}</p>
          )}
        </div>

        <div className="grid-12">

          {/* ── 1. Hero: Recommended Study Window (PRD Section 6.11) ── */}
          <div className="col-8 glass-panel card" style={{ position: 'relative', overflow: 'hidden' }}>
            <div style={{
              position: 'absolute', top: 0, right: 0, width: '16rem', height: '16rem',
              background: 'rgba(180,145,90,0.15)', borderRadius: '50%', filter: 'blur(70px)',
              transform: 'translate(25%, -25%)',
            }} />
            
            <span className="label-sm" style={{ color: 'var(--tertiary-fixed)', display: 'block', marginBottom: '0.5rem' }}>
              STUDY-TIME RECOMMENDATION ENGINE (PRD v1.2)
            </span>
            <h2 style={{
              fontFamily: 'Newsreader, serif', fontSize: 'clamp(1.75rem, 2.5vw, 2.5rem)',
              color: 'var(--primary)', marginBottom: '1.25rem', lineHeight: 1.3,
            }}>
              Your peak cognitive window today is at{' '}
              <span style={{ color: 'var(--tertiary-fixed)', borderBottom: '2px dashed var(--tertiary-fixed)' }}>
                {best_time}
              </span>
            </h2>

            {/* Context Indicators: Fatigue (RF), Commute, Workload */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.25rem', marginTop: '1.5rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem 1rem', borderRadius: 8 }}>
                <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Trained Fatigue Level</span>
                <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem' }}>
                  {fatigue_status?.fatigue_label || 'A little bit'}
                </p>
                <span style={{ fontSize: '0.7rem', color: '#4ade80' }}>
                  {fatigue_status?.readiness_score !== undefined ? `${fatigue_status.readiness_score}% Cognitive Readiness` : '82% Cognitive Readiness'}
                </span>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem 1rem', borderRadius: 8 }}>
                <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Commute Context</span>
                <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem' }}>
                  +{commute_status?.deviation_min ?? 3} min delay
                </p>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Actual: {commute_status?.actual_duration_min ?? 38}m (Google: {commute_status?.expected_duration_min ?? 35}m)
                </span>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem 1rem', borderRadius: 8 }}>
                <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Academic Workload</span>
                <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem' }}>
                  {workload_metrics?.load_level || 'Moderate'} ({workload_metrics?.workload_score || 35} / 100)
                </p>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {workload_metrics?.class_hours_day || 2}h Classes · {workload_metrics?.scheduled_free_hours_day || 12}h Free
                </span>
              </div>
            </div>
          </div>

          {/* ── 2. Candidate Free Windows ── */}
          <div className="col-4 glass-panel card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="material-symbols-outlined" style={{ color: 'var(--tertiary)', fontSize: '1.5rem' }}>schedule</span>
                <span className="label-sm">Free Windows</span>
              </div>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.35rem', color: 'var(--primary)', marginTop: '0.5rem' }}>
                Ranked Free Slots
              </h3>
              <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Classes and travel periods excluded.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
              {recommended_windows && recommended_windows.length > 0 ? (
                recommended_windows.map((w, idx) => (
                  <div key={idx} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.55rem 0.75rem', background: 'rgba(255,255,255,0.04)', borderRadius: 6,
                    borderLeft: idx === 0 ? '3px solid var(--accent)' : '3px solid rgba(255,255,255,0.1)'
                  }}>
                    <div>
                      <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{w.start_time} - {w.end_time}</span>
                      <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{w.reason}</span>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent)' }}>
                      {w.predicted_effectiveness}%
                    </span>
                  </div>
                ))
              ) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No candidate windows available.</p>
              )}
            </div>

            <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.75rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Twin Retraining: {log_count} / 14 sessions logged ({progress_percentage}%)
              </span>
            </div>
          </div>

          {/* ── 3. Retention & Assessment Trends ── */}
          <div className="col-8 glass-panel card">
            <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.35rem', color: 'var(--primary)', marginBottom: '0.25rem' }}>
              Topic Assessment & Retention History
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
              Observed quiz attempts and topic calibration scores.
            </p>
            {chartData && (
              <div style={{ height: 260 }}>
                <Line 
                  data={chartData} 
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
            )}
          </div>

          {/* ── 4. Study Workspace & Syllabuses (PRD Section 6.6) ── */}
          <div className="col-4 glass-panel card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.35rem', color: 'var(--primary)' }}>Study Workspace</h3>
              <button 
                onClick={() => syllabusInputRef.current?.click()} 
                style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: 'var(--text-primary)', borderRadius: 4, padding: '0.25rem 0.6rem', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                + Add PDF
              </button>
              <input type="file" ref={syllabusInputRef} style={{ display: 'none' }} accept=".pdf" onChange={handleSyllabusUpload} />
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Uploaded lecture & textbook material parsed for RAG quiz generation.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 220, overflowY: 'auto' }}>
              {syllabuses.length > 0 ? (
                syllabuses.map((s, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: 6 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 500 }}>{s.display_name}</span>
                      <span style={{ display: 'block', fontSize: '0.68rem', color: 'var(--accent)' }}>{s.category || 'study_pdf'}</span>
                    </div>
                    <button 
                      onClick={async () => {
                        await deleteSingleSyllabus(s.filename);
                        fetchDashboardData();
                      }}
                      style={{ background: 'transparent', border: 'none', color: '#f87171', fontSize: '0.75rem', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                ))
              ) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No study documents uploaded yet.</p>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

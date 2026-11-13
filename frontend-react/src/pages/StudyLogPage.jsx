import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { addStudySession, getStudySessions, getDashboardMeta } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

export default function StudyLogPage() {
  const [form, setForm] = useState({
    subject: 'Operating Systems',
    topic: 'Virtual Memory & Paging',
    duration_min: '60',
  });
  const [meta, setMeta]       = useState(null);
  const [sessions, setSessions] = useState([]);
  const [msg, setMsg]         = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getDashboardMeta().then(res => setMeta(res.data)).catch(() => {});
    getStudySessions().then(res => setSessions(res.data.sessions || [])).catch(() => {});
  }, []);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg({ type: '', text: '' });
    setLoading(true);
    try {
      await addStudySession(form);
      setMsg({ type: 'success', text: 'Study session recorded and integrated into context.' });
      const res = await getStudySessions();
      setSessions(res.data.sessions || []);
    } catch (err) {
      setMsg({ type: 'error', text: err?.response?.data?.error || 'Failed to save session.' });
    } finally {
      setLoading(false);
    }
  };

  const fatigue = meta?.fatigue_status || {};
  const commute = meta?.commute_status || {};
  const workload = meta?.workload_metrics || {};

  return (
    <div className="page-container ambient-bg">
      <NoiseOverlay />
      <main className="page-main" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2.5rem' }}>

        <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', borderRadius: 'var(--radius-2xl)', padding: '2.5rem 3rem', position: 'relative' }}>
          
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <span className="label-sm" style={{ color: 'var(--tertiary-fixed)', display: 'block', marginBottom: '0.25rem' }}>
              IN-APP STUDY ACTIVITY CAPTURE (PRD SECTION 6.7)
            </span>
            <h1 style={{ fontFamily: 'Newsreader, serif', fontSize: '2.2rem', color: 'var(--primary)', marginBottom: '0.4rem' }}>
              Confirm Study Session
            </h1>
            <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.85rem' }}>
              Review or confirm your academic study block. Physical readiness and commute constraints are automatically derived.
            </p>
          </div>

          {/* ── Context Signals (Derived from Trained Models & Integrations) ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '1rem' }}>
              <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Trained Fatigue State</span>
              <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--accent)', fontSize: '1.05rem' }}>
                {fatigue.fatigue_label || 'A little bit'} ({fatigue.readiness_score || 82}% Readiness)
              </p>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Inferred via Random Forest Model</span>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '1rem' }}>
              <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Android Commute Trip</span>
              <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '1.05rem' }}>
                +{commute.deviation_min || 3} min delay
              </p>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Google Maps expected: {commute.expected_duration_min || 35}m</span>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '1rem' }}>
              <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Academic Timetable Load</span>
              <p style={{ margin: '0.25rem 0 0', fontWeight: 600, color: 'var(--text-primary)', fontSize: '1.05rem' }}>
                {workload.load_level || 'Moderate'} ({workload.workload_score || 35} / 100)
              </p>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{workload.class_hours_day || 2}h scheduled classes</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.5rem' }}>Subject Name</label>
                <input className="ghost-input" name="subject" type="text" value={form.subject} onChange={handleChange} required />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.5rem' }}>Topic / Chapter</label>
                <input className="ghost-input" name="topic" type="text" value={form.topic} onChange={handleChange} required />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.5rem' }}>Active Study Duration (Minutes)</label>
                <input className="ghost-input" name="duration_min" type="number" min="10" max="300" step="5" value={form.duration_min} onChange={handleChange} required />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                <Link to="/quiz-setup" style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                  fontSize: '0.78rem', letterSpacing: '0.05em', textTransform: 'uppercase',
                  color: 'var(--accent)', border: '1px solid var(--accent)',
                  padding: '0.75rem 1rem', borderRadius: 8, textDecoration: 'none',
                }}>
                  Test Topic Retention via Quiz
                </Link>
              </div>
            </div>

            {msg.text && (
              <p className={msg.type === 'error' ? 'msg-error' : 'msg-success'} style={{ textAlign: 'center' }}>
                {msg.text}
              </p>
            )}

            <button className="glow-button" type="submit" disabled={loading} style={{ width: '100%', marginTop: '0.5rem' }}>
              {loading ? 'Confirming…' : 'Confirm & Save Study Session'}
            </button>
          </form>
        </div>

        {/* ── Recent Confirmed Sessions ── */}
        <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', borderRadius: 'var(--radius-xl)', padding: '1.5rem 2rem' }}>
          <h2 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.35rem', color: 'var(--primary)', marginBottom: '1rem' }}>
            Recent Confirmed Sessions
          </h2>
          {sessions.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {sessions.map(s => (
                <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 1rem', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                  <div>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.subject} — {s.topic}</span>
                    <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)' }}>Recorded on {s.created_at}</span>
                  </div>
                  <span style={{ fontSize: '0.85rem', color: 'var(--accent)', fontWeight: 600 }}>
                    {s.duration_min} mins
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No study sessions confirmed yet.</p>
          )}
        </div>

      </main>
    </div>
  );
}

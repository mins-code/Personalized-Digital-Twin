import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { addStudyLog, deleteLog } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

export default function StudyLogPage() {
  const [form, setForm] = useState({
    sleep_hours: '', study_duration: '', study_hour: '10',
    subject_complexity: 'medium', energy_score: '3',
    retention_score: '50',
  });
  const [logs, setLogs]   = useState([]);
  const [msg, setMsg]     = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg({ type: '', text: '' });
    setLoading(true);
    try {
      await addStudyLog(form);
      setMsg({ type: 'success', text: 'Neural Data Synchronized. Your twin is updated.' });
      setForm({ sleep_hours: '', study_duration: '', study_hour: '10', subject_complexity: 'medium', energy_score: '3', retention_score: '50' });
    } catch (err) {
      setMsg({ type: 'error', text: err?.response?.data?.error || 'Failed to save log.' });
    } finally {
      setLoading(false);
    }
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const complexity_labels = { low: 'Low (1)', medium: 'Medium (3)', high: 'High (5)' };

  return (
    <div className="page-container ambient-bg">
      <NoiseOverlay />
      <main className="page-main" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3rem' }}>

        {/* ── Log Form ── */}
        <div className="glass-panel" style={{ width: '100%', maxWidth: '800px', borderRadius: 'var(--radius-2xl)', padding: '3rem 3.5rem', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 0, right: 0, width: '16rem', height: '16rem', background: 'rgba(69,80,31,0.1)', borderRadius: '50%', filter: 'blur(80px)', transform: 'translate(25%,-25%)' }} />

          <div style={{ textAlign: 'center', marginBottom: '2.5rem', position: 'relative', zIndex: 1 }}>
            <h1 style={{ fontFamily: 'Newsreader, serif', fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>Neural Input</h1>
            <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.875rem' }}>Synchronize your daily variables in under 90 seconds.</p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '2rem', position: 'relative', zIndex: 1 }}>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Sleep Duration (Hours)</label>
                <input className="ghost-input" name="sleep_hours" type="number" min="3" max="12" step="0.5" value={form.sleep_hours} onChange={handleChange} placeholder="e.g. 7.5" required />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Study Duration (Hours)</label>
                <input className="ghost-input" name="study_duration" type="number" min="0.1" step="0.1" value={form.study_duration} onChange={handleChange} placeholder="e.g. 2.5" required />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Hour of Day</label>
                <select className="ghost-select" name="study_hour" value={form.study_hour} onChange={handleChange} required>
                  {hours.map(h => (
                    <option key={h} value={h}>{String(h).padStart(2,'0')}:00</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Subject Complexity</label>
                <select className="ghost-select" name="subject_complexity" value={form.subject_complexity} onChange={handleChange} required>
                  <option value="low">Low (Easy)</option>
                  <option value="medium">Medium (Standard)</option>
                  <option value="high">High (Challenging)</option>
                </select>
              </div>
            </div>

            {/* Sliders */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '2rem', paddingTop: '0.5rem' }}>
              {[
                { name: 'energy_score', label: 'Physical Energy & Focus', min: 1, max: 5, lo: 'Drained', hi: 'Peak' },
              ].map(({ name, label, min, max, lo, hi }) => (
                <div key={name} style={{ display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <label className="label-sm">{label}</label>
                    <span style={{ color: 'var(--secondary-fixed)', fontSize: '0.875rem' }}>{form[name]}</span>
                  </div>
                  <input type="range" name={name} min={min} max={max} step="1" value={form[name]} onChange={handleChange} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.625rem', color: 'var(--outline-variant)' }}>
                    <span>{lo}</span><span>{hi}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Retention slider */}
            <div style={{ paddingTop: '1.5rem', paddingBottom: '0.5rem', borderTop: '1px solid rgba(69,71,66,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
                <div>
                  <label className="label-sm" style={{ display: 'block', marginBottom: '0.25rem' }}>Self-Reported Retention</label>
                  <p style={{ color: 'var(--outline)', fontSize: '0.625rem' }}>How well do you feel you absorbed this session?</p>
                </div>
                <span style={{ fontFamily: 'Newsreader, serif', fontSize: '1.5rem', color: 'var(--tertiary-fixed)' }}>{form.retention_score}%</span>
              </div>
              <input type="range" name="retention_score" min="0" max="100" step="1" value={form.retention_score} onChange={handleChange} />
              <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center' }}>
                <Link to="/quiz-setup" style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  fontSize: '0.75rem', letterSpacing: '0.15em', textTransform: 'uppercase',
                  color: 'var(--tertiary-fixed)', border: '1px solid rgba(244,223,203,0.3)',
                  padding: '0.75rem 1.5rem', borderRadius: '9999px', transition: 'all 0.2s',
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '0.875rem' }}>quiz</span>
                  Test your retention score
                </Link>
              </div>
            </div>

            {msg.text && (
              <p className={msg.type === 'error' ? 'msg-error' : 'msg-success'} style={{ textAlign: 'center' }}>
                {msg.text}
              </p>
            )}

            <button className="glow-button" type="submit" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Synchronizing…' : 'Synchronize Log'}
            </button>
          </form>
        </div>

        {/* ── History placeholder ── */}
        <div className="glass-panel" style={{ width: '100%', maxWidth: '900px', borderRadius: 'var(--radius-2xl)', padding: '2rem 2.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid rgba(69,71,66,0.3)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <h2 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.75rem', color: 'var(--primary)' }}>Synchronization History</h2>
              <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.875rem', marginTop: '0.25rem' }}>Review your most recent neural uploads.</p>
            </div>
            <span className="material-symbols-outlined" style={{ color: 'var(--tertiary-fixed)', fontSize: '2rem' }}>history</span>
          </div>
          <p style={{ color: 'var(--outline)', fontSize: '0.875rem', fontStyle: 'italic' }}>
            Recent logs appear here after synchronisation.
          </p>
        </div>

      </main>
    </div>
  );
}


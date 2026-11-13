import { useState } from 'react';
import { Navigate, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NoiseOverlay from '../components/NoiseOverlay';

export default function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ student_id: '', password: '', confirm_password: '' });
  const [error, setError]   = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await register(form.student_id, form.password, form.confirm_password);
      navigate('/dashboard');
    } catch (err) {
      setError(err?.response?.data?.error || 'Registration failed. Try a different Student ID.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container ambient-bg" style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem',
    }}>
      <NoiseOverlay />

      <div className="glass-panel" style={{
        width: '100%', maxWidth: '440px', borderRadius: 'var(--radius-2xl)',
        padding: '3rem 2.5rem', position: 'relative', overflow: 'hidden', zIndex: 10,
      }}>
        <div style={{
          position: 'absolute', top: 0, right: 0, width: '16rem', height: '16rem',
          background: 'rgba(69,80,31,0.1)', borderRadius: '50%', filter: 'blur(80px)',
          transform: 'translate(25%, -25%)',
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          <p className="label-sm text-on-surface-variant mb-4" style={{ textAlign: 'center' }}>
            Initialise Profile
          </p>
          <h1 style={{
            fontFamily: 'Newsreader, serif', fontSize: '2.25rem', textAlign: 'center',
            color: 'var(--primary)', marginBottom: '2.5rem',
          }}>
            Create Account
          </h1>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Student ID</label>
              <input
                className="ghost-input"
                type="text"
                value={form.student_id}
                onChange={e => setForm({ ...form, student_id: e.target.value })}
                placeholder="Choose a unique student ID"
                required
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Password</label>
              <input
                className="ghost-input"
                type="password"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label className="label-sm" style={{ marginBottom: '0.75rem' }}>Confirm Password</label>
              <input
                className="ghost-input"
                type="password"
                value={form.confirm_password}
                onChange={e => setForm({ ...form, confirm_password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>

            {error && <p className="msg-error" style={{ textAlign: 'center' }}>{error}</p>}

            <button className="glow-button" type="submit" disabled={loading} style={{ marginTop: '0.5rem' }}>
              {loading ? 'Initialising Twin…' : 'Initialise Neural Twin'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '2rem', fontSize: '0.875rem', color: 'var(--on-surface-variant)' }}>
            Already have a profile?{' '}
            <Link to="/login" style={{ color: 'var(--secondary-fixed)', textDecoration: 'underline' }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}


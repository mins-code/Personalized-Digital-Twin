import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NoiseOverlay from '../components/NoiseOverlay';

const features = [
  {
    icon: 'psychology',
    title: 'Personalised Prediction',
    desc: 'Your own retention model learns from your quiz history and study context to predict when you study most effectively.',
  },
  {
    icon: 'auto_stories',
    title: 'Study Workspace',
    desc: 'Upload lecture PDFs, generate topic quizzes and get source-grounded summaries — all from your own material.',
  },
  {
    icon: 'schedule',
    title: 'Smart Window Planner',
    desc: 'Compare candidate study times against your predicted retention, workload and schedule to find the best window.',
  },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="page-container ambient-bg" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <NoiseOverlay />

      {/* ── Hero ── */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8rem 1.5rem 4rem',
        textAlign: 'center',
        position: 'relative',
        zIndex: 10,
      }}>
        {/* Logo label */}
        <p className="label-sm text-on-surface-variant mb-6" style={{ letterSpacing: '0.3em' }}>
          Cognitive Digital Twin
        </p>

        <h1 style={{
          fontFamily: 'Newsreader, serif',
          fontSize: 'clamp(3rem, 8vw, 5.5rem)',
          fontWeight: 300,
          lineHeight: 1.1,
          letterSpacing: '-0.02em',
          color: 'var(--primary)',
          marginBottom: '1.5rem',
          maxWidth: '800px',
        }}>
          CogniSync
        </h1>

        <p style={{
          fontFamily: 'Manrope, sans-serif',
          fontSize: '1.125rem',
          lineHeight: 1.6,
          fontWeight: 300,
          color: 'var(--on-surface-variant)',
          maxWidth: '580px',
          marginBottom: '3rem',
        }}>
          Predict your quiz performance. Discover your best study windows.
          Adapt your learning with a personalised AI model that grows with you.
        </p>

        <div className="flex gap-4" style={{ flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link to="/register" className="glow-button" style={{ minWidth: '180px' }}>
            Create Profile
          </Link>
          <Link to="/login" style={{
            padding: '1rem 2rem', borderRadius: 'var(--radius-xl)',
            border: '1px solid rgba(215,195,176,0.3)',
            color: 'var(--tertiary-fixed)', fontSize: '0.75rem',
            letterSpacing: '0.15em', textTransform: 'uppercase', fontWeight: 600,
            transition: 'all 0.3s',
          }}>
            Sign In
          </Link>
        </div>
      </main>

      {/* ── Feature cards ── */}
      <section style={{
        maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem 5rem',
        width: '100%', position: 'relative', zIndex: 10,
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {features.map(({ icon, title, desc }) => (
            <div key={title} className="glass-panel" style={{ borderRadius: 'var(--radius-2xl)', padding: '2rem' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '2rem', color: 'var(--tertiary)', marginBottom: '1rem', display: 'block' }}>
                {icon}
              </span>
              <h3 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.25rem', color: 'var(--primary)', marginBottom: '0.75rem' }}>
                {title}
              </h3>
              <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.9rem', lineHeight: 1.6 }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}


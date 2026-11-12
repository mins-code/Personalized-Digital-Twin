export default function LoadingSpinner({ message = 'Loading…' }) {
  return (
    <div style={{
      minHeight: '60vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: '1rem',
    }}>
      <span
        className="material-symbols-outlined spin"
        style={{ fontSize: '2.5rem', color: 'var(--tertiary-fixed)' }}
      >
        sync
      </span>
      <p className="label-sm" style={{ color: 'var(--on-surface-variant)' }}>
        {message}
      </p>
    </div>
  );
}


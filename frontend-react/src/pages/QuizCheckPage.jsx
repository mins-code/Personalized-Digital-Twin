import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import NoiseOverlay from '../components/NoiseOverlay';

export default function QuizCheckPage() {
  const location = useLocation();
  const { score, total, message } = location.state || {};

  return (
    <div className="page-main">
      <NoiseOverlay />
      <div className="ambient-bg" />

      <div style={{ maxWidth: 640, margin: '0 auto', padding: '3rem 1.5rem' }}>
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 2.5rem' }}>
          {/* Icon */}
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            background: 'rgba(var(--accent-rgb, 180,145,90), 0.15)',
            border: '2px solid rgba(var(--accent-rgb, 180,145,90), 0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.75rem',
            fontSize: '2rem',
          }}>
            🎯
          </div>

          <h1 className="newsreader" style={{ fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            Quiz Complete
          </h1>

          {score !== undefined && total !== undefined ? (
            <>
              <p style={{ color: 'var(--text-muted)', marginBottom: '0.25rem', fontSize: '0.95rem' }}>
                Your score
              </p>
              <div style={{
                fontSize: '3.5rem', fontWeight: 700, letterSpacing: '-1px',
                color: 'var(--accent)',
                lineHeight: 1.1,
                margin: '0.5rem 0 1.25rem',
              }}>
                {score} <span style={{ fontSize: '1.5rem', color: 'var(--text-muted)', fontWeight: 400 }}>/ {total}</span>
              </div>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)', margin: '1rem 0 1.5rem' }}>
              Your results have been recorded.
            </p>
          )}

          {message && (
            <div style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 10,
              padding: '0.85rem 1.25rem',
              marginBottom: '2rem',
              fontSize: '0.92rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
            }}>
              {message}
            </div>
          )}

          {!message && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '2rem', lineHeight: 1.6 }}>
              Great work! Consistent quizzing helps reinforce memory consolidation and spaced-repetition benefits.
              Keep logging your study sessions to improve your retention predictions.
            </p>
          )}

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/quiz-setup" className="glow-button" style={{ textDecoration: 'none' }}>
              Take Another Quiz
            </Link>
            <Link to="/dashboard" style={{
              padding: '0.65rem 1.5rem',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.12)',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              fontSize: '0.9rem',
              transition: 'border-color 0.2s, color 0.2s',
            }}>
              Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Tip card */}
        <div className="glass-panel" style={{ marginTop: '1.25rem', padding: '1.25rem 1.5rem' }}>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>💡 Tip: </span>
            Your quiz score is factored into CogniSync's retention calibration. The more quizzes you take,
            the more accurate your predicted retention windows become.
          </p>
        </div>
      </div>
    </div>
  );
}


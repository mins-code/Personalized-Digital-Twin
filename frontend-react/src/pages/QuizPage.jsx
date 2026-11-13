import { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { submitQuizScore } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

export default function QuizPage() {
  const location = useLocation();
  const navigate  = useNavigate();
  const questions = location.state?.questions || [];
  const topic     = location.state?.topic     || 'Quiz';

  const [answers,  setAnswers]  = useState({});   // { qIdx: optionString }
  const [revealed, setRevealed] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [calibrateMsg, setCalibrateMsg] = useState('');
  const [score, setScore] = useState(null);

  const totalQ   = questions.length;
  const answered = Object.keys(answers).length;

  const selectAnswer = (qIdx, opt) => {
    if (revealed) return;
    setAnswers(prev => ({ ...prev, [qIdx]: opt }));
  };

  const handleReveal = () => setRevealed(true);

  const calculateScore = () => {
    let correct = 0;
    questions.forEach((q, i) => {
      if (answers[i] === q.answer) correct++;
    });
    return Math.round((correct / totalQ) * 100);
  };

  const handleSubmitScore = async () => {
    setSubmitting(true);
    const pct = calculateScore();
    setScore(pct);
    try {
      const res = await submitQuizScore(pct);
      setCalibrateMsg(res.data.message || `Score: ${pct}% — Neural calibration complete.`);
    } catch (err) {
      setCalibrateMsg(`Score: ${pct}% — Calibration unavailable (no active study log).`);
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  };

  if (totalQ === 0) {
    return (
      <div className="page-container ambient-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <NoiseOverlay />
        <div className="glass-panel" style={{ borderRadius: 'var(--radius-2xl)', padding: '3rem', textAlign: 'center', maxWidth: '480px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '3rem', color: 'var(--outline)', display: 'block', marginBottom: '1rem' }}>quiz</span>
          <h2 style={{ fontFamily: 'Newsreader, serif', fontSize: '1.75rem', color: 'var(--primary)', marginBottom: '1rem' }}>No questions generated.</h2>
          <p style={{ color: 'var(--on-surface-variant)', marginBottom: '1.5rem' }}>Go back to Quiz Setup and configure your quiz.</p>
          <Link to="/quiz-setup" className="glow-button">Back to Setup</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container ambient-bg">
      <NoiseOverlay />
      <main className="page-main" style={{ maxWidth: '860px' }}>

        {/* Header */}
        <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
          <h1 style={{ fontFamily: 'Newsreader, serif', fontSize: '2.5rem', color: 'var(--primary)' }}>
            {topic}
          </h1>
          <p className="label-sm" style={{ marginTop: '0.5rem' }}>
            {answered}/{totalQ} answered
          </p>
        </div>

        {/* Questions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '2.5rem' }}>
          {questions.map((q, qIdx) => {
            const userAnswer   = answers[qIdx];
            const correctAnswer = q.answer;

            return (
              <div key={qIdx} className="glass-panel" style={{ borderRadius: 'var(--radius-2xl)', padding: '1.75rem' }}>
                <p style={{ fontFamily: 'Newsreader, serif', fontSize: '1.2rem', color: 'var(--primary)', marginBottom: '1.25rem', lineHeight: 1.4 }}>
                  {qIdx + 1}. {q.question}
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                  {q.options.map((opt, oIdx) => {
                    let extraClass = '';
                    if (revealed) {
                      if (opt === correctAnswer) extraClass = ' correct';
                      else if (opt === userAnswer && opt !== correctAnswer) extraClass = ' incorrect';
                    } else if (opt === userAnswer) {
                      extraClass = ' selected';
                    }
                    return (
                      <div
                        key={oIdx}
                        className={`quiz-option${extraClass}`}
                        onClick={() => selectAnswer(qIdx, opt)}
                      >
                        <span style={{
                          width: '1.5rem', height: '1.5rem', borderRadius: '50%',
                          border: '1px solid rgba(69,71,66,0.6)', display: 'flex',
                          alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                          fontSize: '0.75rem', color: 'var(--on-surface-variant)',
                        }}>
                          {String.fromCharCode(65 + oIdx)}
                        </span>
                        <span style={{ fontSize: '0.9rem', color: 'var(--on-surface-variant)' }}>{opt}</span>
                        {revealed && opt === correctAnswer && (
                          <span className="material-symbols-outlined" style={{ marginLeft: 'auto', color: 'var(--secondary-fixed)', fontSize: '1.125rem' }}>check_circle</span>
                        )}
                        {revealed && opt === userAnswer && opt !== correctAnswer && (
                          <span className="material-symbols-outlined" style={{ marginLeft: 'auto', color: 'var(--error)', fontSize: '1.125rem' }}>cancel</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Controls */}
        {!submitted ? (
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            {!revealed ? (
              <button
                className="glow-button"
                onClick={handleReveal}
                disabled={answered < totalQ}
                style={{ minWidth: '200px' }}
              >
                {answered < totalQ ? `Answer all ${totalQ} questions first` : 'Reveal Answers'}
              </button>
            ) : (
              <button
                className="glow-button"
                onClick={handleSubmitScore}
                disabled={submitting}
                style={{ minWidth: '200px' }}
              >
                {submitting ? 'Calibrating…' : 'Submit & Calibrate Twin'}
              </button>
            )}
          </div>
        ) : (
          <div style={{
            padding: '2rem', borderRadius: 'var(--radius-2xl)',
            background: 'rgba(69,80,31,0.2)', border: '1px solid rgba(219,233,169,0.3)',
            textAlign: 'center',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '3rem', color: 'var(--secondary-fixed)', display: 'block', marginBottom: '0.75rem' }}>check_circle</span>
            <p style={{ fontFamily: 'Newsreader, serif', fontSize: '2rem', color: 'var(--tertiary-fixed)', marginBottom: '0.5rem' }}>
              Score: {score}%
            </p>
            <p style={{ color: 'var(--on-surface-variant)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>{calibrateMsg}</p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link to="/quiz-setup" className="glow-button">New Quiz</Link>
              <Link to="/dashboard" style={{
                padding: '0.875rem 1.75rem', border: '1px solid rgba(215,195,176,0.3)',
                borderRadius: 'var(--radius-xl)', color: 'var(--tertiary-fixed)',
                fontSize: '0.75rem', letterSpacing: '0.15em', textTransform: 'uppercase',
              }}>
                Dashboard
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}


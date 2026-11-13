import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateQuiz, listSyllabuses } from '../api';
import NoiseOverlay from '../components/NoiseOverlay';

export default function QuizSetupPage() {
  const navigate = useNavigate();
  const [topic, setTopic]       = useState('');
  const [difficulty, setDiff]   = useState('medium');
  const [quantity, setQuantity] = useState(5);
  const [syllabuses, setSyllabuses] = useState([]);
  const [selected, setSelected]     = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  useEffect(() => {
    listSyllabuses()
      .then(res => {
        const files = res.data.syllabuses || [];
        setSyllabuses(files);
        setSelected(files.map(f => f.filename));  // select all by default
      })
      .catch(() => {});
  }, []);

  const toggleFile = (filename) => {
    setSelected(prev =>
      prev.includes(filename) ? prev.filter(f => f !== filename) : [...prev, filename]
    );
  };

  const handleBeginScan = async () => {
    if (!topic.trim()) { setError('Please enter a topic focus.'); return; }
    setError('');
    setLoading(true);
    try {
      const res = await generateQuiz(topic, selected, quantity, difficulty);
      navigate('/quiz', { state: { questions: res.data.questions, topic } });
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to generate quiz. Make sure a syllabus is uploaded.');
    } finally {
      setLoading(false);
    }
  };

  const diffs = ['easy', 'medium', 'hard'];

  return (
    <div className="page-container ambient-bg" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '5rem 1.5rem' }}>
      <NoiseOverlay />

      <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', borderRadius: '1.75rem', padding: '2.5rem', position: 'relative', overflow: 'hidden', zIndex: 10 }}>
        <div style={{ position: 'absolute', top: 0, right: 0, width: '16rem', height: '16rem', background: 'rgba(69,80,31,0.1)', borderRadius: '50%', filter: 'blur(80px)', transform: 'translate(25%,-25%)' }} />

        <h1 style={{ fontFamily: 'Newsreader, serif', fontSize: '2.5rem', textAlign: 'center', color: 'var(--secondary-fixed)', marginBottom: '2.5rem', textShadow: '0 0 15px rgba(219,233,169,0.3)', position: 'relative', zIndex: 1 }}>
          Quiz Parameters
        </h1>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem', position: 'relative', zIndex: 1 }}>

          {/* Topic */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <label className="label-sm" style={{ marginBottom: '1rem', color: 'var(--tertiary-fixed)' }}>Topic Focus</label>
            <input
              className="ghost-input"
              type="text"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="e.g. Cellular Respiration or 'all topics'"
            />
          </div>

          {/* Difficulty */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <label className="label-sm" style={{ marginBottom: '1rem', color: 'var(--tertiary-fixed)' }}>Complexity Depth</label>
            <div className="diff-toggle">
              {diffs.map(d => (
                <button
                  key={d}
                  className={`diff-btn${difficulty === d ? ' active' : ''}`}
                  onClick={() => setDiff(d)}
                  type="button"
                >
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Quantity */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <label className="label-sm" style={{ marginBottom: '1rem', color: 'var(--tertiary-fixed)' }}>Question Quantity</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <input
                className="ghost-input"
                type="number"
                min="1"
                max="20"
                value={quantity}
                onChange={e => setQuantity(parseInt(e.target.value) || 5)}
                style={{ maxWidth: '5rem' }}
              />
              <span style={{ fontSize: '0.75rem', color: 'rgba(219,233,169,0.6)', textTransform: 'uppercase', letterSpacing: '0.15em' }}>Questions</span>
            </div>
          </div>

          {/* File selection */}
          {syllabuses.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label className="label-sm" style={{ marginBottom: '1rem', color: 'var(--tertiary-fixed)' }}>Syllabus Source</label>
              {syllabuses.map(s => (
                <label key={s.filename} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem', cursor: 'pointer', fontSize: '0.875rem', color: 'var(--on-surface-variant)' }}>
                  <input
                    type="checkbox"
                    checked={selected.includes(s.filename)}
                    onChange={() => toggleFile(s.filename)}
                    style={{ accentColor: 'var(--secondary-fixed)', width: '1rem', height: '1rem' }}
                  />
                  {s.display_name}
                </label>
              ))}
            </div>
          )}

          {error && <p className="msg-error" style={{ textAlign: 'center' }}>{error}</p>}

          <button
            className="glow-button"
            onClick={handleBeginScan}
            disabled={loading}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', paddingTop: '1.25rem', paddingBottom: '1.25rem' }}
          >
            <span className="material-symbols-outlined" style={{ transition: 'transform 0.7s', transform: loading ? 'rotate(180deg)' : 'none' }}>radar</span>
            {loading ? 'Scanning Neural Memory…' : 'Begin Neural Scan'}
          </button>
        </div>
      </div>
    </div>
  );
}


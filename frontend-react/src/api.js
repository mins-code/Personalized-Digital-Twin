import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '',
  withCredentials: true,  // send Flask session cookie on every request
});

/* ── Auth ───────────────────────────────────────────────── */

export const loginUser = (student_id, password) => {
  const fd = new FormData();
  fd.append('student_id', student_id);
  fd.append('password', password);
  return api.post('/login', fd);
};

export const registerUser = (student_id, password, confirm_password) => {
  const fd = new FormData();
  fd.append('student_id', student_id);
  fd.append('password', password);
  fd.append('confirm_password', confirm_password);
  return api.post('/register', fd);
};

export const logoutUser = () => api.get('/logout');

export const getCurrentUser = () => api.get('/api/me');

/* ── Dashboard ──────────────────────────────────────────── */

export const getDashboardStats = () => api.get('/api/dashboard-stats');

// NOTE: The Flask backend renders best_time/log_count/shap_path via the
// HTML template. A /api/dashboard-meta endpoint should be added to Flask
// so the React client can fetch these values as JSON. For now we fall back
// to hardcoded defaults while that endpoint exists.
export const getDashboardMeta = () => api.get('/api/dashboard-meta').catch(() => ({
  data: { student_id: '', best_time: '10:00', log_count: 0, progress_percentage: 0, shap_path: '' }
}));

/* ── Study Logs ─────────────────────────────────────────── */

export const addStudyLog = (fields) => {
  const fd = new FormData();
  Object.entries(fields).forEach(([k, v]) => fd.append(k, v));
  return api.post('/log', fd);
};

export const getStudyLogs = () => api.get('/api/study-logs').catch(() => ({ data: { logs: [] } }));

export const deleteLog = (log_id) => api.post(`/log/${log_id}/delete`);

/* ── Simulator ──────────────────────────────────────────── */

export const predictInstant = (data) => api.post('/api/predict-instant', data);

/* ── Syllabus / RAG ─────────────────────────────────────── */

export const uploadSyllabus = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return api.post('/api/upload-syllabus', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const listSyllabuses = () => api.get('/api/syllabuses');

export const deleteSyllabus = () => api.post('/api/delete-syllabus');

export const deleteSingleSyllabus = (filename) =>
  api.post('/api/delete-single-syllabus', { filename });

/* ── Quiz ────────────────────────────────────────────────── */

export const generateQuiz = (topic, selected_files, quantity, difficulty) =>
  api.post('/api/generate-quiz', { topic, selected_files, quantity, difficulty });

export const submitQuizScore = (score) => api.post('/api/submit-quiz-score', { score });

export default api;


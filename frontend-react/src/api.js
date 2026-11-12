import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '',
  withCredentials: true,
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

/* ── Dashboard & Context ────────────────────────────────── */
export const getDashboardStats = () => api.get('/api/dashboard-stats');
export const getDashboardMeta = () => api.get('/api/dashboard-meta');

/* ── Timetable & Academic Calendar ──────────────────────── */
export const getAcademicEvents = () => api.get('/api/academic-events');
export const addAcademicEvent = (event) => api.post('/api/academic-events', event);
export const uploadSchedulePDF = (file, category) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('category', category); // 'timetable' or 'calendar'
  return api.post('/api/upload-schedule', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

/* ── Commute Tracking ───────────────────────────────────── */
export const getCommuteRecords = () => api.get('/api/commute');
export const addCommuteRecord = (data) => api.post('/api/commute', data);

/* ── In-App Study Sessions ──────────────────────────────── */
export const getStudySessions = () => api.get('/api/study-sessions');
export const addStudySession = (data) => api.post('/api/study-sessions', data);

/* ── What-If Simulator ──────────────────────────────────── */
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

export const submitQuizScore = (score, topic, difficulty, total_questions) => 
  api.post('/api/submit-quiz-score', { score, topic, difficulty, total_questions });

export default api;

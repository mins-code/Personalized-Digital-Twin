# CogniSync: Integrated Full-Stack Application

This repository contains the complete, PRD-compliant CogniSync system connecting the React frontend, the Flask backend, and the trained Machine Learning & Fatigue Models.

---

## Architecture Overview

1. **`frontend-react/`**: React 18 single-page application using React Router v6, Chart.js, and responsive glass-morphism styling.
2. **`backend/`**: Lightweight Flask server implementing RESTful endpoints strictly aligned with PRD v1.2:
   - Session-based pseudonymous authentication (`/register`, `/login`, `/logout`, `/api/me`)
   - Study log synchronization without mood/stress variables (`/log`, `/api/study-logs`)
   - Dashboard statistics & meta indicators (`/api/dashboard-stats`, `/api/dashboard-meta`)
   - What-If Simulator with circadian and sleep sweeps (`/api/predict-instant`)
   - RAG syllabus indexing and PDF text extraction via PyMuPDF (`/api/upload-syllabus`, `/api/syllabuses`)
   - AI quiz question generator and objective calibration (`/api/generate-quiz`, `/api/submit-quiz-score`)
3. **`fatigue_model/`**: Trained Random Forest (`random_forest_model.joblib`) and Logistic Regression models evaluated on 16 physiological & behavioural features. The backend dynamically uses these models to provide non-clinical fatigue status on the dashboard (PRD Section 6.10).

---

## How to Run Backend and Frontend Together

### Terminal 1: Start the Backend (Port 5000)

```powershell
cd backend
python app.py
```

You should see:
```text
============================================================
CogniSync Backend Server starting on http://localhost:5000
Connected to PRD v1.2 Specifications & Fatigue Models
============================================================
```

### Terminal 2: Start the React Frontend (Port 3000)

```powershell
cd frontend-react
npm install
npm start
```

The frontend will start at **http://localhost:3000** and automatically route API requests to the Flask server at **http://localhost:5000** through the configured proxy.


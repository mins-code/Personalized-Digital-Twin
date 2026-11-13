# CogniSync — React Frontend

A complete React frontend for CogniSync, integrated with the existing Flask backend.

## Quick Start

```bash
# 1. Install dependencies
cd frontend-react
npm install

# 2. Start the React dev server (Flask must be running simultaneously)
npm start
```

The dev server starts at **http://localhost:3000** and proxies all `/api/*` and Flask route calls to **http://localhost:5000** (the Flask backend).

## Prerequisites

- **Node.js ≥ 18** and npm
- **Flask backend** running at `localhost:5000`
  - `cd ../cognisync && python backend/app.py` (adjust path as needed)

## Environment

Copy `.env.example` to `.env` if you need to point to a non-default backend:

```bash
cp .env.example .env
# Then edit REACT_APP_API_BASE_URL if needed
```

## Pages & Flask Routes

| Page | Path | Flask Route(s) |
|------|------|----------------|
| Landing | `/` | — |
| Login | `/login` | `POST /login` |
| Register | `/register` | `POST /register` |
| Dashboard | `/dashboard` | `GET /api/dashboard-stats`, `GET/POST/DELETE /api/syllabuses`, `POST /api/upload-syllabus` |
| Study Log | `/log` | `GET /log`, `POST /log` |
| Quiz Setup | `/quiz-setup` | `GET /api/syllabuses`, `POST /api/generate-quiz` |
| Quiz | `/quiz` | `POST /api/submit-quiz-score` |
| Quiz Review | `/quiz-check` | — (score passed via router state) |
| Analytics | `/analytics` | `GET /api/dashboard-stats` |
| Simulator | `/simulator` | `POST /api/predict-instant` |

## Known Limitations

- **`/api/dashboard-meta` does not exist** in the current Flask backend. The Dashboard page shows placeholder values (`best_time`, `log_count`, `progress_percentage`) until this endpoint is added to Flask.
- **SHAP image** (`/static/<student_id>_shap.png`) is served by Flask — will only appear after at least 7 logs trigger model retraining.
- **Study Planner** page is not yet implemented as a separate page; recommended windows are surfaced on the Dashboard via the best-time indicator.

## Project Structure

```
frontend-react/
├── public/
│   └── index.html          # Google Fonts: Newsreader, Manrope, Material Symbols
├── src/
│   ├── api.js              # Axios instance + all named API functions
│   ├── App.jsx             # React Router v6 routes + AuthGuard
│   ├── App.css             # Full design system (glass panels, tokens, animations)
│   ├── index.jsx           # ReactDOM.createRoot entry
│   ├── contexts/
│   │   └── AuthContext.jsx # Auth state, login/register/logout
│   ├── components/
│   │   ├── AuthGuard.jsx
│   │   ├── Navbar.jsx
│   │   ├── LoadingSpinner.jsx
│   │   └── NoiseOverlay.jsx
│   └── pages/
│       ├── LandingPage.jsx
│       ├── LoginPage.jsx
│       ├── RegisterPage.jsx
│       ├── DashboardPage.jsx
│       ├── StudyLogPage.jsx
│       ├── QuizSetupPage.jsx
│       ├── QuizPage.jsx
│       ├── QuizCheckPage.jsx
│       ├── SimulatorPage.jsx
│       └── AnalyticsPage.jsx
├── .env.example
├── package.json
└── README.md
```

## Design System

Replicates the existing CogniSync visual language:
- **Background:** dark olive + charcoal (`#1a1f14` → `#0f120b`)
- **Accent:** muted bronze (`#b4915a`)
- **Typography:** Newsreader (headings) + Manrope (body)
- **Glass panels:** `backdrop-filter: blur` with subtle border
- **Noise overlay:** procedural grain texture for depth


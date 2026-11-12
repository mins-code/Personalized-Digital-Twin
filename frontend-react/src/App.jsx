import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AuthGuard from './components/AuthGuard';
import Navbar from './components/Navbar';
import NoiseOverlay from './components/NoiseOverlay';

import LandingPage    from './pages/LandingPage';
import LoginPage      from './pages/LoginPage';
import RegisterPage   from './pages/RegisterPage';
import DashboardPage  from './pages/DashboardPage';
import StudyLogPage   from './pages/StudyLogPage';
import QuizCheckPage  from './pages/QuizCheckPage';
import QuizSetupPage  from './pages/QuizSetupPage';
import QuizPage       from './pages/QuizPage';
import SimulatorPage  from './pages/SimulatorPage';
import AnalyticsPage  from './pages/AnalyticsPage';

export default function App() {
  return (
    <AuthProvider>
      <NoiseOverlay />
      <Navbar />
      <Routes>
        {/* Public */}
        <Route path="/"         element={<LandingPage />} />
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected */}
        <Route path="/dashboard" element={<AuthGuard><DashboardPage /></AuthGuard>} />
        <Route path="/log"       element={<AuthGuard><StudyLogPage /></AuthGuard>} />
        <Route path="/quiz-check" element={<AuthGuard><QuizCheckPage /></AuthGuard>} />
        <Route path="/quiz-setup" element={<AuthGuard><QuizSetupPage /></AuthGuard>} />
        <Route path="/quiz"       element={<AuthGuard><QuizPage /></AuthGuard>} />
        <Route path="/simulator"  element={<AuthGuard><SimulatorPage /></AuthGuard>} />
        <Route path="/analytics"  element={<AuthGuard><AnalyticsPage /></AuthGuard>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}


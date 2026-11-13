import os
import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'cognisync.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users table (pseudonymous student ID per PRD FR-AUTH-02)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        home_location TEXT,
        college_location TEXT,
        commute_tracking_opt_in INTEGER DEFAULT 0,
        google_health_connected INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Study Sessions / In-app Activity & Confirmed Sessions (PRD Section 6.7)
    # Strictly NO mood, NO stress.
    # Inputs: subject, topic, start_time, duration_min, is_confirmed
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        topic TEXT,
        start_time TIMESTAMP NOT NULL,
        duration_min REAL NOT NULL,
        is_confirmed INTEGER DEFAULT 1,
        source TEXT DEFAULT 'in_app', -- 'in_app_observed', 'student_confirmed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 3. Google Health API Ingestion (PRD Section 6.2)
    # Stores consented sleep and physical activity records (NO mood, NO stress)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        record_date TEXT NOT NULL, -- YYYY-MM-DD
        sleep_duration_min REAL,
        sleep_efficiency_pct REAL,
        sleep_onset_latency_min REAL,
        total_steps REAL,
        active_minutes REAL,
        resting_hr_bpm REAL,
        hr_mean_bpm REAL,
        fitbit_wear_fraction REAL DEFAULT 0.95,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 4. Academic Timetable & Calendar Events (PRD Section 6.3 & 6.4)
    # Uploaded via PDF or added/confirmed by student
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS academic_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        subject TEXT,
        event_type TEXT NOT NULL, -- class, exam, deadline, holiday, project
        day_of_week INTEGER,      -- 0=Monday, 6=Sunday for recurring classes
        start_time TEXT,          -- HH:MM
        end_time TEXT,            -- HH:MM
        event_date TEXT,          -- YYYY-MM-DD for one-off exams/deadlines
        is_confirmed INTEGER DEFAULT 1,
        source_doc TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 5. Commute Tracking Records (PRD Section 6.5)
    # Android geofence detection + Google Maps comparison
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS commute_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        trip_date TEXT NOT NULL,
        direction TEXT NOT NULL, -- home_to_college, college_to_home
        expected_duration_min REAL NOT NULL, -- from Google Maps Routes API
        actual_duration_min REAL NOT NULL,   -- detected by Android geofence
        deviation_min REAL NOT NULL,         -- actual - expected
        is_confirmed INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 6. Quizzes & Retention Assessments (PRD Section 6.6, 6.8 & 6.9)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        score REAL NOT NULL,
        total_questions INTEGER NOT NULL,
        is_delayed_retention INTEGER DEFAULT 0,
        linked_study_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 7. Syllabuses / PDF Study Material (PRD Section 6.6)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS syllabuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        display_name TEXT NOT NULL,
        category TEXT DEFAULT 'syllabus', -- 'timetable', 'calendar', 'study_pdf'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database schema successfully upgraded and verified for PRD v1.2 specifications.")

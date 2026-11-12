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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Study Sessions / Logs (Strictly PRD-compliant: NO mood, NO stress)
    # Features: sleep_hours, energy_score, study_hour, study_duration, subject_difficulty, retention_score
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sleep_hours REAL NOT NULL,
        energy_score REAL NOT NULL,
        study_hour INTEGER NOT NULL,
        study_duration REAL NOT NULL,
        subject_difficulty REAL NOT NULL,
        retention_score REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 3. Quizzes & Attempts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        difficulty REAL NOT NULL,
        score REAL NOT NULL,
        total_questions INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 4. Syllabuses / Document Metadata
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS syllabuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        display_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # 5. Academic Timetable & Calendar Events (PRD Section 6.3 & 6.4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS academic_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        event_type TEXT NOT NULL, -- class, exam, deadline, holiday
        day_of_week INTEGER,     -- 0=Monday, 6=Sunday for recurring
        start_time TEXT,         -- HH:MM
        end_time TEXT,           -- HH:MM
        event_date TEXT,         -- YYYY-MM-DD for one-off events
        weight REAL DEFAULT 1.0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)


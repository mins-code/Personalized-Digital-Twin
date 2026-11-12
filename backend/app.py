import os
import json
import sqlite3
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, session, make_response
from flask_cors import CORS

from db import init_db, get_db, hash_password, check_password
from models import estimate_fatigue, predict_retention_instant
from rag_engine import extract_text_from_pdf, generate_quiz_questions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cognisync-prd-v1.2-secure-key'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set False for localhost development

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# Enable CORS for React dev server on localhost:3000
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Ensure DB tables are initialized
init_db()

# ── Helpers ────────────────────────────────────────────────────────
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

# ── Auth Endpoints ─────────────────────────────────────────────────
@app.route('/register', methods=['POST'])
def register():
    # Support both FormData (from React api.js) and JSON
    student_id = request.form.get('student_id') or (request.json and request.json.get('student_id'))
    password = request.form.get('password') or (request.json and request.json.get('password'))
    confirm_password = request.form.get('confirm_password') or (request.json and request.json.get('confirm_password'))

    if not student_id or not password:
        return jsonify({'error': 'Student ID and password are required'}), 400

    if confirm_password and password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE student_id = ?', (student_id,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Student ID already registered'}), 400

    hashed = hash_password(password)
    cur = conn.cursor()
    cur.execute('INSERT INTO users (student_id, password_hash) VALUES (?, ?)', (student_id, hashed))
    new_user_id = cur.lastrowid
    conn.commit()
    conn.close()

    session['user_id'] = new_user_id
    session['student_id'] = student_id
    return jsonify({'success': True, 'student_id': student_id, 'message': 'Registration successful'})

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form.get('student_id') or (request.json and request.json.get('student_id'))
    password = request.form.get('password') or (request.json and request.json.get('password'))

    if not student_id or not password:
        return jsonify({'error': 'Student ID and password are required'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE student_id = ?', (student_id,)).fetchone()
    conn.close()

    if not user or not check_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid student ID or password'}), 401

    session['user_id'] = user['id']
    session['student_id'] = user['student_id']
    return jsonify({'success': True, 'student_id': user['student_id'], 'message': 'Login successful'})

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 401
    return jsonify({
        'authenticated': True,
        'student_id': user['student_id'],
        'id': user['id']
    })

# ── Dashboard & Meta Endpoints ─────────────────────────────────────
@app.route('/api/dashboard-meta', methods=['GET'])
def dashboard_meta():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    logs = conn.execute('SELECT * FROM study_logs WHERE user_id = ? ORDER BY id DESC', (user['id'],)).fetchall()
    log_count = len(logs)
    progress_percentage = min(round((log_count / 14.0) * 100), 100)

    # Determine recommended best study time window (PRD FR-REC-01 to FR-REC-04)
    best_time = "10:00"
    if logs:
        # Check historical retention scores by hour
        hour_retention = {}
        for l in logs:
            h = l['study_hour']
            hour_retention.setdefault(h, []).append(l['retention_score'])
        if hour_retention:
            best_hour = max(hour_retention.keys(), key=lambda h: sum(hour_retention[h])/len(hour_retention[h]))
            best_time = f"{best_hour:02d}:00"

    # Contextual Fatigue estimation using our trained Random Forest model (PRD Section 6.10)
    last_log = logs[0] if logs else None
    context = {
        'sleep_hours': last_log['sleep_hours'] if last_log else 7.0,
        'energy_score': last_log['energy_score'] if last_log else 3.0
    }
    fatigue_status = estimate_fatigue(context)

    conn.close()

    return jsonify({
        'student_id': user['student_id'],
        'best_time': best_time,
        'log_count': log_count,
        'progress_percentage': progress_percentage,
        'shap_path': '',
        'fatigue_status': fatigue_status
    })

@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    logs = conn.execute(
        'SELECT id, retention_score FROM study_logs WHERE user_id = ? ORDER BY id DESC LIMIT 7',
        (user['id'],)
    ).fetchall()
    conn.close()

    logs = list(reversed(logs))
    if not logs:
        return jsonify({
            'labels': ['Baseline Session'],
            'scores': [65.0]
        })

    return jsonify({
        'labels': [f"Log {l['id']}" for l in logs],
        'scores': [round(float(l['retention_score']), 1) for l in logs]
    })

# ── Study Logging (Strictly PRD-Compliant: NO mood, NO stress) ─────
@app.route('/log', methods=['POST'])
def add_study_log():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Read from FormData or JSON
    data = request.form if request.form else (request.json or {})
    
    try:
        sleep_hours = float(data.get('sleep_hours', 7.0))
        energy_score = float(data.get('energy_score', 3.0))
        study_hour = int(data.get('study_hour', 10))
        study_duration = float(data.get('study_duration', 2.0))
        
        complexity_map = {'low': 1.0, 'medium': 3.0, 'high': 5.0}
        subject_complexity = data.get('subject_complexity', 'medium')
        if isinstance(subject_complexity, str) and subject_complexity.lower() in complexity_map:
            subject_difficulty = complexity_map[subject_complexity.lower()]
        else:
            subject_difficulty = float(data.get('subject_difficulty', 3.0))

        retention_score = float(data.get('retention_score', 50.0))

        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
        INSERT INTO study_logs 
        (user_id, sleep_hours, energy_score, study_hour, study_duration, subject_difficulty, retention_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], sleep_hours, energy_score, study_hour, study_duration, subject_difficulty, retention_score))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Study log synchronized successfully'})
    except Exception as e:
        return jsonify({'error': f'Invalid input parameters: {str(e)}'}), 400

@app.route('/api/study-logs', methods=['GET'])
def list_study_logs():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    logs = conn.execute(
        'SELECT * FROM study_logs WHERE user_id = ? ORDER BY id DESC LIMIT 20',
        (user['id'],)
    ).fetchall()
    conn.close()

    return jsonify({
        'logs': [dict(l) for l in logs]
    })

@app.route('/log/<int:log_id>/delete', methods=['POST'])
def delete_study_log(log_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    conn.execute('DELETE FROM study_logs WHERE id = ? AND user_id = ?', (log_id, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Log deleted'})

# ── What-If Simulator (PRD Section 6.13) ───────────────────────────
@app.route('/api/predict-instant', methods=['POST'])
def predict_instant():
    data = request.json or {}
    
    # Calculate instant prediction with multi-model breakdown
    pred_res = predict_retention_instant(data)

    # Sweep sleep_hours from 3.0 to 12.0 in steps of 0.5 for the correlation curve
    sweep_labels = []
    sweep_scores = []
    sweep_data = data.copy()
    
    for s_step in range(6, 25):  # 3.0 to 12.0
        s_val = s_step / 2.0
        sweep_data['sleep_hours'] = s_val
        s_res = predict_retention_instant(sweep_data)
        sweep_labels.append(f"{s_val}h")
        sweep_scores.append(s_res['ensemble'])

    return jsonify({
        'predicted_retention': pred_res['ensemble'],
        'model_breakdown': {
            'rf': pred_res['rf'],
            'xgb': pred_res['xgb'],
            'svr': pred_res['svr'],
            'ensemble': pred_res['ensemble'],
            'uncertainty': pred_res['uncertainty']
        },
        'sweep_labels': sweep_labels,
        'sweep_scores': sweep_scores
    })

# ── Syllabus Management & RAG (PRD Section 6.6) ───────────────────
@app.route('/api/upload-syllabus', methods=['POST'])
def upload_syllabus():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    clean_name = secure_filename(file.filename)
    stored_filename = f"{user['student_id']}_{clean_name}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
    file.save(save_path)

    conn = get_db()
    conn.execute(
        'INSERT INTO syllabuses (user_id, filename, display_name) VALUES (?, ?, ?)',
        (user['id'], stored_filename, file.filename)
    )
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'filename': stored_filename,
        'display_name': file.filename,
        'message': 'Syllabus indexed and uploaded successfully'
    })

@app.route('/api/syllabuses', methods=['GET'])
def list_syllabuses():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    items = conn.execute(
        'SELECT filename, display_name FROM syllabuses WHERE user_id = ? ORDER BY id DESC',
        (user['id'],)
    ).fetchall()
    conn.close()

    return jsonify({
        'syllabuses': [{'filename': i['filename'], 'display_name': i['display_name']} for i in items]
    })

@app.route('/api/delete-single-syllabus', methods=['POST'])
def delete_single_syllabus():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    conn = get_db()
    conn.execute('DELETE FROM syllabuses WHERE user_id = ? AND filename = ?', (user['id'], filename))
    conn.commit()
    conn.close()

    # Remove file from disk
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return jsonify({'success': True, 'message': 'File deleted successfully'})

@app.route('/api/delete-syllabus', methods=['POST'])
def delete_all_syllabuses():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    items = conn.execute('SELECT filename FROM syllabuses WHERE user_id = ?', (user['id'],)).fetchall()
    conn.execute('DELETE FROM syllabuses WHERE user_id = ?', (user['id'],))
    conn.commit()
    conn.close()

    for item in items:
        p = os.path.join(app.config['UPLOAD_FOLDER'], item['filename'])
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return jsonify({'success': True, 'message': 'All study memory wiped successfully'})

# ── Quiz Engine (PRD Section 6.6 & 6.8) ───────────────────────────
@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    topic = data.get('topic')
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    quantity = int(data.get('quantity', 5))
    difficulty = str(data.get('difficulty', 'medium'))
    selected_files = data.get('selected_files', [])

    # Extract text from selected files if provided
    combined_text = ""
    for fn in selected_files:
        p = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        if os.path.exists(p):
            combined_text += "\n" + extract_text_from_pdf(p)

    questions = generate_quiz_questions(topic, combined_text, quantity=quantity, difficulty=difficulty)
    return jsonify({'questions': questions})

@app.route('/api/submit-quiz-score', methods=['POST'])
def submit_quiz_score():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    score = data.get('score')
    if score is None:
        return jsonify({'error': 'Score is required'}), 400

    conn = get_db()
    # Find latest study log to calibrate (PRD FR-STUDY-06 & FR-STUDY-10)
    latest_log = conn.execute(
        'SELECT * FROM study_logs WHERE user_id = ? ORDER BY id DESC LIMIT 1',
        (user['id'],)
    ).fetchone()

    new_retention = float(score)
    if latest_log:
        # Calibrate prior estimation with objective quiz assessment score
        calibrated = round((latest_log['retention_score'] + float(score)) / 2.0, 1)
        conn.execute('UPDATE study_logs SET retention_score = ? WHERE id = ?', (calibrated, latest_log['id']))
        new_retention = calibrated

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'new_score': new_retention,
        'message': f'Quiz results synchronized. Calibrated retention score: {new_retention}%'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("CogniSync Backend Server starting on http://localhost:5000")
    print("Connected to PRD v1.2 Specifications & Fatigue Models")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)


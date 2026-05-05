from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
import re
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = 'nutriplan_super_secret_key_2024_xyz'

DB_PATH = 'data/nutriplan.db'

# ─── Database Setup ───────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('data', exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            calorie_goal INTEGER DEFAULT 2000,
            protein_goal INTEGER DEFAULT 150,
            weight REAL DEFAULT 70,
            height REAL DEFAULT 170,
            age INTEGER DEFAULT 25,
            gender TEXT DEFAULT 'male',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            emoji TEXT DEFAULT '🍽️',
            calories INTEGER DEFAULT 0,
            protein INTEGER DEFAULT 0,
            carbs INTEGER DEFAULT 0,
            fat INTEGER DEFAULT 0,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── Auth Decorator ───────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

# ─── Meal Database ────────────────────────────────────────────────────────────

MEAL_DATABASE = {
    "breakfast": [
        {"name": "Oatmeal with Berries", "calories": 320, "protein": 12, "carbs": 58, "fat": 6, "emoji": "🥣"},
        {"name": "Greek Yogurt Parfait", "calories": 280, "protein": 18, "carbs": 35, "fat": 8, "emoji": "🍓"},
        {"name": "Avocado Toast", "calories": 350, "protein": 9, "carbs": 32, "fat": 20, "emoji": "🥑"},
        {"name": "Egg White Omelette", "calories": 180, "protein": 24, "carbs": 4, "fat": 6, "emoji": "🍳"},
        {"name": "Banana Smoothie", "calories": 260, "protein": 8, "carbs": 48, "fat": 5, "emoji": "🍌"},
        {"name": "Whole Wheat Pancakes", "calories": 340, "protein": 10, "carbs": 56, "fat": 9, "emoji": "🥞"},
    ],
    "lunch": [
        {"name": "Grilled Chicken Salad", "calories": 420, "protein": 38, "carbs": 18, "fat": 22, "emoji": "🥗"},
        {"name": "Quinoa Buddha Bowl", "calories": 480, "protein": 16, "carbs": 65, "fat": 18, "emoji": "🍲"},
        {"name": "Turkey Wrap", "calories": 390, "protein": 28, "carbs": 42, "fat": 12, "emoji": "🌯"},
        {"name": "Lentil Soup", "calories": 310, "protein": 18, "carbs": 45, "fat": 6, "emoji": "🍜"},
        {"name": "Tuna Sandwich", "calories": 360, "protein": 30, "carbs": 38, "fat": 10, "emoji": "🥪"},
        {"name": "Chickpea Salad", "calories": 350, "protein": 14, "carbs": 48, "fat": 12, "emoji": "🥙"},
    ],
    "dinner": [
        {"name": "Baked Salmon & Veggies", "calories": 520, "protein": 42, "carbs": 22, "fat": 28, "emoji": "🐟"},
        {"name": "Chicken Stir Fry", "calories": 450, "protein": 35, "carbs": 40, "fat": 16, "emoji": "🍗"},
        {"name": "Vegetable Curry", "calories": 380, "protein": 14, "carbs": 55, "fat": 14, "emoji": "🍛"},
        {"name": "Grilled Steak & Salad", "calories": 580, "protein": 48, "carbs": 12, "fat": 36, "emoji": "🥩"},
        {"name": "Pasta Primavera", "calories": 440, "protein": 16, "carbs": 72, "fat": 12, "emoji": "🍝"},
        {"name": "Tofu Stir Fry", "calories": 360, "protein": 20, "carbs": 38, "fat": 16, "emoji": "🥢"},
    ],
    "snack": [
        {"name": "Mixed Nuts", "calories": 180, "protein": 5, "carbs": 8, "fat": 16, "emoji": "🥜"},
        {"name": "Apple & Peanut Butter", "calories": 200, "protein": 6, "carbs": 28, "fat": 8, "emoji": "🍎"},
        {"name": "Protein Bar", "calories": 220, "protein": 20, "carbs": 25, "fat": 6, "emoji": "🍫"},
        {"name": "Hummus & Veggies", "calories": 150, "protein": 6, "carbs": 18, "fat": 7, "emoji": "🥦"},
        {"name": "Cottage Cheese", "calories": 160, "protein": 22, "carbs": 8, "fat": 4, "emoji": "🧀"},
    ]
}

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not name or not email or not password:
            error = 'All fields are required.'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            error = 'Please enter a valid email address.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        else:
            try:
                conn = get_db()
                conn.execute(
                    'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                    (name, email, hash_password(password))
                )
                conn.commit()
                user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                conn.close()
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                error = 'An account with this email already exists.'
            finally:
                if 'conn' in dir() and conn:
                    conn.close()
    return render_template('auth.html', mode='signup', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND password_hash = ?',
            (email, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
    return render_template('auth.html', mode='login', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Main Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', logged_in='user_id' in session)

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    today = str(date.today())
    conn = get_db()
    today_logs = conn.execute(
        'SELECT * FROM meal_logs WHERE user_id = ? AND log_date = ? ORDER BY logged_at',
        (user['id'], today)
    ).fetchall()
    conn.close()
    total_calories = sum(m['calories'] for m in today_logs)
    total_protein = sum(m['protein'] for m in today_logs)
    total_carbs = sum(m['carbs'] for m in today_logs)
    total_fat = sum(m['fat'] for m in today_logs)
    return render_template('dashboard.html',
        user=user,
        today_logs=today_logs,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        meal_database=MEAL_DATABASE,
        today=today
    )

@app.route('/meal-planner')
@login_required
def meal_planner():
    return render_template('meal_planner.html', meal_database=MEAL_DATABASE, user=get_current_user())

@app.route('/bmi-calculator')
@login_required
def bmi_calculator():
    return render_template('bmi_calculator.html', user=get_current_user())

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    conn = get_db()
    logs = conn.execute(
        'SELECT log_date, SUM(calories) as total_cal FROM meal_logs WHERE user_id = ? GROUP BY log_date ORDER BY log_date DESC LIMIT 7',
        (user['id'],)
    ).fetchall()
    total_meals = conn.execute('SELECT COUNT(*) as c FROM meal_logs WHERE user_id = ?', (user['id'],)).fetchone()['c']
    conn.close()
    return render_template('profile.html', user=user, logs=logs, total_meals=total_meals)

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route('/api/log_meal', methods=['POST'])
@login_required
def log_meal():
    user_id = session['user_id']
    m = request.json
    today = str(date.today())
    now = datetime.now().strftime('%H:%M')
    conn = get_db()
    conn.execute(
        'INSERT INTO meal_logs (user_id, log_date, meal_type, meal_name, emoji, calories, protein, carbs, fat, logged_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (user_id, today, m['meal_type'], m['name'], m['emoji'], m['calories'], m['protein'], m['carbs'], m['fat'], now)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/remove_meal', methods=['POST'])
@login_required
def remove_meal():
    meal_id = request.json.get('id')
    conn = get_db()
    conn.execute('DELETE FROM meal_logs WHERE id = ? AND user_id = ?', (meal_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/save_profile', methods=['POST'])
@login_required
def save_profile():
    d = request.json
    conn = get_db()
    conn.execute('''
        UPDATE users SET name=?, calorie_goal=?, protein_goal=?, weight=?, height=?, age=?, gender=?
        WHERE id=?
    ''', (d['name'], d['calorie_goal'], d['protein_goal'], d['weight'], d['height'], d['age'], d['gender'], session['user_id']))
    conn.commit()
    conn.close()
    session['user_name'] = d['name']
    return jsonify({'success': True})

@app.route('/api/bmi', methods=['POST'])
@login_required
def calculate_bmi():
    b = request.json
    w = float(b.get('weight', 70))
    h = float(b.get('height', 170)) / 100
    a = int(b.get('age', 30))
    g = b.get('gender', 'male')
    bmi = round(w / (h ** 2), 1)
    if bmi < 18.5: cat, advice = 'Underweight', 'Focus on nutrient-dense foods to reach a healthy weight.'
    elif bmi < 25: cat, advice = 'Normal Weight', 'Great! Maintain your healthy lifestyle with balanced meals.'
    elif bmi < 30: cat, advice = 'Overweight', 'Reduce calorie intake slightly and increase physical activity.'
    else: cat, advice = 'Obese', 'Consult a nutritionist for a tailored diet plan.'
    bmr = (10*w + 6.25*(h*100) - 5*a + 5) if g == 'male' else (10*w + 6.25*(h*100) - 5*a - 161)
    tdee = round(bmr * 1.55)
    return jsonify({'bmi': bmi, 'category': cat, 'advice': advice, 'tdee': tdee})

@app.route('/api/history')
@login_required
def history():
    conn = get_db()
    rows = conn.execute(
        'SELECT log_date, SUM(calories) as cal, SUM(protein) as pro FROM meal_logs WHERE user_id=? GROUP BY log_date ORDER BY log_date DESC LIMIT 14',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

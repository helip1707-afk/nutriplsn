# 🌿 NutriPlan — Diet Tracker with Full Authentication

A professional Flask diet website with user accounts, login/signup, and per-user data persistence using SQLite.

## ✨ New in this version
- ✅ **Sign Up** — create a personal account (name, email, password)
- ✅ **Log In / Log Out** — secure session-based authentication
- ✅ **Password hashing** — SHA-256 hashed passwords (never stored in plain text)
- ✅ **Password strength meter** on signup
- ✅ **Per-user meal logs** — each user's data is isolated in SQLite
- ✅ **Profile page** with calorie history chart
- ✅ **Edit profile** — update name, goals, weight, height, age, gender
- ✅ **Protected routes** — dashboard/planner/BMI redirect to login if not authenticated

## Tech Stack
- Python 3.10+ · Flask 3.0
- SQLite (via built-in `sqlite3` — no extra install needed)
- Vanilla JS · Google Fonts (Playfair Display + Outfit)
- Responsive CSS Grid

## Quick Start

```bash
# 1. Install Flask
pip install flask

# 2. Run
python app.py

# 3. Open in browser
http://localhost:5000

# 4. Sign up for a new account and start tracking!
```

## Database Schema

```sql
-- Users table
users (id, name, email, password_hash, calorie_goal, protein_goal, weight, height, age, gender, created_at)

-- Meal logs per user per day
meal_logs (id, user_id, log_date, meal_type, meal_name, emoji, calories, protein, carbs, fat, logged_at)
```

## Routes

| Route | Auth | Description |
|-------|------|-------------|
| `/` | Public | Landing page |
| `/signup` | Public | Create account |
| `/login` | Public | Log in |
| `/logout` | Auth | Clear session |
| `/dashboard` | 🔒 | Daily tracker |
| `/meal-planner` | 🔒 | Weekly planner |
| `/bmi-calculator` | 🔒 | BMI & TDEE |
| `/profile` | 🔒 | Profile & history |
| `/api/log_meal` | 🔒 | POST: log meal |
| `/api/remove_meal` | 🔒 | POST: delete meal |
| `/api/save_profile` | 🔒 | POST: update profile |

## Project Structure
```
nutriplan2/
├── app.py                  # All routes, auth, DB logic
├── requirements.txt
├── data/
│   └── nutriplan.db        # Auto-created SQLite database
└── templates/
    ├── base.html           # Shared nav (auth-aware)
    ├── auth.html           # Login + Signup (split layout)
    ├── index.html          # Landing page
    ├── dashboard.html      # Main tracker
    ├── meal_planner.html   # 7-day planner
    ├── bmi_calculator.html # BMI tool
    └── profile.html        # Profile + history
```

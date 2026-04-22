"""
Database Service for Meal Planner MAS
Handles session + agent outputs persistence
"""

import sqlite3
from typing import List, Dict, Any

DB_PATH = "meal_planner.db"


# =========================
# DB INITIALIZATION
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT,
        age INTEGER,
        weight INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Coordinator
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coordinator_results (
        session_id INTEGER,
        goal TEXT,
        diet_type TEXT,
        target_calories INTEGER,
        ingredients TEXT,
        avoid_ingredients TEXT,
        steps TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)

    # Meals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_results (
        session_id INTEGER,
        meal_name TEXT,
        description TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)

    # Nutrition
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nutrition_results (
        session_id INTEGER,
        total_calories INTEGER,
        protein REAL,
        carbs REAL,
        fat REAL,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)

    # Final Output
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS final_outputs (
        session_id INTEGER,
        output TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)

    conn.commit()
    conn.close()


# =========================
# SESSION SAVE
# =========================
def create_session(user_input: str, age: int, weight: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sessions (user_input, age, weight) VALUES (?, ?, ?)",
        (user_input, age, weight)
    )

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


# =========================
# COORDINATOR SAVE
# =========================
def save_coordinator(session_id: int, parsed: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO coordinator_results 
    (session_id, goal, diet_type, target_calories, ingredients, avoid_ingredients, steps)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        parsed.get("goal"),
        parsed.get("diet_type"),
        parsed.get("target_calories"),
        str(parsed.get("ingredients")),
        str(parsed.get("avoid_ingredients")),
        str(parsed.get("steps"))
    ))

    conn.commit()
    conn.close()


# =========================
# MEALS SAVE
# =========================
def save_meals(session_id: int, meals: List[Dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for meal in meals:
        cursor.execute(
            "INSERT INTO meal_results (session_id, meal_name, description) VALUES (?, ?, ?)",
            (
                session_id,
                meal.get("name"),
                meal.get("description")
            )
        )

    conn.commit()
    conn.close()


# =========================
# NUTRITION SAVE
# =========================
def save_nutrition(session_id: int, totals: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO nutrition_results 
    (session_id, total_calories, protein, carbs, fat)
    VALUES (?, ?, ?, ?, ?)
    """, (
        session_id,
        totals.get("total_calories", 0),
        totals.get("total_protein_g", 0),
        totals.get("total_carbs_g", 0),
        totals.get("total_fat_g", 0),
    ))

    conn.commit()
    conn.close()


# =========================
# FINAL OUTPUT SAVE
# =========================
def save_final_output(session_id: int, output: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO final_outputs (session_id, output) VALUES (?, ?)",
        (session_id, output)
    )

    conn.commit()
    conn.close()
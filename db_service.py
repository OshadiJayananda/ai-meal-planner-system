"""
Database Service for Meal Planner MAS
Handles session + agent outputs persistence
"""

import ast
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


def _parse_list(value: str | None) -> list:
    if not value:
        return []

    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []

    return parsed if isinstance(parsed, list) else []


def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.id,
            s.user_input,
            s.age,
            s.weight,
            s.created_at,
            c.goal,
            c.diet_type,
            c.target_calories,
            n.total_calories
        FROM sessions s
        LEFT JOIN coordinator_results c ON c.session_id = s.id
        LEFT JOIN nutrition_results n ON n.session_id = s.id
        ORDER BY s.id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_session_detail(session_id: int) -> Dict[str, Any] | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    if session is None:
        conn.close()
        return None

    cursor.execute("SELECT * FROM coordinator_results WHERE session_id = ?", (session_id,))
    coordinator = cursor.fetchone()

    cursor.execute("SELECT * FROM meal_results WHERE session_id = ?", (session_id,))
    meals = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM nutrition_results WHERE session_id = ?", (session_id,))
    nutrition = cursor.fetchone()

    cursor.execute("SELECT output FROM final_outputs WHERE session_id = ?", (session_id,))
    final_output = cursor.fetchone()

    conn.close()

    coordinator_data = dict(coordinator) if coordinator else {}
    return {
        "session": dict(session),
        "coordinator": {
            **coordinator_data,
            "ingredients": _parse_list(coordinator_data.get("ingredients")),
            "avoid_ingredients": _parse_list(coordinator_data.get("avoid_ingredients")),
            "steps": _parse_list(coordinator_data.get("steps")),
        },
        "meals": meals,
        "nutrition": dict(nutrition) if nutrition else {},
        "final_output": final_output["output"] if final_output else "",
    }

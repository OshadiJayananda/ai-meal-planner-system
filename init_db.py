"""
Database Initialization Script for Nutrition Agent
Author: Oshadi Jayananda
Date: 22.04.2026
"""

import sqlite3
import os

def init_db():
    db_path = "nutrition.db"
    
    # Remove existing DB if it exists to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing {db_path}")

    # Connect to (and create) the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nutrition (
        ingredient TEXT PRIMARY KEY,
        calories INTEGER,
        protein REAL,
        carbs REAL,
        fat REAL,
        serving TEXT
    )
    ''')

    # Initial data
    nutrition_data = [
        # Proteins
        ("chicken breast", 165, 31, 0, 3.6, "100g"),
        ("chicken", 165, 31, 0, 3.6, "100g"),
        ("egg", 70, 6, 0.5, 5, "1 large"),
        ("eggs", 70, 6, 0.5, 5, "1 large"),
        ("beef", 250, 26, 0, 17, "100g"),
        ("fish", 206, 22, 0, 12, "100g"),
        ("salmon", 208, 20, 0, 13, "100g"),
        ("tofu", 76, 8, 2, 4.8, "100g"),
        
        # Carbs
        ("rice", 130, 2.7, 28, 0.3, "100g"),
        ("bread", 79, 2.7, 15, 1, "1 slice"),
        ("toast", 79, 2.7, 15, 1, "1 slice"),
        ("pasta", 131, 5, 25, 1.1, "100g"),
        ("potato", 77, 2, 17, 0.1, "100g"),
        ("oatmeal", 68, 2.4, 12, 1.4, "100g"),
        ("quinoa", 120, 4.4, 21, 1.9, "100g"),
        
        # Vegetables
        ("broccoli", 34, 2.8, 7, 0.4, "100g"),
        ("spinach", 23, 2.9, 3.6, 0.4, "100g"),
        ("salad", 15, 1, 3, 0.1, "100g"),
        ("vegetables", 30, 2, 5, 0.5, "100g"),
        ("vegetable", 30, 2, 5, 0.5, "100g"),
        ("veggies", 30, 2, 5, 0.5, "100g"),
        ("greens", 25, 2, 4, 0.3, "100g"),
        
        # Fats/Oils
        ("olive oil", 119, 0, 0, 13.5, "1 tbsp"),
        ("butter", 102, 0.1, 0, 11.5, "1 tbsp"),
        
        # Fruits
        ("banana", 105, 1.3, 27, 0.4, "1 medium"),
        ("apple", 95, 0.5, 25, 0.3, "1 medium"),
        
        # Dairy
        ("milk", 42, 3.4, 5, 1, "100ml"),
        ("cheese", 402, 25, 1.3, 33, "100g"),
        ("yogurt", 59, 10, 3.6, 0.4, "100g")
    ]

    # Insert data
    cursor.executemany(
        'INSERT INTO nutrition (ingredient, calories, protein, carbs, fat, serving) VALUES (?, ?, ?, ?, ?, ?)',
        nutrition_data
    )

    conn.commit()
    conn.close()
    print(f"Successfully initialized {db_path} with {len(nutrition_data)} ingredients.")

if __name__ == "__main__":
    init_db()

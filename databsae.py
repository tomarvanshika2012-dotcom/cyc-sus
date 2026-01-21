import sqlite3
from datetime import datetime

DB_NAME = "cyclone_ai.db"

# ----------------------------------
# Create database & tables
# ----------------------------------
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Weather + Risk table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pressure REAL,
        risk_level TEXT,
        date_time TEXT
    )
    """)

    # Prediction history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_level TEXT,
        location TEXT,
        date_time TEXT
    )
    """)

    # SOS alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sos_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        latitude REAL,
        longitude REAL,
        date_time TEXT
    )
    """)

    conn.commit()
    conn.close()

# ----------------------------------
# Save weather + risk
# ----------------------------------
def save_weather(pressure, risk):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO weather_data (pressure, risk_level, date_time)
    VALUES (?, ?, ?)
    """, (pressure, risk, datetime.now()))

    conn.commit()
    conn.close()

# ----------------------------------
# Save prediction history
# ----------------------------------
def save_prediction(risk, location):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO prediction_history (risk_level, location, date_time)
    VALUES (?, ?, ?)
    """, (risk, location, datetime.now()))

    conn.commit()
    conn.close()

# ----------------------------------
# Save SOS alert
# ----------------------------------
def save_sos(phone, lat, lon):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sos_alerts (phone, latitude, longitude, date_time)
    VALUES (?, ?, ?, ?)
    """, (phone, lat, lon, datetime.now()))

    conn.commit()
    conn.close()

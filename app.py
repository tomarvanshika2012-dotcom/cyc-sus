import streamlit as st
import joblib
import numpy as np
import pandas as pd
import requests
import os
import random
import sqlite3
from datetime import datetime
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from twilio.rest import Client

# =====================================================
# DATABASE (SQLite – OFFLINE)
# =====================================================
DB_NAME = "cyclone_ai.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pressure REAL,
        risk_level TEXT,
        location TEXT,
        date_time TEXT
    )
    """)

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

def save_prediction_db(pressure, risk, location):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO prediction_history (pressure, risk_level, location, date_time)
    VALUES (?, ?, ?, ?)
    """, (pressure, risk, location, datetime.now()))

    conn.commit()
    conn.close()

def save_sos_db(phone, lat, lon):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sos_alerts (phone, latitude, longitude, date_time)
    VALUES (?, ?, ?, ?)
    """, (phone, lat, lon, datetime.now()))

    conn.commit()
    conn.close()

create_db()

# =====================================================
# CONFIGURATION
# =====================================================
CONFIG = {
    "APP_TITLE": "Vizag Command Center",
    "API_KEY": "22223eb27d4a61523a6bbad9f42a14a7",
    "MODEL_PATH": "cyclone_model.joblib",
    "TARGET_CITY": "Visakhapatnam",
    "DEFAULT_COORDS": (17.6868, 83.2185)
}

# =====================================================
# TWILIO CONFIG
# =====================================================
TWILIO_ACCOUNTS = [
    {
        "sid": "ACc9b9941c778de30e2ed7ba57f87cdfbc",
        "token": "b524116dc4b14af314a5919594df9121",
        "number": "+15075195618"
    }
]

# =====================================================
# SOS LOGIC
# =====================================================
def trigger_emergency_comms(location, risk_level, contact_number):
    body = f"⚠️ CYCLONE ALERT ⚠️\nLocation: {location}\nRisk: {risk_level}"
    for acc in TWILIO_ACCOUNTS:
        try:
            client = Client(acc["sid"], acc["token"])
            client.messages.create(
                body=body,
                from_=acc["number"],
                to=contact_number
            )
            return "SOS Sent Successfully"
        except:
            pass
    return "SOS Failed"

# =====================================================
# WEATHER + MODEL
# =====================================================
def get_live_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={CONFIG['API_KEY']}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        return None

if os.path.exists(CONFIG["MODEL_PATH"]):
    model = joblib.load(CONFIG["MODEL_PATH"])
else:
    class MockModel:
        def predict(self, x): return [2]
    model = MockModel()

def predict_risk(lat, lon, pressure):
    r = model.predict([[lat, lon, pressure]])[0]
    return "High" if r >= 2 else "Medium" if r == 1 else "Low"

# =====================================================
# STREAMLIT UI
# =====================================================
st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🚨 Map", "📜 History"])

# =====================================================
# TAB 1 – DASHBOARD
# =====================================================
with tab1:
    w = get_live_weather(CONFIG["TARGET_CITY"])
    pressure = w['main']['pressure'] if w else 1005
    lat, lon = (w['coord']['lat'], w['coord']['lon']) if w else CONFIG["DEFAULT_COORDS"]

    risk = predict_risk(lat, lon, pressure)

    st.metric("Atmospheric Pressure", f"{pressure} hPa")
    st.metric("Cyclone Risk Level", risk)

    save_prediction_db(pressure, risk, CONFIG["TARGET_CITY"])

# =====================================================
# TAB 2 – MAP + SOS
# =====================================================
with tab2:
    m = folium.Map(location=[lat, lon], zoom_start=11)

    folium.Circle(
        location=[lat, lon],
        radius=4000,
        color="red",
        fill=True,
        fill_opacity=0.4,
        popup="High Risk Zone"
    ).add_to(m)

    st_folium(m, height=500)

    st.subheader("🚨 SOS Emergency")
    phone = st.text_input("Phone Number (+91...)")
    if st.button("SEND SOS"):
        save_sos_db(phone, lat, lon)
        result = trigger_emergency_comms(CONFIG["TARGET_CITY"], risk, phone)
        st.success(result)

# =====================================================
# TAB 3 – HISTORY
# =====================================================
with tab3:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM prediction_history ORDER BY date_time DESC", conn)
    conn.close()

    st.dataframe(df)

import requests
from bs4 import BeautifulSoup
from langdetect import detect
import sqlite3
from datetime import datetime

# -------- LANGUAGE --------
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"


# -------- URL SCRAPER --------
def extract_text_from_url(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        return text
    except:
        return ""


# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            result TEXT,
            confidence REAL,
            language TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_history(text, result, confidence, language):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO history (text, result, confidence, language, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (text[:200], result, confidence, language, str(datetime.now())))

    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM history ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()
    return rows
import os
import requests
import time
import pytz
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# -----------------------------
# FLASK WEB SERVER
# -----------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Football AI Bot Running ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -----------------------------
# ENV VARIABLES
# -----------------------------
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

# -----------------------------
# MONGODB
# -----------------------------
client = MongoClient(MONGO_URI)
db = client["football_ai"]
history = db["history"]

# -----------------------------
# LEAGUES
# -----------------------------
LEAGUES = [39, 140, 78, 61]

# -----------------------------
# TELEGRAM SEND
# -----------------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    requests.post(url, data=data)

# -----------------------------
# GET MATCHES
# -----------------------------
def get_matches():

    for league in LEAGUES:

        url = f"https://v3.football.api-sports.io/fixtures?live=all&league={league}"

        headers = {
            "x-apisports-key": API_KEY
        }

        try:

            res = requests.get(url, headers=headers)

            data = res.json()

            matches = data.get("response", [])

            for match in matches:

                fixture_id = match["fixture"]["id"]

                # already sent?
                exists = history.find_one({
                    "fixture_id": fixture_id
                })

                if exists:
                    continue

                home = match["teams"]["home"]["name"]
                away = match["teams"]["away"]["name"]

                h_score = match["goals"]["home"] or 0
                a_score = match["goals"]["away"] or 0

                league_name = match["league"]["name"]

                # SIMPLE AI
                total = h_score + a_score

                if total >= 2:
                    prediction = "🔥 Over 2.5 Goals"

                elif h_score > a_score:
                    prediction = "🏠 Home Team Strong"

                else:
                    prediction = "⚠️ Wait & Monitor"

                # MESSAGE
                msg = f"""
🏆 {league_name}

⚽ {home} {h_score} - {a_score} {away}

🤖 AI Prediction:
{prediction}

🕒 {datetime.now(pytz.timezone('Asia/Yangon')).strftime('%I:%M %p')}
"""

                send_telegram(msg)

                history.insert_one({
                    "fixture_id": fixture_id,
                    "home": home,
                    "away": away,
                    "prediction": prediction,
                    "time": datetime.now()
                })

                print("Sent:", home, "vs", away)

        except Exception as e:
            print("ERROR:", e)

# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":

    keep_alive()

    while True:

        print("Checking matches...")

        get_matches()

        time.sleep(600)

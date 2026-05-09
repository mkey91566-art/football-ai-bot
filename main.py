import os
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
from pymongo import MongoClient
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client['football_data']
history_col = db['predictions']

def get_predictions():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {'x-apisports-key': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        for match in data.get('response', []):
            fixture_id = match['fixture']['id']
            if history_col.find_one({"fixture_id": fixture_id}):
                continue
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            h_score = match['goals']['home']
            a_score = match['goals']['away']
            msg = f"⚽ **Match Alert**\n{home} ({h_score}) vs {away} ({a_score})\n💡 AI Tip: Check Live Stats!"
            send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            requests.post(send_url, data=payload)
            history_col.insert_one({"fixture_id": fixture_id, "sent_at": datetime.now(pytz.timezone('Asia/Yangon'))})
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    keep_alive() 
    while True:
        get_predictions()
        time.sleep(600)

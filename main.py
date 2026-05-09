import os, requests, time, pytz
from datetime import datetime
from pymongo import MongoClient
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_web_server).start()

# Environment Variables မှ Key များကို ဖတ်ခြင်း
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
        data = requests.get(url, headers=headers).json()
        for match in data.get('response', []):
            fixture_id = match['fixture']['id']
            if history_col.find_one({"fixture_id": fixture_id}): continue
            
            home, away = match['teams']['home']['name'], match['teams']['away']['name']
            h_score, a_score = match['goals']['home'], match['goals']['away']
            
            msg = f"⚽ **Match Alert**\n{home} ({h_score}) vs {away} ({a_score})\n💡 AI Tip: Check Stats!"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            
            history_col.insert_one({"fixture_id": fixture_id, "sent_at": datetime.now(pytz.timezone('Asia/Yangon'))})
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    keep_alive()
    while True:
        get_predictions()
        time.sleep(600)

import os
import re
import asyncio
import threading
import time
import requests
from flask import Flask
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY environment variables are missing!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

STATIONS = [
    {
        "id": "multix_station_1",
        "stream_url": "https://stream.multix.co.il/live"
    }
]

def fetch_now_playing():
    """שולף את השיר המתנגן כרגע מ-OnlineRadioBox בצורה מהירה ומיידית"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://onlineradiobox.com/il/glglz/playlist/", headers=headers, timeout=5)
        if res.status_code == 200:
            m = re.search(r'<td[^>]*class="[^"]*track_history_item[^"]*"[^>]*>(.*?)</td>', res.text, re.DOTALL)
            if m:
                raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if " - " in raw:
                    artist, song = raw.split(" - ", 1)
                    return song.strip(), artist.strip()
                return raw, "תחנת רדיו"
    except Exception as e:
        print(f"Error fetching metadata: {e}")
    return None, None

def update_supabase():
    if not supabase:
        print("Missing Supabase credentials!")
        return

    for station in STATIONS:
        print(f"Checking station: {station['id']}...")
        song_name, artist = fetch_now_playing()

        if not song_name:
            song_name = "Live Radio Stream"
            artist = "Station Playing"

        print(f"-> WRITING TO SUPABASE: {song_name} - {artist}")
        try:
            data = {
                "station_id": station["id"],
                "song_name": song_name,
                "artist": artist or "Unknown Artist"
            }
            res = supabase.table("radio_metadata").upsert(data).execute()
            print(f"SUCCESS: Supabase updated! -> {res}")
        except Exception as e:
            print(f"Supabase write ERROR: {e}")

def run_loop():
    print("Worker loop running...")
    while True:
        try:
            update_supabase()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(15)  # מעדכן בכל 15 שניות

threading.Thread(target=run_loop, daemon=True).start()

@app.route('/')
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

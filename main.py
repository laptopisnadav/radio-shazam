import os
import asyncio
import threading
import time
import requests
from flask import Flask
from supabase import create_client
from shazamio import Shazam

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
shazam = Shazam()

STATIONS = [
    {
        "id": "multix_station_1",
        "stream_url": "https://stream.multix.co.il/live",
        "api_url": "https://stream.multix.co.il/status-json.xsl"  # שליפה ישרה מה-API של התחנה
    }
]

def fetch_from_api(station):
    """מנסה לשלוף את השיר מה-API של הסטרים"""
    try:
        res = requests.get(station["api_url"], timeout=5)
        if res.status_code == 200:
            data = res.json()
            source = data.get("icestats", {}).get("source", {})
            if isinstance(source, list):
                source = source[0]
            title = source.get("title") or source.get("server_name")
            if title and " - " in title:
                artist, song = title.split(" - ", 1)
                return song.strip(), artist.strip()
            elif title:
                return title.strip(), "תחנת רדיו"
    except Exception as e:
        print(f"API fetch failed for {station['id']}: {e}")
    return None, None

async def recognize_and_update():
    if not supabase:
        print("Missing Supabase credentials!")
        return

    for station in STATIONS:
        print(f"Checking station: {station['id']}...")
        song_name, artist = None, None

        # ניסיון 1: שליפה מהירה מה-API
        if "api_url" in station:
            song_name, artist = fetch_from_api(station)

        # ניסיון 2: Shazam אם ה-API לא החזיר מידע
        if not song_name:
            try:
                out = await shazam.recognize_song(station["stream_url"])
                track = out.get("track", {})
                song_name = track.get("title")
                artist = track.get("subtitle")
            except Exception as e:
                print(f"Shazam failed for {station['id']}: {e}")

        # עדכון ב-Supabase
        if song_name:
            print(f"-> SUCCESS: {song_name} - {artist}")
            try:
                data = {
                    "station_id": station["id"],
                    "song_name": song_name,
                    "artist": artist or "Unknown Artist"
                }
                supabase.table("radio_metadata").upsert(data).execute()
                print(f"Updated Supabase for {station['id']}!")
            except Exception as e:
                print(f"Supabase write error: {e}")
        else:
            print(f"No song metadata found for {station['id']}")

def run_loop():
    print("Worker running...")
    while True:
        try:
            asyncio.run(recognize_and_update())
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(15) # עדכון מהיר כל 15 שניות

threading.Thread(target=run_loop, daemon=True).start()

@app.route('/')
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

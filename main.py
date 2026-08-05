import os
import asyncio
import threading
import time
from flask import Flask
from supabase import create_client
from shazamio import Shazam

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY environment variables are missing!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
shazam = Shazam()

STATIONS = [
    {
        "id": "multix_station_1",
        "stream_url": "https://stream.multix.co.il/live"
    }
]

async def recognize_and_update():
    if not supabase:
        print("Supabase client is not initialized.")
        return

    for station in STATIONS:
        print(f"Checking station: {station['id']}...")
        try:
            out = await shazam.recognize(station["stream_url"])
            track = out.get("track", {})
            song_name = track.get("title")
            artist = track.get("subtitle")

            if song_name:
                print(f"Identified: {song_name} - {artist}")
                data = {
                    "station_id": station["id"],
                    "song_name": song_name,
                    "artist": artist
                }
                res = supabase.table("radio_metadata").upsert(data).execute()
                print(f"Successfully updated Supabase for {station['id']}: {res}")
            else:
                print(f"No song identified for {station['id']}")

        except Exception as e:
            print(f"Error checking {station['id']}: {e}")

def run_loop():
    print("Background worker loop started...")
    while True:
        try:
            asyncio.run(recognize_and_update())
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(90)

threading.Thread(target=run_loop, daemon=True).start()

@app.route('/')
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

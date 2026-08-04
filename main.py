import os
import asyncio
import threading
import time
from flask import Flask
from supabase import create_client
from shazamio import Shazam

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://I1U4I614Hq13v3DrRFQZ9w.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
shazam = Shazam()

STATIONS = [
    {
        "id": "multix_station_1",
        "stream_url": "https://stream.multix.co.il/live"
    }
]

async def recognize_and_update():
    for station in STATIONS:
        try:
            out = await shazam.recognize(station["stream_url"])
            track = out.get("track", {})
            song_name = track.get("title")
            artist = track.get("subtitle")

            if song_name:
                supabase.table("radio_metadata").upsert({
                    "station_id": station["id"],
                    "song_name": song_name,
                    "artist": artist
                }).execute()
        except Exception as e:
            print(f"Error checking {station['id']}: {e}")

def run_loop():
    while True:
        asyncio.run(recognize_and_update())
        time.sleep(90)

# מריץ את הלולאה ברקע ברגע שהשרת עולה
threading.Thread(target=run_loop, daemon=True).start()

@app.route('/')
def health_check():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

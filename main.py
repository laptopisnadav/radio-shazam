import os
import asyncio
import time
from supabase import create_client
from shazamio import Shazam

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://I1U4I614Hq13v3DrRFQZ9w.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
shazam = Shazam()

# רשימת התחנות של Multix (עדכן את ה-id וה-stream_url של כל תחנה)
STATIONS = [
    {
        "id": "multix_station_1",
        "stream_url": "https://stream.multix.co.il/live"  # הכנס כאן את ה-Stream URL האמיתי
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
                print(f"Updated {station['id']}: {song_name} - {artist}")
        except Exception as e:
            print(f"Error checking {station['id']}: {e}")

if __name__ == "__main__":
    while True:
        asyncio.run(recognize_and_update())
        time.sleep(90)  # בדיקה כל דקה וחצי (90 שניות)

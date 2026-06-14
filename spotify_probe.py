"""
spotify_probe.py
Probes every relevant Spotify endpoint to see exactly what your app tier returns.
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

CHRIS_LAKE_ID = "5Igpc9iLZ3YGtKeYfSrrOE"

# Probe 1: Full artist object
print("PROBE 1: sp.artist(id) — available keys:")
try:
    r = sp.artist(CHRIS_LAKE_ID)
    print(f"  Keys: {list(r.keys())}")
    for k, v in r.items():
        print(f"  {k}: {str(v)[:80]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Probe 2: Top tracks
print("\nPROBE 2: sp.artist_top_tracks() — available keys:")
try:
    r = sp.artist_top_tracks(CHRIS_LAKE_ID, country="US")
    if r["tracks"]:
        track = r["tracks"][0]
        print(f"  Track keys: {list(track.keys())}")
        print(f"  Name: {track['name']}")
        print(f"  Popularity: {track.get('popularity', 'MISSING')}")
        print(f"  ID: {track['id']}")
except Exception as e:
    print(f"  ERROR: {e}")

# Probe 3: Audio features (deprecated for many apps)
print("\nPROBE 3: sp.audio_features() — BPM/Energy:")
try:
    r = sp.artist_top_tracks(CHRIS_LAKE_ID, country="US")
    track_id = r["tracks"][0]["id"]
    feats = sp.audio_features([track_id])
    if feats and feats[0]:
        print(f"  Audio features keys: {list(feats[0].keys())}")
        print(f"  BPM: {feats[0].get('tempo')}")
        print(f"  Energy: {feats[0].get('energy')}")
    else:
        print("  Returned None/empty — endpoint likely deprecated for this app tier")
except Exception as e:
    print(f"  ERROR: {e}")

# Probe 4: Search
print("\nPROBE 4: sp.search() — artist object keys:")
try:
    r = sp.search(q="artist:Chris Lake", type="artist", limit=1)
    artist = r["artists"]["items"][0]
    print(f"  Keys: {list(artist.keys())}")
except Exception as e:
    print(f"  ERROR: {e}")

# Probe 5: Discography/albums
print("\nPROBE 5: sp.artist_albums() — available keys:")
try:
    r = sp.artist_albums(CHRIS_LAKE_ID, limit=3)
    if r["items"]:
        album = r["items"][0]
        print(f"  Album keys: {list(album.keys())}")
        print(f"  Name: {album['name']}")
        print(f"  Release date: {album.get('release_date')}")
        print(f"  Label: {album.get('label', 'MISSING — need sp.album(id) call')}")
except Exception as e:
    print(f"  ERROR: {e}")

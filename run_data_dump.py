import json
import httpx
import os
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, computed_field

load_dotenv('c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/.env')

# Setup Spotify client (optional/fallback/cross-reference)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))

ARTIST_NAME = 'Chris Lake'
CHRIS_LAKE_ID = '5Igpc9iLZ3YGtKeYfSrrOE'
MB_HEADERS = {"User-Agent": "LegionJackedPipeline/1.0 (research@legionjacked.ai)"}

class WebDataFusionEngine(BaseModel):
    track_title: str
    primary_artist: str
    apple_genre: str
    spotify_raw_albums: List[Dict]
    discogs_raw_results: List[Dict]
    musicbrainz_raw_recordings: List[Dict]
    
    @computed_field
    @property
    def validated_artists(self) -> str:
        # Check Spotify raw albums for any match to refine artist names
        target = self.track_title.lower()
        for alb in self.spotify_raw_albums:
            alb_title = alb.get('name', '').lower()
            if target in alb_title or alb_title in target:
                artists = [ar['name'] for ar in alb.get('artists', [])]
                if artists:
                    return ', '.join(artists)
        return self.primary_artist
        
    @computed_field
    @property
    def validated_genre(self) -> str:
        # Default to Apple Music genre (which has clean subgenres like House/Dance)
        if self.apple_genre and self.apple_genre not in ['Music', 'Electronic']:
            return self.apple_genre
            
        target = self.track_title.lower()
        # Fallback to Discogs genres
        for d in self.discogs_raw_results:
            d_title = d.get('title', '').lower()
            if target in d_title or d_title in target:
                genres = d.get('genre', [])
                if genres:
                    return ', '.join(genres)
        return self.apple_genre or 'Electronic'

    @computed_field
    @property
    def validated_isrc(self) -> str:
        target = self.track_title.lower()
        for rec in self.musicbrainz_raw_recordings:
            mb_title = rec.get('title', '').lower()
            if target in mb_title or mb_title in target:
                isrcs = rec.get('isrcs', [])
                if isrcs:
                    return isrcs[0]
        return ''

# 1. Fetch Apple Music (Primary tracks)
print("[1] Fetching Apple Music (Primary track list)...")
r = httpx.get(
    'https://itunes.apple.com/search',
    params={'term': ARTIST_NAME, 'entity': 'song', 'limit': 30}
)
apple_songs = r.json().get('results', [])

# 2. Fetch Spotify (Auxiliary metadata)
print("[2] Fetching Spotify albums for cross-reference...")
spotify_albums = []
try:
    albums = sp.artist_albums(CHRIS_LAKE_ID, limit=10)
    for a in albums['items']:
        spotify_albums.append(a)
except Exception as e:
    print(f"Spotify error: {e}")

# 3. Fetch Discogs
print("[3] Fetching Discogs...")
discogs_raw = []
try:
    r = httpx.get(
        "https://api.discogs.com/database/search",
        params={"artist": ARTIST_NAME, "type": "release", "per_page": 20},
        headers={"User-Agent": "LegionJackedPipeline/1.0"},
        timeout=15
    )
    discogs_raw = r.json().get("results", [])
except Exception as e:
    print(f"Discogs error: {e}")

# 4. Fetch MusicBrainz
print("[4] Fetching MusicBrainz...")
mb_recordings = []
try:
    r = httpx.get(
        "https://musicbrainz.org/ws/2/artist/",
        params={"query": ARTIST_NAME, "fmt": "json", "limit": 1},
        headers=MB_HEADERS, timeout=15
    )
    mb_artist = r.json()["artists"][0]
    mb_id = mb_artist["id"]
    time.sleep(1)
    r2 = httpx.get(
        "https://musicbrainz.org/ws/2/recording/",
        params={"artist": mb_id, "fmt": "json", "limit": 30, "inc": "isrcs"},
        headers=MB_HEADERS, timeout=15
    )
    mb_recordings = r2.json().get("recordings", [])
except Exception as e:
    print(f"MusicBrainz error: {e}")

print('\nRAW DATA DUMP: FUSED WEB CONSENSUS (APPLE-DRIVEN 4-SOURCE PIPELINE)')
print('=' * 80)

for song in apple_songs:
    engine = WebDataFusionEngine(
        track_title=song.get('trackName', ''),
        primary_artist=song.get('artistName', ''),
        apple_genre=song.get('primaryGenreName', ''),
        spotify_raw_albums=spotify_albums,
        discogs_raw_results=discogs_raw,
        musicbrainz_raw_recordings=mb_recordings
    )
    
    print(f"Song    : {song.get('trackName')}")
    print(f"  Artists : {engine.validated_artists}")
    print(f"  Genre   : {engine.validated_genre}")
    print(f"  ISRC    : {engine.validated_isrc}")
    print(f"  Release : {song.get('collectionName', 'N/A')}")
    print(f"  Date    : {song.get('releaseDate', 'N/A')}")
    print('-' * 60)

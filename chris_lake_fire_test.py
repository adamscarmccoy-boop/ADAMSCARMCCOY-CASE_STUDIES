"""
chris_lake_fire_test.py  — v2
Multi-source: Spotify Albums + MusicBrainz + Discogs cross-verification
All free/available endpoints only.
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')

import httpx
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

CHRIS_LAKE_ID   = "5Igpc9iLZ3YGtKeYfSrrOE"
ARTIST_NAME     = "Chris Lake"
MB_HEADERS      = {"User-Agent": "LegionJackedPipeline/1.0 (research@legionjacked.ai)"}

# ─────────────────────────────────────────────────────────────
# SOURCE 1: SPOTIFY — Album Discography
# ─────────────────────────────────────────────────────────────
def spotify_discography():
    print("=" * 60)
    print("SOURCE 1: SPOTIFY — Album Discography")
    print("=" * 60)

    albums = sp.artist_albums(CHRIS_LAKE_ID, limit=10)
    results = []
    for a in albums["items"]:
        # Fetch full album for label info
        full = sp.album(a["id"])
        entry = {
            "title":        a["name"],
            "release_date": a.get("release_date", ""),
            "album_type":   a.get("album_type", ""),
            "spotify_id":   a["id"],
            "spotify_url":  a["external_urls"]["spotify"],
            "label":        full.get("label", ""),
            "total_tracks": full.get("total_tracks", 0),
            "tracks":       [t["name"] for t in full["tracks"]["items"]]
        }
        results.append(entry)
        print(f"  [{entry['release_date']}] {entry['title']:<40} | Label: {entry['label']}")

    print(f"\nTotal Spotify releases found: {len(results)}")
    return results

# ─────────────────────────────────────────────────────────────
# SOURCE 2: MUSICBRAINZ — ISRCs, Recordings, Labels
# ─────────────────────────────────────────────────────────────
def musicbrainz_data():
    print("\n" + "=" * 60)
    print("SOURCE 2: MUSICBRAINZ — ISRCs + Labels + Recordings")
    print("=" * 60)

    # Get the artist
    r = httpx.get(
        "https://musicbrainz.org/ws/2/artist/",
        params={"query": ARTIST_NAME, "fmt": "json", "limit": 1},
        headers=MB_HEADERS, timeout=15
    )
    mb_artist = r.json()["artists"][0]
    mb_id = mb_artist["id"]
    print(f"Artist: {mb_artist['name']}")
    print(f"MBID  : {mb_id}")
    print(f"Country: {mb_artist.get('country', 'N/A')}")

    time.sleep(1)  # MusicBrainz rate limit: 1 req/sec

    # Get recordings with ISRCs
    r2 = httpx.get(
        "https://musicbrainz.org/ws/2/recording/",
        params={
            "artist":  mb_id,
            "fmt":     "json",
            "limit":   20,
            "inc":     "isrcs+releases"
        },
        headers=MB_HEADERS, timeout=15
    )
    recordings = r2.json().get("recordings", [])

    results = []
    print(f"\nTop recordings with ISRCs:")
    for rec in recordings[:15]:
        isrcs = rec.get("isrcs", [])
        releases = rec.get("releases", [])
        label = releases[0].get("label-info", [{}])[0].get("label", {}).get("name", "") if releases else ""
        entry = {
            "title":   rec["title"],
            "isrc":    isrcs[0] if isrcs else "",
            "length_ms": rec.get("length", 0),
            "label":   label,
            "mb_id":   rec["id"]
        }
        results.append(entry)
        length_sec = entry["length_ms"] // 1000 if entry["length_ms"] else 0
        print(f"  {entry['title']:<40} | ISRC: {entry['isrc'] or 'N/A':<15} | {length_sec}s")

    return mb_artist, results

# ─────────────────────────────────────────────────────────────
# SOURCE 3: DISCOGS — Genre Tags + BPM + Cross-Verify
# ─────────────────────────────────────────────────────────────
def discogs_data():
    print("\n" + "=" * 60)
    print("SOURCE 3: DISCOGS — Genre + Style + BPM Cross-Verify")
    print("=" * 60)

    r = httpx.get(
        "https://api.discogs.com/database/search",
        params={"artist": ARTIST_NAME, "type": "release", "per_page": 10},
        headers={"User-Agent": "LegionJackedPipeline/1.0"},
        timeout=15
    )
    releases = r.json().get("results", [])

    genres_seen = set()
    styles_seen = set()
    results = []
    for rel in releases:
        genres = rel.get("genre", [])
        styles = rel.get("style", [])
        genres_seen.update(genres)
        styles_seen.update(styles)
        results.append({
            "title":   rel.get("title", ""),
            "year":    rel.get("year", ""),
            "genre":   genres,
            "style":   styles,
            "label":   rel.get("label", []),
            "country": rel.get("country", "")
        })
        print(f"  {str(rel.get('year','?')):<6} {rel.get('title','')[:40]:<40} | {', '.join(genres)} | {', '.join(styles[:2])}")

    print(f"\nAll genres detected: {', '.join(sorted(genres_seen))}")
    print(f"All styles detected: {', '.join(sorted(styles_seen))}")
    return results, sorted(genres_seen), sorted(styles_seen)

# ─────────────────────────────────────────────────────────────
# AUGMENTED VECTOR PAYLOAD PREVIEW
# ─────────────────────────────────────────────────────────────
def build_vector_preview(spotify_releases, mb_recordings, genres, styles):
    print("\n" + "=" * 60)
    print("AUGMENTED OMNI-VECTOR PAYLOAD PREVIEW")
    print("What Snowflake Arctic will embed for each track:")
    print("=" * 60)

    # Cross-reference: match Spotify albums with MB ISRCs where possible
    for sp_rel in spotify_releases[:3]:
        # Find matching MB recording by title similarity
        mb_match = next((r for r in mb_recordings if r["title"].lower() in sp_rel["title"].lower()), None)

        payload_text = (
            f"artist: {ARTIST_NAME} "
            f"release: {sp_rel['title']} "
            f"label: {sp_rel['label']} "
            f"release_date: {sp_rel['release_date']} "
            f"album_type: {sp_rel['album_type']} "
            f"total_tracks: {sp_rel['total_tracks']} "
            f"genre: {' '.join(genres[:3])} "
            f"style: {' '.join(styles[:4])} "
            + (f"isrc: {mb_match['isrc']} " if mb_match and mb_match['isrc'] else "")
        )
        print(f"\nRelease: {sp_rel['title']}")
        print(f"  ISRC match: {mb_match['isrc'] if mb_match and mb_match['isrc'] else 'not found'}")
        print(f"  Embed text: {payload_text[:200]}...")

if __name__ == "__main__":
    print(f"CHRIS LAKE — MULTI-SOURCE FIRE TEST v2")
    print(f"Spotify + MusicBrainz + Discogs")
    print()

    sp_releases                      = spotify_discography()
    mb_artist, mb_recordings         = musicbrainz_data()
    discogs_releases, genres, styles = discogs_data()
    build_vector_preview(sp_releases, mb_recordings, genres, styles)

    print("\n" + "=" * 60)
    print("FIRE TEST COMPLETE")
    print(f"  Spotify releases : {len(sp_releases)}")
    print(f"  MB recordings    : {len(mb_recordings)}")
    print(f"  Discogs releases : {len(discogs_releases)}")
    print(f"  Genre dimensions : {genres}")
    print("  Ready to flush to DuckDB + LanceDB")
    print("=" * 60)

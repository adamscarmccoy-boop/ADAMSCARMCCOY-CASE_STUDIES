import httpx
import json

url = 'https://itunes.apple.com/search?term=chris+lake&entity=song&limit=10'
r = httpx.get(url)
print(f'Status: {r.status_code}')
data = r.json()
for song in data['results']:
    print(f"{song.get('trackName')} | Artists: {song.get('artistName')} | Genre: {song.get('primaryGenreName')}")

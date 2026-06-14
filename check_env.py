from dotenv import load_dotenv
import os
load_dotenv()
cid  = os.getenv("SPOTIFY_CLIENT_ID", "")
csec = os.getenv("SPOTIFY_CLIENT_SECRET", "")
print(f"CLIENT_ID    : {'SET (' + cid[:8] + '...)' if len(cid) > 8 else 'NOT SET or placeholder'}")
print(f"CLIENT_SECRET: {'SET (' + csec[:4] + '...)' if len(csec) > 8 else 'NOT SET or placeholder'}")

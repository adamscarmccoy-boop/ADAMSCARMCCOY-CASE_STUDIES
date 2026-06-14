import lancedb
db = lancedb.connect(r'c:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag')
tbl = db.open_table('chris_lake_web_intel')
df = tbl.to_pandas()
print(f"Total songs/releases in Web Intel LanceDB: {len(df)}\n")
for i, row in df.iterrows():
    print(f"- {row['release_title']} ({row['release_date']}) | Genre: {row['genre'][:20]}...")

"""
MUSIC CATALOG GENERATOR
Takes your music data (Parquet + JSON + DuckDB) and outputs a unified catalog

OUTPUT: 
- music_catalog.parquet (queryable)
- music_catalog.json (human-readable)
- music_catalog_by_artist.md (organized)
- music_readiness_report.md (what's ready to analyze)
"""

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import json
from pathlib import Path
from datetime import datetime

DATA_PATH = r"G:\My Drive\Google AI Studio\CODE\WORKSPACE\data"

def load_all_data():
    """Load all your music data from various sources"""
    
    print("📚 Loading music data from all sources...")
    
    # Try to load from your existing Parquet files
    conn = duckdb.connect(":memory:")
    
    # Look for files with audio/track/dsp data
    duckdb_audio_features = f"{DATA_PATH}/duckdb_audio_features.parquet"
    fused_metadata = f"{DATA_PATH}/fused_track_metadata.parquet"
    chris_lake_raw = f"{DATA_PATH}/chris_lake_raw_features.json"
    
    catalog_data = []
    
    # Load DuckDB audio features
    try:
        print(f"  ✅ Loading {duckdb_audio_features}")
        result = conn.execute(f"""
            SELECT * FROM read_parquet('{duckdb_audio_features}')
        """).fetchall()
        for row in result:
            catalog_data.append(dict(row) if hasattr(row, '__dict__') else row)
    except Exception as e:
        print(f"  ⚠️ {duckdb_audio_features}: {e}")
    
    # Load fused metadata
    try:
        print(f"  ✅ Loading {fused_metadata}")
        result = conn.execute(f"""
            SELECT * FROM read_parquet('{fused_metadata}')
        """).fetchall()
        for row in result:
            catalog_data.append(dict(row) if hasattr(row, '__dict__') else row)
    except Exception as e:
        print(f"  ⚠️ {fused_metadata}: {e}")
    
    # Load JSON raw features
    try:
        print(f"  ✅ Loading {chris_lake_raw}")
        with open(chris_lake_raw, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                catalog_data.extend(data)
            elif isinstance(data, dict):
                catalog_data.append(data)
    except Exception as e:
        print(f"  ⚠️ {chris_lake_raw}: {e}")
    
    print(f"\n📊 Total records loaded: {len(catalog_data)}\n")
    
    return catalog_data

def enrich_catalog(catalog_data):
    """Add computed fields and status to catalog"""
    
    enriched = []
    
    for track in catalog_data:
        # Ensure we have basic track info
        if not isinstance(track, dict):
            continue
        
        # Normalize track data
        enriched_track = {
            "track_id": track.get("track_id", track.get("id", f"unknown_{len(enriched)}")),
            "track_name": track.get("track_name", track.get("name", "Unknown")),
            "artist": track.get("artist", track.get("artists", "Unknown")),
            "dsp_rms": track.get("dsp_rms", track.get("rms_db", None)),
            "dsp_crest_factor": track.get("dsp_crest_factor", track.get("crest_factor", None)),
            "dsp_spectral_centroid": track.get("dsp_spectral_centroid", track.get("spectral_centroid_hz", None)),
            "dsp_sub_bass_energy": track.get("dsp_sub_bass_energy", track.get("sub_bass_energy", None)),
            "bpm": track.get("bpm", track.get("tempo", None)),
            "key": track.get("key", None),
            "energy": track.get("energy", None),
            "streams": track.get("streams", track.get("stream_count", 0)),
            "popularity": track.get("popularity", track.get("spotify_popularity", None)),
            "release_date": track.get("release_date", None),
            "source": track.get("source", "unknown"),
        }
        
        # Compute readiness score
        readiness_score = 0
        missing_fields = []
        
        if enriched_track["dsp_rms"]: readiness_score += 20
        else: missing_fields.append("dsp_rms")
        
        if enriched_track["dsp_crest_factor"]: readiness_score += 20
        else: missing_fields.append("dsp_crest_factor")
        
        if enriched_track["bpm"]: readiness_score += 15
        else: missing_fields.append("bpm")
        
        if enriched_track["streams"]: readiness_score += 15
        else: missing_fields.append("streams")
        
        if enriched_track["popularity"]: readiness_score += 15
        else: missing_fields.append("popularity")
        
        if enriched_track["release_date"]: readiness_score += 15
        else: missing_fields.append("release_date")
        
        # Readiness status
        if readiness_score >= 80:
            status = "🟢 READY_FOR_ANALYSIS"
        elif readiness_score >= 50:
            status = "🟡 PARTIAL_DATA"
        else:
            status = "🔴 INCOMPLETE"
        
        enriched_track["readiness_score"] = readiness_score
        enriched_track["readiness_status"] = status
        enriched_track["missing_fields"] = missing_fields
        
        enriched.append(enriched_track)
    
    return enriched

def export_catalog(enriched_data):
    """Export catalog in multiple formats"""
    
    print("📤 Exporting catalog...\n")
    
    # 1. Parquet (for fast querying)
    try:
        table = pa.Table.from_pylist(enriched_data)
        parquet_path = f"{DATA_PATH}/music_catalog.parquet"
        pq.write_table(table, parquet_path, compression="snappy")
        print(f"  ✅ Parquet: {parquet_path}")
    except Exception as e:
        print(f"  ⚠️ Parquet export failed: {e}")
    
    # 2. JSON (human-readable)
    try:
        json_path = f"{DATA_PATH}/music_catalog.json"
        with open(json_path, 'w') as f:
            json.dump(enriched_data, f, indent=2, default=str)
        print(f"  ✅ JSON: {json_path}")
    except Exception as e:
        print(f"  ⚠️ JSON export failed: {e}")
    
    # 3. Markdown by Artist
    try:
        md_path = f"{DATA_PATH}/music_catalog_by_artist.md"
        
        # Group by artist
        by_artist = {}
        for track in enriched_data:
            artist = track.get("artist", "Unknown")
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(track)
        
        md_content = f"# 🎵 Music Catalog by Artist\n"
        md_content += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_content += f"**Total Tracks**: {len(enriched_data)}\n"
        md_content += f"**Total Artists**: {len(by_artist)}\n\n"
        
        for artist in sorted(by_artist.keys()):
            tracks = by_artist[artist]
            ready_count = sum(1 for t in tracks if "READY" in t["readiness_status"])
            
            md_content += f"## {artist} ({len(tracks)} tracks, {ready_count} ready)\n\n"
            
            for track in sorted(tracks, key=lambda t: t.get("streams", 0), reverse=True):
                md_content += f"### {track['track_name']}\n"
                md_content += f"- **Status**: {track['readiness_status']}\n"
                md_content += f"- **Readiness**: {track['readiness_score']}/100\n"
                
                if track['dsp_rms']:
                    md_content += f"- **RMS**: {track['dsp_rms']} dB\n"
                if track['dsp_crest_factor']:
                    md_content += f"- **Crest Factor**: {track['dsp_crest_factor']}\n"
                if track['bpm']:
                    md_content += f"- **BPM**: {track['bpm']}\n"
                if track['streams']:
                    md_content += f"- **Streams**: {track['streams']:,}\n"
                if track['popularity']:
                    md_content += f"- **Popularity**: {track['popularity']}/100\n"
                
                if track['missing_fields']:
                    md_content += f"- **Missing**: {', '.join(track['missing_fields'])}\n"
                
                md_content += "\n"
        
        with open(md_path, 'w') as f:
            f.write(md_content)
        print(f"  ✅ Markdown (by artist): {md_path}")
    except Exception as e:
        print(f"  ⚠️ Markdown export failed: {e}")
    
    # 4. Readiness Report
    try:
        report_path = f"{DATA_PATH}/music_readiness_report.md"
        
        ready = [t for t in enriched_data if "READY" in t["readiness_status"]]
        partial = [t for t in enriched_data if "PARTIAL" in t["readiness_status"]]
        incomplete = [t for t in enriched_data if "INCOMPLETE" in t["readiness_status"]]
        
        report = f"# 🎯 Music Readiness Report\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += f"## Summary\n"
        report += f"- 🟢 **Ready for Analysis**: {len(ready)} tracks ({len(ready)/len(enriched_data)*100:.1f}%)\n"
        report += f"- 🟡 **Partial Data**: {len(partial)} tracks ({len(partial)/len(enriched_data)*100:.1f}%)\n"
        report += f"- 🔴 **Incomplete**: {len(incomplete)} tracks ({len(incomplete)/len(enriched_data)*100:.1f}%)\n\n"
        
        if ready:
            report += f"## 🟢 Ready for Analysis ({len(ready)} tracks)\n"
            report += "These tracks have all DSP metrics and can be analyzed immediately:\n\n"
            for track in sorted(ready, key=lambda t: t["readiness_score"], reverse=True)[:10]:
                report += f"- **{track['track_name']}** by {track['artist']}\n"
                report += f"  - Readiness: {track['readiness_score']}/100\n"
                report += f"  - RMS: {track['dsp_rms']} dB | Crest: {track['dsp_crest_factor']}\n\n"
            if len(ready) > 10:
                report += f"... and {len(ready) - 10} more\n\n"
        
        if partial:
            report += f"## 🟡 Partial Data ({len(partial)} tracks)\n"
            report += "These tracks have some DSP metrics but are missing others:\n\n"
            for track in sorted(partial, key=lambda t: t["readiness_score"], reverse=True)[:5]:
                missing = ", ".join(track['missing_fields'][:3])
                report += f"- **{track['track_name']}** by {track['artist']}\n"
                report += f"  - Missing: {missing}\n\n"
        
        if incomplete:
            report += f"## 🔴 Incomplete ({len(incomplete)} tracks)\n"
            report += f"These tracks need DSP analysis or metadata enrichment.\n"
            report += f"**Action**: Run audio feature extraction on these tracks.\n\n"
        
        report += f"## Next Steps\n"
        report += f"1. Prioritize 🟢 Ready tracks for immediate analysis\n"
        report += f"2. Extract DSP metrics for 🟡 Partial tracks\n"
        report += f"3. Full audio analysis for 🔴 Incomplete tracks\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"  ✅ Readiness report: {report_path}")
    except Exception as e:
        print(f"  ⚠️ Readiness report failed: {e}")

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🎵 MUSIC CATALOG GENERATOR                               ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Load
    catalog_data = load_all_data()
    
    # Enrich
    print("🧬 Enriching catalog with readiness scores...")
    enriched = enrich_catalog(catalog_data)
    
    # Export
    export_catalog(enriched)
    
    print("\n✅ Catalog generation complete!")
    print(f"\n📍 All outputs saved to: {DATA_PATH}\n")

if __name__ == "__main__":
    main()
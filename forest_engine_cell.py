"""
FOREST ENGINE CELL — Paste into web_intel_pipeline.ipynb
=========================================================
Multi-class RandomForest + IsolationForest + Market Data Fusion
+ Full visual dashboard
"""
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

# ── FOREST ENGINE CELL ──────────────────────────────────────────────────────
import os, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import cross_val_score
from math import pi

# ── 1. LOAD DATA ─────────────────────────────────────────────────────────────
FEATURES_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
MARKET_PATH   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/fused_web_data.json"

with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
    df = pd.DataFrame(json.load(f))

with open(MARKET_PATH, 'r', encoding='utf-8') as f:
    market_raw = json.load(f)
market_df = pd.DataFrame(market_raw if isinstance(market_raw, list) else list(market_raw.values()))
market_df = market_df[['artist_name','popularity','trending_score','dsp_rms','dsp_crest',
                         'dsp_sub','dsp_bass','dsp_mid','dsp_high']].dropna(subset=['dsp_rms'])

print(f"DSP Catalog:  {len(df)} tracks")
print(f"Market Intel: {len(market_df)} records")

# ── 2. MULTI-ARTIST LABELING ──────────────────────────────────────────────────
ARTIST_MAP = {
    'chris lake':         'Chris Lake',
    'fisher':             'Fisher',
    'charlotte de witte': 'Charlotte de Witte',
    'sam shure':          'Sam Shure',
    'eli brown':          'Eli Brown',
}

def label_artist(path):
    p = str(path).lower()
    for key, name in ARTIST_MAP.items():
        if key in p:
            return name
    return 'Other'

df['artist'] = df['filepath'].apply(label_artist)

# ── 3. DSP FEATURES + MARKET SIGNAL FUSION ────────────────────────────────────
DSP_FEATURES = ['tempo','rms_db','crest_factor','sub_bass_energy',
                'bass_energy','mid_energy','high_energy','spectral_centroid']

# Merge market popularity score per artist
artist_market = market_df.groupby('artist_name').agg(
    market_popularity=('popularity','mean'),
    market_trending=('trending_score','mean')
).reset_index().rename(columns={'artist_name':'artist'})

df = df.merge(artist_market, on='artist', how='left')
df['market_popularity'] = df['market_popularity'].fillna(df['market_popularity'].median())
df['market_trending']   = df['market_trending'].fillna(0)

ALL_FEATURES = DSP_FEATURES + ['market_popularity', 'market_trending']
df_clean = df.dropna(subset=ALL_FEATURES + ['artist'])
X = df_clean[ALL_FEATURES]
y_labels = df_clean['artist']

# ── 4. SCALE + ENCODE ─────────────────────────────────────────────────────────
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
le = LabelEncoder()
y = le.fit_transform(y_labels)

print(f"\nClass distribution:\n{y_labels.value_counts().to_string()}")

# Drop classes with fewer than 5 samples (too few for CV)
class_counts = y_labels.value_counts()
valid_classes = class_counts[class_counts >= 5].index
df_clean = df_clean[df_clean['artist'].isin(valid_classes)].copy()
X = df_clean[ALL_FEATURES]
y_labels = df_clean['artist']
le = LabelEncoder()
y = le.fit_transform(y_labels)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"Training on {len(df_clean)} tracks across {len(le.classes_)} classes: {list(le.classes_)}")

# ── 5. RANDOM FOREST — MULTI-CLASS ────────────────────────────────────────────
rf = RandomForestClassifier(n_estimators=500, random_state=42,
                             class_weight='balanced', n_jobs=-1)
rf.fit(X_scaled, y)
y_pred = rf.predict(X_scaled)
n_splits = min(5, min(pd.Series(y).value_counts()))
cv_scores = cross_val_score(rf, X_scaled, y, cv=n_splits, scoring='f1_weighted')

print(f"\n{'='*60}")
print("FOREST ENGINE -- MULTI-CLASS CLASSIFICATION REPORT")
print(f"{'='*60}")
print(classification_report(y, y_pred, target_names=le.classes_))
print(f"Cross-Val F1 ({n_splits}-fold): {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}")

# ── 6. ISOLATION FOREST — ANOMALY DETECTION ───────────────────────────────────
iso = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
df_clean = df_clean.copy()
df_clean['anomaly_score'] = iso.fit_predict(X_scaled)
df_clean['outlier'] = df_clean['anomaly_score'] == -1

print(f"\nIsolation Forest: {df_clean['outlier'].sum()} anomalous tracks flagged")

# ── 7. FEATURE IMPORTANCES ────────────────────────────────────────────────────
importances = rf.feature_importances_
feat_order  = np.argsort(importances)[::-1]
feat_names  = ALL_FEATURES

# ── 8. VISUAL DASHBOARD ───────────────────────────────────────────────────────
plt.style.use('dark_background')
fig = plt.figure(figsize=(22, 20), facecolor='#0d0d14')
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

PALETTE = ['#00f0ff','#ff3cac','#ffe600','#7dff8a','#ff6b35','#c77dff']

# ── Panel A: Feature Importances ─────────────────────────────────────────────
ax_imp = fig.add_subplot(gs[0, :2])
colors_imp = [PALETTE[i % len(PALETTE)] for i in range(len(feat_names))]
bars = ax_imp.barh([feat_names[i] for i in feat_order],
                   [importances[i] for i in feat_order],
                   color=[colors_imp[i] for i in feat_order], edgecolor='none')
ax_imp.set_facecolor('#13131f')
ax_imp.set_title('🔑 FEATURE IMPORTANCES — What Defines Each Sound', 
                  color='white', fontsize=13, fontweight='bold', pad=10)
ax_imp.set_xlabel('Importance', color='#aaa')
ax_imp.tick_params(colors='white')
ax_imp.spines['bottom'].set_color('#333')
ax_imp.spines['left'].set_color('#333')
for s in ['top','right']: ax_imp.spines[s].set_visible(False)
for bar, val in zip(bars, [importances[i] for i in feat_order]):
    ax_imp.text(val + 0.002, bar.get_y() + bar.get_height()/2,
                f'{val*100:.1f}%', va='center', color='white', fontsize=9)

# ── Panel B: Market Popularity by Artist ─────────────────────────────────────
ax_mkt = fig.add_subplot(gs[0, 2])
mkt_summary = df_clean.groupby('artist')['market_popularity'].mean().sort_values(ascending=False)
artist_colors = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(mkt_summary.index)}
ax_mkt.barh(mkt_summary.index, mkt_summary.values,
            color=[artist_colors[a] for a in mkt_summary.index])
ax_mkt.set_facecolor('#13131f')
ax_mkt.set_title('📈 MARKET POPULARITY\nby Artist', color='white', fontsize=12, fontweight='bold')
ax_mkt.set_xlabel('Avg Popularity Score', color='#aaa')
ax_mkt.tick_params(colors='white')
for s in ['top','right']: ax_mkt.spines[s].set_visible(False)
ax_mkt.spines['bottom'].set_color('#333')
ax_mkt.spines['left'].set_color('#333')

# ── Panel C: Confusion Matrix ─────────────────────────────────────────────────
ax_cm = fig.add_subplot(gs[1, 0])
cm = confusion_matrix(y, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.classes_)
disp.plot(ax=ax_cm, colorbar=False, cmap='plasma')
ax_cm.set_facecolor('#13131f')
ax_cm.set_title('🎯 CONFUSION MATRIX', color='white', fontsize=12, fontweight='bold')
ax_cm.tick_params(colors='white', labelsize=7)
ax_cm.xaxis.label.set_color('white')
ax_cm.yaxis.label.set_color('white')
plt.setp(ax_cm.get_xticklabels(), rotation=35, ha='right')

# ── Panel D: Radar / Spider Chart per Artist ──────────────────────────────────
ax_radar = fig.add_subplot(gs[1, 1:], polar=True)
radar_features = ['rms_db','crest_factor','sub_bass_energy',
                   'bass_energy','mid_energy','high_energy','spectral_centroid']
N = len(radar_features)
angles = [n / float(N) * 2 * pi for n in range(N)] + [0]

ax_radar.set_facecolor('#13131f')
ax_radar.set_title('🕸️ DSP FINGERPRINT RADAR\nper Artist', color='white',
                    fontsize=12, fontweight='bold', pad=20)
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(radar_features, size=8, color='#ccc')
ax_radar.set_yticklabels([], color='white')
ax_radar.spines['polar'].set_color('#333')
ax_radar.grid(color='#333', linestyle='--', alpha=0.5)

scaler_radar = StandardScaler()
radar_scaled = pd.DataFrame(
    scaler_radar.fit_transform(df_clean[radar_features].fillna(0)),
    columns=radar_features,
    index=df_clean.index
)
df_clean_idx = df_clean.copy()
df_clean_idx[radar_features] = radar_scaled

for i, artist in enumerate(sorted(df_clean['artist'].unique())):
    group = df_clean_idx[df_clean_idx['artist'] == artist][radar_features].mean()
    vals  = group.tolist() + [group.tolist()[0]]
    color = PALETTE[i % len(PALETTE)]
    ax_radar.plot(angles, vals, color=color, linewidth=2, label=artist)
    ax_radar.fill(angles, vals, color=color, alpha=0.08)

ax_radar.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1),
                fontsize=8, labelcolor='white', facecolor='#1a1a2e')

# ── Panel E: Anomaly scatter — RMS vs Sub Bass ────────────────────────────────
ax_anom = fig.add_subplot(gs[2, :2])
ax_anom.set_facecolor('#13131f')
normal  = df_clean[~df_clean['outlier']]
outlier = df_clean[df_clean['outlier']]
for i, artist in enumerate(sorted(normal['artist'].unique())):
    grp = normal[normal['artist'] == artist]
    ax_anom.scatter(grp['rms_db'], grp['sub_bass_energy'],
                    color=PALETTE[i % len(PALETTE)], alpha=0.6, s=20, label=artist)
ax_anom.scatter(outlier['rms_db'], outlier['sub_bass_energy'],
                color='red', alpha=0.9, s=60, marker='X', label='⚠ Anomaly', zorder=5)
ax_anom.set_title('🚨 ISOLATION FOREST — Anomaly Detection (RMS vs Sub Bass)',
                   color='white', fontsize=12, fontweight='bold')
ax_anom.set_xlabel('RMS dB', color='#aaa')
ax_anom.set_ylabel('Sub Bass Energy', color='#aaa')
ax_anom.tick_params(colors='white')
for s in ['top','right']: ax_anom.spines[s].set_visible(False)
ax_anom.spines['bottom'].set_color('#333')
ax_anom.spines['left'].set_color('#333')
ax_anom.legend(fontsize=8, labelcolor='white', facecolor='#1a1a2e')

# ── Panel F: Probability distribution for YOUR track ─────────────────────────
ax_prob = fig.add_subplot(gs[2, 2])
ax_prob.set_facecolor('#13131f')

# Use the median track as "your track" — swap in your own DSP values here
your_track = pd.DataFrame([dict(zip(ALL_FEATURES, X_scaled.mean(axis=0)))])
proba = rf.predict_proba(your_track)[0]
sorted_idx = np.argsort(proba)[::-1]

ax_prob.barh([le.classes_[i] for i in sorted_idx],
             [proba[i] for i in sorted_idx],
             color=[PALETTE[i % len(PALETTE)] for i in sorted_idx])
ax_prob.set_title('🎲 YOUR TRACK\nStyle Probability', color='white',
                   fontsize=12, fontweight='bold')
ax_prob.set_xlabel('Probability', color='#aaa')
ax_prob.tick_params(colors='white')
ax_prob.set_xlim(0, 1)
for s in ['top','right']: ax_prob.spines[s].set_visible(False)
ax_prob.spines['bottom'].set_color('#333')
ax_prob.spines['left'].set_color('#333')
for i, (cls_i, prob) in enumerate(zip([le.classes_[i] for i in sorted_idx],
                                        [proba[i] for i in sorted_idx])):
    ax_prob.text(prob + 0.01, i, f'{prob*100:.1f}%', va='center',
                 color='white', fontsize=9, fontweight='bold')

# ── Title ─────────────────────────────────────────────────────────────────────
fig.suptitle('🌲 FOREST ENGINE — Multi-Class DSP Intelligence + Market Fusion',
             color='white', fontsize=16, fontweight='bold', y=0.98)

plt.savefig('forest_engine_dashboard.png', dpi=150, bbox_inches='tight',
            facecolor='#0d0d14')
plt.show()
print("\nForest Engine Dashboard saved -> forest_engine_dashboard.png")
print(f"  {len(df_clean)} tracks | {len(le.classes_)} artist classes | {df_clean['outlier'].sum()} anomalies flagged")

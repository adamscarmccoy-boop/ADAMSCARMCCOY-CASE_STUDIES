# %%
# Import necessary libraries
import os
import time
import json
import warnings
import numpy as np
import librosa
import soundfile as sf
from pydantic import BaseModel
from typing import Dict, List, Tuple
from pedalboard import Pedalboard, Compressor, Gain, LowpassFilter, Distortion, Chorus, Reverb, Phaser, Delay, LowShelfFilter, HighShelfFilter, PeakFilter
import pedalboard as pb

warnings.filterwarnings("ignore", category=UserWarning, module="pedalboard")

# --- 1. Exact LanceDB Physics Schema ---
class ExpandedTrackFeature(BaseModel):
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float
    spectral_rolloff: float
    spectral_bandwidth: float
    spectral_contrast: float
    zcr: float

class TrackSegment(BaseModel):
    segment_name: str
    start_time_sec: float
    end_time_sec: float

# --- Configuration Constants ---
SAMPLE_RATE = 44100
CROSSFADE_DURATION_MS = 30
CROSSFADE_SAMPLES = int(SAMPLE_RATE * CROSSFADE_DURATION_MS / 1000)
MAX_ITERATIONS = 5
ACCURACY_THRESHOLD = 0.90

# --- Vector Scaling Multipliers ---
VECTOR_MULTS = {
    'sub_bass': 4.53,
    'bass': 2.32,
    'mid': 289.34,
    'high': 163.93
}

# --- Master Target: Chris Lake ---
CHRIS_LAKE_MASTER = ExpandedTrackFeature(
    rms_db=-14.317,
    crest_factor=5.638,
    sub_bass_energy=20.56 / VECTOR_MULTS['sub_bass'],
    bass_energy=15.17 / VECTOR_MULTS['bass'],
    mid_energy=1.55 / VECTOR_MULTS['mid'],
    high_energy=0.65 / VECTOR_MULTS['high'],
    spectral_centroid=2331.31,
    spectral_rolloff=4775.95,
    spectral_bandwidth=2415.98,
    spectral_contrast=21.65,
    zcr=0.082
)

CHRIS_LAKE_BASELINES: Dict[str, ExpandedTrackFeature] = {
    'Drop': CHRIS_LAKE_MASTER,
    'Breakdown': CHRIS_LAKE_MASTER,
    'Intro': CHRIS_LAKE_MASTER,
    'Build-up': CHRIS_LAKE_MASTER
}

# --- Dynamic MACRO Blueprint Generation ---
def _generate_blueprint(y_mono: np.ndarray, sr: int) -> List[TrackSegment]:
    print("  Generating MACRO track blueprint...")
    rms_contour = librosa.feature.rms(y=y_mono)[0]
    times = librosa.times_like(rms_contour, sr=sr)
    
    # 1300 frames @ 44100Hz = ~15 seconds.
    # This massive smoothing window ignores micro-dips and identifies true Macro Sections (Intro, Drop, etc).
    smoothed_rms = np.convolve(rms_contour, np.ones(1300)/1300, mode='same')
    
    p75 = np.percentile(smoothed_rms, 75)
    p25 = np.percentile(smoothed_rms, 25)
    
    blueprint_segments = []
    current_state = None
    seg_start_time = 0.0
    
    for i, t in enumerate(times):
        val = smoothed_rms[i]
        if val > p75: state = "Drop"
        elif val < p25: state = "Breakdown"
        else: state = "Build-up"
        
        if current_state is None:
            current_state = state
            
        if state != current_state or i == len(times) - 1:
            if (t - seg_start_time) > 10.0 or i == len(times) - 1:
                final_name = "Intro" if len(blueprint_segments) == 0 and state != "Drop" else current_state
                blueprint_segments.append(TrackSegment(
                    segment_name=final_name,
                    start_time_sec=seg_start_time,
                    end_time_sec=t
                ))
                seg_start_time = t
                current_state = state
                
    print(f"  Macro Blueprint Generated! Sliced into {len(blueprint_segments)} sections.")
    return blueprint_segments

# --- Absolute Physics Extraction (EQUAL FACTORS ALIGNMENT) ---
def _extract_real_features(audio_segment: np.ndarray, sr: int) -> ExpandedTrackFeature:
    if audio_segment.ndim > 1:
        y_mono = librosa.to_mono(audio_segment).astype(float)
    else:
        y_mono = audio_segment.astype(float)
        
    # CRITICAL EQUAL FACTORS ALIGNMENT:
    # Instead of analyzing the variable length segment, we MUST extract EXACTLY 4 seconds from the midpoint,
    # because that is exactly how the LanceDB Chris Lake baseline was vectorized in headless_audio_processing.ipynb.
    num_frames = int(4.0 * sr)
    if len(y_mono) > num_frames:
        midpoint_sample = len(y_mono) // 2
        start_sample = max(0, midpoint_sample - (num_frames // 2))
        end_sample = start_sample + num_frames
        y_chunk = y_mono[start_sample:end_sample]
    else:
        y_chunk = np.pad(y_mono, (0, num_frames - len(y_mono)), 'constant')

    # We use librosa but scale n_fft to match torchaudio defaults (n_fft=1200) to ensure the freq bin mapping is identical.
    stft = np.abs(librosa.stft(y_chunk, n_fft=1200, hop_length=600))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1200)
    
    # Do NOT divide by duration here. We sum the power spectrum matrix just like the torchaudio headless notebook did.
    power_spectrum = np.sum(stft**2, axis=1)

    rms_linear = np.sqrt(np.mean(y_chunk**2))
    peak = np.max(np.abs(y_chunk))
    
    return ExpandedTrackFeature(
        rms_db=float(20 * np.log10(rms_linear + 1e-9)),
        crest_factor=float(peak / (rms_linear + 1e-9)),
        sub_bass_energy=float(np.sum(power_spectrum[(freqs >= 20) & (freqs < 60)])),
        bass_energy=float(np.sum(power_spectrum[(freqs >= 60) & (freqs < 250)])),
        mid_energy=float(np.sum(power_spectrum[(freqs >= 250) & (freqs < 2000)])),
        high_energy=float(np.sum(power_spectrum[(freqs >= 2000) & (freqs < 20000)])),
        spectral_centroid=float(np.mean(librosa.feature.spectral_centroid(y=y_chunk, sr=sr))),
        spectral_rolloff=float(np.mean(librosa.feature.spectral_rolloff(y=y_chunk, sr=sr))),
        spectral_bandwidth=float(np.mean(librosa.feature.spectral_bandwidth(y=y_chunk, sr=sr))),
        spectral_contrast=float(np.mean(librosa.feature.spectral_contrast(y=y_chunk, sr=sr))),
        zcr=float(np.mean(librosa.feature.zero_crossing_rate(y=y_chunk)))
    )

def _evaluate_accuracy(processed: ExpandedTrackFeature, target: ExpandedTrackFeature) -> float:
    errors = []
    p_dict = processed.model_dump()
    t_dict = target.model_dump()
    
    for key in p_dict:
        t_val = t_dict[key]
        p_val = p_dict[key]
        if t_val == 0: err = 0.0 if p_val == 0 else 1.0 
        else: err = abs(p_val - t_val) / abs(t_val)
        errors.append(min(err, 1.0))
        
    avg_error = sum(errors) / len(errors)
    return 1.0 - avg_error

# --- Recalibrated DSP Application ---
def _apply_pedalboard_effects(audio_segment: np.ndarray, sr: int, live_features: ExpandedTrackFeature, baseline_features: ExpandedTrackFeature, aggression: float = 1.0) -> np.ndarray:
    if audio_segment.ndim == 1: audio_segment = audio_segment[np.newaxis, :]
    board = Pedalboard([])

    deltas = {
        'rms_db': (live_features.rms_db - baseline_features.rms_db) * aggression,
        'crest_factor': (live_features.crest_factor - baseline_features.crest_factor) * aggression,
        'sub_bass_energy': (live_features.sub_bass_energy - baseline_features.sub_bass_energy) * aggression,
        'bass_energy': (live_features.bass_energy - baseline_features.bass_energy) * aggression,
        'mid_energy': (live_features.mid_energy - baseline_features.mid_energy) * aggression,
        'high_energy': (live_features.high_energy - baseline_features.high_energy) * aggression,
        'spectral_centroid': (live_features.spectral_centroid - baseline_features.spectral_centroid) * aggression,
        'spectral_bandwidth': (live_features.spectral_bandwidth - baseline_features.spectral_bandwidth) * aggression,
        'spectral_rolloff': (live_features.spectral_rolloff - baseline_features.spectral_rolloff) * aggression,
        'spectral_contrast': (live_features.spectral_contrast - baseline_features.spectral_contrast) * aggression,
        'zcr': (live_features.zcr - baseline_features.zcr) * aggression,
    }

    gain_db = np.clip(-deltas['rms_db'], -20.0, 20.0)
    board.append(pb.Gain(gain_db=gain_db))

    comp_ratio = 1.0 + np.clip(deltas['crest_factor'] * 1.5, 0.0, 10.0)
    comp_thresh = -14.0 - np.clip(deltas['crest_factor'] * 5.0, -10.0, 10.0)
    board.append(pb.Compressor(threshold_db=comp_thresh, ratio=comp_ratio, attack_ms=10.0, release_ms=100.0))

    # The Equal Factor tuning is in effect, but we must respect Pedalboard's clipping thresholds
    sb_gain = np.clip(-deltas['sub_bass_energy'] * 1.0, -12.0, 12.0)
    board.append(pb.LowShelfFilter(cutoff_frequency_hz=60, gain_db=sb_gain))

    b_gain = np.clip(-deltas['bass_energy'] * 1.0, -12.0, 12.0)
    board.append(pb.PeakFilter(cutoff_frequency_hz=120, gain_db=b_gain, q=1.0))

    m_gain = np.clip(-deltas['mid_energy'] * 1.0, -12.0, 12.0)
    board.append(pb.PeakFilter(cutoff_frequency_hz=1000, gain_db=m_gain, q=1.0))

    h_gain = np.clip(-deltas['high_energy'] * 1.0, -12.0, 12.0)
    board.append(pb.HighShelfFilter(cutoff_frequency_hz=5000, gain_db=h_gain))

    lpf_hz = np.clip(10000 + (deltas['spectral_rolloff']), 500.0, 20000.0)
    board.append(pb.LowpassFilter(cutoff_frequency_hz=lpf_hz))

    chorus_mix = np.clip((deltas['spectral_bandwidth'] / 1000.0), 0.0, 0.5)
    board.append(pb.Chorus(depth=0.5, rate_hz=0.8, mix=chorus_mix))

    delay_mix = np.clip(abs(deltas['zcr']) * 5.0, 0.0, 0.4)
    board.append(pb.Delay(delay_seconds=0.3, feedback=0.2, mix=delay_mix))

    rev_mix = np.clip(0.0 + (deltas['spectral_contrast'] / 20.0 * 0.3), 0.0, 0.5)
    board.append(pb.Reverb(room_size=0.6, wet_level=rev_mix))

    processed_audio = board(audio_segment, sr)
    return np.clip(processed_audio, -1.0, 1.0).astype(np.float32)

def _crossfade(segment1: np.ndarray, segment2: np.ndarray, crossfade_samples: int) -> np.ndarray:
    if segment1.shape[0] != segment2.shape[0]: return np.concatenate((segment1, segment2), axis=1)
    overlap_length = min(crossfade_samples, segment1.shape[1], segment2.shape[1])
    if overlap_length <= 0: return np.concatenate((segment1, segment2), axis=1)
    fade_out = np.linspace(1.0, 0.0, overlap_length, dtype=np.float32)[np.newaxis, :]
    fade_in = np.linspace(0.0, 1.0, overlap_length, dtype=np.float32)[np.newaxis, :]
    overlap1 = segment1[:, -overlap_length:]
    overlap2 = segment2[:, :overlap_length]
    crossfaded_overlap = (overlap1 * fade_out) + (overlap2 * fade_in)
    return np.concatenate((segment1[:, :-overlap_length], crossfaded_overlap, segment2[:, overlap_length:]), axis=1)

# --- Main Processing Loop ---
if __name__ == "__main__":
    print("Initiating FULL RECALIBRATED MACRO-SECTION Pipeline:")
    print("-----------------------------------------------------------------")
    
    TARGET_AUDIO_FILE = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\venom_gemma_mastered.wav"
    if not os.path.exists(TARGET_AUDIO_FILE):
        print(f"Error: Could not find {TARGET_AUDIO_FILE}")
        exit()
        
    print(f"Loading real audio track: {os.path.basename(TARGET_AUDIO_FILE)}")
    y, sr = librosa.load(TARGET_AUDIO_FILE, sr=SAMPLE_RATE, mono=False)
    if y.ndim == 1: y = y[np.newaxis, :]
    y_mono = librosa.to_mono(y).astype(float)
    
    blueprints = _generate_blueprint(y_mono, sr)
    processed_sections_list = []

    for i, seg in enumerate(blueprints):
        print(f"\n--- MACRO SECTION: '{seg.segment_name}' [{seg.start_time_sec:.2f}s - {seg.end_time_sec:.2f}s] ({i+1}/{len(blueprints)}) ---")
        
        start_sample = int(seg.start_time_sec * sr)
        end_sample = int(seg.end_time_sec * sr)
        audio_segment = y[:, start_sample:end_sample]
        
        if audio_segment.shape[1] == 0: continue
            
        baseline = CHRIS_LAKE_BASELINES.get(seg.segment_name, CHRIS_LAKE_MASTER)
        current_features = _extract_real_features(audio_segment, sr)
        
        accuracy = 0.0
        iteration = 1
        aggression_multiplier = 1.0
        best_processed_segment = audio_segment
        best_accuracy = 0.0
        
        while accuracy < ACCURACY_THRESHOLD and iteration <= MAX_ITERATIONS:
            print(f"  [Loop {iteration}/{MAX_ITERATIONS}] Applying Pedalboard (Aggression: {aggression_multiplier:.2f}x)...")
            processed_segment = _apply_pedalboard_effects(
                audio_segment=audio_segment, sr=SAMPLE_RATE,
                live_features=current_features, baseline_features=baseline,
                aggression=aggression_multiplier
            )
            
            output_features = _extract_real_features(processed_segment, sr)
            accuracy = _evaluate_accuracy(output_features, baseline)
            
            print(f"    -> Accuracy: {accuracy * 100:.1f}%")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_processed_segment = processed_segment
                
            if accuracy < ACCURACY_THRESHOLD:
                aggression_multiplier += 0.5
                iteration += 1
                
        if accuracy >= ACCURACY_THRESHOLD:
            print(f"  [SUCCESS] Converged at {accuracy * 100:.1f}% similarity!")
        else:
            print(f"  [TIMEOUT] Max iterations reached. Best accuracy: {best_accuracy * 100:.1f}%.")

        processed_sections_list.append(best_processed_segment)

    print("\n--- Reassembling MACRO processed sections with 30ms linear crossfades ---")
    if processed_sections_list:
        final_output_audio = processed_sections_list[0]
        for i in range(1, len(processed_sections_list)):
            final_output_audio = _crossfade(final_output_audio, processed_sections_list[i], crossfade_samples=CROSSFADE_SAMPLES)

        output_path = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\processed_12_param_track_macro.wav"
        sf.write(output_path, final_output_audio.T, SAMPLE_RATE)
        print(f"\nSaved True Equal Factors Output to: {output_path}")
    else:
        print("No sections were processed.")

import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, filtfilt, chirp
import os
import traceback
import random

def create_notch_filter(center_freq, q, fs):
    bandwidth = center_freq / q
    low = center_freq - bandwidth / 2
    high = center_freq + bandwidth / 2
    nyq = 0.5 * fs
    low = low / nyq
    high = high / nyq
    low = max(0.0, min(low, 1.0))
    high = max(0.0, min(high, 1.0))
    b, a = butter(2, [low, high], btype='bandstop', analog=False, output='ba')
    return b, a

def apply_notch_filter(data, center_freq, q, fs):
    b, a = create_notch_filter(center_freq, q, fs)
    return filtfilt(b, a, data)

def generate_am_tone(freq, duration, sample_rate, mod_freq):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    carrier = np.sin(2 * np.pi * freq * t)
    modulator = 0.5 * (1 + np.sin(2 * np.pi * mod_freq * t))
    return carrier * modulator

def generate_fm_tone(freq, duration, sample_rate, mod_freq, mod_index):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t + mod_index * np.sin(2 * np.pi * mod_freq * t))

def generate_tinnitus_matched_noise(duration, sample_rate, center_freq, bandwidth):
    noise = np.random.normal(0, 1, int(duration * sample_rate))
    nyq = 0.5 * sample_rate
    low = (center_freq - bandwidth/2) / nyq
    high = (center_freq + bandwidth/2) / nyq
    b, a = butter(4, [low, high], btype='band')
    filtered_noise = filtfilt(b, a, noise)
    return filtered_noise

def generate_ladder_pattern(data, start_freq, end_freq, bandwidth, step_duration, sample_rate, beep_duration):
    filtered_data = np.zeros_like(data)
    current_freq = start_freq
    samples_per_step = int(step_duration * sample_rate)
    beep_samples = int(beep_duration * sample_rate)
    
    for i in range(0, data.shape[1], samples_per_step):
        t = np.linspace(0, beep_duration, beep_samples, False)
        beep = np.sin(2 * np.pi * current_freq * t)
        stereo_beep = np.zeros((2, beep_samples))
        
        if random.choice([True, False]):
            stereo_beep[0, :] = beep  # Left channel
        else:
            stereo_beep[1, :] = beep  # Right channel
        
        chunk_with_beep = data[:, i:i+beep_samples]
        if chunk_with_beep.shape[1] < beep_samples:
            padding = np.zeros((2, beep_samples - chunk_with_beep.shape[1]))
            chunk_with_beep = np.hstack((chunk_with_beep, padding))
        
        mixed_beep = 0.7 * chunk_with_beep + 0.3 * stereo_beep
        filtered_data[:, i:i+beep_samples] = mixed_beep
        
        chunk_to_filter = data[:, i+beep_samples:i+samples_per_step]
        if chunk_to_filter.shape[1] > 0:
            filtered_chunk = np.vstack((
                apply_notch_filter(chunk_to_filter[0], current_freq, 30, sample_rate),
                apply_notch_filter(chunk_to_filter[1], current_freq, 30, sample_rate)
            ))
            filtered_data[:, i+beep_samples:i+samples_per_step] = filtered_chunk
        
        current_freq += bandwidth
        if current_freq > end_freq:
            current_freq = start_freq
    
    return filtered_data

def create_dynamic_tinnitus_treatment(input_file, output_dir, params):
    try:
        print(f"Loading audio file: {input_file}")
        audio, sr = librosa.load(input_file, sr=None, duration=params['duration'], mono=False)
        print(f"Audio loaded. Shape: {audio.shape}, Sample rate: {sr}")

        if len(audio.shape) == 1:
            audio = np.expand_dims(audio, axis=0)
            audio = np.repeat(audio, 2, axis=0)
        
        desired_length = int(params['duration'] * sr)
        if audio.shape[1] < desired_length:
            padding_length = desired_length - audio.shape[1]
            padding = np.zeros((2, padding_length))
            audio = np.hstack((audio, padding))
        elif audio.shape[1] > desired_length:
            audio = audio[:, :desired_length]
        
        print(f"Audio shape after preprocessing: {audio.shape}")
        audio = librosa.util.normalize(audio, axis=1)

        notched_music = np.vstack((
            apply_notch_filter(audio[0], params['tinnitus_freq'], params['notch_q'], sr),
            apply_notch_filter(audio[1], params['tinnitus_freq'], params['notch_q'], sr)
        ))
        
        ladder_pattern = generate_ladder_pattern(audio, params['ladder_start_freq'], params['ladder_end_freq'],
                                                 params['ladder_bandwidth'], params['ladder_step_duration'],
                                                 sr, params['ladder_beep_duration'])
        
        fm_tone = generate_fm_tone(params['tinnitus_freq'], params['duration'], sr, params['fm_mod_freq'], params['fm_mod_index'])
        fm_tone = np.vstack((fm_tone, fm_tone))

        matched_noise = generate_tinnitus_matched_noise(params['duration'], sr, params['tinnitus_freq'], params['noise_bandwidth'])
        matched_noise = np.vstack((matched_noise, matched_noise))

        treatments = {
            "original": audio,
            "notched": notched_music,
            "ladder": ladder_pattern,
            "fm": fm_tone,
            "noise": matched_noise
        }

        segment_duration = params['segment_duration']  # 4 seconds per segment
        samples_per_segment = segment_duration * sr
        mixed_audio = np.zeros_like(audio)
        
        for i in range(0, mixed_audio.shape[1], samples_per_segment):
            segment_index = (i // samples_per_segment) % len(params['segments'])
            segment_name, segment_mix = params['segments'][segment_index]
            end_index = min(i + samples_per_segment, mixed_audio.shape[1])
            
            segment_audio = sum(treatments[key] * volume for key, volume in segment_mix.items())
            mixed_audio[:, i:end_index] = segment_audio[:, i:end_index]
            print(f"Added segment: {segment_name} from {i/sr:.1f}s to {end_index/sr:.1f}s")

        mixed_audio = librosa.util.normalize(mixed_audio, axis=1)

        output_filename = f"Dynamic_TinnitusFreq_{params['tinnitus_freq']}.wav"
        output_file = os.path.join(output_dir, output_filename)
        sf.write(output_file, mixed_audio.T, sr)
        print(f"Saved dynamic treatment to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())

# Example usage and parameters
input_file = r"C:\web\python\tinitius\Sugar Babes - Stronger.mp3"
output_dir = r"C:\web\python\tinitius"

params = {
    'tinnitus_freq': 9996,  # Your tinnitus frequency
    'duration': 300,  # 5 minutes
    'notch_q': 30,  # Q factor for the notch filter
    'ladder_start_freq': 9496,  # 500 Hz below tinnitus frequency
    'ladder_end_freq': 10496,  # 500 Hz above tinnitus frequency
    'ladder_bandwidth': 100,  # Smaller bandwidth for more precise targeting
    'ladder_step_duration': 1,  # 1 second per step
    'ladder_beep_duration': 0.1,  # 0.1 second beep
    'fm_mod_freq': 5,  # 5 Hz modulation frequency
    'fm_mod_index': 10,  # Modulation index
    'noise_bandwidth': 1000,  # Bandwidth for tinnitus-matched noise (in Hz)
    'segment_duration': 4,  # 4 seconds per segment
    'segments': [
        ("Original + Notched", {"original": 0.7, "notched": 0.3}),
        ("Original + Ladder", {"original": 0.7, "ladder": 0.3}),
        ("Original + FM Tone", {"original": 0.7, "fm": 0.3}),
        ("Original + Matched Noise", {"original": 0.7, "noise": 0.3}),
        ("All Combined", {"original": 0.4, "notched": 0.15, "ladder": 0.15, "fm": 0.15, "noise": 0.15})
    ]
}

create_dynamic_tinnitus_treatment(input_file, output_dir, params)
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import iirnotch, filtfilt
import os

def apply_notch_filter(data, freq, q, fs):
    nyq = 0.5 * fs
    freq_normalized = freq / nyq
    b, a = iirnotch(freq_normalized, q)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

def generate_alternating_stereo_beep(freq, duration, sample_rate, left_channel):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    beep = np.sin(2 * np.pi * freq * t)
    stereo_beep = np.zeros((len(beep), 2))
    if left_channel:
        stereo_beep[:, 0] = beep  # Left channel
        print(f"Beep at {freq:.0f} Hz in Left channel")
    else:
        stereo_beep[:, 1] = beep  # Right channel
        print(f"Beep at {freq:.0f} Hz in Right channel")
    return stereo_beep

def create_ladder_notched_music_with_stereo_beeps(input_file, output_dir, start_freq, end_freq, bandwidth, step_duration, beep_duration=0.1, q_factor=30, filter_mix_ratio=0.7, beep_mix_ratio=0.4):
    try:
        print(f"Processing file: {input_file}")
        print(f"Frequency range: {start_freq} Hz - {end_freq} Hz")
        print(f"Bandwidth: {bandwidth} Hz, Step duration: {step_duration} seconds")
        
        # Load the audio file
        print("Loading audio file...")
        data, sample_rate = librosa.load(input_file, sr=None, mono=False)
        if data.ndim == 1:
            data = np.stack([data, data])  # Convert mono to stereo
        duration = data.shape[1] / sample_rate
        print(f"Audio loaded. Duration: {duration:.2f} seconds, Sample rate: {sample_rate} Hz")
        
        # Calculate number of samples for different durations
        samples_per_step = int(step_duration * sample_rate)
        beep_samples = int(beep_duration * sample_rate)
        filter_samples = samples_per_step - beep_samples
        
        # Process audio in steps
        filtered_data = np.zeros_like(data)
        current_freq = start_freq
        left_channel = True  # Start with left channel
        for i in range(0, data.shape[1], samples_per_step):
            # Generate and mix in the stereo beep
            stereo_beep = generate_alternating_stereo_beep(current_freq, beep_duration, sample_rate, left_channel)
            chunk_with_beep = data[:, i:i+beep_samples]
            mixed_beep = (1 - beep_mix_ratio) * chunk_with_beep + beep_mix_ratio * stereo_beep.T
            filtered_data[:, i:i+beep_samples] = mixed_beep
            
            # Apply notch filter to the remaining part of the chunk
            chunk_to_filter = data[:, i+beep_samples:i+samples_per_step]
            filtered_chunk = apply_notch_filter(chunk_to_filter, current_freq, q_factor, sample_rate)
            mixed_filtered = (1 - filter_mix_ratio) * chunk_to_filter + filter_mix_ratio * filtered_chunk
            filtered_data[:, i+beep_samples:i+samples_per_step] = mixed_filtered
            
            print(f"Applied stereo beep and notch filter at {current_freq:.0f} Hz for {i/sample_rate:.1f}-{(i+samples_per_step)/sample_rate:.1f}s")
            
            # Move to next frequency step
            current_freq += bandwidth
            if current_freq > end_freq:
                current_freq = start_freq  # Reset to start frequency
            
            # Alternate between left and right channels
            left_channel = not left_channel
        
        # Normalize the filtered data
        filtered_data = filtered_data / np.max(np.abs(filtered_data))
        
        # Generate output filename
        input_filename = os.path.basename(input_file)
        output_filename = f"RandomLR_beep_ladder_{input_filename}"
        output_file = os.path.join(output_dir, output_filename)
        
        # Export the filtered audio
        print(f"Saving filtered audio to {output_file}")
        sf.write(output_file, filtered_data.T, sample_rate)
        
        print(f"Ladder notched music with alternating stereo beeps saved to {output_file}")
        
        # Verify output file
        filtered_duration = librosa.get_duration(filename=output_file)
        print(f"Filtered audio duration: {filtered_duration:.2f} seconds")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
input_file = r"C:\web\python\tinitius\Sugar Babes - Stronger.mp3"
output_dir = r"C:\web\python\tinitius"
start_freq = 8996
end_freq = 11000
bandwidth = 500
step_duration = 0.1
beep_duration = 0.01
q_factor = 30
filter_mix_ratio = 0.1  # 10% original, 90% filtered for the main audio
beep_mix_ratio = 0.4  # 60% original, 40% beep for the beep sound

create_ladder_notched_music_with_stereo_beeps(input_file, output_dir, start_freq, end_freq, bandwidth, step_duration, 
                                              beep_duration, q_factor, filter_mix_ratio, beep_mix_ratio)
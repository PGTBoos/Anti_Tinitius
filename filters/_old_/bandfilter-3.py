import numpy as np
import librosa
import soundfile as sf
from scipy.signal import iirnotch, filtfilt

def apply_notch_filter(data, freq, q, fs):
    nyq = 0.5 * fs
    freq_normalized = freq / nyq
    b, a = iirnotch(freq_normalized, q)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

def create_ladder_notched_music(input_file, output_file, start_freq, end_freq, bandwidth, step_duration, q_factor=30, mix_ratio=0.5):
    try:
        print(f"Processing file: {input_file}")
        print(f"Frequency range: {start_freq} Hz - {end_freq} Hz")
        print(f"Bandwidth: {bandwidth} Hz, Step duration: {step_duration} seconds")
        
        # Load the audio file
        print("Loading audio file...")
        data, sample_rate = librosa.load(input_file, sr=None)
        duration = len(data) / sample_rate
        print(f"Audio loaded. Duration: {duration:.2f} seconds, Sample rate: {sample_rate} Hz")
        
        # Calculate number of samples per step
        samples_per_step = int(step_duration * sample_rate)
        
        # Process audio in steps
        filtered_data = np.zeros_like(data)
        current_freq = start_freq
        for i in range(0, len(data), samples_per_step):
            chunk = data[i:i+samples_per_step]
            
            # Apply notch filter to the chunk
            filtered_chunk = apply_notch_filter(chunk, current_freq, q_factor, sample_rate)
            
            # Mix filtered and original audio
            mixed_chunk = (1 - mix_ratio) * chunk + mix_ratio * filtered_chunk
            
            filtered_data[i:i+len(mixed_chunk)] = mixed_chunk
            
            print(f"Applied notch filter at {current_freq:.0f} Hz for {i/sample_rate:.1f}-{(i+samples_per_step)/sample_rate:.1f}s")
            
            # Move to next frequency step
            current_freq += bandwidth
            if current_freq > end_freq:
                current_freq = start_freq  # Reset to start frequency
        
        # Normalize the filtered data
        filtered_data = filtered_data / np.max(np.abs(filtered_data))
        
        # Export the filtered audio
        print(f"Saving filtered audio to {output_file}")
        sf.write(output_file, filtered_data, sample_rate)
        
        # Export unfiltered audio for comparison
        unfiltered_output = output_file.replace('.mp3', '_unfiltered.mp3')
        sf.write(unfiltered_output, data, sample_rate)
        
        print(f"Ladder notched music saved to {output_file}")
        print(f"Unfiltered music saved to {unfiltered_output}")
        
        # Verify output files
        filtered_duration = librosa.get_duration(filename=output_file)
        unfiltered_duration = librosa.get_duration(filename=unfiltered_output)
        print(f"Filtered audio duration: {filtered_duration:.2f} seconds")
        print(f"Unfiltered audio duration: {unfiltered_duration:.2f} seconds")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
input_file = r"C:\web\python\tinitius\Sugar Babes - Stronger.mp3"
output_file = r"C:\web\python\tinitius\ladder_notched_Sugar_Babes_Stronger.mp3"
start_freq = 5996
end_freq = 11000
bandwidth = 300
step_duration = 0.2
q_factor = 30
mix_ratio = 0.1  # 70% original, 30% filtered

create_ladder_notched_music(input_file, output_file, start_freq, end_freq, bandwidth, step_duration, q_factor, mix_ratio)
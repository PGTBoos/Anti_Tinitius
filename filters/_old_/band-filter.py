import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, lfilter
import os
import time

def create_notch_filter(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if low >= 1 or high >= 1:
        raise ValueError(f"Filter frequencies must be below Nyquist frequency ({nyq} Hz)")
    b, a = butter(order, [low, high], btype='bandstop')
    return b, a

def apply_notch_filter(data, lowcut, highcut, fs, order=5):
    b, a = create_notch_filter(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def create_notched_music(input_file, output_file, center_freq, bandwidth=50, intermittent=False, interval=1.0):
    try:
        print(f"Processing file: {input_file}")
        print(f"Tinnitus frequency: {center_freq} Hz")
        
        # Normalize file path
        input_file = os.path.normpath(input_file)
        output_file = os.path.normpath(output_file)

        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Load the audio file
        print("Loading audio file...")
        data, sample_rate = librosa.load(input_file, sr=None)
        print(f"Audio loaded. Duration: {len(data)/sample_rate:.2f} seconds, Sample rate: {sample_rate} Hz")
        
        # Calculate notch filter boundaries
        lowcut = max(20, center_freq - bandwidth / 2)  # Ensure lowcut is at least 20 Hz
        highcut = min(sample_rate/2 - 1, center_freq + bandwidth / 2)  # Ensure highcut is below Nyquist
        print(f"Notch filter range: {lowcut:.2f} Hz - {highcut:.2f} Hz")
        
        if intermittent:
            print(f"Applying intermittent filter with {interval} second interval")
            # Create a sine wave for intermittent application
            t = np.linspace(0, len(data) / sample_rate, num=len(data))
            sine_wave = 0.5 * (1 + np.sin(2 * np.pi * (1/interval) * t))
            
            # Apply the notch filter intermittently
            filtered_data = np.zeros_like(data)
            chunk_size = int(sample_rate)  # Process 1 second at a time
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                if np.mean(sine_wave[i:i+chunk_size]) > 0.5:
                    filtered_chunk = apply_notch_filter(chunk, lowcut, highcut, sample_rate)
                else:
                    filtered_chunk = chunk
                filtered_data[i:i+chunk_size] = filtered_chunk
                if i % (10 * chunk_size) == 0:
                    print(f"Processed {i/sample_rate:.1f} seconds...")
        else:
            print("Applying continuous filter")
            # Apply the notch filter continuously
            filtered_data = apply_notch_filter(data, lowcut, highcut, sample_rate)
        
        # Normalize the filtered data
        filtered_data = filtered_data / np.max(np.abs(filtered_data))
        
        # Export the filtered audio
        print(f"Saving filtered audio to {output_file}")
        sf.write(output_file, filtered_data, sample_rate)
        
        print(f"Notched music saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify that the input file path is correct and the file exists.")
        print("2. Ensure you have write permissions for the output file location.")
        print("3. Make sure you have installed all required libraries (numpy, librosa, soundfile, scipy).")
        print("4. Try with a different audio file to see if the issue is file-specific.")
        print("5. If the error persists, please provide the full error message for further assistance.")

# Example usage
input_file = r"C:\web\python\tinitius\Sugar Babes - Stronger.mp3"  # Use raw string for Windows paths
output_file = r"C:\web\python\tinitius\notched_Sugar_Babes_Stronger.mp3"
tinnitus_frequency = 9996  # Use the frequency you found
intermittent = True  # Set to False for continuous filtering
interval = 2.0  # Interval for intermittent filtering in seconds

start_time = time.time()
create_notched_music(input_file, output_file, tinnitus_frequency, intermittent=intermittent, interval=interval)
print(f"Total processing time: {time.time() - start_time:.2f} seconds")
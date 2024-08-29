# LadderFilter.py  as a module based upon json
# requires a main

import os
import json
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import iirnotch, filtfilt

class TinnitusFilterModule:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.config = {
                "start_freq": {"default": 8996, "description": {"UK": "Starting frequency of the ladder filter", "NL": "Start frequentie van de ladder functie"}},
                "end_freq": {"default": 11000, "description": {"UK": "Ending frequency of the ladder filter", "NL": "Eind frequentie van de ladder functie"}},
                "bandwidth": {"default": 500, "description": {"UK": "Bandwidth of each notch filter", "NL": "Bandbreedte van elk notch filter"}},
                "step_duration": {"default": 0.1, "description": {"UK": "Duration of each frequency step", "NL": "Duur van elke frequentiestap"}},
                "beep_duration": {"default": 0.01, "description": {"UK": "Duration of the stereo beep", "NL": "Duur van de stereo pieptoon"}},
                "q_factor": {"default": 30, "description": {"UK": "Q-factor of the notch filters", "NL": "Q-factor van de notch filters"}},
                "filter_mix_ratio": {"default": 0.1, "description": {"UK": "Ratio of filtered to original audio", "NL": "Verhouding gefilterde tot originele audio"}},
                "beep_mix_ratio": {"default": 0.4, "description": {"UK": "Ratio of beep to original audio", "NL": "Verhouding pieptoon tot originele audio"}}
            }
            self.save_config()
        else:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def update_parameter(self, param_name, value):
        if param_name in self.config:
            self.config[param_name]["default"] = value
            self.save_config()
        else:
            raise ValueError(f"Unknown parameter: {param_name}")

    def apply_notch_filter(self, data, freq, q, fs):
        nyq = 0.5 * fs
        freq_normalized = freq / nyq
        b, a = iirnotch(freq_normalized, q)
        filtered_data = filtfilt(b, a, data)
        return filtered_data

    def generate_alternating_stereo_beep(self, freq, duration, sample_rate, left_channel):
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        beep = np.sin(2 * np.pi * freq * t)
        stereo_beep = np.zeros((len(beep), 2))
        if left_channel:
            stereo_beep[:, 0] = beep  # Left channel
        else:
            stereo_beep[:, 1] = beep  # Right channel
        return stereo_beep

    def execute(self, input_file, output_file):
        start_freq = self.config["start_freq"]["default"]
        end_freq = self.config["end_freq"]["default"]
        bandwidth = self.config["bandwidth"]["default"]
        step_duration = self.config["step_duration"]["default"]
        beep_duration = self.config["beep_duration"]["default"]
        q_factor = self.config["q_factor"]["default"]
        filter_mix_ratio = self.config["filter_mix_ratio"]["default"]
        beep_mix_ratio = self.config["beep_mix_ratio"]["default"]

        data, sample_rate = librosa.load(input_file, sr=None, mono=False)
        if data.ndim == 1:
            data = np.stack([data, data])  # Convert mono to stereo

        samples_per_step = int(step_duration * sample_rate)
        beep_samples = int(beep_duration * sample_rate)
        filter_samples = samples_per_step - beep_samples

        filtered_data = np.zeros_like(data)
        current_freq = start_freq
        left_channel = True  # Start with left channel

        for i in range(0, data.shape[1], samples_per_step):
            stereo_beep = self.generate_alternating_stereo_beep(current_freq, beep_duration, sample_rate, left_channel)
            chunk_with_beep = data[:, i:i+beep_samples]
            mixed_beep = (1 - beep_mix_ratio) * chunk_with_beep + beep_mix_ratio * stereo_beep.T
            filtered_data[:, i:i+beep_samples] = mixed_beep

            chunk_to_filter = data[:, i+beep_samples:i+samples_per_step]
            filtered_chunk = self.apply_notch_filter(chunk_to_filter, current_freq, q_factor, sample_rate)
            mixed_filtered = (1 - filter_mix_ratio) * chunk_to_filter + filter_mix_ratio * filtered_chunk
            filtered_data[:, i+beep_samples:i+samples_per_step] = mixed_filtered

            current_freq += bandwidth
            if current_freq > end_freq:
                current_freq = start_freq
            left_channel = not left_channel

        filtered_data = filtered_data / np.max(np.abs(filtered_data))
        sf.write(output_file, filtered_data.T, sample_rate)

# Example usage in the main program
config_file = "tinnitus_filter_config.json"
filter_module = TinnitusFilterModule(config_file)

input_file = "input.mp3"
output_file = "output.mp3"

filter_module.execute(input_file, output_file)

# Adjusting a parameter
filter_module.update_parameter("start_freq", 9000)

# ladder filter based upon new structurals, accepts audio in and has an raw audio out

import json
import numpy as np
from scipy.signal import iirnotch, filtfilt

class TinnitusFilter:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_config()
        self.raw_in = None
        self.raw_out = None
        self.sample_rate = None

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "name": "Tinnitus Filter",
                "description": "Applies a ladder notch filter with alternating stereo beeps to an audio file.",
                "parameters": {
                    "start_freq": {"default": 8996, "description": {"en": "Starting frequency of the ladder filter", "nl": "Startfrequentie van de ladder filter"}},
                    "end_freq": {"default": 11000, "description": {"en": "Ending frequency of the ladder filter", "nl": "Eindfrequentie van de ladder filter"}},
                    "bandwidth": {"default": 500, "description": {"en": "Bandwidth of each notch filter", "nl": "Bandbreedte van elk notch filter"}},
                    "step_duration": {"default": 0.1, "description": {"en": "Duration of each frequency step", "nl": "Duur van elke frequentiestap"}},
                    "beep_duration": {"default": 0.01, "description": {"en": "Duration of the stereo beep", "nl": "Duur van de stereo piep"}},
                    "q_factor": {"default": 30, "description": {"en": "Quality factor of the notch filter", "nl": "Kwaliteitsfactor van het notch filter"}},
                    "filter_mix_ratio": {"default": 0.1, "description": {"en": "Mixing ratio for the filtered audio", "nl": "Mixverhouding voor de gefilterde audio"}},
                    "beep_mix_ratio": {"default": 0.4, "description": {"en": "Mixing ratio for the stereo beep", "nl": "Mixverhouding voor de stereo piep"}}
                }
            }

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def adjust_parameter(self, param_name, value):
        if param_name in self.config["parameters"]:
            self.config["parameters"][param_name]["default"] = value
        else:
            raise ValueError(f"Invalid parameter name: {param_name}")

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
            print(f"Beep at {freq:.0f} Hz in Left channel")
        else:
            stereo_beep[:, 1] = beep  # Right channel
            print(f"Beep at {freq:.0f} Hz in Right channel")
        return stereo_beep

    def execute(self):
        try:
            data = self.raw_in
            sample_rate = self.sample_rate
            duration = data.shape[1] / sample_rate
            
            # Get parameter values
            start_freq = self.config["parameters"]["start_freq"]["default"]
            end_freq = self.config["parameters"]["end_freq"]["default"]
            bandwidth = self.config["parameters"]["bandwidth"]["default"]
            step_duration = self.config["parameters"]["step_duration"]["default"]
            beep_duration = self.config["parameters"]["beep_duration"]["default"]
            q_factor = self.config["parameters"]["q_factor"]["default"]
            filter_mix_ratio = self.config["parameters"]["filter_mix_ratio"]["default"]
            beep_mix_ratio = self.config["parameters"]["beep_mix_ratio"]["default"]

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
                stereo_beep = self.generate_alternating_stereo_beep(current_freq, beep_duration, sample_rate, left_channel)
                chunk_with_beep = data[:, i:i+beep_samples]
                mixed_beep = (1 - beep_mix_ratio) * chunk_with_beep + beep_mix_ratio * stereo_beep.T
                filtered_data[:, i:i+beep_samples] = mixed_beep

                # Apply notch filter to the remaining part of the chunk
                chunk_to_filter = data[:, i+beep_samples:i+samples_per_step]
                filtered_chunk = self.apply_notch_filter(chunk_to_filter, current_freq, q_factor, sample_rate)
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
            self.raw_out = filtered_data / np.max(np.abs(filtered_data))

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
    def set_input(self, raw_in, sample_rate):
        self.raw_in = raw_in
        self.sample_rate = sample_rate

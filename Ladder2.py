# ladder2.py

# I'm still a bit searching exploring, i dont want json translations inside the code, but in a separate json
# i wand default and custom values in seperated jsons to
# still concept code.. (but should work kinda). uses audio raww in and out


import json
import numpy as np
from scipy.signal import iirnotch, filtfilt

class TinnitusFilter:
    def __init__(self, translations_file, default_values_file, custom_values_file=None):
        self.translations = self.load_json(translations_file)
        self.default_values = self.load_json(default_values_file)
        self.custom_values = self.load_json(custom_values_file) if custom_values_file else {}
        self.language = "en"
        self.raw_in = None
        self.raw_out = None
        self.sample_rate = None

    def load_json(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found. Using empty dictionary.")
            return {}

    def get_value(self, key):
        return self.custom_values.get(key, self.default_values.get(key))

    def get_translation(self, key):
        return self.translations.get(key, {}).get(self.language, key)

    def set_language(self, language):
        if language in self.translations.get("supported_languages", []):
            self.language = language
        else:
            raise ValueError(f"Unsupported language: {language}")

    def generate_alternating_stereo_beep(self, freq, duration, sample_rate, left_channel):
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        beep = np.sin(2 * np.pi * freq * t)
        stereo_beep = np.zeros((2, len(beep)))
        stereo_beep[0 if left_channel else 1] = beep
        return stereo_beep

    def apply_notch_filter(self, data, freq, q, fs):
        nyq = 0.5 * fs
        freq_normalized = freq / nyq
        b, a = iirnotch(freq_normalized, q)
        return filtfilt(b, a, data)

    def process_audio(self, audio_data, sample_rate):
        self.raw_in = audio_data
        self.sample_rate = sample_rate
        
        start_freq = self.get_value("start_freq")
        end_freq = self.get_value("end_freq")
        bandwidth = self.get_value("bandwidth")
        step_duration = self.get_value("step_duration")
        beep_duration = self.get_value("beep_duration")
        q_factor = self.get_value("q_factor")
        filter_mix_ratio = self.get_value("filter_mix_ratio")
        beep_mix_ratio = self.get_value("beep_mix_ratio")

        num_steps = int((end_freq - start_freq) / bandwidth)
        step_samples = int(step_duration * sample_rate)
        beep_samples = int(beep_duration * sample_rate)

        filtered_audio = np.zeros_like(audio_data)
        beep_audio = np.zeros_like(audio_data)

        for i in range(num_steps):
            freq = start_freq + i * bandwidth
            start_sample = i * step_samples
            end_sample = min((i + 1) * step_samples, audio_data.shape[1])

            filtered_chunk = self.apply_notch_filter(audio_data[:, start_sample:end_sample], freq, q_factor, sample_rate)
            filtered_audio[:, start_sample:end_sample] = filtered_chunk

            beep = self.generate_alternating_stereo_beep(freq, beep_duration, sample_rate, i % 2 == 0)
            beep_start = start_sample
            beep_end = min(beep_start + beep_samples, audio_data.shape[1])
            beep_audio[:, beep_start:beep_end] += beep[:, :beep_end-beep_start]

        self.raw_out = (1 - filter_mix_ratio - beep_mix_ratio) * audio_data + \
                       filter_mix_ratio * filtered_audio + \
                       beep_mix_ratio * beep_audio

        return self.raw_out

    def get_info(self):
        info = {
            "name": self.get_translation("name"),
            "description": self.get_translation("description"),
            "parameters": {}
        }
        for param in self.default_values.keys():
            info["parameters"][param] = {
                "value": self.get_value(param),
                "description": self.get_translation(f"{param}_description")
            }
        return info

    def get_parameter_description(self, param_name):
        return self.get_translation(f"{param_name}_description")

    def adjust_parameter(self, param_name, value):
        if param_name in self.default_values:
            self.custom_values[param_name] = value
        else:
            raise ValueError(f"Invalid parameter name: {param_name}")

    def save_custom_values(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.custom_values, file, indent=4)

    def execute(self):
        if self.raw_in is None or self.sample_rate is None:
            raise ValueError("Input audio data and sample rate must be set before execution.")
        return self.process_audio(self.raw_in, self.sample_rate)

    def set_input(self, raw_in, sample_rate):
        self.raw_in = raw_in
        self.sample_rate = sample_rate

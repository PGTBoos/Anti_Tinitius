import os
import librosa
import soundfile as sf
from tinnitus_filter import TinnitusFilter

def load_audio_file(file_path):
    data, sample_rate = librosa.load(file_path, sr=None, mono=False)
    if data.ndim == 1:
        data = np.stack([data, data])  # Convert mono to stereo
    return data, sample_rate

def save_audio_file(file_path, data, sample_rate):
    sf.write(file_path, data.T, sample_rate)

def main():
    print("Welcome to the Tinnitus Filter Program!")
    print("This program applies various audio filters to help with tinnitus.")

    # Get the list of available MP3 files in the current directory
    mp3_files = [file for file in os.listdir(".") if file.endswith(".mp3")]
    if not mp3_files:
        print("No MP3 files found in the current directory.")
        return

    # Display the list of MP3 files and let the user choose one
    print("Available MP3 files:")
    for i, file in enumerate(mp3_files, start=1):
        print(f"{i}. {file}")
    choice = int(input("Enter the number of the MP3 file you want to process: "))
    input_file = mp3_files[choice - 1]

    # Load the selected MP3 file
    raw_audio, sample_rate = load_audio_file(input_file)

    # Get the list of available filter modules
    filter_modules = ["tinnitus_filter"]  # Add more filter modules as needed

    # Display the list of filter modules and let the user choose one
    print("Available filter modules:")
    for i, module in enumerate(filter_modules, start=1):
        print(f"{i}. {module}")
    choice = int(input("Enter the number of the filter module you want to use: "))
    filter_module_name = filter_modules[choice - 1]

    # Load the selected filter module
    filter_config_file = f"{filter_module_name}_config.json"
    filter_module = TinnitusFilter(filter_config_file)

    # Display the current parameter values and let the user modify them
    print("Current filter parameters:")
    for param, value in filter_module.config["parameters"].items():
        print(f"{param}: {value['default']} - {value['description']['en']}")
    print("Enter 'k' to keep the current values or 'm' to modify them.")
    choice = input("Enter your choice: ")
    if choice.lower() == "m":
        for param in filter_module.config["parameters"]:
            value = input(f"Enter the new value for {param}: ")
            filter_module.adjust_parameter(param, float(value))
        filter_module.save_config()

    # Apply the selected filter to the audio data
    filter_module.set_input(raw_audio, sample_rate)
    filter_module.execute()
    filtered_audio = filter_module.raw_out

    # Save the filtered audio to a new file
    output_file = f"{os.path.splitext(input_file)[0]}_{filter_module_name}.mp3"
    save_audio_file(output_file, filtered_audio, sample_rate)
    print(f"Filtered audio saved to {output_file}")

if __name__ == "__main__":
    main()

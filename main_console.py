import os
import importlib
import numpy as np
from pydub import AudioSegment

class FilterManager:
    def __init__(self, filter_dir='filters'):
        self.filter_dir = filter_dir
        self.filters = self.load_filters()

    def load_filters(self):
        filters = {}
        for folder in os.listdir(self.filter_dir):
            folder_path = os.path.join(self.filter_dir, folder)
            if os.path.isdir(folder_path):
                module_path = os.path.join(folder_path, f"{folder}.py")
                if os.path.exists(module_path):
                    module_name = f"filters.{folder}.{folder}"
                    module = importlib.import_module(module_name)
                    filter_class = getattr(module, folder.capitalize())
                    filters[folder] = filter_class(
                        os.path.join(folder_path, 'translations.json'),
                        os.path.join(folder_path, 'default_values.json'),
                        os.path.join(folder_path, 'custom_values.json')
                    )
        return filters

    def list_filters(self):
        for name, filter_obj in self.filters.items():
            info = filter_obj.get_info()
            print(f"\n{name.capitalize()} Filter:")
            print(f"  Description: {info['description']}")

    def get_filter(self, name):
        return self.filters.get(name.lower())

def print_filter_info(filter_obj):
    info = filter_obj.get_info()
    print(f"\n{info['name']}:")
    print(f"{info['description']}\n")
    print("Current parameters:")
    for param, details in info['parameters'].items():
        print(f"  {param}: {details['value']} - {details['description']}")

def get_user_input(prompt, value_type):
    while True:
        user_input = input(prompt)
        try:
            return value_type(user_input)
        except ValueError:
            print(f"Invalid input. Please enter a valid {value_type.__name__}.")

def adjust_filter_parameters(filter_obj):
    while True:
        adjust = input("\nDo you want to adjust any parameters? (yes/no): ").lower()
        if adjust != 'yes':
            break

        param = input("Enter the parameter name you want to adjust: ")
        try:
            current_value = filter_obj.get_value(param)
            description = filter_obj.get_parameter_description(param)
            print(f"Current value: {current_value}")
            print(f"Description: {description}")
            new_value = get_user_input(f"Enter new value for {param}: ", type(current_value))
            filter_obj.adjust_parameter(param, new_value)
            print(f"{param} updated to {new_value}")
        except ValueError as e:
            print(f"Error: {str(e)}")

def process_audio(filter_obj, input_file, output_file):
    # Load the MP3 file
    audio = AudioSegment.from_mp3(input_file)

    # Convert to numpy array
    samples = np.array(audio.get_array_of_samples()).reshape((-1, audio.channels)).T
    sample_rate = audio.frame_rate

    # Set the input for the filter
    filter_obj.set_input(samples, sample_rate)

    # Process the audio
    print("\nProcessing audio...")
    filtered_samples = filter_obj.execute()

    # Convert back to AudioSegment
    filtered_audio = AudioSegment(
        filtered_samples.T.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )

    # Export the filtered audio
    filtered_audio.export(output_file, format="mp3")

    print(f"\nAudio processing complete. Output saved as '{output_file}'.")

def main():
    manager = FilterManager()

    print("Available filters:")
    manager.list_filters()

    filter_name = input("\nEnter the name of the filter you want to use: ").lower()
    filter_obj = manager.get_filter(filter_name)

    if filter_obj is None:
        print(f"Filter '{filter_name}' not found.")
        return

    # Set language (you can change this to 'nl' for Dutch)
    filter_obj.set_language('en')

    # Print initial filter information
    print_filter_info(filter_obj)

    # Allow user to adjust parameters
    adjust_filter_parameters(filter_obj)

    # Print updated filter information
    print("\nUpdated filter information:")
    print_filter_info(filter_obj)

    # Process audio
    input_file = input("\nEnter the name of the input MP3 file: ")
    output_file = input("Enter the name for the output MP3 file: ")

    process_audio(filter_obj, input_file, output_file)

    # Save custom values
    save_custom = input("Do you want to save your custom values? (yes/no): ").lower()
    if save_custom == 'yes':
        filter_obj.save_custom_values(os.path.join('filters', filter_name, 'new_custom_values.json'))
        print(f"Custom values saved for {filter_name} filter.")

if __name__ == "__main__":
    main()

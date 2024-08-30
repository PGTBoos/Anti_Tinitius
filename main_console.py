import numpy as np
from pydub import AudioSegment
from tinnitus_filter import TinnitusFilter

def print_filter_info(filter):
    info = filter.get_info()
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

def main():
    # Initialize the TinnitusFilter
    filter = TinnitusFilter('translations.json', 'default_values.json', 'custom_values.json')

    # Set language (you can change this to 'nl' for Dutch)
    filter.set_language('en')

    # Print initial filter information
    print_filter_info(filter)

    # Allow user to adjust parameters
    while True:
        adjust = input("\nDo you want to adjust any parameters? (yes/no): ").lower()
        if adjust != 'yes':
            break

        param = input("Enter the parameter name you want to adjust: ")
        try:
            current_value = filter.get_value(param)
            description = filter.get_parameter_description(param)
            print(f"Current value: {current_value}")
            print(f"Description: {description}")
            new_value = get_user_input(f"Enter new value for {param}: ", type(current_value))
            filter.adjust_parameter(param, new_value)
            print(f"{param} updated to {new_value}")
        except ValueError as e:
            print(f"Error: {str(e)}")

    # Print updated filter information
    print("\nUpdated filter information:")
    print_filter_info(filter)

    # Process audio
    input_file = input("\nEnter the name of the input MP3 file: ")
    output_file = input("Enter the name for the output MP3 file: ")

    # Load the MP3 file
    audio = AudioSegment.from_mp3(input_file)

    # Convert to numpy array
    samples = np.array(audio.get_array_of_samples()).reshape((-1, audio.channels)).T
    sample_rate = audio.frame_rate

    # Set the input for the filter
    filter.set_input(samples, sample_rate)

    # Process the audio
    print("\nProcessing audio...")
    filtered_samples = filter.execute()

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

    # Save custom values
    save_custom = input("Do you want to save your custom values? (yes/no): ").lower()
    if save_custom == 'yes':
        filter.save_custom_values('new_custom_values.json')
        print("Custom values saved to 'new_custom_values.json'")

if __name__ == "__main__":
    main()

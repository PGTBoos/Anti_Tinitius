import numpy as np
import sounddevice as sd
import time

def generate_tone(frequency, duration=1, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    return tone

def play_tone(frequency, duration=1, sample_rate=44100):
    tone = generate_tone(frequency, duration, sample_rate)
    sd.play(tone, sample_rate)
    sd.wait()

def find_tinnitus_frequency():
    print("Welcome to the Tinnitus Tone Finder")
    print("We'll play a series of tones. Use the following keys:")
    print("  + : if your tinnitus is higher than the tone")
    print("  - : if your tinnitus is lower than the tone")
    print("  Space : if the tone matches your tinnitus")
    print("  q : to quit the process")
    
    low = 100
    high = 20000
    
    while high - low > 10:
        mid = (low + high) // 2
        print(f"\nPlaying tone at {mid} Hz")
        play_tone(mid)
        
        response = input("Your input (+/-/space/q): ").lower()
        
        if response == " ":
            return mid
        elif response == "+":
            low = mid
        elif response == "-":
            high = mid
        elif response == "q":
            return None
    
    return (low + high) // 2

if __name__ == "__main__":
    result = find_tinnitus_frequency()
    if result:
        print(f"\nYour tinnitus frequency is approximately {result} Hz")
    else:
        print("\nTone finding process was interrupted.")
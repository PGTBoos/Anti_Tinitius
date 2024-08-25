import sys
import platform
import numpy
import librosa
import soundfile
import scipy

def get_version_info():
    info = {
        "Python": sys.version,
        "OS": platform.platform(),
        "NumPy": numpy.__version__,
        "Librosa": librosa.__version__,
        "SoundFile": soundfile.__version__,
        "SciPy": scipy.__version__
    }
    return info

def print_version_info(info):
    print("Tinnitus Treatment Tool - Dependency Versions")
    print("=============================================")
    for key, value in info.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    version_info = get_version_info()
    print_version_info(version_info)

    # Optionally, save to a file
    with open("version_info.txt", "w") as f:
        for key, value in version_info.items():
            f.write(f"{key}: {value}\n")
    print("\nVersion information has been saved to 'version_info.txt'")
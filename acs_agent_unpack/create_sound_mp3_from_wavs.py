import os
import base64
import urllib.parse
from pydub import AudioSegment
from io import BytesIO
import tempfile # Import for creating temporary files
import shutil   # Import for cleaning up temporary directories
import subprocess # Import subprocess for direct ffmpeg calls

def convert_wav_to_mp3_data_url(wav_file_path):
    """
    Converts a WAV file to MP3, then base64 encodes it and returns a data URL.
    This function now includes an intermediate step:
    1. Uses a direct ffmpeg call to convert the original WAV to a temporary WAV
       file with 'adpcm_ms' encoding (as requested).
    2. Loads this temporary, normalized WAV file.
    3. Exports the normalized audio to MP3 in memory.
    """
    temp_dir = None # Initialize temp_dir to None for cleanup in finally block
    temp_intermediate_wav_path = None # Path for the intermediate WAV file
    try:
        # Create a temporary directory for intermediate files
        temp_dir = tempfile.mkdtemp()
        
        # Construct the path for the temporary intermediate WAV file
        original_filename_base = os.path.splitext(os.path.basename(wav_file_path))[0]
        temp_intermediate_wav_path = os.path.join(temp_dir, f"{original_filename_base}_pcm_s16le_intermediate.wav")

        print(f"Attempting to convert '{wav_file_path}' to intermediate PCM S16LE WAV using ffmpeg...")
        # Direct ffmpeg call to convert the original WAV to an intermediate WAV with pcm_s16le codec.
        # This is done to explicitly control the intermediate format as per your request.
        ffmpeg_command_intermediate = [
            'ffmpeg',
            '-y', # Overwrite output file if it exists
            '-i', wav_file_path, # Input file
            '-acodec', 'pcm_s16le', # Output audio codec: PCM S16LE (as requested)
            '-f', 'wav', # Output format: WAV
            temp_intermediate_wav_path # Output file path for the intermediate WAV
        ]
        
        process_intermediate = subprocess.run(ffmpeg_command_intermediate, capture_output=True, text=True, check=False)

        if process_intermediate.returncode != 0:
            print(f"FFmpeg intermediate conversion to ADPCM MS WAV failed for '{wav_file_path}'. Error output:")
            print(process_intermediate.stderr)
            raise Exception(f"FFmpeg intermediate conversion failed with code {process_intermediate.returncode}")

        print(f"Intermediate conversion successful. Loading intermediate WAV: '{temp_intermediate_wav_path}'")
        # Load the newly created intermediate WAV file using pydub.
        intermediate_audio = AudioSegment.from_wav(temp_intermediate_wav_path)

        # Export the intermediate audio to MP3 in memory
        # Explicitly set the codec to 'libmp3lame' for MP3 export.
        mp3_buffer = BytesIO()
        intermediate_audio.export(mp3_buffer, format="mp3")
        mp3_buffer.seek(0) # Rewind the buffer to the beginning

        # Base64 encode the MP3 data
        encoded_mp3 = base64.b64encode(mp3_buffer.read()).decode('utf-8')

        # Construct the data URL
        data_url = f"data:audio/mpeg;base64,{encoded_mp3}"

        return data_url

    except Exception as e:
        print(f"Error processing '{wav_file_path}': {e}")
        print(f"This often indicates an issue with FFmpeg's ability to decode/encode the specific WAV format.")
        print(f"Please ensure your FFmpeg installation is complete and supports all necessary codecs.")
        # Suggest the more robust pcm_s16le alternative if this fails
        print(f"Consider changing the intermediate codec to 'pcm_s16le' for better compatibility if this continues to fail.")
        return None
    finally:
        # Clean up the temporary directory and its contents
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except OSError as e:
                print(f"Error removing temporary directory '{temp_dir}': {e}")


def generate_sounds_mp3_js(directory_path, agent_name="Dolphin", output_file_name="sounds-mp3.js"):
    """
    Generates a JavaScript file containing URL-encoded MP3 data for WAV files
    in the specified directory.
    """
    sound_data = {}
    
    # Iterate through files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".wav"):
            wav_file_path = os.path.join(directory_path, filename)
            print(f"Processing {filename}...")
            mp3_data_url = convert_wav_to_mp3_data_url(wav_file_path)
            if mp3_data_url:
                sound_data[filename] = mp3_data_url
            else:
                print(f"Skipping {filename} due to an error.")

    # Format the sound data into a JavaScript string for clippy.soundsReady()
    js_content_lines = []
    js_content_lines.append(f"clippy.soundsReady('{agent_name}', {{")
    for key, value in sound_data.items():
        js_content_lines.append(f"    '{key}':'{value}',")
    
    if sound_data:
        last_line = js_content_lines[-1]
        js_content_lines[-1] = last_line.rstrip(',')
    
    js_content_lines.append("});")

    with open(output_file_name, "w") as f:
        f.write("\n".join(js_content_lines))
    
    print(f"\nSuccessfully generated {output_file_name} in the current directory.")
    return sound_data

if __name__ == "__main__":
    print("This script will convert WAV files in a specified directory to MP3 data URLs")
    print("and generate a JavaScript file ('sound-mp3.js') with the encoded audio.")
    print("\n--- Prerequisites ---")
    print("1. Install Python (if you don't have it): https://www.python.org/downloads/")
    print("2. Install FFmpeg (required by pydub for audio conversion):")
    print("   - Windows: https://www.gyan.dev/ffmpeg/builds/")
    print("   - macOS: `brew install ffmpeg` (using Homebrew)")
    print("   - Linux: `sudo apt update && sudo apt install ffmpeg` (Debian/Ubuntu)")
    print("3. Install pydub: `pip install pydub`")
    print("\n--- How to use ---")
    print("1. Save this code as a Python file (e.g., `convert_audio.py`).")
    print("2. Open your terminal or command prompt.")
    print("3. Navigate to the directory where you saved `convert_audio.py`.")
    print("4. Run the script with the path to your WAV files directory:")
    print("   `python convert_audio.py`")

    input_directory = "./DOLPHIN ACS Decompiled/Audio"

    if not os.path.isdir(input_directory):
        print(f"Error: The directory '{input_directory}' does not exist.")
        print("Please ensure the 'DOLPHIN ACS Decompiled/Audio' directory exists")
        print("in the same location as your Python script, or provide the full path.")
    else:
        generate_sounds_mp3_js(input_directory, "Dolphin", "sounds-mp3.js")

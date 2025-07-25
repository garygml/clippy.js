import os
import base64
import urllib.parse
from pydub import AudioSegment

def convert_wav_to_mp3_data_url(wav_file_path):
    """
    Converts a WAV file to MP3, then base64 encodes it and returns a data URL.
    """
    try:
        # Load the WAV file
        audio = AudioSegment.from_wav(wav_file_path)

        # Export to MP3 in memory
        # We use a BytesIO object to avoid creating temporary files
        from io import BytesIO
        mp3_buffer = BytesIO()
        audio.export(mp3_buffer, format="mp3")
        mp3_buffer.seek(0) # Rewind the buffer to the beginning

        # Base64 encode the MP3 data
        encoded_mp3 = base64.b64encode(mp3_buffer.read()).decode('utf-8')

        # Construct the data URL
        data_url = f"data:audio/mpeg;base64,{encoded_mp3}"

        # URL encode the data URL (though typically not strictly necessary for base64 data URLs in JS,
        # it ensures full compatibility if the JS environment expects it or if the string is used in a URL context)
        # For the specific format requested, the base64 string itself is part of a JS string literal,
        # so direct URL encoding of the base64 part is not needed unless the entire string literal
        # is then passed to a URL parameter. Given the example, it's just a string value.
        # Let's keep it as base64 for direct embedding as a string literal.
        # If actual URL encoding of the base64 string itself is needed, it would be:
        # url_encoded_data_url = urllib.parse.quote(data_url)
        # For the requested output, we just need the base64 string.
        return data_url

    except Exception as e:
        print(f"Error processing {wav_file_path}: {e}")
        return None

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

    # Hardcode clippy and dolphin as requested
    # The example provided shows 'Dolphin' as the first argument and an object as the second.
    # The keys in the object are '1', '2', '3', etc., for Dolphin, and '0000.wav', '0001.wav' for the user's files.
    # This implies the user wants their files added to the existing structure.
    # Let's assume 'clippy' is an existing object/library in their web environment,
    # and we are adding to its 'soundsReady' method.

    # For the example, '1', '2', '3' etc. are keys for 'Dolphin'.
    # The user's request for '0000.wav':'data:audio/mpeg......' suggests they want
    # their files to be keyed by their original filenames.

    # Let's create the output in the format:
    # clippy.soundsReady('Dolphin', {
    #   '1': 'data:audio/mpeg;base64,...',
    #   '2': 'data:audio/mpeg;base64,...',
    #   ...,
    #   '0000.wav': 'data:audio/mpeg;base64,...',
    #   '0001.wav': 'data:audio/mpeg;base64,...'
    # });


    # Format the sound data into a JavaScript string
    js_content_lines = []
    js_content_lines.append(f"clippy.soundsReady('{agent_name}', {{")
    for key, value in sound_data.items():
        # Ensure keys are properly quoted for JavaScript
        js_content_lines.append(f"    '{key}':'{value}',")
    
    # Remove the trailing comma from the last entry
    if js_content_lines:
        last_line = js_content_lines[-1]
        js_content_lines[-1] = last_line.rstrip(',') # Remove trailing comma
    
    js_content_lines.append("});")

    # Write to the output file
    with open(output_file_name, "w") as f:
        f.write("\n".join(js_content_lines))
    
    print(f"\nSuccessfully generated {output_file_name} in the current directory.")
    return sound_data

# --- Instructions for the user ---
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

    # Get directory path from user
    input_directory = "./DOLPHIN ACS Decompiled/Audio"

    if not os.path.isdir(input_directory):
        print(f"Error: The directory '{input_directory}' does not exist.")
    else:
        generate_sounds_mp3_js(input_directory, "Dolphin", "sound-mp3.js")


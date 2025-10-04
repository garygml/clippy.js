import struct
import os
import json # Import json for output
from create_map_png_from_bmps import create_sprite_sheet_from_bmps
from create_sound_mp3_from_wavs import generate_sounds_mp3_js

def read_acd_animations(file_path, sprite_coordinates):
    """
    Reads an MS Agent .acd file and extracts animation names and their frames.

    Args:
        file_path (str): The path to the .acd file.

    Returns:
        dict: A dictionary where keys are animation names and values are
              lists of frame names (or frame indices).
    """
    animations = {}
    current_animation = None
    current_frames = []
    in_animation = False
    in_frame = False
    frame_data = {}
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                if line.startswith('DefineAnimation'):
                    # Start new animation
                    in_animation = True
                    current_animation = line.split('"')[1]
                    current_frames = []
                elif line == 'EndAnimation':
                    # End current animation
                    if current_animation and current_frames:
                        animations[current_animation] = {"frames": current_frames}
                    in_animation = False
                    current_animation = None
                    current_frames = []
                elif in_animation and line.startswith('DefineFrame'):
                    in_frame = True
                    frame_data = {}
                elif in_animation and line == 'EndFrame':
                    in_frame = False
                    # Normalize branching structure if present
                    if 'branching' in frame_data and isinstance(frame_data['branching'], list):
                        frame_data['branching'] = {"branches": frame_data['branching']}
                    # Ensure images key exists
                    if 'images' not in frame_data:
                        frame_data['images'] = []
                    current_frames.append(frame_data)
                    frame_data = {}
                elif in_animation and in_frame:
                    # Parse frame properties
                    if line.startswith('Duration ='):
                        frame_data['duration'] = int(line.split('=')[1].strip()) * 10
                    elif line.startswith('SoundEffect ='):
                        sound_path = line.split('=')[1].strip().strip('"')
                        # Normalize Windows style backslashes before basename
                        sound_path_norm = sound_path.replace('\\', '/')
                        frame_data['sound'] = os.path.basename(sound_path_norm)
                    elif line.startswith('ExitBranch ='):
                        # Adjust to zero-based index
                        try:
                            frame_data['exitBranch'] = int(line.split('=')[1].strip()) - 1
                        except ValueError:
                            pass
                    elif line.startswith('DefineBranching'):
                        frame_data['branching'] = []
                    elif line.startswith('BranchTo ='):
                        try:
                            branch_to = int(line.split('=')[1].strip()) - 1
                            frame_data.setdefault('branching', []).append({'frameIndex': branch_to})
                        except ValueError:
                            pass
                    elif line.startswith('Probability ='):
                        try:
                            prob = int(line.split('=')[1].strip())
                            if 'branching' in frame_data and frame_data['branching']:
                                frame_data['branching'][-1]['weight'] = prob
                        except ValueError:
                            pass
                    elif line.startswith('Filename ='):
                        filename = line.split('=')[1].strip().strip('"')
                        key = os.path.basename(filename)
                        coord = sprite_coordinates.get(key)
                        if coord is None:
                            # Attempt alternative key forms
                            alt_key = key.replace('Images\\', '').replace('Images/', '')
                            coord = sprite_coordinates.get(alt_key, [0,0])
                        # Ensure coord is a 2-length list
                        if isinstance(coord, (tuple, list)) and len(coord) == 2:
                            frame_data['images'] = [list(coord)]
                        else:
                            frame_data['images'] = [[0,0]]
        # No need to save last animation, handled by EndAnimation
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred while reading ACD: {e}")
    return animations


# --- How to use the function ---
if __name__ == "__main__":

    agent_name = "RsAgentxx"
    acd_file_path = './RsAgentxx ACS Decompiled/RsAgentxx.acd'

    # Create the sprite sheet from BMPs
    sprite_coordinates, sprite_width, sprite_height = create_sprite_sheet_from_bmps("./RsAgentxx ACS Decompiled/Images", "./map.png")

    sound_data = generate_sounds_mp3_js("./RsAgentxx ACS Decompiled/Audio", agent_name, "sounds-mp3.js")
    sound_names = []
    if sound_data:
        for key, value in sound_data.items():
            sound_names.append(key)

    # print(f"Attempting to read animations and their frame data from: {acs_file_path}")
    animations_with_frames = read_acd_animations(acd_file_path, sprite_coordinates)

    if animations_with_frames:
        # Prepare the data for agent.js
        agent_data = {
            "overlayCount": 1, # You might need to determine this dynamically if it varies
            "sounds": sound_names, # Populate this list with unique sound numbers
            "framesize": [sprite_width, sprite_height], # You'll need to determine this based on your ACS parsing
            "animations": {}
        }
        
        # Collect all unique sound files and assign them numeric IDs
        sound_map = {}
        sound_counter = 1

        for anim_name, anim_data in animations_with_frames.items():
            processed_frames = []
            for frame in anim_data.get("frames", []):
                new_frame = {
                    "duration": frame.get("duration", 0),
                    "images": frame.get("images", [])
                    
                }
                
                # If the frame has a sound, we can include it in the frame data.
                if "sound" in frame:
                    new_frame["sound"] = frame["sound"]

                # If exitBranch is present, we can include it in the frame data.
                if "exitBranch" in frame:
                    new_frame["exitBranch"] = frame["exitBranch"]
                
                # If the frame has branching, we can include it in the frame data.
                if "branching" in frame:
                    new_frame["branching"] = frame["branching"]

                # The clippy.js format doesn't directly use 'exitBranch' in the frame data.
                # If 'exitBranch' is crucial for animation logic, you might need to adapt clippy.js
                # or store it in a custom property if clippy.js allows extensions.
                # For now, we'll omit it as it's not in the target format.
                processed_frames.append(new_frame)
            
            agent_data["animations"][anim_name] = {
                "frames": processed_frames
            }

        # # Sort sounds to ensure consistent output
        # agent_data["sounds"].sort(key=int)

        # Convert the Python dictionary to a JSON string
        # Using an indent of 4 for pretty printing and ensuring ASCII for broad compatibility
        json_output = json.dumps(agent_data, indent=4, ensure_ascii=False)

        # Wrap the JSON in the clippy.ready() function call
        js_content = f"clippy.ready('{agent_name}', {json_output});"

        # Write to agent.js
        output_file_path = "agent.js"
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(js_content)
            print(f"\nSuccessfully exported animations to {output_file_path}")
        except IOError as e:
            print(f"\nError writing to file {output_file_path}: {e}")

    else:
        print("\nNo animation names or frame data found, or an error occurred during parsing.")
        print("Please ensure the file path is correct and the file is a valid MS Agent ACS file.")



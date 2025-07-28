import struct
import os
import json # Import json for output
from create_map_png_from_bmps import create_sprite_sheet_from_bmps
from create_sound_mp3_from_wavs import generate_sounds_mp3_js

# --- Helper Functions for Data Structures ---

def read_ulong(f):
    """Reads a ULONG (4-byte unsigned integer) from the file."""
    return struct.unpack('<I', f.read(4))[0]

def read_ushort(f):
    """Reads a USHORT (2-byte unsigned integer) from the file."""
    return struct.unpack('<H', f.read(2))[0]

def read_byte(f):
    """Reads a BYTE (1-byte unsigned integer) from the file."""
    return struct.unpack('<B', f.read(1))[0]

def read_short(f):
    """Reads a SHORT (2-byte signed integer) from the file."""
    return struct.unpack('<h', f.read(2))[0]

def read_bool(f):
    """Reads a BOOL (1-byte boolean) from the file."""
    return bool(struct.unpack('<B', f.read(1))[0])

def read_guid(f):
    """Reads a GUID (16 bytes) from the file."""
    return f.read(16).hex() # Return as hex string for readability

def read_string(f):
    """
    Reads a STRING as defined in the ACS documentation.
    - ULONG: # of Characters
    - WCHAR: variable (String Characters)
    - Null Terminator (0x0000)
    The # of characters does NOT include the terminator.
    """
    try:
        num_characters = read_ulong(f)
        if num_characters == 0:
            # If num_characters is 0, there's no string data and no terminator.
            # Just return an empty string.
            return ""

        # Read the actual character data (num_characters * 2 bytes for WCHAR/UTF-16-LE)
        string_bytes = f.read(num_characters * 2)

        # Read the null terminator (2 bytes for WCHAR/UTF-16-LE)
        null_terminator = f.read(2)
        if null_terminator != b'\x00\x00':
            # This is a warning, as the file might still be parsable, but it's good to note.
            print(f"WARNING: Expected null terminator (0x0000) but got {null_terminator.hex()} at offset {f.tell()-2}")

        return string_bytes.decode('utf-16-le')
    except struct.error as e:
        print(f"Error reading string length or bytes: {e} at offset {f.tell()}")
        return ""
    except UnicodeDecodeError as e:
        print(f"Error decoding string at offset {f.tell()}: {e}")
        # Fallback to latin-1 if UTF-16-LE fails, but this indicates a potential format issue.
        # errors='ignore' will skip characters that cannot be decoded.
        return string_bytes.decode('latin-1', errors='ignore')

class ACSLOCATOR:
    """Represents the ACSLOCATOR structure."""
    def __init__(self, f):
        self.offset = read_ulong(f)
        self.size = read_ulong(f)

    def __repr__(self):
        return f"ACSLOCATOR(offset={self.offset}, size={self.size})"

def skip_datablock(f):
    """Skips a DATABLOCK structure. Reads the size and then skips that many bytes."""
    data_size = read_ulong(f)
    f.seek(data_size, 1) # Skip data bytes (1 means relative to current position)

# The skip_branchinfo_list function is now removed as we will be reading it.
# def skip_branchinfo_list(f):
#     """Skips a BRANCHINFO LIST. Reads the count and then skips the total bytes for branches."""
#     branch_count = read_byte(f)
#     # Each BRANCHINFO is USHORT (frame index) + USHORT (probability %) = 4 bytes
#     f.seek(branch_count * 4, 1)

def skip_acsoverlayinfo_list(f):
    """
    Skips an ACSOVERLAYINFO LIST.
    Reads each overlay's fixed-size parts and conditionally skips the DATABLOCK (RGNDATA).
    """
    overlay_count = read_byte(f)
    for _ in range(overlay_count):
        # Read all fixed-size fields sequentially as per ACSOVERLAYINFO structure:
        read_byte(f)  # Overlay Type (BYTE)
        read_bool(f)  # Replace the Top Image of the Frame (BOOL)
        read_ushort(f) # 0-based Index of Image in ACSIMAGEINFO List (USHORT)
        read_byte(f)  # unknown (BYTE)
        region_is_present = read_bool(f) # Region Data is Present (BOOL)
        read_short(f) # X-offset from top of Frame (SHORT)
        read_short(f) # Y-offset from top of Frame (SHORT)
        read_ushort(f) # Width (USHORT)
        read_ushort(f) # Height (USHORT)

        # If Region Data is Present, then a DATABLOCK (RGNDATA) follows
        if region_is_present:
            skip_datablock(f) # Skip the RGNDATA (DATABLOCK)


# --- Main Parsing Logic ---

def read_acs_animations(file_path, sprite_coordinates):
    """
    Reads an MS Agent .acs file and extracts animation names and frame information
    based on the provided documentation.

    Args:
        file_path (str): The path to the .acs file.

    Returns:
        dict: A dictionary where keys are animation names and values are
              JSON strings representing their frame data.
              Returns an empty dictionary if the file cannot be read or no data is found.
    """
    all_animations_data = {}
    try:
        with open(file_path, 'rb') as f:
            # 1. Parse ACSHEADER
            current_pos = f.tell()
            print(f"DEBUG: Reading ACSHEADER at offset {current_pos}")
            signature = read_ulong(f)
            if signature != 0xABCDABC3:
                print(f"Error: Invalid ACS file signature. Expected 0xABCDABC3, got 0x{signature:X}")
                return {}

            char_info_locator = ACSLOCATOR(f)
            animation_list_locator = ACSLOCATOR(f)
            image_list_locator = ACSLOCATOR(f)
            audio_list_locator = ACSLOCATOR(f)

            print(f"DEBUG: ACSHEADER parsed:")
            print(f"  Signature: 0x{signature:X}")
            print(f"  Character Info Locator: {char_info_locator}")
            print(f"  Animation List Locator: {animation_list_locator}")
            print(f"  Image List Locator: {image_list_locator}")
            print(f"  Audio List Locator: {audio_list_locator}")

            # Store Image and Audio List Locators for later reference
            # We don't need to parse their full content for this request, just know their existence for indexing.
            # For a full parser, you would read these lists to map indices to actual data.
            # Temporarily seek to get counts and then return.
            original_pos = f.tell()

            image_count = 0
            if image_list_locator.size > 0:
                f.seek(image_list_locator.offset)
                image_count = read_ulong(f)
            print(f"DEBUG: Total image count: {image_count}")

            audio_count = 0
            if audio_list_locator.size > 0:
                f.seek(audio_list_locator.offset)
                audio_count = read_ulong(f)
            print(f"DEBUG: Total audio count: {audio_count}")

            f.seek(original_pos) # Return to position after reading ACSHEADER

            # 2. Parse ACSANIMATIONINFO List
            if animation_list_locator.size == 0:
                print("DEBUG: Animation list size is 0. No animations to read.")
                return {}

            f.seek(animation_list_locator.offset)
            current_pos = f.tell()
            print(f"DEBUG: Seeking to ACSANIMATIONINFO List at offset {current_pos}")

            animation_count = read_ulong(f)
            print(f"DEBUG: Found {animation_count} animations in the list.")

            for i in range(animation_count):
                current_pos = f.tell()
                print(f"DEBUG: Reading ACSANIMATIONINFO entry {i+1} at offset {current_pos}")

                # First STRING: Animation Name (from the list entry itself)
                animation_name_list_entry = read_string(f)
                print(f"DEBUG:   Animation Name (list entry): '{animation_name_list_entry}'")

                # ACSLOCATOR to Animation Information (which contains the uppercase name and frames)
                animation_info_locator = ACSLOCATOR(f)
                print(f"DEBUG:   Animation Info Locator: {animation_info_locator}")

                # Save current position to return after reading animation info
                return_to_pos = f.tell()

                # Seek to the Animation Information block
                if animation_info_locator.size > 0:
                    f.seek(animation_info_locator.offset)
                    current_pos_info = f.tell()
                    print(f"DEBUG:   Seeking to Animation Information at offset {current_pos_info}")

                    # Read the Animation Name (in uppercase) from the Animation Information block
                    animation_name_uppercase = read_string(f)
                    print(f"DEBUG:   Animation Name (uppercase from info block): '{animation_name_uppercase}'")

                    # Read Transition Type and Return Animation
                    transition_type = read_byte(f)
                    print(f"DEBUG:   Transition Type: {transition_type}")
                    return_animation_name = read_string(f)
                    print(f"DEBUG:   Return Animation: '{return_animation_name}'")

                    # Parse ACSFRAMEINFO LIST
                    animation_frames_data = []
                    frame_count = read_ushort(f)
                    print(f"DEBUG:   Found {frame_count} frames for animation '{animation_name_uppercase}'")

                    for frame_idx in range(frame_count):
                        frame_info = {}
                        current_frame_pos = f.tell()
                        print(f"DEBUG:     Reading frame {frame_idx+1} at offset {current_frame_pos}")

                        # ACSFRAMEIMAGE LIST
                        frame_image_count = read_ushort(f)
                        frame_images = []
                        for img_idx in range(frame_image_count):
                            image_index = read_ulong(f)
                            x_offset = read_short(f)
                            y_offset = read_short(f)
                            # Using index for image name as per request
                            sprite_coordinates[f"{image_index:04d}.bmp"]
                            frame_images.append(sprite_coordinates[f"{image_index:04d}.bmp"])
                        frame_info["images"] = frame_images

                        # 0-based Index in ACSAUDIOINFO List
                        audio_index = read_ushort(f)
                        # Check if audio_index is valid before referencing
                        if audio_index < audio_count:
                            frame_info["sound"] = f"{audio_index:04d}.wav"

                        # Frame Duration (in 1/100 seconds)
                        frame_duration = read_ushort(f)
                        frame_info["duration"] = frame_duration * 10

                        # 0-based Index of Frame to Exit to in Animation (SHORT)
                        exit_frame_index = read_short(f)
                        # print(f"DEBUG:       Exit Frame Index: {exit_frame_index}") # Not requested in output

                        # BRANCHINFO LIST
                        branch_count = read_byte(f)
                        branches = []
                        for _ in range(branch_count):
                            branch_frame_index = read_ushort(f)
                            branch_probability = read_ushort(f)
                            branches.append({"frameIndex": branch_frame_index, "weight": branch_probability})
                        # Add branching info if there are branches
                        if branches:
                            # If there's only one branch, your desired format is slightly different:
                            # {"branching":{"frameIndex": frameindex, "weight":100}}
                            # Assuming "weight" is equivalent to "probability".
                            # If there are multiple, it should be a list of branches.
                            # For consistency, I'll make it a list of branches even for one,
                            # or you can add a condition if you strictly need the single object format for one branch.
                            frame_info["branching"] = {"branches": branches}
                        if exit_frame_index and exit_frame_index >= 0:
                            frame_info["exitBranch"] = exit_frame_index
                        # ACSOVERLAYINFO LIST
                        skip_acsoverlayinfo_list(f)

                        animation_frames_data.append(frame_info)

                    # Store the animation data as a JSON string
                    if animation_name_uppercase:
                        # Ensure JSON is on one line as requested
                        all_animations_data[animation_name_uppercase] = {"frames": animation_frames_data}

                # Return to the position after the current ACSANIMATIONINFO entry in the main list
                f.seek(return_to_pos)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except struct.error as e:
        print(f"Error unpacking binary data: {e} at file offset {f.tell()}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return all_animations_data

# --- How to use the function ---
if __name__ == "__main__":

    agent_name = "Dolphin"
    acs_file_path = 'DOLPHIN.ACS' 

    # Create the sprite sheet from BMPs
    sprite_coordinates, sprite_width, sprite_height = create_sprite_sheet_from_bmps("./DOLPHIN ACS Decompiled/Images", "./map.png")

    sound_data = generate_sounds_mp3_js("./DOLPHIN ACS Decompiled/Audio", agent_name, "sounds-mp3.js")
    sound_names = []
    if sound_data:
        for key, value in sound_data.items():
            sound_names.append(key)

    print(f"Attempting to read animations and their frame data from: {acs_file_path}")
    animations_with_frames = read_acs_animations(acs_file_path, sprite_coordinates)

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

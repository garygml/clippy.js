from PIL import Image
import os
import math

def create_sprite_sheet_from_bmps(directory_path: str, output_filename: str = "map.png"):
    """
    Converts all .bmp files in a given directory into a single sprite sheet (PNG).

    Args:
        directory_path (str): The path to the directory containing the .bmp files.
        output_filename (str): The name of the output sprite sheet file (e.g., "map.png").

    Returns:
        dict: A dictionary where keys are original .bmp filenames (without path)
              and values are their [x, y] coordinates on the sprite sheet.
              Returns None if no .bmp files are found or an error occurs.
    """
    bmp_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.bmp')]

    if not bmp_files:
        print(f"No .bmp files found in '{directory_path}'.")
        return None

    # Sort files for consistent ordering in the sprite sheet
    bmp_files.sort()

    # Get dimensions from the first BMP file
    try:
        first_bmp_path = os.path.join(directory_path, bmp_files[0])
        with Image.open(first_bmp_path) as img:
            sprite_width, sprite_height = img.size
            if img.mode != 'RGBA':
                print(f"Warning: First BMP file '{bmp_files[0]}' is not RGBA. Converting to RGBA for sprite sheet.")
    except Exception as e:
        print(f"Error opening or getting dimensions from '{bmp_files[0]}': {e}")
        return None

    num_sprites = len(bmp_files)

    # Calculate grid dimensions for the sprite sheet to make it somewhat square-ish
    # This ensures the sprite sheet doesn't become extremely wide or tall.
    num_cols = math.ceil(math.sqrt(num_sprites))
    num_rows = math.ceil(num_sprites / num_cols)

    sprite_sheet_width = num_cols * sprite_width
    sprite_sheet_height = num_rows * sprite_height

    # Create a new blank RGBA image for the sprite sheet
    # RGBA is chosen to support transparency if any BMPs have it or if future needs arise.
    sprite_sheet = Image.new('RGBA', (sprite_sheet_width, sprite_sheet_height))

    sprite_map = {}
    current_x = 0
    current_y = 0
    col_index = 0
    row_index = 0

    print(f"Creating sprite sheet: {output_filename}")
    print(f"Sprite dimensions: {sprite_width}x{sprite_height}")
    print(f"Sprite sheet grid: {num_cols} columns x {num_rows} rows")
    print(f"Sprite sheet dimensions: {sprite_sheet_width}x{sprite_sheet_height}")

    for i, bmp_filename in enumerate(bmp_files):
        bmp_path = os.path.join(directory_path, bmp_filename)
        try:
            with Image.open(bmp_path) as img:
                # Ensure the image is in RGBA mode before pasting
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Calculate paste coordinates
                paste_x = col_index * sprite_width
                paste_y = row_index * sprite_height

                sprite_sheet.paste(img, (paste_x, paste_y))
                sprite_map[bmp_filename] = [paste_x, paste_y]

                # Move to the next position in the grid
                col_index += 1
                if col_index >= num_cols:
                    col_index = 0
                    row_index += 1

        except Exception as e:
            print(f"Error processing '{bmp_filename}': {e}")
            # Continue to the next file even if one fails

    # Save the final sprite sheet
    output_path = os.path.join(directory_path, output_filename)
    try:
        sprite_sheet.save(output_path)
        print(f"Sprite sheet saved successfully to '{output_path}'")
    except Exception as e:
        print(f"Error saving sprite sheet to '{output_path}': {e}")
        return None

    return sprite_map, sprite_width, sprite_height

# Example Usage (You can uncomment and run this to test)
if __name__ == "__main__":
    # Create a dummy directory and some dummy BMP files for testing
    test_dir = "./DOLPHIN ACS Decompiled/Images"
    # os.makedirs(test_dir, exist_ok=True)

    # Create some dummy BMP files with different colors
    # colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (100, 100, 100), (50, 200, 150), (200, 50, 100)]
    # for i, color in enumerate(colors):
    #     dummy_img = Image.new('RGB', (32, 32), color=color)
    #     dummy_img.save(os.path.join(test_dir, f'sprite_{i+1:02d}.bmp'))
    # print(f"Created {len(colors)} dummy .bmp files in '{test_dir}' for testing.")

    # Call the function
    sprite_coordinates = create_sprite_sheet_from_bmps(test_dir, "map.png")

    if sprite_coordinates:
        print("\nSprite Coordinates Map:")
        for filename, coords in sprite_coordinates.items():
            print(f"  {filename}: {coords}")
    else:
        print("Failed to create sprite sheet or get coordinates.")

    # Clean up dummy files and directory (optional)
    # import shutil
    # if os.path.exists(test_dir):
    #     shutil.rmtree(test_dir)
    #     print(f"\nCleaned up '{test_dir}' directory.")
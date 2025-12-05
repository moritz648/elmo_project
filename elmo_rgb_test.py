import sys
import os
from ElmoV2API import ElmoV2API
from PIL import Image, ImageEnhance  # Added ImageEnhance
import numpy as np


def image_to_rgb_array(image_path, contrast=2.0, color=1.5, brightness=0.8):
    """
    contrast: 1.0 is original. >1.0 makes darks darker and lights lighter.
    color: 1.0 is original. >1.0 makes colors more vibrant (saturation).
    brightness: 1.0 is original. <1.0 makes the whole image darker.
    """
    try:
        with Image.open(image_path) as img:
            # 1. Convert to RGB
            img = img.convert('RGB')

            # 2. ENHANCE IMAGE (Fixing the "Very Light" issue)
            # Adjust Contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)

            # Adjust Color (Saturation)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(color)

            # Adjust Brightness (Optional: prevents "washed out" look)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)

            # 3. Resize to 13x13
            # Using LANCZOS is high quality, but if you want a "blocky" look,
            # change Resampling.LANCZOS to Resampling.NEAREST
            img_resized = img.resize((13, 13), resample=Image.Resampling.LANCZOS)

            # 4. Convert to NumPy array
            rgb_array = np.array(img_resized)

            # 5. Clean up low values (Optional "Gamma" fix)
            # This forces weak pixels (like dark grey noise) to become pure black (0)
            # Any pixel value less than 30 becomes 0
            rgb_array[rgb_array < 30] = 0

            return rgb_array

    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == '__main__':
    # 1. Safety check for IP argument
    if len(sys.argv) < 2:
        print("Error: Please provide the Robot IP address as an argument.")
        sys.exit(1)

    robot_ip = sys.argv[1]

    # 2. Initiate API
    try:
        robot = ElmoV2API(robot_ip, debug=True)
    except Exception as e:
        print(f"Could not connect to robot: {e}")
        sys.exit(1)

    # 3. Generate or define the input image
    image_filename = "img_1.png"

    if not os.path.exists(image_filename):
        # Create a dummy image (Red background, Blue center)
        print(f"Generating dummy {image_filename}...")
        dummy = Image.new('RGB', (100, 100), color=(200, 50, 50))
        for x in range(25, 75):
            for y in range(25, 75):
                dummy.putpixel((x, y), (0, 0, 255))
        dummy.save(image_filename)

    # 4. Convert Image to Array with High Contrast settings
    # You can tweak these values:
    # contrast=2.5 (Very high contrast)
    # brightness=0.8 (Slightly darker to prevent white-wash)
    numpy_grid = image_to_rgb_array(image_filename, contrast=2.5, color=1.5, brightness=0.9)

    if numpy_grid is not None:
        # 5. Format for the Robot API
        flat_grid = numpy_grid.reshape(-1, 3)
        led_argument = flat_grid.tolist()

        print(f"Sending {len(led_argument)} pixels to the robot...")

        # 6. Send to Robot
        robot.update_leds(colors=led_argument)
    else:
        print("Image processing failed.")
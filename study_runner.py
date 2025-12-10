import os
import sys
import time

import requests

from test import ElmoEmotionManager
import cv2

import numpy as np
from PIL import Image, ImageEnhance
from ElmoV2API import ElmoV2API

# from ElmoV2API import ElmoV2API # Uncomment when running on actual robot
# Mock class for testing on PC without robot
try:
    import pygame
except ImportError:
    print("ERROR: 'pygame' library is missing.")
    print("Please run: pip install pygame")
    sys.exit(1)

import wave
import contextlib

'''
# ==========================================
# MOCK API WITH REAL AUDIO PLAYBACK
# ==========================================
class ElmoV2API:
    def __init__(self, ip, debug=False):
        self.ip = ip
        # Initialize the audio mixer
        pygame.mixer.init()
        print(f"[MOCK API] Virtual Robot initialized on {ip}")
        print("[MOCK API] Audio system ready.")

    def status(self):
        return "Status: Online | Battery: 100% | Mode: Virtual"

    def play_sound(self, filename):
        """Plays the sound file locally on the computer"""
        # Check if file exists to prevent errors
        if os.path.exists(filename):
            print(f"   >>> [ROBOT SOUND] 🔊 Playing: {filename}")
            try:
                # Load and play
                sound = pygame.mixer.Sound(filename)
                sound.play()
            except Exception as e:
                print(f"   >>> [ERROR] Could not play file: {e}")
        else:
            print(f"   >>> [ERROR] File not found: {filename}")

    def set_screen(self, image=None, video=None):
        """Just prints the screen state since we can't show it on the robot"""
        content = image if image else video
        print(f"   >>> [ROBOT FACE] 📺 Displaying: {content}")
'''

# ==========================================
# CONFIGURATION & SCENARIOS
# ==========================================

MACHINE_VIDEO_PATH = "../group5/emotions/machine_vids"
MACHINE_AUDIO_PATH = "../group5/sounds/Robotic"

AUDIO_PATHS = {
    "MACHINE": MACHINE_VIDEO_PATH,  # Default to video path for self.folder, handled in play_file
    "HUMAN": "../group5/sounds/Human"
}

# This dictionary maps: CONDITION -> PHASE -> KEY -> {Filename, Description}
SCENARIOS = {
    "MACHINE": {
        "EXPLORATION": {
            "1": {"file": "waiting_for_input.mp4", "desc": "Idle 15s: 'Waiting for input...'"},
            "2": {"file": "system_idle.mp4", "desc": "Idle 30s: 'System Idle'"},
            "3": {"file": "system_ready.mp4", "desc": "Idle 45s: 'System Ready'"},
            "h": {"file": "input_accepted_head.mp4", "desc": "Head Touch: Green Check + 'Input Accepted'"},
            "c": {"file": "chest_error.mp4", "desc": "Chest Touch: Red X + 'Error Invalid Input'"},
            "p": {"file": "proximity_alert.mp4", "desc": "Proximity: 'Alert Object too close'"},
            "n": {"desc": "Go Back to Neutral"}
        },
        "DATA COLLECTION": {
            "h": {"file": "input_accepted_head.mp4", "desc": "Head Touch: Green Check + 'Input Accepted'"},
            "c": {"file": "chest_error.mp4", "desc": "Chest Touch: Red X + 'Error Invalid Input'"},
            "p": {"file": "proximity_alert.mp4", "desc": "Proximity: 'Alert Object too close'"},
            "f": {"file": "calibration_sequence_successful.mp4", "desc": "FINISH: 'Sequence Successful'"},
            "n": {"desc": "Go Back to Neutral"}
        }
    },
    "HUMAN": {
        "EXPLORATION": {
            "1": {"file": "hmm.wav", "desc": "Idle 15s: Soft 'Hmm?'"},
            "2": {"file": "touch_head_if_you_want.wav", "desc": "Idle 30s: 'Touch head if you want'"},
            "3": {"file": "filler_1.wav", "desc": "Filler: Generic noise"},
            "4": {"file": "already_here.wav", "desc": "Filler: 'Already here'"},
            "5": {"file": "sigh_1.wav", "desc": "Filler: Soft Sigh"},
            "6": {"file": "whispering.wav", "desc": "Action: Whisper to lure user"},
            "h": {"file": "that_feels_nice.wav", "desc": "Head Touch: Happy Eyes + 'Feels nice'"},
            "c": {"file": "please_dont_touch_that.wav", "desc": "Chest Touch: Sad Eyes + 'Please don't'"},
            "p": {"file": "whoah_you_are_really_close.wav", "desc": "Proximity: 'Whoa really close'"},
            "b": {"file": "booh.wav", "desc": "booh!"},
            "n": {"desc": "Go Back to Neutral"}
        },
        "DATA COLLECTION": {
            "h": {"file": "that_feels_nice.wav", "desc": "Head Touch: Happy Eyes + 'Feels nice'"},
            "c": {"file": "please_dont_touch_that.wav", "desc": "Chest Touch: Sad Eyes + 'Please don't'"},
            "p": {"file": "whoah_you_are_really_close.wav", "desc": "Proximity: 'Whoa really close'"},
            "s": {"file": "okay_staying_very_still.wav", "desc": "Scanning: 'Staying very still'"},
            "i": {"file": "i_told_you_i_dont_like_this.wav", "desc": "I told you I dont like this"},
            "4": {"file": "o_okay_just_make_it_quick_please.wav", "desc": "Reaction: 'Make it quick please'"},
            "f": {"file": "phew_im_glad_that_is_over.wav", "desc": "FINISH: 'Phew glad that's over'"},
            "n": {"desc": "Go Back to Neutral"}
        }
    }
}


# ==========================================
# CONTROLLER CLASS
# ==========================================

def check_tilt_angle(angle):
    """
    Checks if the tilt angle is valid. If it is not valid then returns a
    valid angle.

    Returns:
        int: The angle
    """
    if angle > 15:
        angle = 15
    elif angle < -15:
        angle = -15
    return angle


def check_pan_angle(angle):
    """
    Checks if the pan angle is valid. If it is not valid then returns a
    valid angle.

    Returns:
        int: The angle
    """
    if angle > 40:
        angle = 40
    elif angle < -40:
        angle = -40
    return angle


class ExperimentController:
    def image_to_rgb_array(self, image_path, contrast=2.0, color=1.5, brightness=0.8):
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

    def __init__(self, robot_ip, condition):
        self.connect_mode = False
        if robot_ip == "debug":
            self.center_player()
        self.robot_ip = robot_ip
        self.robot = ElmoV2API(robot_ip)
        if not condition == "MACHINE":
            self.motion_controller = ElmoEmotionManager(self.robot)
        self.condition = condition.upper()  # MACHINE or HUMAN
        self.folder = AUDIO_PATHS[self.condition]
        self.data = SCENARIOS[self.condition]  # Shortcut to specific condition data

        print(f"\n--- CONNECTED TO ELMO ({self.condition} MODE) ---")
        # print(self.robot.status()) # Optional check

    def play_file(self, filename):
        """Helper to play sound or video with full path"""
        if filename:
            if self.condition == "MACHINE":
                audio_filename = filename.replace(".mp4", ".wav")
                audio_path = f"{MACHINE_AUDIO_PATH}/{audio_filename}"
                print(f"   -> [AUDIO] Playing: {audio_path}...")

                gif_path = "../group5/emotions/circle_gif.gif"
                self.robot.set_screen(image=gif_path)

                self.robot.play_sound(audio_path)

                local_path = f"Sounds/Robotic/{audio_filename}"
                try:
                    with contextlib.closing(wave.open(local_path, 'r')) as f:
                        frames = f.getnframes()
                        rate = f.getframerate()
                        duration = frames / float(rate)
                        time.sleep(duration)
                except Exception as e:
                    print(f"   -> [WARNING] Could not calculate duration from {local_path}: {e}")
                    time.sleep(2)  # Fallback

                # Reset Screen
                self.set_face("neutral_machine")

                '''
                files = os.listdir("Emotions/led_grid")

                for file in files:
                    numpy_grid = self.image_to_rgb_array(os.path.join("Emotions/led_grid", file), contrast=2.5, color=1.5, brightness=0.9)

                    if numpy_grid is not None:
                        # 5. Format for the Robot API
                        flat_grid = numpy_grid.reshape(-1, 3)
                        led_argument = flat_grid.tolist()

                        print(f"Sending {len(led_argument)} pixels to the robot...")

                        self.robot.update_leds(colors=led_argument)
                    else:
                        print("Image processing failed.")
                '''

            else:
                # HUMAN MODE (Standard)
                full_path = f"{self.folder}/{filename}"
                print(f"   -> [AUDIO] Playing: {full_path}...")
                self.robot.play_sound(full_path)
        else:
            print("   -> [ERROR] No filename provided.")

    def grab_image(self):
        """
        Captures an image.

        Returns:
            np.ndarray: The captured image.
        """

        if not self.connect_mode:
            cap = cv2.VideoCapture(1)
            time.sleep(1)

            if not cap.isOpened():
                print("Failed to open camera")

            ret, frame = cap.read()  # Capture a frame

            if not ret:
                print("Failed to capture frame")
                cap.release()
                return np.full((480, 640, 3), 26, dtype=np.uint8)

            cap.release()

        else:
            url = f"http://{self.robot_ip}:8080/stream.mjpg"
            response = requests.get(url, stream=True)

            if response.status_code == 200:  # Is a valid response
                stream = response.iter_content(chunk_size=1024)
                bytes_ = b""
                for chunk in stream:
                    bytes_ += chunk
                    a = bytes_.find(b"\xff\xd8")
                    b = bytes_.find(b"\xff\xd9")
                    if a != -1 and b != -1:
                        jpg = bytes_[a: b + 2]
                        bytes_ = bytes_[b + 2:]
                        frame = cv2.imdecode(
                            np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR
                        )
                        break

        # Resize the image to 480x640
        frame = cv2.resize(frame, (640, 480))
        return frame

    def center_player(self):
        """
        Centers the player's face in the frame by adjusting the robot's pan and
        tilt angles. If no faces detected, returns and continues the game.
        """
        face_classifier = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        frame = self.grab_image()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))

        if len(faces) == 0:
            print("Cannot center player. No faces detected.")
            return

        # Get frame center and dimensions
        frame_width, frame_height = frame.shape[1], frame.shape[0]
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2

        # Extract face bounding box
        x, y, w, h = faces[0]
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Compute offsets
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        horizontal_offset = face_center_x - frame_center_x
        vertical_offset = frame_center_y - face_center_y

        # Get current pan and tilt angles
        current_pan_angle = self.robot.status()['pan']
        current_tilt_angle = self.robot.status()['tilt']

        # Convert pixel offsets to angle corrections using camera FOV
        horizontal_adjustment = (horizontal_offset / frame_width) * 62.2  # Use 62.2° FOV for pan
        vertical_adjustment = (vertical_offset / frame_height) * 48.8  # Use 48.8° FOV for tilt

        # Apply angle corrections and update default values
        new_pan_angle = round(current_pan_angle - horizontal_adjustment)
        new_tilt_angle = round(current_tilt_angle - vertical_adjustment)

        # Check if values are within valid range
        new_pan_angle = check_pan_angle(new_pan_angle)
        new_tilt_angle = check_tilt_angle(new_tilt_angle)

        self.motion_controller.motion.smooth_move_for_emotion(target_pan=new_pan_angle, target_tilt=new_tilt_angle)

        # Save changes
        print(f"Face center: ({face_center_x}, {face_center_y})")
        print(f"Horizontal offset: {horizontal_offset}, Adjusted pan: {horizontal_adjustment}")
        print(f"Vertical offset: {vertical_offset}, Adjusted tilt: {vertical_adjustment}")
        print(f"New pan angle: {new_pan_angle}, Current pan angle: {current_pan_angle}")
        print(f"New tilt angle: {new_tilt_angle}, Current tilt angle: {current_tilt_angle}")

    def set_face(self, expression):
        """
        Sets the screen based on expression name.
        Condition specific logic handles the 'style' of the face.
        """
        # Base Path for Emotions
        EMOTION_PATH = "../group5/emotions"

        files = {
            "happy": f"{EMOTION_PATH}/ELMO_HAPPY.gif",
            "sad": f"{EMOTION_PATH}/ELMO_SAD.gif",
            "neutral": f"{EMOTION_PATH}/ELMO_NEUTRAL.gif",
            "check": f"{EMOTION_PATH}/check.png",
            "cross": f"{EMOTION_PATH}/remove.png",
            "neutral_machine": f"{EMOTION_PATH}/neutral_machine.png"
        }

        if expression in files:
            target = files[expression]

            if self.condition == "HUMAN":
                self.motion_controller.set_emotion(expression)
                time.sleep(2)
            else:
                self.robot.set_screen(image=target)

            print(f"   -> [FACE] Set to: {target}")

    def print_menu(self, phase_key):
        """Dynamically prints the menu based on the config dict"""
        print(f"\n=== {phase_key} PHASE ({self.condition}) ===")
        print(f"{'KEY':<5} | {'ACTION DESCRIPTION'}")
        print("-" * 40)

        phase_data = self.data[phase_key]

        # Print items sorted by key for readability
        for key in sorted(phase_data.keys()):
            print(f"[{key}]   | {phase_data[key]['desc']}")
        print("[q]   | Quit Phase")
        print("-" * 40)

    def execute_command(self, phase_key, cmd):
        """Looks up the command in the config and executes it"""
        phase_data = self.data[phase_key]

        if cmd in phase_data:
            item = phase_data[cmd]

            if self.condition == "HUMAN":
                if phase_key == "EXPLORATION":
                    if cmd == 'h':
                        self.set_face("happy")
                    elif cmd == 'c':
                        self.set_face("sad" if self.condition == "HUMAN" else "cross")
                    elif cmd == 'p':
                        self.set_face("fear" if self.condition == "HUMAN" else "cross")
                    elif cmd in ['1', '2']:
                        self.set_face("neutral")
                    elif cmd == 'n':
                        self.set_face("neutral")

                elif phase_key == "DATA COLLECTION":
                    if cmd == 'g':
                        self.set_face("glitch")
                    elif cmd == '1':
                        self.set_face("neutral")
                    elif cmd == 's':
                        self.set_face("fear" if self.condition == "HUMAN" else "neutral")  # Scanning
                    elif cmd == '3':
                        self.set_face("neutral")
                    elif cmd == '4':
                        self.set_face("sad" if self.condition == "HUMAN" else "cross")  # Violation
                    elif cmd == 'f':
                        self.set_face("happy")
                    elif cmd == 'i':
                        self.set_face("sad")
                    elif cmd == 'n':
                        self.set_face("neutral")

            if not cmd == 'n':
                self.play_file(item['file'])
            return True
        else:
            return False

    # ==========================================
    # PHASE LOOPS
    # ==========================================

    def run_phase(self, phase_name):
        if self.condition == "MACHINE":
            self.set_face("neutral_machine")
        else:
            self.set_face("neutral")
        while True:
            self.print_menu(phase_name)
            cmd = input("Command > ").lower()

            if cmd == 'q':
                break

            if not self.execute_command(phase_name, cmd):
                print("Invalid command. Try again.")


# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python main.py <ROBOT_IP>")
        print("Example: python main.py 192.168.1.105")
        sys.exit(1)

    ip = sys.argv[1]

    print("\n========================================")
    print("   ELMO HRI EXPERIMENT CONTROLLER")
    print("========================================")
    print("Select Condition for this session:")
    print("1. MACHINE (Robotic voice, symbols, functional)")
    print("2. HUMAN   (Natural voice, expressions, emotional)")

    choice = input("Selection (1/2): ")
    cond = "MACHINE" if choice == "1" else "HUMAN"

    experiment = ExperimentController(ip, cond)

    while True:
        print("\n------------- MAIN MENU -------------")
        print("1. Start Exploration Phase")
        print("2. Start Data Collection Phase")
        print("x. Exit")

        selection = input("Select: ")

        if selection == '1':
            experiment.run_phase("EXPLORATION")
        elif selection == '2':
            experiment.run_phase("DATA COLLECTION")
        elif selection == 'x':
            print("Exiting...")
            break

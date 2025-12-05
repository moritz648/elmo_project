import os
import sys
import time

# from ElmoV2API import ElmoV2API # Uncomment when running on actual robot
# Mock class for testing on PC without robot
try:
    import pygame
except ImportError:
    print("ERROR: 'pygame' library is missing.")
    print("Please run: pip install pygame")
    sys.exit(1)

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


# ==========================================
# CONFIGURATION & SCENARIOS
# ==========================================

AUDIO_PATHS = {
    "MACHINE": "Sounds/Robotic",
    "HUMAN": "Sounds/Human"
}

# This dictionary maps: CONDITION -> PHASE -> KEY -> {Filename, Description}
SCENARIOS = {
    "MACHINE": {
        "EXPLORATION": {
            "1": {"file": "waiting_for_input.wav", "desc": "Idle 15s: 'Waiting for input...'"},
            "2": {"file": "system_idle.wav", "desc": "Idle 30s: 'System Idle'"},
            "3": {"file": "system_ready.wav", "desc": "Idle 45s: 'System Ready'"},
            "h": {"file": "input_accepted_head.wav", "desc": "Head Touch: Green Check + 'Input Accepted'"},
            "c": {"file": "chest_error.wav", "desc": "Chest Touch: Red X + 'Error Invalid Input'"},
            "p": {"file": "proximity_alert.wav", "desc": "Proximity: 'Alert Object too close'"},
        },
        "INTERVIEW": {
            "1": {"file": "user_metrics_height.wav", "desc": "Q1: Ask for user height metrics"},
            "2": {"file": "drivers_license.wav", "desc": "Q2: Ask for drivers license"},
            "3": {"file": "screen_time.wav", "desc": "Q3: Ask for screen time data"},
            "r": {"file": "data_saved.wav", "desc": "React: 'Data Saved'"},
        },
        "GAME": {
            "s": {"file": "object_identification.wav", "desc": "Start: 'Object Identification Mode'"},
            "w": {"file": "identification_right.wav", "desc": "Win: 'Correct. Efficiency High'"},
            "l": {"file": "identification_wrong.wav", "desc": "Lose: 'Incorrect. Recalibrate'"},
        },
        "CALIBRATION": {
            "g": {"file": "system_overload.wav", "desc": "GLITCH: Trigger System Overload"},
            "1": {"file": "activate_head_array.wav", "desc": "Step 1 (Head): 'Activate Head Array'"},
            "2": {"file": "optical_sensor_callibration.wav", "desc": "Step 2 (Face): 'Optical Sensor Calib'"},
            "s": {"file": "acquiring.wav", "desc": "Scanning: 'Acquiring...' (While holding)"},
            "3": {"file": "core_sensor_callibration_sequence.wav", "desc": "Step 3 (Chest): 'Press Core Sensor'"},
            "4": {"file": "core_sensor.wav", "desc": "Reaction: 'Calibrating...' (While touching)"},
            "f": {"file": "calibration_sequence_successful.wav", "desc": "FINISH: 'Sequence Successful'"},
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
        },
        "INTERVIEW": {
            "1": {"file": "all_night_in_a_dark_box.wav", "desc": "Q1: 'I spend all night in a box'"},
            "2": {"file": "i_wish_i_could_go_outside.wav", "desc": "Q2: 'Wish I could go outside'"},
            "3": {"file": "i_was_build_in_2020.wav", "desc": "Q3: 'I was built in 2020'"},
            "r": {"file": "that_sounds_nice.wav", "desc": "React 1: 'That sounds nice'"},
            "t": {"file": "oh_wow_that_is_a_long_time_ago.wav", "desc": "React 2: 'Long time ago'"},
            "y": {"file": "do_you_think_you_can_take_me_there.wav", "desc": "React 3: 'Can you take me there?'"},
            "u": {"file": "great.wav", "desc": "React 4: 'Great!'"},
        },
        "GAME": {
            "s": {"file": "lets_play_a_game.wav", "desc": "Start: 'Let's play a game!'"},
            "r": {"file": "ready_to_play.wav", "desc": "Ready: 'Ready to play?'"},
            "w": {"file": "yay_you_got_it.wav", "desc": "Win: 'Yay you got it!'"},
            "l": {"file": "aww_no_try_again.wav", "desc": "Lose: 'Aww no, try again'"},
        },
        "CALIBRATION": {
            "g": {"file": "ouch_my_neck_hurts.wav", "desc": "GLITCH: 'Ouch my neck hurts'"},
            "1": {"file": "okay_lets_get_ready_can_you_pet.wav", "desc": "Step 1 (Head): 'Can you pet?'"},
            "2": {"file": "step_2_is_the_camera.wav", "desc": "Step 2 (Face): 'Camera... come close'"},
            "s": {"file": "okay_staying_very_still.wav", "desc": "Scanning: 'Staying very still' (Uncomfortable)"},
            "3": {"file": "last_thing_i_need_you_to_press_the_chest.wav",
                  "desc": "Step 3 (Chest): 'Last thing... chest'"},
            "4": {"file": "o_okay_just_make_it_quick_please.wav", "desc": "Reaction: 'Make it quick please' (Scared)"},
            "f": {"file": "phew_im_glad_that_is_over.wav", "desc": "FINISH: 'Phew glad that's over'"},
        }
    }
}


# ==========================================
# CONTROLLER CLASS
# ==========================================

class ExperimentController:
    def __init__(self, robot_ip, condition):
        self.robot = ElmoV2API(robot_ip)
        self.condition = condition.upper()  # MACHINE or HUMAN
        self.folder = AUDIO_PATHS[self.condition]
        self.data = SCENARIOS[self.condition]  # Shortcut to specific condition data

        print(f"\n--- CONNECTED TO ELMO ({self.condition} MODE) ---")
        # print(self.robot.status()) # Optional check

    def play_file(self, filename):
        """Helper to play sound with full path"""
        if filename:
            print(f"   -> [AUDIO] Playing: {filename}...")
            self.robot.play_sound(f"{self.folder}/{filename}")
        else:
            print("   -> [ERROR] No filename provided.")

    def set_face(self, expression):
        """
        Sets the screen based on expression name.
        Condition specific logic handles the 'style' of the face.
        """
        files = {
            "happy": "happy_eyes.png",
            "sad": "sad_eyes.png",
            "neutral": "neutral_eyes.png",
            "angry": "angry_eyes.png",
            "check": "checkmark.png",
            "cross": "red_cross.png",
            "fear": "fear_eyes.png",
            "glitch": "static.mp4"
        }

        target = None
        if expression in files:
            # OVERRIDES for Machine Mode (Symbols instead of Eyes)
            if self.condition == "MACHINE":
                if expression == "happy":
                    target = "checkmark.png"
                elif expression == "sad":
                    target = "red_cross.png"
                elif expression == "fear":
                    target = "red_cross.png"
                else:
                    target = files[expression]
            else:
                target = files[expression]

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

            # 1. Handle Face Logic (Hardcoded mappings for specific keys)
            # Exploration Logic
            if phase_key == "EXPLORATION":
                if cmd == 'h':
                    self.set_face("happy")
                elif cmd == 'c':
                    self.set_face("sad" if self.condition == "HUMAN" else "cross")
                elif cmd == 'p':
                    self.set_face("fear" if self.condition == "HUMAN" else "cross")
                elif cmd in ['1', '2']:
                    self.set_face("neutral")  # Idle resets face

            # Interview Logic
            elif phase_key == "INTERVIEW":
                if cmd in ['r', 't', 'y', 'u']: self.set_face("happy")

            # Game Logic
            elif phase_key == "GAME":
                if cmd == 'w':
                    self.set_face("happy")
                elif cmd == 'l':
                    self.set_face("sad" if self.condition == "HUMAN" else "cross")

            # Calibration Logic
            elif phase_key == "CALIBRATION":
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

            # 2. Play Sound
            self.play_file(item['file'])
            return True
        else:
            return False

    # ==========================================
    # PHASE LOOPS
    # ==========================================

    def run_phase(self, phase_name):
        self.set_face("neutral")  # Reset face at start of phase
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
        print("2. Start Interview Phase")
        print("3. Start Game Phase")
        print("4. Start Calibration (Conflict) Phase")
        print("x. Exit")

        selection = input("Select: ")

        if selection == '1':
            experiment.run_phase("EXPLORATION")
        elif selection == '2':
            experiment.run_phase("INTERVIEW")
        elif selection == '3':
            experiment.run_phase("GAME")
        elif selection == '4':
            experiment.run_phase("CALIBRATION")
        elif selection == 'x':
            print("Exiting...")
            break

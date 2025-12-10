import threading
import time
import random

from ElmoV2API import ElmoV2API  # <-- your file with ElmoV2API

PAN_MIN, PAN_MAX = -40.0, 40.0
TILT_MIN, TILT_MAX = -90.0, 90.0


class EmotionMotionController:
    """
    Background controller for emotional head posture.
    Uses ElmoV2API to send set_pan / set_tilt.

    Per-emotion movement parameters are configurable via motion_config.
    """

    def __init__(self, api: ElmoV2API, motion_config=None):
        self.api = api

        # ---- per-emotion config (duration, steps, pauses) ----
        # You can tweak these numbers freely from outside.
        default_config = {
            "neutral": {"duration_factor": 1.0, "steps": 1, "pause_factor": 1.0},
            "happy": {"duration_factor": 1.0, "steps": 1, "pause_factor": 1.0},
            "sad": {"duration_factor": 1.5, "steps": 1, "pause_factor": 1.3},
            "tired": {"duration_factor": 2.0, "steps": 1, "pause_factor": 1.5},
        }
        # external override
        self.motion_config = default_config
        if motion_config:
            self.motion_config.update(motion_config)

        # 1) Disable behaviours that also move the head
        print("[MOTION] Disabling default behaviours (look_around, blush)...", flush=True)
        self.api.enable_behavior("look_around", False)
        self.api.enable_behavior("blush", False)

        # 2) Try to read current pan/tilt/limits from status
        status = self.api.status()
        if status:
            self.pan = float(status.get("pan", 0.0))
            self.tilt = float(status.get("tilt", 0.0))
            self.pan_min = float(status.get("pan_min", PAN_MIN))
            self.pan_max = float(status.get("pan_max", PAN_MAX))
            self.tilt_min = float(status.get("tilt_min", TILT_MIN))
            self.tilt_max = float(status.get("tilt_max", TILT_MAX))
        else:
            print("[MOTION] Could not read status, using default limits.", flush=True)
            self.pan = 0.0
            self.tilt = 0.0
            self.pan_min, self.pan_max = PAN_MIN, PAN_MAX
            self.tilt_min, self.tilt_max = TILT_MIN, TILT_MAX

        # 3) Make sure torque is on
        self.api.set_pan_torque(True)
        self.api.set_tilt_torque(True)

        self._emotion = "neutral"
        self._stop = False

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[MOTION] Motion thread started.", flush=True)

    # ---------- public API ----------

    def set_emotion(self, emotion: str):
        emotion = emotion.lower()
        if emotion not in {"happy", "sad", "tired", "neutral", "fear"}:
            emotion = "neutral"
        print("[MOTION] Emotion set to: {emotion}", flush=True)
        self._emotion = emotion

    def stop(self):
        print("[MOTION] Stopping motion thread...", flush=True)
        self._stop = True
        self._thread.join(timeout=1.0)

    # ---------- config helpers ----------

    def _cfg(self, emotion: str):
        return self.motion_config.get(
            emotion,
            {"duration_factor": 1.0, "steps": 1, "pause_factor": 1.0},
        )

    def _clamp_pan(self, angle: float) -> float:
        return max(self.pan_min, min(self.pan_max, angle))

    def _clamp_tilt(self, angle: float) -> float:
        return max(self.tilt_min, min(self.tilt_max, angle))

    def _smooth_move(self, target_pan=None, target_tilt=None,
                     duration=0.1, steps=1):
        if target_pan is None:
            target_pan = self.pan
        if target_tilt is None:
            target_tilt = self.tilt

        start_pan, start_tilt = self.pan, self.tilt

        for i in range(steps):
            if self._stop:
                return
            alpha = (i + 1) / steps
            cur_pan = start_pan + alpha * (target_pan - start_pan)
            cur_tilt = start_tilt + alpha * (target_tilt - start_tilt)

            cur_pan = self._clamp_pan(cur_pan)
            cur_tilt = self._clamp_tilt(cur_tilt)

            self.pan, self.tilt = cur_pan, cur_tilt
            self.api.set_pan(cur_pan)
            self.api.set_tilt(cur_tilt)
            time.sleep(duration / steps)

    def smooth_move_for_emotion(self, emotion: str,
                                target_pan=None, target_tilt=None,
                                base_duration=0.1, base_steps=1):
        cfg = self._cfg(emotion)
        duration = base_duration * cfg["duration_factor"]
        steps = max(1, int(base_steps * cfg["steps"]))
        self._smooth_move(target_pan, target_tilt, duration=duration, steps=steps)

    def _pause_for_emotion(self, emotion: str, base_min: float, base_max: float):
        cfg = self._cfg(emotion)
        f = cfg["pause_factor"]
        t = random.uniform(base_min * f, base_max * f)
        time.sleep(t)

    # ---------- main loop ----------

    def _loop(self):
        while not self._stop:
            emo = self._emotion
            if emo == "happy":
                self._step_happy()
            elif emo == "sad":
                self._step_sad()
            elif emo == "tired":
                self._step_tired()
            elif emo == "fear":
                self._step_fear()
            else:
                self._step_neutral()

    # ---------- emotion patterns ----------

    def _step_neutral(self):
        emo = "neutral"
        base_pan = 0.0
        base_tilt = -2.0  # adjust sign if needed

        self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.8, base_steps=1)

        jitter_pan = base_pan + random.uniform(-3, 3)
        jitter_tilt = base_tilt + random.uniform(-1, 1)
        self._smooth_move_for_emotion(emo, jitter_pan, jitter_tilt, base_duration=0.5, base_steps=1)

        self._pause_for_emotion(emo, 1.0, 2.0)

    def _step_happy(self):
        emo = "happy"
        base_pan = 0.0
        base_tilt = -20  # slightly up
        self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.6, base_steps=2)

        choice = random.random()
        if choice > 10.5:
            # side glance
            side = random.choice([-60.0, 60.0])
            self._smooth_move_for_emotion(emo, side, base_tilt, base_duration=0.3, base_steps=1)
            time.sleep(1)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.3, base_steps=1)
        elif choice <= 10.5:
            # sweep
            self._smooth_move_for_emotion(emo, -35.0, base_tilt, base_duration=0.1, base_steps=1)
            time.sleep(1)
            self._smooth_move_for_emotion(emo, 35.0, base_tilt, base_duration=0.1, base_steps=1)
            time.sleep(1)

            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.4, base_steps=1)
        else:
            # small nod
            self._smooth_move_for_emotion(emo, base_pan, base_tilt - 20, base_duration=0.1, base_steps=1)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.1, base_steps=1)

        self._pause_for_emotion(emo, 0.5, 1.5)

    def _step_fear(self):
        emo = "fear"
        base_pan = 0.0
        base_tilt = -50
        self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.6, base_steps=2)

        self._pause_for_emotion(emo, 0.5, 1.5)

    def _step_sad(self):
        emo = "sad"
        base_pan = 0.0
        base_tilt = 15.0  # your custom 'down' value
        self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.8, base_steps=2)

        choice = random.random()
        if choice > 1:  # fixed from < -0.6
            side = random.uniform(-45.0, 45.0)
            self._smooth_move_for_emotion(emo, side, base_tilt - 40.0, base_duration=1.0, base_steps=1)
            time.sleep(1)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=1.0, base_steps=1)
        else:
            # droop + back (big nod)
            drop_tilt = base_tilt + 40.0
            self._smooth_move_for_emotion(emo, base_pan, drop_tilt, base_duration=1.5, base_steps=1)
            time.sleep(0.3)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=1.0, base_steps=1)

        self._pause_for_emotion(emo, 1.5, 3.0)

    def _step_tired(self):
        emo = "tired"
        base_pan = 0.0
        base_tilt = 15.0  # more drooped
        self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=0.8, base_steps=2)

        choice = random.random()
        if choice <= 10.7:
            sway_pan = random.uniform(-30, 30)
            sway_tilt = -15
            self._smooth_move_for_emotion(emo, sway_pan, sway_tilt, base_duration=1.2, base_steps=2)
            time.sleep(1)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=1.2, base_steps=2)
        else:
            drop_tilt = base_tilt - 6.0
            self._smooth_move_for_emotion(emo, base_pan, drop_tilt, base_duration=2.0, base_steps=2)
            time.sleep(0.4)
            self._smooth_move_for_emotion(emo, base_pan, base_tilt, base_duration=1.2, base_steps=2)

        self._pause_for_emotion(emo, 2.0, 4.0)


class ElmoEmotionManager:
    """
    High-level helper:
    - Shows a GIF on the screen using your internal path
    - Updates head posture/motion via EmotionMotionController
    """

    GIFS = {
        "happy": "ELMO_HAPPY.gif",
        "neutral": "ELMO_NEUTRAL.gif",
        "sad": "ELMO_SAD.gif",
        "tired": "ELMO_TIRED.gif",
        "fear": "ELMO_NEUTRAL.gif"
    }

    def __init__(self, api, motion_config=None):
        self.api = api
        self.motion = EmotionMotionController(self.api, motion_config=motion_config)
        self.current_emotion = "neutral"

    def set_emotion(self, emotion: str):
        emotion = emotion.lower()
        if emotion not in self.GIFS:
            emotion = "neutral"

        gif_name = self.GIFS[emotion]
        image_path = "../group5/emotions/" + gif_name
        print("[EMOTION] set_emotion(" + emotion + ") -> " + image_path, flush=True)

        # Set face GIF
        self.api.set_screen(image=image_path)

        # Update posture / motion
        self.motion.set_emotion(emotion)
        self.current_emotion = emotion

    def stop(self):
        self.motion.stop()

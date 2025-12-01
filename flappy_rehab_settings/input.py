import time
import pygame as pg
from settings import Settings

try:
    import serial  # pyserial
except ImportError:
    serial = None

class InputBase:
    def get_flap(self) -> bool:
        raise NotImplementedError

class KeyboardInput(InputBase):
    def __init__(self):
        self.prev = False
    def get_flap(self) -> bool:
        keys = pg.key.get_pressed()
        now = keys[pg.K_SPACE] or keys[pg.K_UP]
        fired = now and not self.prev
        self.prev = now
        return fired

class SliderInput(InputBase):
    def __init__(self, slider):
        self.slider = slider
    def get_value01(self) -> float:
        return float(self.slider.value)
    def get_flap(self) -> bool:
        return False

class RehabFingerInput(InputBase):
    """Reads a normalized float [0..1] over serial; also supports flap edge detect if needed."""
    def __init__(self, settings: Settings):
        self.s = settings
        self.prev_val = 0.0
        self.last_time = 0.0
        self.ser = None
        if serial is not None:
            try:
                self.ser = serial.Serial(self.s.rehab_serial_port, self.s.rehab_baud, timeout=0)
            except Exception:
                self.ser = None

    def read_signal(self) -> float:
        if self.ser is None:
            return 0.0
        try:
            raw = self.ser.readline().strip()
            if not raw:
                return 0.0
            val = float(raw)
            if val < 0: val = 0.0
            if val > 1: val = 1.0
            return val
        except Exception:
            return 0.0

    def get_value01(self) -> float:
        return self.read_signal()

    def get_flap(self) -> bool:
        now_val = self.read_signal()
        t = time.time()
        crossed = (self.prev_val < self.s.rehab_flap_threshold) and (now_val >= self.s.rehab_flap_threshold)
        allowed = (t - self.last_time) >= self.s.rehab_cooldown
        fire = crossed and allowed
        if fire:
            self.last_time = t
        self.prev_val = now_val
        return fire

def make_input(settings: Settings, slider=None) -> InputBase:
    if settings.input_mode == "rehab":
        return RehabFingerInput(settings)
    if settings.input_mode == "slider" and slider is not None:
        return SliderInput(slider)
    return KeyboardInput()

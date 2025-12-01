"""Runtime game settings with disk persistence (settings.json).
Edit settings.json or press F5 in-game to hot-reload.
"""
from __future__ import annotations
import json, os
from dataclasses import dataclass, asdict

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

@dataclass
class Settings:
    # Control & Input
    control_mode: str = "position"   # "flap" | "position"
    input_mode: str = "slider"       # "keyboard" | "rehab" | "slider"
    invert_input: bool = False       # if True, flips 0..1 mapping

    # Rehab serial (used when input_mode == 'rehab')
    rehab_serial_port: str = "COM3"
    rehab_baud: int = 115200
    rehab_flap_threshold: float = 0.65
    rehab_cooldown: float = 0.18

    # Gameplay tuning
    gravity: float = 1200.0
    flap_impulse: float = -320.0
    max_fall_speed: float = 700.0
    ground_height: int = 70
    pipe_gap: int = 160
    pipe_width: int = 60
    pipe_spawn_every: float = 1.25
    pipe_speed: float = -160.0  # negative -> leftwards

    # Difficulty preset name (not enforced, just informational)
    difficulty: str = "normal"  # "easy" | "normal" | "hard"

def load_settings(path: str = DEFAULT_PATH) -> Settings:
    s = Settings()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(s, k):
                    setattr(s, k, v)
    except Exception:
        pass
    return s

def save_settings(s: Settings, path: str = DEFAULT_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(s), f, indent=2)
    except Exception:
        pass

# ---- Persona presets ----
PRESETS = {
    # "slower, bigger gaps"
    "old_lady": {
        "difficulty": "easy",
        "pipe_gap": 210,          # vertical gap between tube openings
        "pipe_speed": -140.0,     # moves left slower (less negative)
        "pipe_spawn_every": 1.60, # more time between pipes (further apart)
    },
    # "a bit faster" (stroke rehab male)
    "stroke_man": {
        "difficulty": "normal",
        "pipe_gap": 170,
        "pipe_speed": -170.0,
        "pipe_spawn_every": 1.30,
    },
    # "hard mode" (young girl)
    "young_girl_hard": {
        "difficulty": "hard",
        "pipe_gap": 130,
        "pipe_speed": -200.0,
        "pipe_spawn_every": 1.00,
    },
}

def apply_preset(s: Settings, preset_key: str) -> Settings:
    d = PRESETS.get(preset_key)
    if not d:
        return s
    for k, v in d.items():
        if hasattr(s, k):
            setattr(s, k, v)
    return s

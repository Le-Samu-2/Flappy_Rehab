Flappy Rehab — Settings System

Now you can change gameplay & input in settings.json and hot-reload with F5.

Key settings (settings.json):
  "control_mode": "position" | "flap"
  "input_mode": "slider" | "keyboard" | "rehab"
  "invert_input": false
  "gravity": 1200.0
  "flap_impulse": -320.0
  "max_fall_speed": 700.0
  "ground_height": 70
  "pipe_gap": 160
  "pipe_width": 60
  "pipe_spawn_every": 1.25
  "pipe_speed": -160.0
  "rehab_serial_port": "COM3"
  "rehab_baud": 115200
  "rehab_flap_threshold": 0.65
  "rehab_cooldown": 0.18

Run:
  pip install pygame pyserial
  python main.py

Controls:
  Drag slider (if input_mode='slider')
  R = restart   |  ESC = quit   |  F5 = reload settings.json

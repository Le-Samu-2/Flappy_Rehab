import pygame as pg
from config import (
    COLOR_BG, WINDOW_H,
    SLIDER_X, SLIDER_TOP, SLIDER_WIDTH, SLIDER_HANDLE_H
)
from graphics import draw_hud_text
from ui import VerticalSlider, Button, draw_label
from entities import Bird, PipeManager, Ground
from input import make_input
from settings import load_settings, save_settings, apply_preset

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.settings = load_settings()

        # Slider (for slider input testing)
        slider_bottom = WINDOW_H - self.settings.ground_height - 20
        self.slider = VerticalSlider(SLIDER_X, SLIDER_TOP, slider_bottom, SLIDER_WIDTH, SLIDER_HANDLE_H, value=0.5)

        sw, sh = self.screen.get_size()
        cx = sw // 2
        bw, bh = 220, 44  # slimmer buttons

        # ---- MENU buttons ----
        self.btn_start    = Button((cx - bw//2, 200, bw, bh), "Start", self._action_start)
        self.btn_settings = Button((cx - bw//2, 260, bw, bh), "Settings", self._action_go_settings)
        self.btn_quit     = Button((cx - bw//2, 320, bw, bh), "Quit", self._action_quit)

        # ---- SETTINGS buttons ----
        self.btn_ctrl  = Button((cx - bw//2, 180, bw, bh),
                                f"control_mode: {self.settings.control_mode}", self._toggle_control_mode)
        self.btn_input = Button((cx - bw//2, 240, bw, bh),
                                f"input_mode: {self.settings.input_mode}", self._toggle_input_mode)

        # single preset cycler
        self._preset_order = ["old_lady", "stroke_man", "young_girl_hard"]
        self._preset_idx = 0
        self.btn_preset = Button(
            (cx - bw//2, 300, bw, bh),
            f"Preset: {self._preset_label(self._preset_order[self._preset_idx])}",
            self._cycle_preset
        )

        # apply/back
        self.btn_apply = Button((cx - bw//2, WINDOW_H - 100, bw, bh), "Apply & Back", self._apply_and_back)
        self.btn_back  = Button((20,            WINDOW_H - 50,  140, 40), "Back", self._action_go_menu)

        self.scene = "menu"    # "menu" | "settings" | "playing" | "dead"
        self._running = True
        self.input = None
        self.reset()

    # ---------- helpers for preset cycler ----------
    def _preset_label(self, key: str) -> str:
        return {
            "old_lady": "Easy (Old Lady)",
            "stroke_man": "Normal (Stroke Man)",
            "young_girl_hard": "Hard (Young Girl)",
        }.get(key, key)

    def _cycle_preset(self):
        self._preset_idx = (self._preset_idx + 1) % len(self._preset_order)
        key = self._preset_order[self._preset_idx]
        apply_preset(self.settings, key)
        # refresh button labels
        self.btn_preset.label = f"Preset: {self._preset_label(key)}"
        self.btn_ctrl.label   = f"control_mode: {self.settings.control_mode}"
        self.btn_input.label  = f"input_mode: {self.settings.input_mode}"

    # ---------- actions ----------
    def _action_start(self):
        self.scene = "playing"
        self.input = make_input(self.settings, slider=self.slider)
        self.reset()

    def _action_go_settings(self):
        self.scene = "settings"

    def _action_go_menu(self):
        self.scene = "menu"

    def _action_quit(self):
        self._running = False

    def _toggle_control_mode(self):
        self.settings.control_mode = "flap" if self.settings.control_mode == "position" else "position"
        self.btn_ctrl.label = f"control_mode: {self.settings.control_mode}"

    def _toggle_input_mode(self):
        order = ["slider", "keyboard", "rehab"]
        i = order.index(self.settings.input_mode) if self.settings.input_mode in order else 0
        self.settings.input_mode = order[(i + 1) % len(order)]
        self.btn_input.label = f"input_mode: {self.settings.input_mode}"

    def _apply_and_back(self):
        save_settings(self.settings)
        self._hot_reload_settings()
        self.scene = "menu"

    # ---------- core ----------
    def reset(self):
        w, h = self.screen.get_size()
        self.bird = Bird(self.settings)
        self.ground = Ground(w, h, self.settings)
        self.pipes = PipeManager(w, h, self.settings)
        self.score = 0
        if self.scene == "playing":
            v = self._read_input_value()
            self.bird.rect.centery = self._target_from_input_value(v)
            self.bird.vy = 0.0

    def _read_input_value(self) -> float:
        v = 0.0
        if self.input and hasattr(self.input, "get_value01"):
            v = float(self.input.get_value01())
        if getattr(self.settings, "invert_input", False):
            v = 1.0 - v
        return max(0.0, min(1.0, v))

    def _target_from_input_value(self, v01: float) -> int:
        playable_top = 0
        playable_bot = WINDOW_H - self.settings.ground_height
        return int(playable_bot - v01 * (playable_bot - playable_top))

    def _hot_reload_settings(self):
        self.settings = load_settings()
        self.slider.bottom = WINDOW_H - self.settings.ground_height - 20
        self.ground.settings = self.settings
        self.pipes.settings  = self.settings
        self.bird.settings   = self.settings

    # ---------- loop ----------
    def update(self, dt: float) -> bool:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._running = False

            if self.scene == "menu":
                self.btn_start.handle_event(event)
                self.btn_settings.handle_event(event)
                self.btn_quit.handle_event(event)

            elif self.scene == "settings":
                self.btn_ctrl.handle_event(event)
                self.btn_input.handle_event(event)
                self.btn_preset.handle_event(event)
                self.btn_apply.handle_event(event)
                self.btn_back.handle_event(event)

            elif self.scene == "playing":
                self.slider.handle_event(event)

        keys = pg.key.get_pressed()
        mods = pg.key.get_mods()
        if keys[pg.K_ESCAPE]:
            if self.scene == "playing":
                self.scene = "menu"
            else:
                self._running = False
        if keys[pg.K_s] and (mods & pg.KMOD_SHIFT):
            self._hot_reload_settings()
        elif keys[pg.K_s]:
            self.scene = "settings"


        if self.scene == "playing":
            if self.input is None:
                self.input = make_input(self.settings, slider=self.slider)

            if self.settings.control_mode == "position" and hasattr(self.input, "get_value01"):
                v = self._read_input_value()
                target_y = self._target_from_input_value(v)
                self.bird.update_position_control(dt, target_y)
            else:
                flap = getattr(self.input, "get_flap", lambda: False)()
                self.bird.update(dt, flap)

            self.pipes.update(dt)
            self.ground.update(dt)
            self.score += self.pipes.count_passed(self.bird.rect)

            if self.pipes.collides(self.bird.rect) or self.ground.collides(self.bird.rect):
                self.scene = "dead"

        elif self.scene == "dead":
            if keys[pg.K_r]:
                self.scene = "playing"
                self.reset()

        return self._running

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.scene in ("playing", "dead"):
            self.pipes.draw(self.screen)
            self.ground.draw(self.screen)
            self.bird.draw(self.screen)
            self.slider.draw(self.screen)
            title = "FLAPPY REHAB"
            hint = "Drag slider • R restart • ESC menu • S reload settings"
            if self.scene == "dead":
                hint = "Crashed! Press R to restart or ESC for menu"
            draw_hud_text(self.screen, title, 18, (10, 8), color=(200, 230, 255))
            draw_hud_text(self.screen, f"Score: {self.score}", 22, (10, 30))
            draw_hud_text(self.screen, hint, 14, (10, WINDOW_H - 24), color=(180, 200, 220))

        elif self.scene == "menu":
            self._draw_title("FLAPPY REHAB — Menu")
            self.btn_start.draw(self.screen)
            self.btn_settings.draw(self.screen)
            self.btn_quit.draw(self.screen)
            draw_hud_text(self.screen, "Start the game or open Settings for presets.", 14, (10, WINDOW_H - 24))

        elif self.scene == "settings":
            self._draw_title("Settings")
            self.btn_ctrl.draw(self.screen)
            self.btn_input.draw(self.screen)
            self.btn_preset.draw(self.screen)
            # live readout of the three preset-driven settings
            cx = self.screen.get_width() // 2
            draw_label(self.screen, f"Pipe Gap: {int(self.settings.pipe_gap)} px", cx, 360)
            draw_label(self.screen, f"Pipe Speed: {int(self.settings.pipe_speed)} px/s", cx, 390)
            draw_label(self.screen, f"Spawn Every: {self.settings.pipe_spawn_every:.2f} s", cx, 420)
            self.btn_apply.draw(self.screen)
            self.btn_back.draw(self.screen)

    def _draw_title(self, text):
        font = pg.font.SysFont("arial", 28)
        img = font.render(text, True, (220, 235, 250))
        r = img.get_rect(center=(self.screen.get_width()//2, 120))
        self.screen.blit(img, r)

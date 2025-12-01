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
        bw, bh = 220, 44  # slimmer buttons to avoid overlap

        # ---- MENU buttons ----
        self.btn_start    = Button((cx - bw//2, 200, bw, bh), "Start", self._action_start)
        self.btn_settings = Button((cx - bw//2, 260, bw, bh), "Settings", self._action_go_settings)
        self.btn_quit     = Button((cx - bw//2, 320, bw, bh), "Quit", self._action_quit)

        # ---- SETTINGS buttons (basic) ----
        self.btn_ctrl   = Button((cx - bw//2, 180, bw, bh), f"control_mode: {self.settings.control_mode}", self._toggle_control_mode)
        self.btn_input  = Button((cx - bw//2, 240, bw, bh), f"input_mode: {self.settings.input_mode}", self._toggle_input_mode)

        # ---- PERSONA preset buttons ----
        y0 = 320
        self.btn_preset_easy  = Button((cx - bw//2, y0,     bw, bh), "Preset: Old Lady (easy)", lambda: self._apply_preset("old_lady"))
        self.btn_preset_mid   = Button((cx - bw//2, y0+60,  bw, bh), "Preset: Stroke Man (normal+)", lambda: self._apply_preset("stroke_man"))
        self.btn_preset_hard  = Button((cx - bw//2, y0+120, bw, bh), "Preset: Young Girl (hard)", lambda: self._apply_preset("young_girl_hard"))
        self.btn_advanced     = Button((cx - bw//2, y0+180, bw, bh), "Advanced…", self._action_go_advanced)

        # moved to give clear spacing from Back
        self.btn_apply  = Button((cx - bw//2, WINDOW_H - 100, bw, bh), "Apply & Back", self._apply_and_back)
        self.btn_back   = Button((20,             WINDOW_H - 50, 140, 40), "Back", self._action_go_menu)

        # ---- ADVANCED steppers (gap/speed/spawn) ----
        ax = cx
        ay = 180
        step = 70
        self._adv_widgets = []
        def make_stepper(label_get, minus_cb, plus_cb, row):
            y = ay + row*step
            w = 50
            btn_minus = Button((ax - 140, y, w, 40), "–", minus_cb)
            btn_plus  = Button((ax + 90,  y, w, 40), "+", plus_cb)
            self._adv_widgets.append((label_get, btn_minus, btn_plus, y))

        # pipe_gap (vertical opening)
        make_stepper(
            lambda: f"Pipe Gap: {int(self.settings.pipe_gap)} px",
            lambda: self._nudge("pipe_gap", -10, 100, 260, int),
            lambda: self._nudge("pipe_gap", +10, 100, 260, int),
            0
        )
        # pipe_speed (horizontal velocity; more negative = faster)
        make_stepper(
            lambda: f"Pipe Speed: {int(self.settings.pipe_speed)} px/s",
            lambda: self._nudge("pipe_speed", +10, -260, -100, float),  # +10 -> less negative -> slower
            lambda: self._nudge("pipe_speed", -10, -260, -100, float),  # -10 -> more negative -> faster
            1
        )
        # pipe_spawn_every (time between pipes)
        make_stepper(
            lambda: f"Spawn Every: {self.settings.pipe_spawn_every:.2f} s",
            lambda: self._nudge("pipe_spawn_every", +0.10, 0.80, 2.00, float), # more seconds -> further apart
            lambda: self._nudge("pipe_spawn_every", -0.10, 0.80, 2.00, float), # fewer seconds -> closer
            2
        )

        self.scene = "menu"    # "menu" | "settings" | "advanced" | "playing" | "dead"
        self._running = True
        self.input = None
        self.reset()

    # ---------- actions ----------
    def _apply_preset(self, key: str):
        apply_preset(self.settings, key)
        self.btn_ctrl.label  = f"control_mode: {self.settings.control_mode}"
        self.btn_input.label = f"input_mode: {self.settings.input_mode}"

    def _action_go_advanced(self):
        self.scene = "advanced"

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

    # ---------- advanced nudging ----------
    def _nudge(self, field, delta, lo, hi, cast):
        v = getattr(self.settings, field)
        v = cast(max(lo, min(hi, v + delta)))
        setattr(self.settings, field, v)

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
        self.pipes.settings = self.settings
        self.bird.settings = self.settings

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
                self.btn_preset_easy.handle_event(event)
                self.btn_preset_mid.handle_event(event)
                self.btn_preset_hard.handle_event(event)
                self.btn_advanced.handle_event(event)
                self.btn_apply.handle_event(event)
                self.btn_back.handle_event(event)

            elif self.scene == "advanced":
                for _, minus_btn, plus_btn, _y in self._adv_widgets:
                    minus_btn.handle_event(event)
                    plus_btn.handle_event(event)
                self.btn_apply.handle_event(event)
                self.btn_back.handle_event(event)

            elif self.scene == "playing":
                self.slider.handle_event(event)

        keys = pg.key.get_pressed()
        if keys[pg.K_ESCAPE]:
            if self.scene == "playing":
                self.scene = "menu"
            else:
                self._running = False
        if keys[pg.K_F5]:
            self._hot_reload_settings()

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
            hint = "Drag slider • R restart • ESC menu • F5 reload settings"
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
            self.btn_preset_easy.draw(self.screen)
            self.btn_preset_mid.draw(self.screen)
            self.btn_preset_hard.draw(self.screen)
            self.btn_advanced.draw(self.screen)
            self.btn_apply.draw(self.screen)
            self.btn_back.draw(self.screen)

        elif self.scene == "advanced":
            self._draw_title("Advanced")
            for label_get, minus_btn, plus_btn, y in self._adv_widgets:
                draw_label(self.screen, label_get(), self.screen.get_width()//2, y-28)
                minus_btn.draw(self.screen)
                plus_btn.draw(self.screen)
            self.btn_apply.draw(self.screen)
            self.btn_back.draw(self.screen)

    def _draw_title(self, text):
        font = pg.font.SysFont("arial", 28)
        img = font.render(text, True, (220, 235, 250))
        r = img.get_rect(center=(self.screen.get_width()//2, 120))
        self.screen.blit(img, r)

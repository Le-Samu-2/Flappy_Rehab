import pygame as pg
from pygame import Rect
from settings import Settings
from config import COLOR_BIRD, COLOR_PIPE, COLOR_GROUND

class Bird:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.rect = Rect(100, 260, 28, 22)
        self.vy = 0.0
        self.alive = True

    def update(self, dt: float, flap: bool):
        if flap:
            self.vy = self.settings.flap_impulse
        self.vy += self.settings.gravity * dt
        if self.vy > self.settings.max_fall_speed:
            self.vy = self.settings.max_fall_speed
        self.rect.y += int(self.vy * dt)
        if self.rect.top < 0:
            self.rect.top = 0
            self.vy = 0

    def update_position_control(self, dt: float, target_y: int):
        follow_speed = 12.0
        y = float(self.rect.centery)
        y += (target_y - y) * min(1.0, dt * follow_speed)
        self.rect.centery = int(y)
        self.vy = 0.0

    def draw(self, surf: pg.Surface):
        pg.draw.rect(surf, COLOR_BIRD, self.rect, border_radius=6)
        wing = self.rect.copy()
        wing.width = max(8, self.rect.width // 3)
        wing.height = 6
        wing.centerx = self.rect.centerx - 4
        wing.centery = self.rect.centery + 2
        pg.draw.rect(surf, (255, 240, 140), wing, border_radius=3)

class PipeManager:
    def __init__(self, w: int, h: int, settings: Settings):
        self.w, self.h = w, h
        self.settings = settings
        self.t = 0.0
        self.pipes = []  # [top_rect, bot_rect, passed]

    def spawn(self):
        from random import randint
        gh = self.settings.ground_height
        gap = self.settings.pipe_gap
        gap_y = randint(120, self.h - gh - 120)
        top_rect = Rect(self.w, 0, self.settings.pipe_width, gap_y - gap // 2)
        bot_rect = Rect(self.w, gap_y + gap // 2, self.settings.pipe_width, self.h - gh - (gap_y + gap // 2))
        self.pipes.append([top_rect, bot_rect, False])

    def update(self, dt: float):
        self.t += dt
        if self.t >= self.settings.pipe_spawn_every:
            self.t -= self.settings.pipe_spawn_every
            self.spawn()
        dx = int(self.settings.pipe_speed * dt)
        for p in self.pipes:
            p[0].x += dx
            p[1].x += dx
        self.pipes = [p for p in self.pipes if p[0].right > -10]

    def draw(self, surf: pg.Surface):
        for top, bot, _ in self.pipes:
            pg.draw.rect(surf, COLOR_PIPE, top, border_radius=6)
            pg.draw.rect(surf, COLOR_PIPE, bot, border_radius=6)

    def collides(self, rect: Rect) -> bool:
        return any(rect.colliderect(top) or rect.colliderect(bot) for top, bot, _ in self.pipes)

    def count_passed(self, rect: Rect) -> int:
        gained = 0
        for i in range(len(self.pipes)):
            top, bot, passed = self.pipes[i]
            if not passed and top.right < rect.left:
                self.pipes[i][2] = True
                gained += 1
        return gained

class Ground:
    def __init__(self, w: int, h: int, settings: Settings):
        self.w, self.h = w, h
        self.settings = settings
        self.rect = Rect(0, h - settings.ground_height, w, settings.ground_height)
        self.scroll = 0.0

    def update(self, dt: float):
        self.scroll += -self.settings.pipe_speed * dt * 0.25
        if self.scroll > 32:
            self.scroll -= 32
        self.rect.height = self.settings.ground_height
        self.rect.top = self.h - self.settings.ground_height

    def draw(self, surf: pg.Surface):
        pg.draw.rect(surf, COLOR_GROUND, self.rect)
        tile_w = 32
        y = self.rect.top + 8
        for i in range(0, self.w + tile_w, tile_w):
            pg.draw.rect(surf, (120, 95, 70), (i - int(self.scroll) % tile_w, y, tile_w // 2, 10), border_radius=3)

    def collides(self, rect: Rect) -> bool:
        return rect.colliderect(self.rect)

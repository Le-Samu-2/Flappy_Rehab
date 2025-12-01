import pygame as pg
from config import COLOR_FG

_font_cache = {}

def get_font(size: int) -> pg.font.Font:
    key = size
    f = _font_cache.get(key)
    if f is None:
        f = pg.font.SysFont("arial", size)
        _font_cache[key] = f
    return f

def draw_hud_text(surf: pg.Surface, text: str, size: int, pos: tuple[int, int], color=COLOR_FG):
    font = get_font(size)
    img = font.render(text, True, color)
    surf.blit(img, pos)

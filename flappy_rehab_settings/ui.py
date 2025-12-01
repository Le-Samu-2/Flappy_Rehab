import pygame as pg

class VerticalSlider:
    """Value in [0..1], 0 at bottom, 1 at top."""
    def __init__(self, x, top, bottom, track_w=12, handle_h=20, value=0.5):
        self.x, self.top, self.bottom = x, top, bottom
        self.track_w, self.handle_h = track_w, handle_h
        self.value = value
        self.dragging = False

    def _value_to_y(self):
        h = self.bottom - self.top
        return int(self.bottom - self.value * h)

    def _y_to_value(self, y):
        y = max(self.top, min(self.bottom, y))
        h = self.bottom - self.top
        return (self.bottom - y) / h if h > 0 else 0.0

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if abs(mx - self.x) <= max(12, self.track_w) and self.top <= my <= self.bottom:
                self.dragging = True
                self.value = self._y_to_value(my)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION and self.dragging:
            _, my = event.pos
            self.value = self._y_to_value(my)

    def update(self, dt):
        pass

    def draw(self, surf):
        # track
        pg.draw.rect(surf, (200, 210, 230),
                     (self.x - self.track_w//2, self.top, self.track_w, self.bottom - self.top), border_radius=6)
        # handle
        y = self._value_to_y()
        pg.draw.rect(surf, (255, 230, 120),
                     (self.x - self.track_w, y - self.handle_h//2, self.track_w*2, self.handle_h), border_radius=6)
        # ticks
        for t in (0.0, 0.5, 1.0):
            ty = int(self.bottom - t * (self.bottom - self.top))
            pg.draw.line(surf, (160, 170, 185), (self.x - 16, ty), (self.x + 16, ty), 1)

class Button:
    def __init__(self, rect, label, on_click=None):
        import pygame as pg
        self.rect = pg.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.hover = False

    def handle_event(self, event):
        import pygame as pg
        if event.type == pg.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.on_click:
                self.on_click()

    def draw(self, surf):
        import pygame as pg
        bg = (70, 90, 110) if not self.hover else (90, 115, 140)
        pg.draw.rect(surf, bg, self.rect, border_radius=10)
        pg.draw.rect(surf, (200, 220, 240), self.rect, width=2, border_radius=10)
        # label
        font = pg.font.SysFont("arial", 20)
        img = font.render(self.label, True, (240, 250, 255))
        r = img.get_rect(center=self.rect.center)
        surf.blit(img, r)

def draw_label(surf, text, center_x, y):
    import pygame as pg
    font = pg.font.SysFont("arial", 20)
    img = font.render(text, True, (220, 235, 250))
    rect = img.get_rect(midtop=(center_x, y))
    surf.blit(img, rect)

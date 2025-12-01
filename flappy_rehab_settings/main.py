import pygame as pg
from game import Game
from config import WINDOW_SIZE, FPS

def main():
    pg.init()
    pg.display.set_caption("Flappy Rehab — Settings Enabled")
    screen = pg.display.set_mode(WINDOW_SIZE)
    clock = pg.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds
        running = game.update(dt)
        game.draw()
        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()

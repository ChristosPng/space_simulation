"used for making the background stars look dynamic and not static"

import random

class ParallaxStars:

    LAYERS = [
        (160, 0.02, 0.05, 1, 120),    # far
        (100, 0.06, 0.12, 2, 180),    # middle
        (50,  0.14, 0.22, 3, 240),    # near
    ]

    def __init__(self, width, height, seed=None):
        self.w = width
        self.h = height
        self.tile = max(width, height) * 1.25
        rnd = random.Random(seed)

        self.layers = []

        for on_screen, pan, zexp, max_size, bright in self.LAYERS:
            count = int(on_screen * self.tile * self.tile / (width * height))
            stars = []
            for _ in range (count):
                x = rnd.uniform(0, self.tile)
                y = rnd.uniform(0, self.tile)
                size = rnd.randint(1, max_size)
                b = int(bright * rnd.uniform(0.6, 1.0))
                stars.append((x, y, size, (b, b, b)))
            self.layers.append((pan, zexp, stars))

    def draw(self, screen, camera_x, camera_y, zoom):
        w, h = self.w, self.h
        hw, hh = w / 2, h / 2

        for pan, zexp, stars in self.layers:
            s = zoom ** zexp
            period = self.tile * s
            cx = camera_x * pan
            cy = camera_y * pan

            for x, y, size, color in stars:
                x0 = ((x - cx) * s + hw) % period
                y0 = ((y - cy) * s + hh) % period
                px = x0
                while px < w:
                    py = y0
                    while py < h:
                        screen.fill(color, (int(px), int(py), size, size))
                        py += period
                    px += period
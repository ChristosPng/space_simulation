import pygame
import math

class CelestialBody:
    def __init__(self, name, mass, radius, color, position, immovable=False, spin_rate=20):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.color = color
        self.position = position[:]
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.immovable = immovable
        self.age = 0
        self.angle = 0.0
        self.spin_rate = spin_rate

    def apply_force(self, force):
        if self.immovable: return
        self.acceleration[0] += force[0] / self.mass
        self.acceleration[1] += force[1] / self.mass

    def update(self, dt):
        self.age += dt
        self.angle = (self.angle + self.spin_rate * dt) % 360.0

    def draw(self, screen, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        # basic position calculation for everything
        screen_x = (self.position[0] - offset_x) * zoom + WIDTH // 2
        screen_y = (self.position[1] - offset_y) * zoom + HEIGHT // 2
        scaled_radius = max(1, int(self.radius * zoom))

        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)        
        return screen_x, screen_y, scaled_radius

    def draw_trail(self, screen, zoom, offset_x, offset_y, WIDTH, HEIGHT, step=4, segs=4):
        pts = [((p[0] - offset_x) * zoom + WIDTH // 2,
                (p[1] - offset_y) * zoom + HEIGHT // 2) for p in self.trail[::step]]
        n = len(pts)
        for s in range(segs):
            seg = pts[s * n // segs : (s + 1) * n // segs + 1]
            if len(seg) > 1:
                shade = int(255 * (s + 1) / segs)
                pygame.draw.lines(screen, (shade, shade, shade), False, seg, 1)
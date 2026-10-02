import pygame
import math

class CelestialBody:
    def __init__(self, name, mass, radius, color, position, immovable=False):
        self.name = name
        self.mass = mass
        self.radius = radius
        self.color = color
        self.position = position[:]
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.immovable = immovable
        self.age = 0

    def apply_force(self, force):
        if self.immovable: return
        self.acceleration[0] += force[0] / self.mass
        self.acceleration[1] += force[1] / self.mass

    def update(self, dt):
        self.age += dt

    def draw(self, screen, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        # Basic position calculation for everything
        screen_x = (self.position[0] - offset_x) * zoom + WIDTH // 2
        screen_y = (self.position[1] - offset_y) * zoom + HEIGHT // 2
        scaled_radius = max(1, int(self.radius * zoom))
        
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)
        return screen_x, screen_y, scaled_radius
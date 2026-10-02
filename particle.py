import pygame
import math
import random

class Particle:
    def __init__(self, x, y, color):
        self.x = x 
        self.y = y
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(2, 5)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        self.life = 255
        self.decay = random.uniform(3, 7)
        self.size = random.randint(2, 4)
        self.surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (*self.color, 255), (self.size, self.size), self.size)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, screen, zoom, camera_x, camera_y, WIDTH, HEIGHT):
        screen_x = (self.x - camera_x) * zoom + WIDTH // 2
        screen_y = (self.y - camera_y) * zoom + HEIGHT // 2

        if self.life > 0:
            self.surf.set_alpha(max(0, int(self.life)))
            screen.blit(self.surf, (screen_x - self.size, screen_y - self.size))



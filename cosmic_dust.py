import random
import pygame

class CosmicDust:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.1, 0.5)

    def update(self):
        self.y -= self.speed
        if self.y < 0:  
            self.y = self.height
            self.x = random.randint(0, self.width)  
        
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size)
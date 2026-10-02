from celestial_body import CelestialBody
import pygame
import math
from helper import Helper

_shadow_cache = {}

def _get_shadow(sr):
    s = _shadow_cache.get(sr)
    if s is None:
        s = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 0, 0, 180), (sr, sr), sr)
        _shadow_cache[sr] = s
    return s

class Star(CelestialBody):
    def __init__(self, name, mass, radius, color, position):
        super().__init__(name, mass, radius, color, position, immovable=False)
        self.lifetime = 10000
        self.trail = []
        self.max_trail_length = 400

    def update(self, dt):
        super().update(dt)
        # store trail positions
        self.trail.append(self.position[:])
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def draw(self, screen, bodies, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        # draw color based on age
        t = min(self.age / self.lifetime, 1.0)
        if t < 0.33:
            self.color = (255, int(255 * (1 - t / 0.33)), 0)
        elif t < 0.66:
            self.color = (int(255 * (1 - (t - 0.33)/0.33)), 0, int(255 * ((t - 0.33)/0.33)))
        else:
            self.color = (int(150 + 105*(t-0.66)/0.34), int(200 + 55*(t-0.66)/0.34), 255)

        # draw star 
        super().draw(screen, zoom, offset_x, offset_y, WIDTH, HEIGHT)

        for idx, pos in enumerate(self.trail):
            tx = (pos[0] - offset_x) * zoom + WIDTH // 2
            ty = (pos[1] - offset_y) * zoom + HEIGHT // 2
            alpha = int(255 * (idx / len(self.trail)))
            pygame.draw.circle(screen, (alpha, alpha, alpha), (int(tx), int(ty)), max(1, int(1 * zoom)))

class Planet(CelestialBody):
    def __init__(self, name, mass, radius, color, position):
        super().__init__(name, mass, radius, color, position)
        self.trail = []
        self.max_trail_length = 400
        self.closest_star = None

    def update(self, dt):
        super().update(dt)
        # Store trail positions
        self.trail.append(self.position[:])
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def draw(self, screen, bodies, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        # draw trail
        self.draw_trail(screen, zoom, offset_x, offset_y, WIDTH, HEIGHT)

        # draw planet
        sx, sy, sr = super().draw(screen, zoom, offset_x, offset_y, WIDTH, HEIGHT)

        min_dist = float('inf')
        for body in bodies:
            if isinstance(body, Star):
                dx = body.position[0] - self.position[0]
                dy = body.position[1] - self.position[1]
                dist = math.sqrt(dx**2 + dy**2)
                if dist < min_dist:
                    min_dist = dist
                    self.closest_star = body

        # draw shadow
        if self.closest_star:
            dx, dy = self.closest_star.position[0] - self.position[0], self.closest_star.position[1] - self.position[1]
            dist = max(math.sqrt(dx**2 + dy**2), 1)
            # Offset shadow in opposite direction of sun
            sh_x = sx - (dx / dist) * (sr * 0.8)
            sh_y = sy - (dy / dist) * (sr * 0.8)
            
            screen.blit(_get_shadow(sr), (sh_x - sr, sh_y - sr))

class BlackHole(CelestialBody):
    def __init__(self, name, mass, radius, color, position):
        super().__init__(name, mass, radius, (0,0,0), position)
        self.event_horizon = radius * 3
        self.is_static = False

    def update(self, dt):
        if not self.is_static:
            super().update(dt)

        self.radius = self.mass * 0.0001 
        self.event_horizon = self.radius * 3

    def attract(self, bodies):

        removed_bodies = []
        for body in bodies:
            if body is self or isinstance(body, BlackHole):
                continue
            dx = self.position[0] - body.position[0]
            dy = self.position[1] - body.position[1]
            dist = math.sqrt(dx**2 + dy**2)

            if dist < self.event_horizon:
                self.mass += body.mass
                print(f"{body.name} was consumed by {self.name}!")
                removed_bodies.append(body)

        return removed_bodies

    def draw(self, screen, sun, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        screen_x = int((self.position[0] - offset_x) * zoom + WIDTH // 2)
        screen_y = int((self.position[1] - offset_y) * zoom + HEIGHT // 2)

        core_radius = max(1, int(self.radius * zoom))
        horizon_radius = max(2, int(self.event_horizon * zoom))
        glow_radius = int(horizon_radius * 1.5)

        glow_surf = Helper.create_glow_surface(glow_radius, (255, 140, 0), 150)
        screen.blit(glow_surf, (screen_x - glow_radius * 2, screen_y - glow_radius * 2))

        pygame.draw.circle(screen, (20, 20, 20), (screen_x, screen_y), horizon_radius)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), core_radius)

class Moon(Planet):
    def __init__(self, name, mass, radius, color, position, orb_planet=None):
        super().__init__(name, mass, radius, color, position)
        self.orb_planet = orb_planet

    def draw(self, screen, sun, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        super().draw(screen, sun, zoom, offset_x, offset_y, WIDTH, HEIGHT)

    def update(self, dt):
        super().update(dt)


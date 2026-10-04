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

STAR_STAGES = [
    (0.00, (255, 235, 140)),   # young: bright yellow
    (0.35, (255, 170,  60)),   # mature: orange
    (0.65, (230,  60,  40)),   # red giant
    (0.85, (255, 225, 200)),   # collapsing: hot pale cream
    (1.00, (170, 200, 255)),   # white dwarf: blue-white
]

def star_color(t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(STAR_STAGES, STAR_STAGES[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))
    return STAR_STAGES[-1][1]

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
        self.color = star_color(self.age / self.lifetime)

        sx = int((self.position[0] - offset_x) * zoom + WIDTH // 2)
        sy = int((self.position[1] - offset_y) * zoom + HEIGHT // 2)
        glow_r = int(max(1, self.radius * zoom) * 2.2)
        if 6 <= glow_r <= 300:                       # skip when tiny or huge (zoomed way in)
            q = tuple((c // 16) * 16 for c in self.color)   # quantize so the glow cache isn't rebuilt every frame
            glow = Helper.create_glow_surface(glow_r, q, 110)
            screen.blit(glow, (sx - glow_r, sy - glow_r))

        self.draw_trail(screen, zoom, offset_x, offset_y, WIDTH, HEIGHT)

        # draw star 
        super().draw(screen, zoom, offset_x, offset_y, WIDTH, HEIGHT)

        
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
        self.base_radius = radius       
        self.base_mass = mass
        self.event_horizon = radius * 3
        self.is_static = False

    def update(self, dt):
        if not self.is_static:
            super().update(dt)

        self.radius = self.base_radius * self.mass / self.base_mass
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

    def draw(self, screen, bodies, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        screen_x = int((self.position[0] - offset_x) * zoom + WIDTH // 2)
        screen_y = int((self.position[1] - offset_y) * zoom + HEIGHT // 2)

        core_radius = max(1, int(self.radius * zoom))
        horizon_radius = max(2, int(self.event_horizon * zoom))
        glow_radius = int(horizon_radius * 1.5)

        glow_surf = Helper.create_glow_surface(glow_radius, (255, 140, 0), 150)
        screen.blit(glow_surf, (screen_x - glow_radius, screen_y - glow_radius))

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


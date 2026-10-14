import pygame
import math

VISUAL_SPIN_SCALE = 0.12   
MAX_VISUAL_SPIN = 3.0
VISUAL_TIME_SCALE = 0.2
MAX_VISUAL_TIME = 0.04

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
        self.visual_angle = 0.0
        self.visual_t = 0.0

    def apply_force(self, force):
        if self.immovable: return
        self.acceleration[0] += force[0] / self.mass
        self.acceleration[1] += force[1] / self.mass

    def update(self, dt):
        self.age += dt
        self.angle = (self.angle + self.spin_rate * dt) % 360.0
        step = max(-MAX_VISUAL_SPIN, min(MAX_VISUAL_SPIN, self.spin_rate * dt * VISUAL_SPIN_SCALE))
        self.visual_angle = (self.visual_angle + step) % 360.0
        self.visual_t += min(dt * VISUAL_TIME_SCALE, MAX_VISUAL_TIME)

    def draw(self, screen, zoom, offset_x, offset_y, WIDTH, HEIGHT):
        # basic position calculation for everything
        screen_x = (self.position[0] - offset_x) * zoom + WIDTH // 2
        screen_y = (self.position[1] - offset_y) * zoom + HEIGHT // 2
        scaled_radius = max(1, int(self.radius * zoom))

        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)        
        return screen_x, screen_y, scaled_radius

    def draw_trail(self, screen, zoom, offset_x, offset_y, WIDTH, HEIGHT, step=4, segs=4):
        if not hasattr(self, 'trail') or len(self.trail) < 2: 
            return
            
        current_screen_x = (self.position[0] - offset_x) * zoom + WIDTH // 2
        current_screen_y = (self.position[1] - offset_y) * zoom + HEIGHT // 2
        scaled_radius = max(1, self.radius * zoom)

        valid_pts = []
        for p in self.trail:
            px = (p[0] - offset_x) * zoom + WIDTH // 2
            py = (p[1] - offset_y) * zoom + HEIGHT // 2
            if math.hypot(px - current_screen_x, py - current_screen_y) > scaled_radius:
                valid_pts.append((px, py))
                
        if not valid_pts:
            return
            
        last_px, last_py = valid_pts[-1]
        dx = current_screen_x - last_px
        dy = current_screen_y - last_py
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            edge_x = current_screen_x - (dx / dist) * scaled_radius
            edge_y = current_screen_y - (dy / dist) * scaled_radius
            valid_pts.append((edge_x, edge_y))

        n = len(valid_pts)
        if n < 2: 
            return

        for s in range(segs):
            seg = valid_pts[s * n // segs : (s + 1) * n // segs + 1]
            if len(seg) > 1:
                shade = int(255 * (s + 1) / segs)
                pygame.draw.lines(screen, (shade, shade, shade), False, seg, 1)